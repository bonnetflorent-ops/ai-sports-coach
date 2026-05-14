# Spécification du Sélecteur de Connaissances — AI Sports Coach

## Architecture

```
MESSAGE UTILISATEUR
       │
       ▼
┌─────────────────────┐
│  SÉLECTEUR LLM      │  ← Petit call LLM (GPT-4o-mini / DeepSeek V4)
│  Analyse la question │     Coût: ~0.001€ par message
│  + profil utilisateur│
│  + historique récent │
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│  IDs des concepts   │  Ex: ["recuperation/sommeil", "seances/travail-seuil"]
│  + niveau cible     │
│  + priorité          │
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│  PROMPT BUILDER     │  Charge les lignes Layer N de chaque concept
│  Assemble le prompt │  Ajoute le profil utilisateur + règles coaching
│  système complet    │
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│  LLM COACH          │  DeepSeek V4 / Sonnet 4
│  Réponse finale     │  Avec tout le contexte injecté
└─────────────────────┘
```

---

## 1. Le Sélecteur LLM (Prompt Système)

Ce prompt est envoyé à un petit LLM rapide et pas cher. Il prend en entrée :
- La question de l'utilisateur
- Son profil (niveau, sport(s), objectif actuel)
- Les 3 derniers messages échangés (pour le contexte)
- Son état actuel si connu (CTL, TSB, fatigue déclarée)

Le sélecteur retourne un JSON structuré avec les concepts à injecter.

### Prompt

```
Tu es un classifieur spécialisé en sciences du sport. Ta seule mission est de
sélectionner les concepts de connaissance les plus pertinents pour répondre à
la question d'un utilisateur.

Tu reçois :
1. La question de l'utilisateur
2. Son profil (niveau, sport, objectif)
3. Ses 3 derniers messages (contexte)

Tu dois retourner UNIQUEMENT un objet JSON avec ce format exact :

{
  "concepts": ["id/concept1", "id/concept2", ...],
  "level": 1,
  "reasoning": "Explication courte (1 phrase)"
}

RÈGLES DE SÉLECTION :

1. Choisis 2 à 4 concepts MAXIMUM parmi la liste ci-dessous.
2. Le `level` doit correspondre au niveau de l'utilisateur :
   - 1 = Débutant (langage simple, métaphores, pas de jargon)
   - 2 = Intermédiaire (chiffré, conseils actionnables, utilisation des zones/métriques)
   - 3 = Expert (mécanismes cellulaires, littérature scientifique, métriques avancées)
3. Si l'utilisateur mentionne une douleur physique → priorité CRITIQUE, sélectionne
   le concept blessure correspondant à son sport EN PREMIER.
4. Si l'utilisateur exprime de la fatigue, de l'épuisement, ou dit "je n'en peux plus"
   → injecte TOUJOURS recuperation/surcompensation-surentrainement.
5. Si l'utilisateur semble démotivé, parle d'abandon → injecte
   psychologie/motivation-autodetermination.
6. Ne sélectionne PAS de concept qui n'a aucun rapport avec la question.
7. Si la question est vague ("comment progresser ?"), favorise les concepts
   fondamentaux de son sport plutôt que des concepts avancés.

CONCEPTS DISPONIBLES :

PHYSIOLOGIE DE L'EFFORT
  - physiologie/systemes-energetiques : Comment le corps produit l'énergie
    (aérobie, anaérobie, phosphocréatine). Mots-clés: énergie, ATP, lactate,
    filières, endurance, sprint, brûler graisses.
  - physiologie/vo2max-seuils : VO2max, seuils ventilatoires (SV1/SV2), FTP,
    VMA, PMA. Mots-clés: VO2max, FTP, seuil, test d'effort, puissance.
  - physiologie/adaptations-entrainement : Comment le corps s'adapte à
    l'entraînement. Mots-clés: progression, stagnation, plateau, mitochondries,
    fibres musculaires.
  - physiologie/frequence-cardiaque-hrv : FC, zones cardiaques, HRV, dérive
    cardiaque. Mots-clés: cardio, pulsations, HRV, zone FC, FCM.

PLANIFICATION & PÉRIODISATION
  - planification/modeles-periodisation : Comment organiser l'entraînement sur
    une saison (linéaire, par blocs, ondulatoire, polarisé).
  - planification/gestion-charge : TRIMP, TSS, CTL, ATL, TSB, ACWR.
  - planification/structure-temporelle : Microcycles, mésocycles, macrocycles,
    semaines de récupération.
  - planification/tapering-pic-forme : Affûtage avant compétition, pic de forme.
  - planification/adaptations-amateurs : Contraintes travail/famille, minimum
    efficace.

SÉANCES TYPES PAR FILIÈRE
  - seances/endurance-fondamentale : Zone 2, endurance de base, sortie longue.
  - seances/travail-seuil : Sweet Spot, seuil, FTP, tempo.
  - seances/intervalles-haute-intensite : HIIT, fractionné, VMA, PMA, 30/30, 4x4.
  - seances/travail-neuromusculaire : Sprints, explosivité, force-vitesse,
    pliométrie.
  - seances/recuperation-active : Décrassage, sortie facile, récup active.

RÉCUPÉRATION & ADAPTATION
  - recuperation/sommeil : Sommeil, sieste, qualité, insomnie.
  - recuperation/nutrition-recuperation : Que manger après l'effort, fenêtre
    métabolique.
  - recuperation/surcompensation-surentrainement : Surcompensation,
    surentraînement, OTS, fatigue chronique. [CRITIQUE si fatigue]
  - recuperation/outils-monitoring : HRV, RPE, capteurs, suivi fatigue.

BLESSURES & PRÉVENTION
  - blessures/cyclisme : Genou cycliste, tendinites, réglages vélo, lombalgie.
    [CRITIQUE si douleur + cyclisme]
  - blessures/running : Périostite, genou coureur, aponévrose, tendinite Achille.
    [CRITIQUE si douleur + course]
  - blessures/fitness-musculation : Blessures en salle, squat, deadlift, hernie.
    [CRITIQUE si douleur + musculation]

NUTRITION SPORTIVE
  - nutrition/periodisation-nutritionnelle : Adapter l'alimentation à
    l'entraînement, low carb, train low, sleep low.
  - nutrition/glucides-timing : Glucides avant/pendant l'effort, gels, ravito,
    carbo loading.
  - nutrition/proteines-besoins : Besoins en protéines, MPS, whey, BCAA, dose.
  - nutrition/hydratation-electrolytes : Eau, déshydratation, sodium, crampes.
  - nutrition/supplements-preuve-a : Créatine, caféine, beta-alanine, nitrate.

PSYCHOLOGIE & MENTAL
  - psychologie/motivation-autodetermination : Motivation intrinsèque/extrinsèque,
    autodétermination, pourquoi s'entraîner.
  - psychologie/gestion-effort-rpe : RPE, perception de l'effort, gouverneur
    central, tenir la douleur.
  - psychologie/fixation-objectifs : SMART, objectifs processus vs résultat.
  - psychologie/preparation-mentale : Imagerie, visualisation, self-talk,
    gestion stress.
  - psychologie/resilience-ennui-plateaux : Résilience, ennui, stagnation
    mentale, peur après blessure.
```

