# CLAUDE.md

Ce fichier fournit des directives à Claude Code (claude.ai/code) pour travailler dans ce dépôt.

## Démarrage rapide

```bash
# Frontend (Next.js dev server → localhost:3000)
cd frontend && npm run dev

# Backend (FastAPI → localhost:8000)
/c/Users/bonne/AppData/Local/Python/pythoncore-3.14-64/python.exe -m uvicorn src.api.main:app --reload --port 8000
```

## Commandes essentielles

```bash
# Backend : tous les tests unitaires (exclut bot/ et integration/)
/c/Users/bonne/AppData/Local/Python/pythoncore-3.14-64/python.exe -m pytest tests/ --ignore=tests/bot --ignore=tests/integration -v

# Backend : un seul fichier de test
/c/Users/bonne/AppData/Local/Python/pythoncore-3.14-64/python.exe -m pytest tests/api/test_auth.py -v

# Backend : une seule fonction de test
/c/Users/bonne/AppData/Local/Python/pythoncore-3.14-64/python.exe -m pytest tests/api/test_auth.py::test_register_success -v

# Backend : avec couverture
/c/Users/bonne/AppData/Local/Python/pythoncore-3.14-64/python.exe -m pytest tests/ --ignore=tests/bot --ignore=tests/integration -v --cov=src --cov-report=term-missing

# Frontend : vérification du build (obligatoire : --webpack, pas Turbopack)
cd frontend && SERWIST_SUPPRESS_TURBOPACK_WARNING=1 npx next build --webpack

# Frontend : lint
cd frontend && npm run lint

# Vérification rapide backend
curl http://localhost:8000/api/health
```

## Variables d'environnement

### Backend (`.env` à la racine, pas `backend/.env`)
Les variables essentielles au développement local :
- `LLM_API_KEY` — clé API DeepSeek directe (plus OpenRouter). Pour utiliser OpenRouter, mettre la clé OpenRouter et changer `LLM_BASE_URL`
- `LLM_BASE_URL` — URL de l'API LLM (défaut: `https://openrouter.ai/api/v1`, pour DeepSeek direct: `https://api.deepseek.com`)
- `LLM_MODEL` — modèle coach principal (défaut: `deepseek-chat`)
- `SELECTOR_MODEL` — petit modèle pour tâches auxiliaires (défaut: `deepseek-chat`)
- `SUPABASE_URL`, `SUPABASE_ANON_KEY`, `SUPABASE_SERVICE_KEY` — connexion Supabase
- `GEMINI_API_KEY` — embeddings (⚠️ utilisé uniquement par le bot Telegram, pas par la PWA)
- `CORS_ORIGINS` — origines autorisées (local: `http://localhost:3000`, production: `https://pwa.srv780916.hstgr.cloud`). Format: liste séparée par virgules.
- `VAPID_PRIVATE_KEY`, `VAPID_PUBLIC_KEY`, `VAPID_SUBJECT` — push notifications web (générer avec `npx web-push generate-vapid-keys`)
- `OPENROUTER_API_KEY`, `OPENROUTER_BASE_URL` — backward compat, `LLM_API_KEY` et `LLM_BASE_URL` prennent le dessus si définis

⚠️ **Gotcha** : La variable s'appelle `SUPABASE_SERVICE_KEY` dans le code (`src/utils/config.py`), mais `SUPABASE_SERVICE_ROLE_KEY` dans `docs/deploy.md`. Le code lit `SUPABASE_SERVICE_KEY`.
⚠️ **Gotcha** : Le `.env` est à la racine du projet, pas dans `backend/`. Le fichier est dans `.gitignore`.
⚠️ **Gotcha** : `CORS_ORIGINS` doit inclure l'URL de production du frontend (ex: `https://pwa.srv780916.hstgr.cloud`). En local: `http://localhost:3000`. Le format est une liste séparée par des virgules, sans guillemets ni crochets.

### Frontend (`frontend/.env.local`)
```
NEXT_PUBLIC_SUPABASE_URL=https://xxx.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJ...
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## Architecture

Le projet est une application **double interface** : un bot Telegram (aiogram 3, l'interface d'origine) et une **API REST FastAPI** (la nouvelle PWA). Les deux partagent les couches `src/engine/`, `src/db/` et `src/utils/`.

**Architecture de déploiement réelle :**
```
Navigateur ──HTTPS──▶ Traefik VPS Hostinger (:443) ──▶ conteneur frontend Next.js (:3000)
                                                   ──▶ conteneur backend FastAPI (:8000)

