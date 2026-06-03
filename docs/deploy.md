# AI Sports Coach — Guide de déploiement

## Architecture

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  Vercel     │────▶│  VPS Docker │────▶│  Supabase   │
│  Frontend   │     │  Backend    │     │  DB + Auth  │
│  Next.js 16 │     │  FastAPI    │     │  pgvector   │
└─────────────┘     └─────────────┘     └─────────────┘
                           │
                           ▼
                    ┌─────────────┐
                    │  OpenRouter │
                    │  DeepSeekV4 │
                    └─────────────┘
```

## Prérequis

- Compte Vercel (frontend)
- VPS avec Docker (backend) — recommandé: 2 vCPU, 4 GB RAM
- Projet Supabase (base de données + auth)
- Clé API OpenRouter
- Domaine: coach-sportif.app

## 1. Supabase

### 1.1 Créer le projet
1. Aller sur https://supabase.com
2. Créer un nouveau projet
3. Noter l'URL et les clés (anon, service_role)

### 1.2 Exécuter les migrations
1. SQL Editor → Nouvelle requête
2. Exécuter `src/migrations/001_pwa_tables.sql`
3. Exécuter `src/migrations/002_rls_policies.sql`
4. Activer Vault dans Dashboard > Settings > Vault
5. Exécuter `src/migrations/003_enable_vault.sql`

### 1.3 Configurer l'auth
1. Authentication > Settings
2. Activer "Email" provider (sans confirmation pour MVP)
3. Site URL: https://coach-sportif.app
4. Redirect URLs: http://localhost:3000/**, https://coach-sportif.app/**

## 2. Backend (VPS Docker)

### 2.1 Variables d'environnement
Créer `/app/.env` sur le VPS:
```bash
OPENROUTER_API_KEY=sk-or-...
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
LLM_MODEL=deepseek/deepseek-chat
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_SERVICE_ROLE_KEY=eyJ...
SUPABASE_ANON_KEY=eyJ...
GEMINI_API_KEY=...
CORS_ORIGINS=["http://localhost:3000","https://coach-sportif.app"]
VAPID_PRIVATE_KEY=...
VAPID_PUBLIC_KEY=...
VAPID_SUBJECT=mailto:admin@coach-sportif.app
HEALTH_ENCRYPTION_KEY=...
```

### 2.2 Build et run
```bash
# Sur le VPS
cd /app
docker build -t ai-sports-coach -f docker/Dockerfile .
docker run -d \
  --name coach-api \
  --env-file .env \
  -p 8000:8000 \
  --restart unless-stopped \
  ai-sports-coach
```

### 2.3 Cron jobs
```cron
# AI Sports Coach — Proactive coach
0 8 * * * cd /app && docker exec coach-api python -m src.cli.proactive >> /var/log/coach-proactive.log 2>&1
0 18 * * * cd /app && docker exec coach-api python -m src.cli.proactive >> /var/log/coach-proactive.log 2>&1

# RGPD cleanup — delete expired messages
0 3 * * * docker exec coach-api psql $DATABASE_URL -c "SELECT cleanup_expired_messages();" >> /var/log/coach-cleanup.log 2>&1
```

### 2.4 Reverse proxy (nginx)
```nginx
server {
    listen 443 ssl;
    server_name api.coach-sportif.app;

    ssl_certificate /etc/letsencrypt/live/api.coach-sportif.app/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.coach-sportif.app/privkey.pem;

    location / {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_buffering off;  # Important pour SSE
    }
}
```

## 3. Frontend (Vercel)

### 3.1 Variables d'environnement Vercel
```bash
vercel env add NEXT_PUBLIC_SUPABASE_URL
vercel env add NEXT_PUBLIC_SUPABASE_ANON_KEY
vercel env add NEXT_PUBLIC_API_URL
```

Valeurs:
- `NEXT_PUBLIC_SUPABASE_URL`: URL Supabase
- `NEXT_PUBLIC_SUPABASE_ANON_KEY`: Clé anon Supabase
- `NEXT_PUBLIC_API_URL`: https://api.coach-sportif.app

### 3.2 Déployer
```bash
cd frontend
vercel --prod
```

## 4. Vérification post-déploiement

- [ ] `curl https://api.coach-sportif.app/api/health` → `{"status": "ok"}`
- [ ] Frontend accessible sur https://coach-sportif.app
- [ ] Register → Login → Chat fonctionnel
- [ ] SSE streaming fonctionnel
- [ ] PWA installable (Lighthouse PWA ≥ 90%)
- [ ] Push notifications fonctionnelles
- [ ] Cron jobs actifs (vérifier logs après 24h)

## 5. Rollback

```bash
# Frontend
vercel rollback

# Backend
docker stop coach-api
docker run -d --name coach-api --env-file .env -p 8000:8000 ai-sports-coach:previous
```
