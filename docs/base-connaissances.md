# Base de Connaissances — Le Cerveau du Coach

> La qualité du coach dépend à 80% de la qualité de sa base de connaissances.

## Architecture RAG (Retrieval-Augmented Generation)

```
Question utilisateur : "Comment améliorer mon FTP ?"
        ↓
[Recherche sémantique] → pgvector cosine similarity
        ↓
┌─────────────────────────────────────────────┐
│  Documents pertinents récupérés :            │
│  1. "Sweet spot training : 88-94% FTP..."   │
│  2. "Polarized vs threshold : méta-analyse" │
│  3. "Progression FTP débutant 8 semaines"   │
└─────────────────────────────────────────────┘
        ↓
[Prompt LLM] = Question + Documents + Profil athlète
        ↓
Réponse sourcée et personnalisée
```

## Domaines de connaissances

### 1. Physiologie de l'effort ⭐ Priorité maximale

| Sous-domaine | Contenu | Sources types |
|-------------|---------|---------------|
| Filières énergétiques | Aérobie, anaérobie lactique, alactique | Manuels physiologie |
| VO2max, FTP, VMA | Définitions, tests, interprétation | Études PubMed |
| Seuils ventilatoires | SV1, SV2, seuil lactique | Articles scientifiques |
| Adaptation à l'entraînement | Surcharge, surcompensation, plateau | Méta-analyses |

### 2. Méthodologies d'entraînement

| Méthode | Description | Application |
|---------|-------------|-------------|
| Polarized (80/20) | 80% basse intensité, 20% haute | Endurance, triathlon |
| Pyramidal | 70% Z1-Z2, 20% Z3, 10% Z4-Z5 | Polyvalent |
| Seuil / Sweet spot | Focus zone 3-4 | Contre-la-montre, progression FTP |
| HIIT | Intervalles courts haute intensité | VO2max, temps limité |
| Bloc training | Périodes concentrées sur 1 qualité | Avancé |

### 3. Planification et périodisation

- **Macrocycle** : saison complète (6-12 mois)
- **Mésocycle** : bloc de 3-6 semaines (base, build, peak)
- **Microcycle** : semaine type
- **Tapering** : affûtage pré-compétition
- **Périodisation inverse** : commencer par l'intensité, finir par le volume
- **Charge d'entraînement** : TSS, TRIMP, RPE

### 4. Spécifique par sport

#### Cyclisme
- FTP : définition, test 20min, progression
- Cadence optimale, position, technique de pédalage
- Home trainer vs extérieur : équivalences
- Nutrition en selle : glucides/heure, hydratation
- Récupération : stratégies post-sortie longue

#### Course à pied
- VMA : test demi-Cooper, progression
- Allure spécifique : 10km, semi, marathon
- Technique de course, foulée, économie
- Gestion des allures en course
- Choix chaussures, surface, dénivelé

#### Triathlon
- Transitions, enchaînements
- Brick training (vélo + course)
- Natation : technique, CSS, endurance
- Gestion multi-discipline

#### Fitness / Renforcement
- Charges, séries, répétitions, tempo
- Périodisation force (force max, hypertrophie, endurance)
- Exercices polyarticulaires fondamentaux
- Prévention blessures par renforcement

### 5. Nutrition sportive

- Macronutriments avant/pendant/après effort
- Hydratation : sodium, osmolarité
- Périodisation nutritionnelle (train low, compete high)
- Compléments : preuves scientifiques (créatine, caféine, nitrates)
- Poids de corps et performance : approche prudente

### 6. Récupération

- Sommeil et performance
- Récupération active vs passive
- Massage, compression, cryothérapie (niveau de preuve)
- Détection surentraînement

### 7. Prévention des blessures

- Renforcement préventif par sport
- Gestion de charge (ACWR — Acute:Chronic Workload Ratio)
- Étirements : quand, comment, utilité réelle
- Signaux d'alerte à ne pas ignorer

### 8. Psychologie du sport

- Fixation d'objectifs (SMART)
- Motivation intrinsèque vs extrinsèque
- Gestion course : visualisation, dissociation
- Gestion de l'échec et des blessures

## Sources prioritaires

### Base scientifique (PubMed, ResearchGate, Google Scholar)

Recherches à effectuer par sport :
- `"training intensity distribution" cycling running`
- `"periodization endurance performance meta-analysis"`
- `"FTP threshold reliability"`
- `"carbohydrate intake endurance performance"`
- `"sleep athletic performance recovery"`
- `"injury prevention strength training runners"`
- `"tapering strategies endurance meta-analysis"`

### Ouvrages de référence

- **Jack Daniels** — *Running Formula* (VDOT, plans course)
- **Joe Friel** — *Training Bible* (cyclisme, triathlon, périodisation)
- **Andrew Coggan** — *Training and Racing with a Power Meter*
- **Tim Noakes** — *Lore of Running*
- **Inigo San Millan** — Physiologie métabolique

### Directives fédérales

