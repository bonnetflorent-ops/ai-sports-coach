# Session State — PWA AI Sports Coach

> Reprise session 2026-06-03. Tout le code est dans ce worktree.

## Worktree

- **Chemin** : `C:\Projets\ai-sports-coach\.worktrees\pwa-implementation`
- **Branche** : `feature/pwa-implementation`
- **Base** : `master` (commit `5db8697`)

## Commits (9 au total)

```
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
- **Frontend** : Build Next.js propre, 6 routes, 0 erreur TypeScript

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

## Reste à faire (avant merge)

### Intégration réelle (vs stubs/mocks)
- [ ] Tester auth avec une vraie DB Supabase
- [ ] Tester chat SSE avec OpenRouter réel
- [ ] Exécuter les migrations SQL sur Supabase
- [ ] Configurer les variables d'environnement réelles

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
uvicorn src.api.main:app --reload --port 8000

# Tests backend (Python dans AppData)
/c/Users/bonne/AppData/Local/Python/pythoncore-3.14-64/python.exe -m pytest tests/ --ignore=tests/bot --ignore=tests/integration -v

# Build frontend
cd frontend && SERWIST_SUPPRESS_TURBOPACK_WARNING=1 npx next build --webpack
```

## Architecture du projet

```
ai-sports-coach/
├── frontend/          # Next.js 16 PWA (App Router, shadcn/ui, Tailwind)
│   └── src/
│       ├── app/       # Routes: /, /dashboard, /onboarding, /profile, /auth/*
│       ├── components/# chat/, dashboard/, onboarding/, profile/, layout/, ui/
│       ├── hooks/     # useChat, useDashboard, useAthleteModel, usePush
│       ├── lib/       # api.ts (SSE), supabase.ts, utils.ts
│       └── types/     # TypeScript types
├── src/               # Backend Python (FastAPI)
│   ├── api/           # Endpoints: auth, chat, dashboard, athlete, onboarding, feedback, profile
│   ├── engine/        # Logic: summarizer, athlete_model, safety, proactive, weekly_rollup
│   ├── db/            # Supabase CRUD
│   ├── cli/           # proactive.py (cron entrypoint)
│   └── migrations/    # SQL: tables, RLS, vault
├── docker/            # Dockerfile
└── docs/              # deploy.md, spec-pwa.md, memoire.md
```

## Notes importantes

- Python 3.14 est dans `C:\Users\bonne\AppData\Local\Python\pythoncore-3.14-64\python.exe`
- Le projet utilise `bash` comme shell (Git Bash sur Windows)
- Les warnings CRLF/LF sont normaux sur Windows, ignorer
- pyiceberg ne build pas sur Windows → installer supabase avec `--no-deps` puis les sous-packages individuellement
- Le encoding fix (UTF-8) dans knowledge.py est essentiel sur Windows
- @serwist/next nécessite `--webpack` (pas compatible Turbopack)