Frontend + Backend sur le même VPS Hostinger, routés par sous-domaine via Traefik.
Supabase (DB + Auth) → externe, géré par Supabase
DeepSeek (direct, pas OpenRouter) → api.deepseek.com
```

> **Next.js 16 :** Le frontend utilise Next.js 16.2.7, qui a des breaking changes par rapport à Next.js 15 et aux versions antérieures. Consulter [frontend/AGENTS.md](frontend/AGENTS.md) et `frontend/node_modules/next/dist/docs/` avant d'écrire du code frontend. Les APIs, conventions et structures de fichiers peuvent différer de tes connaissances d'entraînement.

```
frontend/src/app/           → Next.js 16 App Router (tout en client-side, pas de server components)
frontend/src/components/    → chat/, dashboard/, onboarding/, profile/, layout/, ui/
frontend/src/hooks/         → useChat, useDashboard, useAthleteModel, usePush
frontend/src/lib/           → api.ts (fetch + SSE), supabase.ts, utils.ts

src/api/                    → Routes FastAPI (auth, chat, profile, dashboard, athlete, onboarding, feedback, push)
src/engine/                 → Logique métier (appels LLM, construction de prompts, connaissances, sécurité, etc.)
src/db/                     → CRUD Supabase (un fichier par table)
src/bot/                    → Bot Telegram (handlers aiogram, middleware, keyboards)
src/cli/                    → Points d'entrée cron (proactive.py)
src/migrations/             → Migrations SQL brutes (ordre: 001_pwa_tables → 002_rls_policies → 003_enable_vault → 004_onboarding_columns)
```

### Flux et patterns clés

**Authentification :** Le frontend POST les credentials → le backend crée/valide l'utilisateur Supabase Auth via la clé `service_role` → retourne un JWT `access_token` + `refresh_token`. Le frontend stocke les tokens dans `localStorage` et les attache via `Authorization: Bearer` à chaque requête. La dépendance `get_current_user()` valide le JWT auprès de Supabase Auth, puis récupère la ligne utilisateur dans la table `users`. Pas de middleware de protection de route côté frontend — les pages vérifient `localStorage` directement.

**Streaming SSE du chat :** `POST /api/chat/message` → vérification rate limit (sliding window en mémoire) → récupération/création de session (expiration 24h) → sauvegarde du message utilisateur → chargement des 15 derniers messages (mémoire chaude) → `select_concepts()` (3 niveaux : détection de mots-clés critiques → matching par mots-clés → sélecteur LLM) → `build_system_prompt()` (blocs de connaissances + profil + règles) → `stream_llm_response()` émet des événements SSE `event: token` → le bloc `finally` sauvegarde le message assistant + suit les coûts. Côté frontend, `sseStream()` parse le flux manuellement via `ReadableStream` (pas `EventSource`, qui ne supporte que GET).

**Système de connaissances :** Les connaissances de coaching sont stockées en markdown dans `knowledge/domains/`, indexées par `knowledge/index.yaml`. Le `Selector` choisit les concepts pertinents par message via trois stratégies en ordre de priorité : (1) détection de mots-clés de douleur/blessure (gratuit), (2) matching par mots-clés contre `INTENT_KEYWORDS` (gratuit, ~80% de couverture), (3) sélection par LLM via `deepseek/deepseek-chat` (payant). Les concepts sélectionnés sont chargés au niveau approprié (1-3) et injectés dans le system prompt. L'architecture complète du sélecteur est documentée dans [knowledge/selector-spec.md](knowledge/selector-spec.md).

**Deux modèles LLM distincts :** Le backend utilise le même modèle pour deux rôles différents (configurable séparément). `LLM_MODEL` (défaut `deepseek-chat`) est le coach principal — raisonnement complexe, réponses longues. `SELECTOR_MODEL` (défaut `deepseek-chat`) est pour les tâches auxiliaires : sélection de connaissances, summarization de session, extraction de faits. Le provider est configurable via `LLM_API_KEY` et `LLM_BASE_URL` — DeepSeek direct par défaut, mais OpenRouter fonctionne aussi. Les embeddings (`src/engine/embeddings.py`) sont utilisés uniquement par le bot Telegram, pas par la PWA.

**Modèle athlète :** Un document JSON versionné qui stocke tout ce que le coach sait sur l'athlète (physique, etat_actuel, blessures, patterns, preferences, objectifs). Mis à jour via `update_model_from_summary()` après chaque session, avec résolution de conflits par priorité de source : `corrected_by_human` (5) > `measured` (4) > `reported` (3) > `estimated` (2) > `auto_extracted` (1). Les corrections humaines passent par `PATCH /api/athlete/model` avec des chemins en notation pointée. Gère les contradictions quand différentes sources donnent des valeurs différentes pour le même champ.

## Conventions

- **Codebase en français** : Tous les commentaires, docstrings, messages de log, textes UI et messages de commit sont en français. Les noms de variables/fonctions sont en anglais.
- **Tout en client components** : Chaque page Next.js est `'use client'`. Pas de server components, pas d'exports `generateMetadata`, pas de pages async. L'app est une SPA client-side qui communique avec un backend séparé.
- **DB synchrone dans un contexte async** : `supabase-py` est synchrone. Les handlers FastAPI l'appellent directement (bloquant brièvement l'event loop). Le bot Telegram wrappe les appels dans `asyncio.to_thread()`. C'est accepté pour le moment.
- **Pas d'ORM** : Toutes les opérations DB utilisent directement le query builder Supabase (`.table().select().eq().execute()`). Pas de SQLAlchemy.
- **Client admin partout** : Les fonctions repository utilisent `get_supabase_admin()` (service_role, bypass RLS). Le client anon n'est utilisé que pour `auth.sign_in_with_password()` et `auth.refresh_session()`.
- **Singletons au niveau module** : Les clients LLM, clients Supabase, caches de connaissances, compteurs de circuit breaker et dicts de rate limit sont des variables globales de module. Pas d'injection de dépendances.
- **État en mémoire** : Le rate limiting et le suivi des coûts sont en mémoire uniquement — ils sont réinitialisés au redémarrage du serveur. Pas de Redis.
- **Dark mode uniquement** : Le `<html>` a `.dark` en dur. Le CSS définit les deux thèmes mais seul le dark est actif.
- **Tâches d'arrière-plan fire-and-forget** : La summarization de session et l'extraction de faits utilisent `asyncio.create_task()` sans await. Les erreurs sont silencieusement ignorées.
- **Tests backend : mock, pas de DB réelle** : Tous les tests unitaires mockent Supabase via `unittest.mock.patch`. Les clients admin et anon sont mockés à chaque point d'import (`patch("src.api.auth.get_supabase_admin", ...)`). Voir `tests/api/test_auth.py` pour le pattern. Les tests d'intégration (`tests/bot/`, `tests/integration/`) sont exclus par défaut.
- **Pas de tests frontend** : Il n'y a pas de suite de tests Jest/Vitest côté frontend. La seule vérification est le build (`next build --webpack`).
- **shadcn/ui v4 sur @base-ui/react** : Les composants UI utilisent shadcn/ui v4 (style new-york), qui est construit sur `@base-ui/react` (pas Radix UI). Tailwind CSS v4 avec espace colorimétrique OKLCH.

## Docker

```bash
# Build
docker build -t ai-sports-coach -f docker/Dockerfile .