- FFC (Fédération Française de Cyclisme)
- FFA (Fédération Française d'Athlétisme)
- FFTri (Fédération Française de Triathlon)

## Modèle d'embedding choisi : Gemini Embedding 2

Après analyse comparative (recommandations Perplexity 05/2026) :

| Modèle | Avantages | Inconvénients | Verdict |
|--------|-----------|---------------|---------|
| **Gemini Embedding 2** ✅ | 10× moins cher qu'OpenAI, excellent sur longs docs (32K tokens), très bon français, multimodal | Nécessite clé API Google | **Choisi** |
| Qwen3-Embedding-8B | Meilleur score français (69.8), auto-hébergé | Nécessite GPU ou 2.5 Go RAM, non multimodal | Trop lourd pour VPS |
| BGE-M3 | Hybride dense+sparse, bon français, <2 Go | Inférieur à Gemini sur longs docs | Bon fallback local |
| text-embedding-3-small (OpenAI) | Simple, bien intégré | Cher (10× Gemini), 1536 dims | Rejeté |

**Pourquoi Gemini :**
- Documents longs (articles PubMed, chapitres) → Gemini est le seul qui tient la perf jusqu'à 32K tokens
- Budget → quasi gratuit à nos volumes
- Techniquement → 768 dimensions (vs 1536 pour OpenAI), stockage vectoriel divisé par 2
- Français → très bon, suffisant pour notre base FR

### Structure de la table `knowledge_base`

```sql
CREATE TABLE knowledge_base (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    sport TEXT NOT NULL,           -- cyclisme, running, triathlon, fitness, general
    domain TEXT NOT NULL,          -- physiologie, methodologie, nutrition, etc.
    subdomain TEXT,                -- ftp, vo2max, seuil...
    title TEXT NOT NULL,           -- Titre lisible
    content TEXT NOT NULL,         -- Contenu complet
    source_type TEXT,              -- scientific_study, textbook, guideline, meta_analysis
    source_url TEXT,               -- URL source si dispo
    source_citation TEXT,          -- Citation formatée
    quality_score INT DEFAULT 5,   -- 1-10, évalué par un pro si possible
    language TEXT DEFAULT 'fr',    -- fr, en
    tags JSONB,                    -- ["ftp", "seuil", "progression"]
    embedding VECTOR(768),        -- Embedding Gemini (text-embedding-004, 768 dims)
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

### Génération des embeddings

```python
# scripts/generate_embeddings.py
import google.generativeai as genai
from supabase import create_client

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# 1. Lire tous les documents sans embedding
docs = supabase.table("knowledge_base") \
    .select("*") \
    .is_("embedding", "null") \
    .execute()

# 2. Générer les embeddings (batch traité séquentiellement, API Gemini)
for doc in docs:
    content = doc["content"][:8000]  # Pas de limite stricte, Gemini tient 32K
    result = genai.embed_content(
        model="models/text-embedding-004",
        content=content,
        task_type="RETRIEVAL_DOCUMENT"
    )
    
    # 3. Mettre à jour (768 dimensions)
    supabase.table("knowledge_base") \
        .update({"embedding": result["embedding"]}) \
        .eq("id", doc["id"]) \
        .execute()
```

### Recherche sémantique

```python
# src/engine/rag.py
async def search_knowledge(query: str, sport: str, limit: int = 5):
    # 1. Embed la question
    embedding = await get_embedding(query)
    
    # 2. Recherche pgvector
    result = supabase.rpc("match_knowledge", {
        "query_embedding": embedding,
        "sport_filter": sport,
        "match_count": limit
    }).execute()
    
    return result.data
```

```sql
-- Fonction RPC Supabase
CREATE OR REPLACE FUNCTION match_knowledge(
    query_embedding VECTOR(768),
    sport_filter TEXT DEFAULT NULL,
    match_count INT DEFAULT 5
)
RETURNS TABLE(
    id UUID,
    title TEXT,
    content TEXT,
    source_citation TEXT,
    similarity FLOAT
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        kb.id,
        kb.title,
        kb.content,
        kb.source_citation,
        1 - (kb.embedding <=> query_embedding) AS similarity
    FROM knowledge_base kb
    WHERE (sport_filter IS NULL OR kb.sport = sport_filter OR kb.sport = 'general')
    ORDER BY kb.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;
```

## Alimentation initiale de la base

### Phase 1 : manuelle (qualité > quantité)

Prioriser 50-100 documents ultra-qualitatifs :

1. **20 documents** sur la physiologie de base (filières, seuils, adaptations)
2. **15 documents** sur les méthodologies (polarisé, pyramidal, HIIT)
3. **20 documents** spécifiques par sport (10 cyclisme, 10 running)
4. **10 documents** nutrition sportive
5. **10 documents** récupération et prévention
6. **5 documents** psychologie du sport

### Phase 2 : semi-automatique

- Script de recherche PubMed → extraction abstracts → validation humaine
- Intégration de livres (Jack Daniels VDOT tables, plans types Joe Friel)
- Récupération de directives fédérales PDF → parsing → embeddings

### Phase 3 : contributive

- Possibilité d'ajouter des articles par l'admin
- Score de qualité modifiable
- Feedback utilisateur ("cette info était utile ?")

## Évaluation de la qualité

Pour que le coach soit crédible, chaque document doit être :
- ✅ Source vérifiable
- ✅ Niveau de preuve acceptable (méta-analyse > RCT > étude observationnelle > avis expert)
- ✅ Non obsolète (< 10 ans sauf ouvrage fondateur)
- ✅ Applicable au coaching (pas juste théorique)
- ✅ Traduit/adapté en français si nécessaire