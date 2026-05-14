# Plan d'Expansion — Base de Connaissances AI Sports Coach

> **Objectif :** Passer de 31 concepts / 7 domaines / ~2400 lignes à ~60 concepts / 12 domaines / ~4500+ lignes.

---

## Architecture cible — 12 domaines, 60 concepts

### Nouveaux domaines (5)

```
échauffement-retour-au-calme.md     ~180 lignes
environnement-et-conditions.md      ~200 lignes
materiel-et-equipement.md           ~220 lignes
populations-specifiques.md          ~250 lignes
entrainement-croise.md              ~180 lignes
```

### Domaines enrichis (7)

```
physiologie-effort.md               +3 concepts → 7 total
planification-periodisation.md      +3 concepts → 8 total
seances-filieres.md                 +3 concepts → 8 total
recuperation-adaptation.md          +3 concepts → 7 total
blessures-prevention.md             +2 concepts → 5 total
nutrition-sportive.md               +3 concepts → 8 total
psychologie-mental.md               +2 concepts → 7 total
```

---

## Nouveau Domaine 1 | Échauffement & Retour au calme

**Fichier :** `knowledge/domains/echauffement-retour-au-calme.md`

| # | Concept ID | Nom | Couches |
|---|-----------|-----|---------|
| 1 | echauffement/principes-generaux | Pourquoi s'échauffer : principes physiologiques | L1: augmentation progressive T° → muscles + lubrifiant articulations. L2: activation aérobie, mouvements articulaires, progressif. L3: PAP (post-activation potentiation), fenêtre optimale, durée. |
| 2 | echauffement/routines-par-sport | Routines d'échauffement par sport | L1: 10 min vélo facile avant de pousser. L2: routines cyclisme (10' Z2 + 3×30'' Z4), running (footing + gammes + lignes droites), natation. L3: spécificité neuro, activation type II, protocoles compétition. |
| 3 | echauffement/etirements-et-mobilite | Étirements et mobilité : quand, comment, pourquoi | L1: étirements dynamiques avant, statiques après. L2: différence actif/passif/balistique/PNF, durée, amplitude. L3: relation force-longueur, inhibition autogénique, foam rolling mécanisme. |
| 4 | echauffement/retour-au-calme | Retour au calme : pourquoi et comment | L1: 10' facile + étirements doux. L2: protocole 15-20' Z1, drainage, réduction cortisol. L3: clairance lactate active vs passive, retour veineux, fenêtre parasympathique. |

---

## Nouveau Domaine 2 | Environnement & Conditions

**Fichier :** `knowledge/domains/environnement-et-conditions.md`

| # | Concept ID | Nom | Couches |
|---|-----------|-----|---------|
| 1 | environnement/chaleur | Entraînement par forte chaleur | L1: boire plus, ralentir, ombre. L2: acclimatation 7-14j, perte sudorale, stratégie refroidissement. L3: heat shock proteins, volume plasmatique, core temp drift, hyponatrémie. |
| 2 | environnement/froid | Entraînement par grand froid | L1: couches, extrémités, vigilance. L2: équipement hiver running/cyclisme, échauffement prolongé, seuils gel. L3: vasoconstriction périphérique, frisson thermogénique, rendement musculaire au froid. |
| 3 | environnement/altitude | Altitude et hypoxie | L1: plus lent, plus essoufflé, progressif. L2: acclimatation 2-3 sem, EPO endogène, stages hypoxie. L3: HIF-1α, production EPO, perte puissance VO2max/1000m, live high train low. |
| 4 | environnement/pluie-vent-securite | Pluie, vent, sécurité météo | L1: fringale hydro, visibilité, vent fort = home-trainer. L2: stratégie vent (abrité, allure adaptée), vêtements pluie respirants. L3: coefficient traînée, impact watt/météo, décision risk/reward. |

---

## Nouveau Domaine 3 | Matériel & Équipement

**Fichier :** `knowledge/domains/materiel-et-equipement.md`

