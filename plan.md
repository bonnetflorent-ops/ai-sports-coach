# AI Sports Coach — Plan Projet

> Mis à jour le 11/05/2026 — décisions techniques et coaching

## 1. Vision

Remplacer les coachs sportifs humains (100€+/mois) par des assistants d'entraînement IA (15-20€/mois), qualité supérieure car basée sur la science.

## 2. Positionnement

"Assistant d'entraînement IA" — PAS "coach sportif" (titre réglementé en France, Code du sport L.212-1, jusqu'à 1 an prison + 15 000€ amende).

## 3. Cibles initiales

Cyclistes, coureurs, triathlètes, fitness.

## 4. Différenciant clé

**Chat IA conversationnel personnalisé.** Aucun concurrent (Freeletics, Runna, JOIN, FizzUp) ne dialogue avec l'utilisateur — ils génèrent des programmes, point. L'utilisateur peut parler à son assistant, poser des questions, ajuster en temps réel. Le coach connaît son historique, ses blessures, son matériel, ses objectifs et adapte tout en continu.

## 5. Distribution

**1 bot Telegram multi-tenant gérant tous les utilisateurs.** Flux :
1. L'utilisateur s'abonne (Stripe/Paddle)
2. Il rejoint le bot Telegram @TonCoachBot
3. Le bot vérifie l'abonnement via email de l'utilisateur
4. Chaque utilisateur a un espace totalement isolé (user_id Telegram + RLS Supabase)

## 6. Décisions techniques clés

| Décision | Choix | Raison |
|----------|-------|--------|
| Modèle LLM | **DeepSeek V4 uniquement** | Rapport qualité/prix imbattable, suffisant pour le coaching |
| Provider | OpenRouter | Accès à DeepSeek, fallback possible, un seul compte |
| Framework bot | aiogram 3.x | Async natif, middleware multi-tenant, standard Python |
| API | FastAPI | Webhooks Telegram + API admin + futur portail web |
| Base de données | Supabase (PostgreSQL) | Managé, auth intégrée, pgvector, RLS |
| Déploiement | Docker sur VPS Hostinger | Maîtrisé, reproductible |
| Cache LLM | Cache sémantique | -80% sur questions redondantes |
| Calendrier | Google Calendar API | Le plus répandu, OAuth2, gratuit |

**Coût LLM projeté** : 0,15€ à 0,50€/mois/utilisateur (DeepSeek V4, 30 messages/jour).

## 7. Fonctionnalités

### V1 (MVP)
- [ ] Chat IA conversationnel personnalisé
- [ ] Onboarding intelligent (questions ciblées, une seule volée, max 5 questions)
- [ ] Planification de séances personnalisées (périodisation, charge progressive)
- [ ] Profil utilisateur (historique, blessures, objectifs, matériel)
- [ ] Intégration Google Calendar (lecture créneaux + écriture séances)
- [ ] Questionnaire PAR-Q obligatoire à l'inscription
- [ ] Safety handler : pour toute douleur → médecin + adaptation immédiate du plan
- [ ] Disclaimers légaux ("ne remplace pas un médecin", transparence IA)
- [ ] Notifications Telegram proactives ("séance à venir", "récap semaine")

### V2 (post-étude utilisateurs)
- [ ] Conseils nutrition (recommandations générales type PNNS)
- [ ] Gamification (badges, streaks)
- [ ] Visuels de progression (graphiques, heatmaps)
- [ ] Plusieurs niveaux d'abonnement
- [ ] Intégration iCal (Apple)
- [ ] Intégration Outlook

## 8. Base de connaissances (le cœur du coach)

Le système reposera sur une base de connaissances scientifiques structurée consultée en RAG (via pgvector) :

- Études scientifiques par sport
- Méthodologies d'entraînement (polarisé, pyramidal, seuil…)
- Plans types par niveau/sport/objectif
- Anatomie & biomécanique
- Nutrition sportive
- Récupération & sommeil
- Prévention des blessures
- Psychologie du sport

→ Voir `docs/base-connaissances.md` pour le détail

## 9. Prompt système

Le prompt est le coach. Il sera personnalisé par utilisateur à partir de son profil (sport, niveau, objectif, contraintes, matériel). Le prompt impose :
- Justification scientifique de chaque recommandation
- Alternatives quand pertinent
- Questions de suivi précises, groupées, pas ouvertes
- Reformulation des infos avant de générer un plan

→ Voir `docs/coaching.md` pour le design complet

## 10. Pricing

- Cible : 14,99€ - 19,99€/mois
- Coût LLM estimé : 0,15€ à 0,50€/mois/utilisateur → marges x30 à x100
- Possibilité d'upsell nutrition/avancé plus tard

## 11. Cadre légal (France)

| Autorisé | Interdit |
|----------|----------|
| Assistant sportif IA, planificateur | Se faire passer pour un coach diplômé |
| Programmes personnalisés | Conseils médicaux, diagnostic, rééducation |
| Conseils nutritionnels généraux (PNNS) | Plans nutrition pour pathologies |
| Adaptation entraînement si douleur signalée | Diagnostic sur une douleur |
| Données santé avec consentement + DPIA | Cacher que c'est une IA (EU AI Act Art. 50) |

**À implémenter obligatoirement :**
- Questionnaire PAR-Q
- Disclaimer : "ne remplace pas un professionnel de santé"
- Consentement GDPR Art. 9 pour données de santé
- Transparence : "vous interagissez avec une IA"
- Mentions légales + CGV

## 12. Concurrence

| App | Prix/mois | Chat IA | Sports | Force | Faiblesse |
|-----|-----------|---------|--------|-------|-----------|
| Freeletics | 9,99-16,99€ | Non | Fitness | Contenu vidéo quali | Zéro personnalisation conversationnelle |
| Runna | 15,99€ | Non | Running | Plans structurés, RP solide | Running uniquement, pas de chat |
| JOIN | 14,99€ | Non | Cyclisme/Running | Belle UI, data-driven | Coaching superficiel, pas de dialogue |
| FizzUp | 9,99€ | Non | Fitness | Contenu français | Pas d'IA, coaching inexistant |

→ Analyse détaillée dans `docs/concurrents.md`

## 13. Prochaines étapes

- [x] Créer le repo GitHub
- [x] Documentation technique complète (docs/)
- [ ] MVP bot Telegram minimum (onboarding + chat basique)
- [ ] Base de connaissances sportive (collecte + structuration)
- [ ] Intégration Stripe/Paddle
- [ ] Intégration Google Calendar
- [ ] Dashboard HTML de suivi projet
- [ ] Bêta fermée (20 utilisateurs gratuits)