---

## 2. Le Prompt Builder (Logique d'assemblage)

Une fois que le sélecteur a retourné les IDs des concepts et le niveau,
le prompt builder construit le système prompt du coach.

```python
# Pseudo-code

def build_coach_prompt(user, selector_output):
    concepts = selector_output["concepts"]
    level = selector_output["level"]

    # 1. Charger le contenu de chaque concept au bon niveau
    knowledge_snippets = []
    for concept_id in concepts:
        content = load_concept_lines(concept_id, level)
        knowledge_snippets.append(f"### {concept_id}\n{content}")

    # 2. Construire le prompt système
    system_prompt = f"""
Tu es un coach sportif IA expert, spécialisé en {user.sports}.

PROFIL DE L'ATHLÈTE :
- Prénom : {user.name}
- Niveau : {user.level}
- Sport(s) : {user.sports}
- Objectif actuel : {user.current_goal}
- Expérience : {user.experience}
- Charge actuelle : CTL={user.ctl}, TSB={user.tsb}
- Dernières séances : {user.recent_sessions}

CONNAISSANCES SCIENTIFIQUES PERTINENTES :
{chr(10).join(knowledge_snippets)}

HISTORIQUE DE COACHING :
{user.coaching_context}

RÈGLES DE COACHING :
1. Adapte ton langage au niveau '{user.level}' — {level_instructions[user.level]}
2. Base TOUJOURS tes conseils sur les connaissances injectées ci-dessus.
   Si une information n'est pas dans les connaissances, dis-le honnêtement.
3. Si une douleur est mentionnée : priorité SÉCURITÉ. Recommande d'abord
   d'arrêter/réduire, puis suggère des pistes.
4. Tiens compte de la charge actuelle (CTL/TSB) avant de recommander
   une intensité. Ne propose pas de HIIT si TSB < -20.
5. Sois encourageant mais honnête. Pas de "tu vas y arriver !" toxique.
6. Si l'utilisateur pose une question hors de ton expertise, oriente-le
   vers un professionnel de santé.
7. Réponds de manière concise et actionnable. L'utilisateur veut des
   conseils, pas un cours magistral.
"""
    return system_prompt

def level_instructions(level):
    return {
        1: "Langage simple, métaphores, pas de jargon. Explique chaque terme technique.",
        2: "Utilise les zones, les métriques (FC, puissance, RPE), donne des fourchettes chiffrées.",
        3: "Va dans le détail physiologique, cite les mécanismes, utilise la terminologie scientifique."
    }[level]
```

