# Changelog

## [0.2.0] — 2026-05-15

### Added
- Logging structuré (structlog)
- Tracking des coûts LLM par utilisateur (cost_tracker.py)
- Quota quotidien par utilisateur (0.50€/jour max via cost_tracker)
- Procédure de rollback (docs/rollback.md)
- Checklist pre-lancement (docs/pre-launch-checklist.md)
- Test d'intégration du flux complet (tests/integration/test_full_flow.py)

### Changed
- Logging standard remplacé par structlog (src/utils/logging_setup.py)
- Coûts réels sauvegardés dans chat_messages (plus de 0.0)

## [0.1.0] — 2026-05-14

### Added
- Moteur de connaissances complet (30 concepts, 7 domaines, 2393 lignes)
- Index YAML (knowledge/index.yaml)
- Loader connaissances (knowledge.py)
- Sélecteur LLM (selector.py) avec fallback mot-clé
- Prompt builder (prompt_builder.py)
- Couche DB Supabase (users, sessions)
- Schéma SQL initial
- Contenu scientifique : 7 fichiers markdown
- Handlers bot (start, chat, feedback)
- Tests unitaires (parser onboarding, sélecteur, prompt builder, knowledge loader)
- Retry + circuit breaker sur les appels OpenRouter
- Tracking des tokens réels (chat_with_metrics)
- 5 nouveaux domaines de connaissance (domaines 8-12, 15/05/2026)

## [0.0.1] — 2026-05-13

### Added
- Bot MVP avec onboarding et chat
- Pipeline LLM 2 étages (sélecteur + coach)
- Base connaissances initiale
- Schéma Supabase + RLS