# Run (local)
docker run -d --name coach-api --env-file .env -p 8000:8000 --restart unless-stopped ai-sports-coach

# Run (VPS Hostinger, avec Traefik — pas de -p, Traefik route en HTTPS)
docker run -d --name coach-api --env-file .env --restart unless-stopped \
  --label "traefik.enable=true" \
  --label "traefik.http.routers.coach-api.rule=Host(\`pwa-api.srv780916.hstgr.cloud\`)" \
  --label "traefik.http.routers.coach-api.entrypoints=websecure" \
  --label "traefik.http.routers.coach-api.tls.certresolver=letsencrypt" \
  ai-sports-coach
```

Le VPS utilise **Traefik** comme reverse proxy (pas Nginx). Traefik écoute sur 80/443 en `network_mode: host` et route par sous-domaine vers les conteneurs. Pas de proxy `/api/*` — le frontend appelle l'API directement via son sous-domaine.

## Gotchas

- **Chemin Python** : Python 3.14 est dans `C:\Users\bonne\AppData\Local\Python\pythoncore-3.14-64\python.exe`. Toujours utiliser le chemin complet.
- **Shell** : Git Bash sur Windows — utiliser les chemins Unix (`/c/...`). Les warnings CRLF sont normaux, les ignorer.
- **`@serwist/next` exige `--webpack`** : Turbopack est incompatible. Toujours ajouter `--webpack` aux commandes de build Next.js.
- **`pyiceberg` ne build pas sur Windows** : Installer supabase avec `--no-deps`, puis les sous-paquets individuellement.
- **Fix d'encodage UTF-8** : Déjà appliqué dans `knowledge.py` — essentiel sur Windows. Ne pas retirer la gestion d'encodage.
- **Deux époques de l'API DB** : `src/db/sessions.py` a des familles de fonctions parallèles — une indexée par `telegram_id` (ère bot), une par `user_id` UUID (ère FastAPI). Les routes FastAPI utilisent uniquement celles basées sur UUID. Ne pas les mélanger.
- **Pas de routes API dans le frontend** : Il n'y a pas de `middleware.ts`, pas de `route.ts`, pas de server actions. Toute la communication backend passe par le serveur FastAPI séparé.
- **SSE sur POST** : Le SSE du chat utilise POST (pas GET comme le `EventSource` standard). Cela nécessite le parseur `sseStream()` personnalisé dans le frontend plutôt que l'API native `EventSource` du navigateur.
- **Circuit breaker sur le LLM** : Après 5 échecs consécutifs, `get_client()` refuse les appels pendant 60 secondes. C'est un compteur global au niveau module — il affecte tous les utilisateurs.
- **Nom de variable Supabase incohérent** : Le code (`src/utils/config.py`) utilise `SUPABASE_SERVICE_KEY`, mais `docs/deploy.md` et `.env.example` référencent `SUPABASE_SERVICE_ROLE_KEY`. Vérifier lequel est utilisé dans le `.env` réel.
- **README.md** : Couvre maintenant le stack complet (PWA + FastAPI + Supabase + LLM). Complété par ce CLAUDE.md et `docs/deploy.md`.
- **`public/sw.js` est généré** : Le fichier `frontend/public/sw.js` est compilé par Serwist à partir de `frontend/src/app/sw.ts` lors du `next build`. Ne jamais l'éditer directement — toute modification sera écrasée au prochain build.
- **Stubs connus** : `/api/dashboard/chart` retourne `series: []` en dur (les daily_summaries ne sont pas encore historisées). Le commentaire `# Résumé de la veille (stub)` dans `src/api/chat.py` signale que l'intégration du summarizer n'est pas finalisée.
- **`/api/admin/feedback` sans contrôle admin** : L'endpoint est accessible à tout utilisateur authentifié (pas de vérification de rôle). C'est intentionnel pour le MVP, marqué comme temporaire.
- **Planification du projet** : `plan.md` et `SESSION_STATE.md` contiennent la roadmap et l'état des tâches. Consulter ces fichiers avant de planifier du nouveau travail.
- **`supabase-py` 2.x API cassante** : `sign_in_with_password()` et `refresh_session()` retournent un `AuthResponse` avec les tokens dans `.session.access_token` (pas `.access_token` directement). De même, `.user` est dans `.session.user`. Les tests mockent cette structure avec `mock_response.session.access_token = "..."`.
- **`telegram_id` NOT NULL** : La colonne `telegram_id` de la table `users` a une contrainte `NOT NULL` héritée de l'ère bot. Les utilisateurs PWA (sans compte Telegram) échouent à l'insertion. Exécuter `ALTER TABLE users ALTER COLUMN telegram_id DROP NOT NULL;` une fois pour toutes.
- **PWA = build production uniquement** : Le Service Worker, le mode hors-ligne, les push notifications et l'installation ne fonctionnent qu'après `next build --webpack && next start`. En `next dev`, seule l'UI est testable, pas les fonctionnalités PWA.
- **Dev server instable** : `next dev` recompile constamment chaque fichier modifié, provoquant des rafraîchissements en boucle. Pour tester l'UI, préférer un build production + `next start` ou déployer sur le VPS.
- **Migrations SQL** : `src/migrations/combined.sql` contient le script combiné (001+002+003) mais **pas encore la 004**. Pour l'onboarding PWA, exécuter aussi `004_onboarding_columns.sql` séparément. Les migrations individuelles sont gardées pour référence.
- **`npm run dev` et `npm run build` incluent déjà `--webpack`** dans `package.json`. Ne pas ajouter le flag en double.
- **`level` est SMALLINT en DB (1,2,3)** : La colonne `level` de `users` est un entier, pas une string. Le frontend envoie `"debutant"`, `"intermediaire"`, `"avance"` — le backend doit convertir via `LEVEL_MAP` dans `src/api/onboarding.py`. Si on ajoute de nouveaux endpoints qui modifient `level`, utiliser le même mapping.
- **Colonnes onboarding** : `equipment`, `weekly_slots`, `onboarding_phase`, `parq_responses`, `parq_any_yes` ont été ajoutées par la migration 004. Sans cette migration, tout appel aux endpoints onboarding (phase1, phase2, parq) retourne une erreur 500.
- **Embeddings = bot uniquement** : `src/engine/embeddings.py` n'est pas utilisé par les routes API PWA. Si `GEMINI_API_KEY` est vide, la PWA fonctionne normalement. Seul le bot Telegram utilise les embeddings pour la recherche de faits similaires.
