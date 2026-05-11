# AI Sports Coach 🏃‍♂️🚴‍♀️

> Assistant d'entraînement IA conversationnel — le premier coach dans ta poche qui te parle vraiment.

## Vision

Remplacer les coachs sportifs humains (100€+/mois) par une IA de qualité professionnelle à 15-20€/mois. Pas juste un générateur de plans — un assistant qui dialogue, comprend ton contexte, adapte en temps réel.

## Pourquoi ça va marcher

**Aucun concurrent n'a de vrai chat IA.** Freeletics, Runna, JOIN, FizzUp génèrent des programmes. Aucun ne te dit "J'ai vu que t'as mal dormi, on adapte ta séance du jour".

## Stack

| Composant | Technologie |
|-----------|-------------|
| Distribution | Telegram (bot unique multi-tenant) |
| LLM | DeepSeek V4 (via OpenRouter) |
| Framework bot | aiogram 3.x |
| API/Backend | FastAPI |
| Base de données | Supabase (PostgreSQL + pgvector) |
| Déploiement | Docker sur VPS Hostinger |

## Documentation

- [📋 Plan projet](plan.md) — Vision, fonctionnalités, roadmap
- [🏗️ Architecture technique](docs/architecture.md) — Stack, multi-tenant, schéma DB, flux
- [🧠 Coaching](docs/coaching.md) — Prompt système, safety, qualité, onboarding
- [📚 Base de connaissances](docs/base-connaissances.md) — RAG, sources scientifiques, structure
- [🔍 Analyse concurrentielle](docs/concurrents.md) — Marché, concurrents, SWOT

## Statut

🚧 **Phase : Documentation & prototypage** — MVP en développement.