# Session State — PWA AI Sports Coach

> Reprise session 2026-06-09. Tout le code est dans ce worktree.

## Worktree

- **Chemin** : `C:\Projets\ai-sports-coach\.worktrees\pwa-implementation`
- **Branche** : `feature/pwa-implementation`
- **Base** : `master` (commit `5db8697`)

## Commits (14 au total)

```
f0e3dbf fix: correction onboarding — level string→int, colonnes manquantes, ParQForm answers→items
bf5255c docs: mettre à jour CLAUDE.md — DeepSeek direct, supabase-py 2.x, gotchas PWA
8add033 feat: bannière d'installation PWA (PwaInstallBanner)
10907c6 feat: intégration réelle — PWA, auth, chat DeepSeek, push notifications
36a8eaf docs: session state file for resumption
edfdc5c feat(c-g): remaining frontend — dashboard, onboarding, profile, error handling
5614165 fix: UTF-8 encoding for knowledge loader on Windows
59d32dc feat(c-e): remaining API endpoints — athlete, onboarding, dashboard, feedback, summarizer
18d956b feat(g): deployment setup + analytics tracking
530b032 feat(a.3-b.2): backend API — auth, chat SSE, rate limiting, profile
e94afa7 feat(c-f): engine modules — safety, athlete model, weekly rollup, proactive
0f6fda0 feat(a.3-b.4): frontend — auth pages, layout nav, chat UI, hooks
d0d3cbb feat(a.2): add PWA database tables + RLS policies
1316855 feat(a.1): scaffold Next.js 15 + shadcn/ui + PWA config
```

## État des tests

- **Backend** : 95/95 passent (excluant bot/ et integration/)
- **Frontend** : Build Next.js propre, 6 routes, 0 erreur TypeScript. Pas de tests Jest/Vitest.

## Déploiement réel

L'app est déployée sur un **VPS Hostinger** (srv780916, IP 195.35.24.232) :

```
Navigateur ──HTTPS──▶ Traefik (:443) ──▶ pwa.srv780916.hstgr.cloud      → conteneur frontend (:3000)
                                      ──▶ pwa-api.srv780916.hstgr.cloud  → conteneur backend (:8000)
```