---

## 3. Logique de fallback (sans appel LLM)

Si l'appel au sélecteur LLM échoue (timeout, erreur API), utiliser les règles
d'intention définies dans `index.yaml` (section `intent_rules`).

```python
def fallback_selector(user_message, user_profile):
    message_lower = user_message.lower()

    # Patterns simples avec priorité
    if any(w in message_lower for w in ["mal", "douleur", "blessure",
                                          "tendinite", "genou"]):
        return select_sport_injury(user_profile)
    if any(w in message_lower for w in ["fatigué", "épuisé", "pas en forme",
                                          "crevé", "récupère pas"]):
        return ["recuperation/surcompensation-surentrainement",
                "recuperation/sommeil"]
    if any(w in message_lower for w in ["manger", "nutrition", "protéine",
                                          "glucide", "repas", "boire"]):
        return ["nutrition/glucides-timing", "nutrition/proteines-besoins"]
    # ... etc
```

---

## 4. Coûts estimés

| Étape | Modèle | Coût par message |
|---|---|---|
| Sélecteur LLM | deepseek-chat | ~0.0001€ |
| Coach LLM | deepseek-v4-pro | ~0.001€ |
| **Total par réponse** | | **~0.0011€** |

Pour 1000 messages/mois/utilisateur : ~1.10€/mois/utilisateur en coûts LLM.
Pour 100 utilisateurs actifs : ~110€/mois.

---

## 5. Exemples de sélection

### Exemple 1 : Fatigue + séance difficile

**Utilisateur (Intermédiaire, Cyclisme) :**
> "J'ai dormi 5h, CTL à 85, séance 4x8' seuil prévue ce soir. Je la fais ?"

**Sélecteur →**
```json
{
  "concepts": [
    "recuperation/sommeil",
    "recuperation/surcompensation-surentrainement",
    "planification/gestion-charge",
    "seances/travail-seuil"
  ],
  "level": 2,
  "reasoning": "L'utilisateur montre des signes de déficit de récupération (sommeil, charge élevée) et questionne une séance seuil planifiée"
}
```

### Exemple 2 : Question débutant

**Utilisateur (Débutant, Running) :**
> "Je commence la course à pied, je dois courir à quelle allure ?"

**Sélecteur →**
```json
{
  "concepts": [
    "seances/endurance-fondamentale",
    "physiologie/systemes-energetiques"
  ],
  "level": 1,
  "reasoning": "Débutant qui a besoin des bases : endurance fondamentale et explication des filières énergétiques"
}
```

### Exemple 3 : Douleur — ALERTE

**Utilisateur (Intermédiaire, Cyclisme) :**
> "J'ai mal au genou droit depuis 3 sorties, surtout en danseuse"

**Sélecteur →**
```json
{
  "concepts": [
    "blessures/cyclisme",
    "planification/gestion-charge"
  ],
  "level": 2,
  "reasoning": "Douleur genou cycliste = CRITIQUE. Ajout gestion charge car souvent lié à une surcharge"
}
```

### Exemple 4 : Question vague

**Utilisateur (Intermédiaire, Triathlon) :**
> "Comment je peux progresser ?"

**Sélecteur →**
```json
{
  "concepts": [
    "planification/modeles-periodisation",
    "physiologie/adaptations-entrainement",
    "seances/intervalles-haute-intensite"
  ],
  "level": 2,
  "reasoning": "Question vague — fondamentaux planification + adaptations + séances clés pour donner des pistes structurées"
}
```