| # | Concept ID | Nom | Couches |
|---|-----------|-----|---------|
| 1 | materiel/capteurs-de-puissance | Capteurs de puissance : comprendre et utiliser | L1: capteur puissance = wattmètre, mesure ton effort réel. L2: types (pédalier, moyeu, pédales), précision +/-1.5%, Normalized Power, IF, VI. L3: calibration, torque zero, left/right balance, pédalage smoothness, torque effectiveness. |
| 2 | materiel/cardio-gps-montres | Cardiofréquencemètres, GPS et montres connectées | L1: montre = alliée, FC = indicateur effort. L2: précision optique vs ceinture, GPS multi-bande, métriques (VO2max estimé, temps de récup, charge). L3: PPG limitations, dérive cardiaque vs cadence lock, Firstbeat analytics. |
| 3 | materiel/home-trainers | Home-trainers et rouleaux | L1: home-trainer = vélo d'intérieur pour jours pluie. L2: smart trainers (Wahoo, Tacx, Elite), ERG mode, simulation pente. L3: inertie et réalisme, calibration, drift thermique, choix wheel-on vs direct drive. |
| 4 | materiel/analyse-donnees-training | Analyser ses données d'entraînement | L1: regarder temps + FC + ressenti. L2: PMC chart (CTL/ATL/TSB), zones puissance, découplage FC/Pw. L3: WKO5, intervals.icu, mFTP, TTE à FTP, W' (W prime), modélisation CP. |
| 5 | materiel/choisir-son-equipement | Choisir son équipement selon son budget | L1: priorité chaussures running ou réglage vélo, puis capteur. L2: rapport qualité/prix, neuf vs occasion, priorités. L3: retour sur investissement (watts gagnés par €), essentials vs nice-to-have. |

---

## Nouveau Domaine 4 | Populations Spécifiques

**Fichier :** `knowledge/domains/populations-specifiques.md`

| # | Concept ID | Nom | Couches |
|---|-----------|-----|---------|
| 1 | populations/femmes-athletes | Femmes athlètes : cycle menstruel, grossesse, ménopause | L1: c'est normal d'avoir des variations, adapter sans culpabiliser. L2: phases folliculaire/lutéale, performances, risque blessure cycle, retour post-partum progressif (périnée). L3: œstrogènes et utilisation substrats, progestérone et thermorégulation, RED-S chez la femme, aménorrhée hypothalamique. |
| 2 | populations/seniors-50-plus | Sportifs de 50 ans et plus | L1: on peut progresser à tout âge, récupération plus lente. L2: sarcopénie (perte musculaire), renforcement prioritaire, adaptation volume/intensité. L3: VO2max decline, testostérone et masse musculaire, densité osseuse, délai récupération ×1.5, check-up médical. |
| 3 | populations/jeunes-athletes | Jeunes sportifs en croissance | L1: plaisir avant performance, multi-sports conseillé. L2: attention pics de croissance (Osgood-Schlatter, Sever), volume par âge. L3: LTAD (Long Term Athlete Development), fenêtres développementales, spécialisation précoce risques. |
| 4 | populations/reprise-apres-pause | Reprise après une longue pause | L1: progressif, pas comparer à avant, 2-3 sem d'adaptation. L2: règle des 10%, test FTP/VMA avant planification, semaines adaptation. L3: désentraînement (détraining), perte VO2max (%/sem), mémoire musculaire, re-sensibilisation. |
| 5 | populations/surpoids-obesite | Sport et surpoids : approche bienveillante | L1: la régularité > l'intensité, sports portés (vélo, natation). L2: progressivité articulaire, monitoring RPE plutôt que FC, nutrition conjointe. L3: adipokines et inflammation, économie de course et poids, thermorégulation altérée. |

---

## Nouveau Domaine 5 | Entraînement Croisé & Complémentaire

**Fichier :** `knowledge/domains/entrainement-croise.md`

