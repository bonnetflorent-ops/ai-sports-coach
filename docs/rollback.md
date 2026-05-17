# Procédure de Rollback

## En cas de problème post-déploiement

```bash
cd ~/ai-sports-coach

# 1. Revenir au commit précédent
git log --oneline -3  # Trouver le commit stable
git revert <commit-id>

# 2. Redéployer la version stable
docker compose down
docker compose up -d --build

# 3. Vérifier
curl http://localhost:8000/health
docker compose logs --tail=20
```

## Rollback urgent (sans git)

```bash
cd ~/ai-sports-coach
docker compose stop
# Restaurer le backup local du .env si corrompu
cp .env.backup .env
docker compose up -d --build
```

## Contacts d'urgence

- **OpenRouter status** : https://status.openrouter.ai
- **Supabase status** : https://status.supabase.com
- **Support VPS Hostinger** : tableau de bord Hostinger → Support
- **Repo GitHub** : https://github.com/bonnetflorent-ops/ai-sports-coach
