# AI Sports Coach — Plan Projet

> Repris après crash VPS — recréé le 05/05/2026 depuis le contexte reconstitué

## 1. Vision

Remplacer les coachs sportifs humains (100€+/mois) par des assistants d'entraînement IA (15-20€/mois), qualité supérieure car basée sur la science.

## 2. Positionnement

"Assistant d'entraînement IA" — PAS "coach sportif" (titre réglementé en France, Code du sport L.212-1, jusqu'à 1 an prison + 15 000€ amende).

## 3. Cibles initiales

Cyclistes, coureurs, triathlètes, fitness.

## 4. Différenciant clé

Chat IA conversationnel. Aucun concurrent (Freeletics, Runna, JOIN, FizzUp) ne dialogue avec l'utilisateur — ils génèrent des programmes, point. L'utilisateur peut parler à son assistant, poser des questions, ajuster en temps réel.

## 5. Distribution

Bots Telegram individuels par utilisateur. Flux :
1. L'utilisateur s'abonne (Stripe/Paddle)
2. Un bot Telegram dédié est créé automatiquement
3. Le bot vérifie que l'adresse mail correspond à un abonnement actif
4. L'utilisateur dialogue avec son assistant via ce bot

## 6. Fonctionnalités

### V1 (MVP)
- Chat IA conversationnel
- Planification de séances personnalisées (périodisation, charge progressive)
- Profil utilisateur (historique, blessures, objectifs, matos)
- Questionnaire PAR-Q obligatoire à l'inscription
- Disclaimers légaux ("ne remplace pas un médecin", transparence IA)
- Notifications Telegram proactives ("séance à venir", "tu n'as pas fait ta séance")

### V2 (post-étude utilisateurs)
- Conseils nutrition (recommandations générales type PNNS, pas de plans pathologiques)
- Gamification (badges, streaks, classements)
- Visuels de progression (graphiques, heatmaps)
- Plusieurs niveaux d'abonnement

## 7. Pricing

- Cible : 14,99€ - 19,99€/mois
- Coût LLM estimé : 0,05€ à 0,50€/mois/utilisateur → marges x30 à x400
- Possibilité d'upsell nutrition/avancé plus tard

## 8. Cadre légal (France)

### Autorisé
- Assistant sportif IA, planificateur de séances
- Programmes personnalisés basés sur les objectifs
- Conseils nutritionnels généraux (type PNNS)
- Données de santé avec consentement explicite + DPIA

### Interdit
- Se faire passer pour un coach diplômé
- Conseils médicaux, diagnostic, rééducation
- Plans nutrition pour pathologies (diabète, obésité…)
- Cacher que c'est une IA (EU AI Act Art. 50)

### À implémenter
- Questionnaire PAR-Q obligatoire
- Disclaimer : "ne remplace pas un professionnel de santé"
- Consentement GDPR Art. 9 pour données de santé
- Transparence : "vous interagissez avec une IA"
- Mentions légales + CGV

## 9. Concurrence

| App | Prix/mois | Chat IA | Cible |
|-----|-----------|---------|-------|
| Freeletics | 9,99-16,99€ | Non | Fitness |
| Runna | 15,99€ | Non | Running |
| JOIN | 14,99€ | Non | Cyclisme/running |
| FizzUp | 9,99€ | Non | Fitness |

Marketing à imiter : Runna et JOIN benchmarkent contre le coach humain à 100-300€, utilisent des chiffres concrets (+19,8% FTP).

## 10. Prochaines étapes

- [ ] Créer le repo GitHub
- [ ] Dashboard HTML de suivi projet
- [ ] Prototype du moteur de coach IA
- [ ] Maquette interface Telegram bot
- [ ] Plan technique (stack, infra, coûts)
- [ ] Stratégie marketing / lancement
