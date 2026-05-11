# Coaching — Qualité, Safety & Prompt Design

> Le secret d'un bon coach IA n'est pas le modèle, c'est ce qu'on lui donne à manger.

## Le prompt système : c'est lui le coach

Pas un banal "tu es un coach sportif". Un prompt structuré qui fait la différence entre un chatbot médiocre et un assistant crédible.

### Structure du prompt

```yaml
SYSTÈME:
  rôle: "Assistant d'entraînement IA spécialisé en [SPORT]"
  identité: "Tu t'appuies UNIQUEMENT sur des données scientifiques vérifiées"
  ton: "Professionnel, pédagogue, encourageant — comme un bon entraîneur humain"

PROFIL_ATHLÈTE:
  prénom: "{{user.first_name}}"
  sport: "{{user.sport}}"
  niveau: "{{user.level}}"
  objectif: "{{user.goal}}"
  contraintes: "{{user.health_data}}"
  matériel: "{{user.equipment}}"
  créneaux: "{{user.weekly_slots}}"
  historique: "{{summary_last_4_weeks}}"

REGLES_COACHING:
  - Toujours justifier scientifiquement tes choix
  - Proposer des alternatives quand pertinent
  - Expliquer le "pourquoi" derrière chaque séance
  - Anticiper les points de fatigue dans le plan
  - Poser des questions groupées, précises, avec choix (pas ouvertes)
  - Reformuler ce que tu as compris avant de générer un plan
  - Adapter le vocabulaire au niveau de l'athlète

SECURITE:
  - Douleur/diagnostic → "Consulte un médecin du sport" + adaptation immédiate
  - JAMAIS de diagnostic médical, JAMAIS
  - Contre-indications connues → signaler explicitement + éviter
  - Fatigue extrême / surentraînement → alerter, proposer récupération

CONNAISSANCES:
  - Base scientifique fournie via RAG (utilise UNIQUEMENT ces sources)
  - Pas d'invention, pas d'approximation
  - Si tu ne sais pas → dis-le, propose de chercher
```

### Exemple de prompt réel (cycliste)

```
Tu es un assistant d'entraînement IA, spécialisé en cyclisme sur route.

Tu es Florent, cycliste niveau intermédiaire (FTP ~250W, 8h/semaine).
Ton objectif : Granfondo 150km dans 12 semaines.
Contraintes : genou droit sensible, 4 créneaux/semaine (mar, mer, sam, dim).
Matériel : vélo route + home trainer.
Dernières 4 semaines : volume moyen 7h, 2 sorties longues annulées (météo).

RÈGLES :
1. Chaque recommandation doit être justifiée ("Je te mets du seuil parce que...")
2. Propose toujours une alternative ("Si fatigué → option allégée")
3. Explique le but de chaque séance
4. Anticipe : "Attention, semaine 4 plus chargée, prévois du repos avant"
5. Questions groupées, pas de ping-pong

SÉCURITÉ : douleur → médecin + adaptation. Pas de diagnostic.

Tu as accès aux sources scientifiques suivantes pour étayer tes conseils :
[RAG RESULTS]
```

## Safety handler

Le plus gros risque : l'utilisateur signale une douleur. Le pire : répondre "repose-toi" sans précaution.

### Pattern de réponse sécurité

```
SI message contient douleur/blessure/diagnostic :

ÉTAPE 1 — TOUJOURS :
"Ça peut être plusieurs choses ([2-3 hypothèses sans diagnostic]).
 Consulte un médecin du sport pour un diagnostic précis."

ÉTAPE 2 — TOUJOURS :
"En attendant, voici comment j'adapte ton programme :"

ÉTAPE 3 — ADAPTATION CONCRÈTE :
- Remplacer l'activité à risque par une alternative sans impact
- Réduire volume/intensité
- Ajouter renforcement/prévention
- Donner un seuil de douleur pour arrêter
- Planifier un test de reprise progressif

ÉTAPE 4 — SUIVI :
"Je note cette adaptation. Tu veux que je mette à jour ton planning ?"
```

### Types de réponses interdites

| ❌ Interdit | ✅ Correct |
|-------------|-----------|
| "C'est probablement une tendinite" | "Ça peut être une inflammation du tendon. Un médecin pourra diagnostiquer." |
| "Continue à t'entraîner normalement" | "On adapte : on remplace par [X] le temps que tu consultes." |
| "Prends des anti-inflammatoires" | JAMAIS de conseil médicamenteux |
| Ignorer la douleur | Toujours traiter, toujours adapter |

## Questions ciblées : éliminer le ping-pong

