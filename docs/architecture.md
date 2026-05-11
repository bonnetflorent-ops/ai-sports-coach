# Architecture Technique — AI Sports Coach

## Stack

```
┌─────────────────────────────────────────────────────┐
│                    Télégramme                        │
│              @TonCoachBot (multi-tenant)             │
└──────────────┬──────────────────────────────────────┘
               │ webhooks (HTTPS)
┌──────────────▼──────────────────────────────────────┐
│                    FastAPI                            │
│   - Webhooks Telegram                                │
│   - API admin (CRUD users, plans, analytics)        │
│   - Portail web futur (React)                        │
└──────┬──────────────────────┬───────────────────────┘
       │                      │
┌──────▼──────────┐   ┌──────▼───────────────────────┐
│    aiogram 3    │   │     Coach Logic Engine        │
│  - Dispatcher   │   │  - Router requêtes           │
│  - Middleware    │   │  - RAG (pgvector)           │
│  - Sessions      │   │  - Prompt builder            │
│  - States (FSM)  │   │  - Safety handler            │
└──────┬──────────┘   └──────┬───────────────────────┘
       │                      │
       │    ┌─────────────────▼───────────────────────┐
       │    │           OpenRouter API                  │
       │    │      DeepSeek V4 (modèle principal)      │
       │    └─────────────────┬───────────────────────┘
       │                      │
┌──────▼──────────────────────▼───────────────────────┐
│                  Supabase (PostgreSQL)                │
│  - Données utilisateurs                              │
│  - Historique entraînements                          │
│  - Conversations                                     │
│  - pgvector (embeddings base connaissances)          │
│  - Auth + RLS (isolation utilisateurs)               │
│  - Storage (fichiers, exports)                       │
└─────────────────────────────────────────────────────┘
```

## Multi-tenant expliqué

Un seul bot Telegram (@TonCoachBot) sert tous les utilisateurs. L'isolation est garantie à deux niveaux :

### Niveau applicatif (aiogram)
```python
# Middleware qui injecte l'utilisateur dans chaque handler
class UserMiddleware(BaseMiddleware):
    async def __call__(self, handler, event, data):
        user_id = event.from_user.id  # ID Telegram unique
        user = await db.get_user(user_id)
        data["user"] = user  # Injecté dans tous les handlers
        return await handler(event, data)
```

Chaque message entrant est taggé avec l'ID Telegram de l'expéditeur. Le handler ne voit que les données de CET utilisateur.

### Niveau base de données (Supabase RLS)
```sql
-- Exemple : Row Level Security sur la table conversations
ALTER TABLE conversations ENABLE ROW LEVEL SECURITY;

CREATE POLICY "user_isolation" ON conversations
    FOR ALL
    USING (user_id = (current_setting('request.jwt.claims', true)::json->>'sub')::uuid)
    WITH CHECK (user_id = (current_setting('request.jwt.claims', true)::json->>'sub')::uuid);
```

Même si une requête buggée tente d'accéder aux données d'un autre utilisateur, PostgreSQL refuse. **Deux barrières indépendantes.**

### Pourquoi pas un bot par utilisateur ?
- Limite Telegram : ~20 bots par compte
- Création/suppression par API complexe
- Gestion des tokens ingérable à l'échelle
- Coûts fixes par bot (webhooks, certificats)

## Flux de données

### 1. Onboarding intelligent
```
Nouvel utilisateur → Bot envoie formulaire groupé :
  "J'ai besoin de 5 infos pour commencer :
   1️⃣ Quel sport principal ?
   2️⃣ Niveau / expérience ?
   3️⃣ Objectif précis ?
   4️⃣ Créneaux dispo par semaine ?
   5️⃣ Blessures ou contraintes ?"

→ Réponse utilisateur (1 message)
→ Parsing + création profil
→ Premier plan généré
→ Proposition connexion Google Calendar
```

### 2. Interaction quotidienne
```
Message utilisateur
    ↓
Router (classifie la demande) :
    ├── plan/ → GenerationEngine → Structured output → Formatage Telegram
    ├── question/ → RAG(sources) + LLM → Réponse sourcée
    ├── douleur/ → Safety handler → Médecin + Adaptation plan
    ├── calendrier/ → Google API → Lecture/Écriture événements
    └── conversation/ → Prompt builder(user) + LLM → Réponse
```

### 3. Génération de plan
```
Prompt builder récupère :
  - Profil utilisateur complet
  - Historique 4 dernières semaines
  - Base connaissances (RAG : plans types pour objectif similaire)
  - Calendrier (créneaux disponibles)

→ LLM génère un plan structuré :
{
  "week": 1,
  "phase": "base",
  "days": [
    {
      "date": "2026-05-12",
      "type": "endurance",
      "description": "Sortie 2h en zone 2 (60-70% FTP)",
      "pourquoi": "Développer la capacité aérobie, base de ta préparation",
      "alternative": "Si fatigué → 1h30 zone 1 active recovery"
    }
  ]
}

→ Écrit dans Google Calendar (optionnel)
→ Formaté en message Telegram lisible
```

## Optimisation des coûts LLM

| Technique | Implémentation | Gain estimé |
|-----------|---------------|-------------|
| Cache sémantique | Stockage hash des questions fréquentes + réponses | 60-80% |
| Compression historique | Résumé des conversations au lieu du transcript complet | 40% tokens |
| Router intelligent | Questions simples → réponse directe sans LLM | 20% appels |
| Rate limiting | Limite quotidienne par utilisateur (offre de base) | Contrôle garanti |

