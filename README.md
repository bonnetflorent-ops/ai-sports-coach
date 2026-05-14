# AI Sports Coach 🏃‍♂️

Assistant d'entraînement IA conversationnel sur Telegram.

## Stack
- **Bot** : aiogram 3 (Telegram)
- **LLM** : DeepSeek V4 via OpenRouter (pipeline 2 étages)
- **Base** : Supabase (PostgreSQL + pgvector)
- **Déploiement** : Docker

## Démarrage rapide

```bash
# 1. Cloner
git clone <repo-url>
cd ai-sports-coach

# 2. Configurer
cp .env.example .env
# Éditer .env avec les vraies clés

# 3. Lancer
pip install .
python -m src.bot.main

# Ou via Docker
docker compose up -d --build
```

## Architecture

Voir `docs/architecture.md` pour l'architecture cible.
Voir `knowledge/index.yaml` pour l'index de la base de connaissances.

## Tests

```bash
pip install ".[dev]"
pytest tests/ -v
```

## Licence

Propriétaire — Tous droits réservés.