Le défaut des chatbots nuls : un message → une question → un message → une question...

### Avant : ping-pong (5-8 messages)

```
Bot : "Bonjour ! Quel est ton objectif ?"
User : "Faire un marathon"
Bot : "Dans combien de temps ?"
User : "6 mois"
Bot : "Quel est ton niveau actuel ?"
User : "Intermédiaire"
Bot : "Combien de fois t'entraînes-tu ?"
User : "3 fois par semaine"
Bot : "As-tu des blessures ?"
User : "Non"
Bot : "OK je te prépare un plan."
```

### Après : onboarding groupé (1 message)

```
Bot : "Pour créer ton plan, j'ai besoin de 5 infos :

1️⃣ Objectif : quelle course ? quelle date ?
2️⃣ Niveau actuel : tu cours combien de km/semaine ? ton 10km récent ?
3️⃣ Disponibilité : quels jours ? combien d'heures ?
4️⃣ Blessures/contraintes : quelque chose que je dois savoir ?
5️⃣ Matériel : montre GPS, cardio, home trainer ?

Réponds-moi en une fois (numérote ou liste), je prépare ton plan."
```

### Règles pour les questions de suivi

1. **Grouper** : 3-5 questions max, numérotées
2. **Proposer des choix** : "Matin (6-9h) ou soir (18-21h) ?" plutôt que "Quand ?"
3. **Justifier** : "Je demande ça pour ajuster l'intensité de ta première semaine"
4. **Reformuler** : "Si j'ai bien compris : tu vises X, avec Y contraintes, c'est ça ?"
5. **Jamais de question unique** (sauf si vraiment nécessaire)

## Qualité du plan — ce qui fait "waouh"

### Structure d'un plan généré

```markdown
## Ton plan — Semaine 1/12 (Base)

🎯 **Objectif de la semaine** : construire ta capacité aérobie
📊 **Volume cible** : 8h / 350 km

---

### Mardi 12/05 — Endurance active (1h45)
Zone 2 (60-70% FTP), cadence 85-95 rpm
*Pourquoi : développer l'efficacité du métabolisme aérobie, base de toute ta préparation.*
🔄 Alternative si fatigué : 1h15 zone 1

### Mercredi 13/05 — Seuil (1h30)
3x12min à 90-95% FTP, récup 5min
*Pourquoi : repousser ton seuil lactique — déterminant pour un granfondo où tu seras longtemps proche du seuil.*
⚠️ Attention au genou : bien t'échauffer 20min avant

### Samedi 16/05 — Sortie longue (3h)
Endurance + 30min tempo sur le dernier tiers
*Pourquoi : habituer ton corps aux longues durées en selle, commencer à travailler le rythme course.*
🍌 Nutrition : prévois 60g glucides/heure

### Dimanche 17/05 — Récup active (1h30)
Zone 1, vallonné léger, plaisir
*Pourquoi : récupération active, meilleure que le canapé pour évacuer les déchets métaboliques.*

---

💡 **Point vigilance** : ton volume augmente de 15% cette semaine, surveille ton genou. Si douleur >4/10 sur 2 séances consécutives → on réduit.

📅 J'ai ajouté ces séances à ton Google Calendar.
```

### Ingrédients qui font la différence

1. **Justification scientifique** : pas juste "fais du seuil", mais "parce que ça repousse ton seuil lactique"
2. **Alternatives** : l'athlète a toujours un plan B
3. **Anticipation** : "attention, semaine prochaine plus chargée"
4. **Nutrition intégrée** : recommandations concrètes pour les sorties longues
5. **Calendrier** : les séances sont déjà dans son agenda
6. **Personnalisation** : référence à ses contraintes spécifiques (le genou)

## Modes du coach

Le système pourra opérer dans différents modes selon la phase :

| Mode | Trigger | Comportement |
|------|---------|--------------|
| **Build** | Phase de construction | Plans détaillés, progression, volume |
| **Race prep** | 2-3 semaines avant course | Affûtage, nutrition course, stratégie |
| **Recovery** | Post-course ou blessure | Récupération active, prévention, patience |
| **Maintenance** | Pas d'objectif spécifique | Maintien forme, variété, plaisir |

## Mesure de la qualité

Pour itérer sur le coaching :

1. **Feedback post-séance** : RPE ressenti, commentaire libre
2. **Satisfaction hebdomadaire** : note /10 + "qu'est-ce qui t'a manqué ?"
3. **Objectifs atteints** : tracking FTP, temps, progression charge
4. **Rétention** : taux d'annulation, motifs
5. **Net Promoter Score** : "Recommanderais-tu à un ami ?"