| # | Concept ID | Nom | Couches |
|---|-----------|-----|---------|
| 1 | entrainement-croise/renforcement-endurance | Renforcement musculaire pour l'endurance | L1: gainage + squats 1×/semaine, pas de gonflette. L2: force max (3-5RM), plyométrie légère, timing dans la semaine. L3: recrutement unités motrices, économie de course (RE), transfert force→endurance, périodisation force. |
| 2 | entrainement-croise/natation-cyclistes-coureurs | Natation pour cyclistes et coureurs | L1: nage = récup active + renforcement doux. L2: protocole bassin (technique > volume), pull-buoy pour jambes lourdes. L3: natation et retour veineux, pression hydrostatique, VMA et VO2max transfert inter-sport. |
| 3 | entrainement-croise/yoga-pilates | Yoga, Pilates et mobilité pour le sportif | L1: 1×/semaine, souplesse et respiration. L2: yoga restauratif vs vinyasa, Pilates et sangle abdominale, quand dans la semaine. L3: fascias et élasticité, mobilité vs souplesse, yoga et système parasympathique. |
| 4 | entrainement-croise/brick-triathlon | Combiner plusieurs sports : le brick workout | L1: enchaîner vélo-course = sensations bizarres au début, normal. L2: protocole brick (vélo 1h Z2 → cap 20' progressif), fréquence, adaptation neuro. L3: transition neuro-musculaire, cadence vélo→foulée, économie de course post-vélo, fenêtre métabolique. |

---

## Enrichissement Domaines Existants | Nouveaux concepts

### Physiologie de l'effort — +3 concepts → 7

| # | Concept ID | Nom |
|---|-----------|-----|
| + | physiologie/systeme-cardiovasculaire | Système cardiovasculaire : cœur, débit, retour veineux |
| + | physiologie/fatigue-centrale-vs-peripherique | Fatigue : centrale vs périphérique |
| + | physiologie/hormones-entrainement | Hormones et entraînement (cortisol, testostérone, GH, catécholamines) |

### Planification & Périodisation — +3 concepts → 8

| # | Concept ID | Nom |
|---|-----------|-----|
| + | planification/tests-de-performance | Tests de performance : FTP 20min, VMA, demi-Cooper, ramp test |
| + | planification/periodisation-polarisee | Périodisation polarisée 80/20 (Seiler) vs pyramidal vs HIIT |
| + | planification/semaine-type | Construire une semaine type équilibrée |

### Séances types — +3 concepts → 8

| # | Concept ID | Nom |
|---|-----------|-----|
| + | seances/sortie-longue | La sortie longue : protocoles, progression, nutrition |
| + | seances/fartlek | Fartlek et variations d'allure libres |
| + | seances/cotes-et-puissance | Travail en côtes et développement de la puissance |

### Récupération — +3 concepts → 7

| # | Concept ID | Nom |
|---|-----------|-----|
| + | recuperation/massage-compression | Massage, compression et drainage |
| + | recuperation/thermotherapie | Bain froid, chaud, contraste : le vrai du faux |
| + | recuperation/voyage-jetlag | Voyage, jet lag et performance |

### Blessures — +2 concepts → 5

| # | Concept ID | Nom |
|---|-----------|-----|
| + | blessures/principes-prevention | Principes généraux de prévention des blessures |
| + | blessures/return-to-play | Return-to-play : protocoles de reprise après blessure |

### Nutrition — +3 concepts → 8

| # | Concept ID | Nom |
|---|-----------|-----|
| + | nutrition/lipides-omega3 | Lipides et oméga-3 : le carburant oublié |
| + | nutrition/micronutriments | Micronutriments critiques : fer, magnésium, vitamine D, zinc |
| + | nutrition/nutrition-vegetale-vegan | Nutrition végétale et végane pour sportifs |

### Psychologie — +2 concepts → 7

| # | Concept ID | Nom |
|---|-----------|-----|
| + | psychologie/anxiete-competition | Anxiété pré-compétition : la transformer en atout |
| + | psychologie/flow-confiance | Flow state, confiance et imagerie mentale |

---

## Récapitulatif

| État | Domaines | Concepts | Lignes estimées |
|------|:--------:|:--------:|:---------------:|
| Actuel | 7 | 31 | ~2400 |
| + Nouveaux domaines | +5 | +18 | +1030 |
| + Concepts enrichis | — | +12 | +600 |
| **Cible** | **12** | **61** | **~4000+** |

---

## Prochaines étapes

Chaque nouveau domaine nécessite :
1. Création du fichier `.md` avec contenu structuré `# Titre` → `## 1.` → `### Concept` → `#### Couche 1/2/3`
2. Ajout du domaine + concepts dans `knowledge/index.yaml`
3. Vérification : `load_concept()` pour chaque concept × 3 niveaux
