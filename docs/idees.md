# 💡 Idées & Évolutions Futures

> Brainstorming post-MVP, priorisation à venir après la bêta fermée.

---

## 1. Parcours d'inscription post-beta (site web + double bot)

Une fois la phase de bêta test terminée et avant le lancement payant :

- **Site vitrine / landing** : les clients s'inscrivent sur un site web (formulaire email + Stripe/Paddle)
- **Bot de vérification** : après inscription, le client est dirigé vers un premier bot Telegram qui vérifie que l'adresse email correspond bien à un client payant (lien email ↔ Telegram ID)
- **Message d'accueil enrichi** : ce bot de vérification affiche :
  - Les consignes d'utilisation
  - Les tips pour tirer le meilleur de l'assistant
  - Les règles (limites, cadre légal, ce que le bot ne fait pas)
  - Un lien vers le **bot assistant final** (@TonCoachBot)
- Ce flux remplace l'onboarding actuel qui mélange inscription et coaching

**Avantages :**
- Parcours client pro et rassurant
- Séparation claire : acquisition (site) → vérification (bot 1) → coaching (bot 2)
- Le message d'accueil peut être modifié sans toucher au bot coach
- Réduit la friction : le client sait exactement à quoi s'attendre avant de commencer

---

## 2. Dashboard personnel & transparence des données

Deux fonctionnalités complémentaires :

### 2a. « Qu'est-ce que tu sais de moi ? »

Le client peut demander à son assistant ce qu'il sait de lui. Le bot répond avec un résumé clair et transparent :

- Données de profil (prénom, sport, niveau, objectif, FTP/VDOT...)
- Données physiologiques (poids, taille, âge, sexe) — si fournies
- Historique récent (dernières séances, progression)
- Blessures signalées et adaptations en cours
- Option : « Veux-tu modifier ou supprimer quelque chose ? »

**Pourquoi c'est important :**
- Confiance : le client voit exactement ce qui est stocké
- RGPD : droit d'accès facilité, directement dans le chat
- Utilitaire : le client peut corriger des infos obsolètes sans refaire l'onboarding

### 2b. Dashboard visuel de suivi

Un espace web connecté à la base de données du bot pour un suivi visuel :

- **Graphiques de progression** : charge d'entraînement (CTL), forme (TSB), volume hebdomadaire
- **Heatmaps** : répartition des séances par type/intensité sur le mois
- **KPIs clés** : FTP/VDOT estimé, régularité, streak actuel
- **Design sobre et épuré** : inspiré des dashboards Strava/TrainingPeaks mais en plus simple

**Technique envisagée :**
- Frontend léger (React/Vite ou même HTML vanilla + Chart.js)
- Connecté à Supabase en lecture seule (RLS : chaque client voit ses données)
- Accessible via un lien unique généré par le bot
- Pas d'auth séparée : lien signed URL ou token JWT temporaire

**Lien avec le plan existant :** déjà mentionné en V2 sous « Visuels de progression (graphiques, heatmaps) » — cette idée précise l'approche.

---

## 3. Note sur les idées déjà au plan

Le fichier `plan.md` contient déjà ces fonctionnalités prévues :

| Idée | Statut |
|------|:------:|
| Visuels de progression (graphiques, heatmaps) | V2 — en lien avec l'idée 2b |
| Gamification (badges, streaks) | V2 |
| Conseils nutrition (PNNS) | V2 |
| Intégration iCal & Outlook | V2 |
| Plusieurs niveaux d'abonnement | V2 |
| Notifications proactives (séance à venir, récap semaine) | V1 |

Les idées **1** (parcours inscription) et **2a** (transparence données) sont nouvelles et n'apparaissent pas encore dans le plan.
