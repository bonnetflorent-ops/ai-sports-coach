# Checklist Pre-Lancement

## Tests
- [ ] `pytest tests/ -v` → tous les tests passent
- [ ] Test manuel du bot Telegram avec un vrai compte
- [ ] Test onboarding complet (6 questions + détails)
- [ ] Test question coaching (3 échanges minimum)
- [ ] Test détection douleur (critical path)

## Infrastructure
- [ ] Docker build + up sans erreur
- [ ] `curl /health` retourne `{"status": "healthy"}` (Phase 3)
- [ ] `curl /metrics` retourne des métriques (Phase 3)
- [ ] Webhook HTTPS accessible depuis internet (Phase 3)
- [ ] Logs visibles (`docker compose logs`)
- [ ] Aucune instance fantôme (`ps aux | grep src.bot.main`)

## Base de données
- [ ] `check_connection()` retourne OK
- [ ] RLS fonctionnel (tester isolation entre 2 utilisateurs)
- [ ] Backup Supabase activé (dashboard Supabase)
- [ ] Schéma SQL à jour (scripts/schema.sql)

## Coûts
- [ ] Quota quotidien par utilisateur configuré (0.50€/jour)
- [ ] Budget OpenRouter défini + alerte activée
- [ ] Prix estimé par utilisateur/mois documenté (0.15-0.50€)
- [ ] Cost tracker fonctionnel (logs structlog)

## Sécurité
- [ ] `.env` jamais dans git (vérifié via `git log --all -- .env`)
- [ ] HTTPS actif sur le webhook (Phase 3)
- [ ] RLS testé (utilisateur A ne voit pas données utilisateur B)
- [ ] Mention RGPD dans le message d'accueil (Phase 5)
- [ ] Questionnaire PAR-Q intégré

## Monitoring
- [ ] Health check cron job actif (Phase 3)
- [ ] Alertes configurées si /health != healthy (Phase 3)
- [ ] Logs structurés (structlog) fonctionnels
- [ ] Circuit breaker OpenRouter actif

## Documentation
- [ ] README.md à jour
- [ ] CHANGELOG.md à jour
- [ ] docs/rollback.md complet
- [ ] docs/architecture.md à jour
- [ ] docs/coaching.md à jour