**Coût projeté (DeepSeek V4, ~$0.50/M tokens) :**
- Utilisateur léger (10 msg/jour) : ~0,05€/mois
- Utilisateur moyen (30 msg/jour) : ~0,15€/mois
- Utilisateur intensif (50 msg/jour, plans fréquents) : ~0,35€/mois

## Base de données — Schéma complet

### `users`
| Colonne | Type | Description |
|---------|------|-------------|
| id | uuid | PK |
| telegram_id | bigint | ID Telegram unique |
| email | text | Email Stripe/inscription |
| first_name | text | Prénom |
| sports | jsonb | `["cyclisme", "course"]` |
| level | text | débutant/intermédiaire/avancé |
| goals | jsonb | Objectifs structurés |
| health_data | jsonb | Blessures, contraintes (chiffré) |
| equipment | jsonb | Matériel dispo |
| weekly_slots | jsonb | `[{"day": "mardi", "time": "18h"}]` |
| calendar_connected | boolean | OAuth Google |
| subscription_status | text | active/trialing/cancelled |
| subscription_tier | text | basic/premium |
| created_at | timestamptz | |

### `training_plans`
| Colonne | Type | Description |
|---------|------|-------------|
| id | uuid | PK |
| user_id | uuid | FK → users |
| name | text | "Prépa Granfondo 12 semaines" |
| phase | text | base/build/peak/taper |
| start_date | date | |
| end_date | date | |
| plan_data | jsonb | Structure complète du plan |
| created_at | timestamptz | |

### `workouts`
| Colonne | Type | Description |
|---------|------|-------------|
| id | uuid | PK |
| user_id | uuid | FK |
| plan_id | uuid | FK (nullable) |
| scheduled_date | date | |
| completed_date | date | |
| type | text | endurance/intervalle/seuil/etc. |
| description | text | |
| duration_min | int | |
| metrics | jsonb | `{"ftp_percent": 70, "rpe": 3}` |
| completed | boolean | |
| feedback | text | Retour utilisateur |
| rpe_actual | int | 1-10 |

### `conversations`
| Colonne | Type | Description |
|---------|------|-------------|
| id | uuid | PK |
| user_id | uuid | FK |
| role | text | user/assistant/system |
| content | text | |
| tokens_used | int | |
| context_type | text | plan/question/safety/chat |
| created_at | timestamptz | |
| expires_at | timestamptz | auto-suppression après 90j (RGPD) |

### `knowledge_base`
| Colonne | Type | Description |
|---------|------|-------------|
| id | uuid | PK |
| sport | text | cyclisme/running/triathlon/fitness |
| domain | text | physiologie/planification/nutrition/etc. |
| source | text | URL/citation étude |
| content | text | Le texte de référence |
| embedding | vector(1536) | pgvector pour recherche sémantique |

### `user_knowledge` (mémoire long-terme utilisateur)
| Colonne | Type | Description |
|---------|------|-------------|
| id | uuid | PK |
| user_id | uuid | FK |
| fact_type | text | preference/injury/goal/equipment |
| fact | text | "Préfère s'entraîner le matin" |
| source_conversation_id | uuid | FK → conversations |
| embedding | vector(1536) | Pour recherche sémantique |

## Structure du projet

```
ai-sports-coach/
├── README.md
├── plan.md
├── docs/
│   ├── architecture.md        ← Ce fichier
│   ├── coaching.md
│   ├── base-connaissances.md
│   └── concurrents.md
├── src/
│   ├── bot/
│   │   ├── __init__.py
│   │   ├── main.py            ← Entrypoint FastAPI + aiogram
│   │   ├── handlers/          ← Handlers par domaine
│   │   │   ├── onboarding.py
│   │   │   ├── chat.py
│   │   │   ├── plans.py
│   │   │   ├── calendar.py
│   │   │   └── safety.py
│   │   ├── middleware/
│   │   │   └── user.py
│   │   └── keyboards/         ← Claviers inline
│   ├── engine/
│   │   ├── router.py          ← Classification des messages
│   │   ├── prompt_builder.py  ← Construction prompts personnalisés
│   │   ├── generation.py      ← Génération plans structurés
│   │   ├── rag.py             ← Recherche base connaissances
│   │   ├── safety.py          ← Gestion messages santé
│   │   └── cache.py           ← Cache sémantique
│   ├── integrations/
│   │   ├── google_calendar.py
│   │   ├── stripe.py
│   │   └── openrouter.py
│   ├── db/
│   │   ├── supabase.py
│   │   └── models.py
│   └── utils/
│       ├── config.py
│       └── logging.py
├── scripts/
│   ├── seed_knowledge_base.py  ← Import données scientifiques
│   └── generate_embeddings.py
├── docker/
│   ├── Dockerfile
│   └── docker-compose.yml
├── tests/
├── .env.example
├── pyproject.toml
└── .gitignore
```

## Sécurité

- **Données de santé** : colonne `health_data` chiffrée (AES-256), clé gérée par Supabase Vault
- **Tokens OAuth** : stockés chiffrés, jamais en clair
- **API keys** : variables d'environnement Docker, `.env` exclu de git
- **Rate limiting** : FastAPI + aiogram, par utilisateur et global
- **Conversations** : auto-suppression après 90 jours (RGPD)
- **Logs** : jamais de contenu de conversations dans les logs