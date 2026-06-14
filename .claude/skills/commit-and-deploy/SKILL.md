---
name: commit-and-deploy
description: |
  Use this skill whenever the user asks to commit, deploy, "commit et déploie",
  "déploie", "push to production", or after a bugfix is complete and they want
  to ship it. Automates the full commit → verify → deploy pipeline for this
  project (AI Sports Coach PWA). Frontend is on Vercel (managed by Claude),
  backend is on VPS Hostinger with Docker/Traefik (managed by Hermes Agent).
  Also use when the user says "je veux déployer", "on déploie", "ship it",
  "mettez en production", or asks for deployment instructions after a fix.
---

# Commit & Déployer — AI Sports Coach

## Architecture cible

```
Frontend (Vercel) ──HTTPS──▶ Backend (VPS Hostinger)
       ▲                          ▲
  Géré par Claude            Géré par Hermes Agent
  (vercel deploy)            (Docker + Traefik)
```

## Workflow

Suis ces étapes dans l'ordre après chaque bugfix :

### Étape 1 : Vérifier les correctifs

```bash
# Frontend build — OBLIGATOIRE (--webpack, pas Turbopack)
cd frontend && SERWIST_SUPPRESS_TURBOPACK_WARNING=1 npx next build --webpack

# Backend tests unitaires
/c/Users/bonne/AppData/Local/Python/pythoncore-3.14-64/python.exe -m pytest tests/ --ignore=tests/bot --ignore=tests/integration -v
```

**Si build échoue ou tests échouent → STOP. Ne pas commiter. Corriger d'abord.**

### Étape 2 : Commiter

Faire un commit atomique avec un message en français. Format :

```
<type>: <description courte en français>

- Point 1 détaillant le changement
- Point 2 détaillant un autre changement

Co-Authored-By: Claude <noreply@anthropic.com>
```

Types : `fix:` (bugfix), `feat:` (nouveauté), `refactor:`, `docs:`, `chore:`

Ne commiter QUE les fichiers liés au correctif. Si d'autres fichiers sont modifiés, les mentionner à l'utilisateur.

### Étape 2b : Pusher vers GitHub ⚠️ OBLIGATOIRE

Hermes Agent (le gestionnaire du VPS Hostinger) se connecte à GitHub pour pull les mises à jour backend. **Toujours pusher après chaque commit**, sinon le backend ne pourra pas être mis à jour.

```bash
git push origin feature/pwa-implementation
```

Vérifier que le push a réussi avant de continuer.

### Étape 3 : Déployer le frontend sur Vercel

Le frontend est hébergé sur Vercel. Pour déployer :

1. D'abord vérifier l'authentification Vercel :
   ```
   mcp__plugin_vercel_vercel__authenticate
   ```
   Si pas encore authentifié, demander à l'utilisateur de compléter le flow OAuth.

2. Une fois authentifié, utiliser les outils Vercel MCP pour déployer :
   - Lister les projets pour trouver le projet frontend
   - Déclencher un déploiement du dossier `frontend/`

3. Si les outils Vercel ne sont pas disponibles, utiliser le skill `vercel:deploy` :
   ```
   Skill: vercel:deploy
   ```

4. Si rien n'est disponible, fournir la commande manuelle à l'utilisateur :
   ```bash
   cd frontend && npx vercel --prod
   ```

Après déploiement, annoncer l'URL de preview et/ou production.

### Étape 4 : Instructions backend pour Hermes Agent

Lister UNIQUEMENT les fichiers backend modifiés. Si aucun → "Aucun changement backend."

Format du bloc Hermes Agent :

```
### 🤖 Pour Hermes Agent (VPS Hostinger)

**Backend modifié :** [oui/non]

[Si oui, lister chaque fichier :]
- Fichier: src/xxx.py
- Changement: ligne N, description exacte
  AVANT:  ancien_code
  APRÈS:  nouveau_code

**Action requise :**
- git pull sur le VPS
- Rebuild image : docker build -t ai-sports-coach -f docker/Dockerfile .
- Redémarrage : docker stop coach-api && docker rm coach-api && docker run -d --name coach-api --env-file .env --restart unless-stopped --label "traefik.enable=true" --label "traefik.http.routers.coach-api.rule=Host(\`pwa-api.srv780916.hstgr.cloud\`)" --label "traefik.http.routers.coach-api.entrypoints=websecure" --label "traefik.http.routers.coach-api.tls.certresolver=letsencrypt" ai-sports-coach
```

### Étape 5 : Résumé final

Produire un résumé clair :

```
## ✅ Déploiement terminé

**Commit :** <hash> — <message>

**Frontend (Vercel) :**
- Preview : <url-preview>
- Production : https://pwa.srv780916.hstgr.cloud (ou URL Vercel)

**Backend (VPS) :**
- [Aucun changement] OU [Instructions envoyées à Hermes Agent]
```

## Règles

- **Ne JAMAIS déployer sans build vert + tests verts**
- **Un commit = un bugfix** — pas de mélange
- **Messages de commit en français**
- **Toujours inclure le bloc Hermes Agent** pour le backend, même s'il est vide
- **Le frontend est prioritaire** — c'est Claude qui le gère via Vercel
- **Le backend change rarement** — ne pas inventer de changements backend
- **Si le déploiement Vercel échoue**, donner la commande manuelle à l'utilisateur
