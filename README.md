# AI Sports Coach 🏃‍♂️

Assistant d'entraînement IA conversationnel, disponible via **PWA web** et **bot Telegram**.

## Stack

- **Frontend** : Next.js 16 (PWA avec Serwist) → déployé sur Vercel
- **Backend** : FastAPI (Python 3.14) → déployé sur VPS Docker
- **LLM** : DeepSeek V4 via OpenRouter (pipeline 2 étages : sélecteur + coach)
- **Base** : Supabase (PostgreSQL + Auth + pgvector)
- **UI** : shadcn/ui v4 + Tailwind CSS v4

## Démarrage rapide

```bash
# 1. Cloner
git clone <repo-url>
cd ai-sports-coach

# 2. Configurer le backend
cp .env.example .env
# Éditer .env avec les vraies clés (OpenRouter, Supabase, etc.)

# 3. Configurer le frontend
cp frontend/.env.example frontend/.env.local
# Éditer avec l'URL Supabase et l'URL API

# 4. Installer et lancer le backend
pip install -e .
python -m uvicorn src.api.main:app --reload --port 8000

# 5. Installer et lancer le frontend
cd frontend
npm install
npm run dev
```

→ Frontend : http://localhost:3000
→ Backend : http://localhost:8000
→ API health : http://localhost:8000/api/health

## Architecture

```
┌──────────────┐     ┌────────────────┐     ┌──────────────┐
│  Vercel      │────▶│  VPS Docker    │────▶│  Supabase    │
│  Frontend    │     │  Backend       │     │  DB + Auth   │
│  Next.js 16  │     │  FastAPI       │     │  pgvector    │
└──────────────┘     └────────────────┘     └──────────────┘
                            │
                            ▼
                     ┌──────────────┐
                     │  OpenRouter  │
                     │  DeepSeek V4 │
                     └──────────────┘
```

Le projet a une **double interface** : un bot Telegram (aiogram 3, l'interface d'origine) et une API REST FastAPI (la PWA). Les deux partagent les couches `src/engine/`, `src/db/` et `src/utils/`.

## Documentation

- **[CLAUDE.md](CLAUDE.md)** — Guide complet pour travailler sur le code (commandes, architecture, conventions, gotchas)
- **[docs/deploy.md](docs/deploy.md)** — Guide de déploiement (Supabase, Docker, Vercel, cron, rollback)
- **[docs/architecture.md](docs/architecture.md)** — Architecture cible
- **[knowledge/selector-spec.md](knowledge/selector-spec.md)** — Spécification du sélecteur de connaissances
- **[knowledge/index.yaml](knowledge/index.yaml)** — Index de la base de connaissances

## Tests

```bash
# Backend : tests unitaires
pytest tests/ --ignore=tests/bot --ignore=tests/integration -v

# Backend : avec couverture
pytest tests/ --ignore=tests/bot --ignore=tests/integration -v --cov=src --cov-report=term-missing

# Frontend : vérification du build
cd frontend && npx next build --webpack
```

## Licence

Propriétaire — Tous droits réservés.