- **Reverse proxy** : Traefik (pas Nginx), network_mode: host, écoute 80/443
- **Pas de proxy /api/*** : le frontend appelle l'API directement via son sous-domaine
- **Supabase** : externe, projet `qorxhwpoxcdxbnnlfjpp`
- **LLM** : DeepSeek direct (`api.deepseek.com`), pas OpenRouter

## Ce qui est fait (checklist du plan)

- [x] A.1 : Scaffold Next.js 15 + shadcn/ui + PWA config
- [x] A.2 : Supabase tables, RLS, pgvector
- [x] A.3 : Auth (register/login/refresh) + pages frontend
- [x] A.4 : Layout (Header, TabNavigation, BottomNav)
- [x] A.5 : Rate limiting + Profile API
- [x] A.6 : PWA Service Worker + icons + manifest
- [x] B.1 : FastAPI app + CORS + SSE infrastructure
- [x] B.2 : POST /api/chat/message (SSE stream)
- [x] B.3 : Chat UI (useChat, MessageBubble, MessageInput, StreamingText)
- [x] B.4 : Feedback 👍👎
- [x] B.5 : Safety handler + AI transparency badge
- [x] C.1 : Summarizer (résumé quotidien structuré JSON)
- [x] C.2 : Athlete Model Manager (CRUD, versioning, priority merge)
- [x] C.3 : Weekly Rollup Engine
- [x] C.4 : Badge "Ce que ton coach sait" (AthleteKnowledge component)
- [x] D.1 : Dashboard API (metrics, chart, recap)
- [x] D.2 : Dashboard UI (MetricCard, LoadChart, UpcomingSession)
- [x] E.1 : Onboarding API (3 phases)
- [x] E.2 : Onboarding UI (OnboardingFlow, Phase1/2/ParQ forms)
- [x] F.1 : Proactive coach cron (5 triggers)
- [x] F.2 : Web Push + Service Worker handler
- [x] G.1 : ErrorBoundary + skeleton loaders + empty/error states
- [x] G.2 : Bug report page
- [x] G.3 : Analytics tracking
- [x] G.4 : Deployment setup (Dockerfile, deploy.md, .env.example)
- [x] Intégration réelle : auth, chat DeepSeek, push notifications, icônes PWA
- [x] Bannière d'installation PWA (PwaInstallBanner)
- [x] Déploiement sur VPS Hostinger avec Traefik

## Reste à faire (avant merge)

### Corrections production
- [x] Fix onboarding : level string→int + colonnes manquantes (migration 004)
- [x] Fix ParQForm : `answers` → `items` pour matcher le backend
- [ ] Exécuter la migration 004 (`equipment`, `weekly_slots`, `onboarding_phase`, `parq_responses`, `parq_any_yes`)
- [ ] Rebuilder et redéployer le backend suite aux corrections onboarding
- [ ] Rebuilder et redéployer le frontend suite au fix ParQForm
- [ ] Vérifier `telegram_id` NOT NULL : exécuter `ALTER TABLE users ALTER COLUMN telegram_id DROP NOT NULL;` si pas déjà fait

### Polish
- [x] Icônes PWA réelles (placeholder 1x1 remplacé)
- [x] Tests end-to-end (scaffolding Playwright créé)
- [x] VAPID config + endpoint push API + hook usePush
- [x] Mode hors-ligne amélioré (offline.html + fallback navigation)
- [ ] Lighthouse PWA audit ≥ 90% (nécessite backend réel + HTTPS local)
- [ ] Tests de performance (taille des bundles, chargement)
- [ ] Exécuter les tests E2E Playwright (nécessite backend local)

### Optionnel / Phase 2
- [ ] Mode hors-ligne amélioré (cache plus agressif)
- [ ] Thème clair
- [ ] i18n (anglais)
- [ ] Admin dashboard (DAU, messages/jour, etc.)
- [ ] Intégration Google Fit / Strava / Garmin
- [ ] Export des données (RGPD)
- [ ] Dark mode toggle

## Commandes utiles

```bash
# Aller dans le worktree
cd C:\Projets\ai-sports-coach\.worktrees\pwa-implementation

# Lancer le frontend
cd frontend && npm run dev

# Lancer le backend
/c/Users/bonne/AppData/Local/Python/pythoncore-3.14-64/python.exe -m uvicorn src.api.main:app --reload --port 8000

# Tests backend
/c/Users/bonne/AppData/Local/Python/pythoncore-3.14-64/python.exe -m pytest tests/ --ignore=tests/bot --ignore=tests/integration -v

# Build frontend
cd frontend && npm run build

# Vérifier l'API en production
curl https://pwa-api.srv780916.hstgr.cloud/api/health

# Connexion directe à Supabase (pooler PgBouncer)
# Host: aws-0-eu-west-3.pooler.supabase.com, port 6543
# User: postgres.qorxhwpoxcdxbnnlfjpp, DB: postgres
```

## Architecture du projet

```
ai-sports-coach/
├── frontend/          # Next.js 16 PWA (App Router, shadcn/ui, Tailwind v4)
│   └── src/
│       ├── app/       # Routes: /, /dashboard, /onboarding, /profile, /auth/*
│       ├── components/# chat/, dashboard/, onboarding/, profile/, layout/, ui/
│       ├── hooks/     # useChat, useDashboard, useAthleteModel, usePush
│       ├── lib/       # api.ts (SSE), supabase.ts, utils.ts
│       └── types/     # TypeScript types
├── src/               # Backend Python (FastAPI)
│   ├── api/           # Endpoints: auth, chat, dashboard, athlete, onboarding, feedback, profile, push
│   ├── engine/        # Logic: summarizer, athlete_model, safety, proactive, weekly_rollup
│   ├── db/            # Supabase CRUD
│   ├── cli/           # proactive.py (cron entrypoint)
│   └── migrations/    # SQL: 001_tables, 002_rls, 003_vault, 004_onboarding
├── docker/            # Dockerfile
├── knowledge/         # Base de connaissances coaching (markdown + index.yaml)
└── docs/              # deploy.md, architecture.md, coaching.md, spec-pwa.md
```

## Notes importantes

- Python 3.14 est dans `C:\Users\bonne\AppData\Local\Python\pythoncore-3.14-64\python.exe`
- Le projet utilise `bash` comme shell (Git Bash sur Windows)
- Les warnings CRLF/LF sont normaux sur Windows, ignorer
- pyiceberg ne build pas sur Windows → installer supabase avec `--no-deps` puis les sous-packages individuellement
- Le encoding fix (UTF-8) dans knowledge.py est essentiel sur Windows
- Les scripts `npm run dev` et `npm run build` incluent déjà `--webpack`, ne pas le rajouter
- `level` est SMALLINT en DB (1,2,3) — le backend convertit via LEVEL_MAP
- migration 004 (`equipment`, `weekly_slots`, `onboarding_phase`, `parq_responses`, `parq_any_yes`) doit être exécutée pour l'onboarding
