# Amélioration Base de Connaissances — Phase 1 Course à pied — Plan d'Implémentation

> **Pour les agents :** Utiliser `superpowers:subagent-driven-development` pour exécuter ce plan. Les étapes utilisent la syntaxe `- [ ]`.

**Objectif :** Élever la base de connaissances au niveau d'un coach professionnel d'élite pour la course à pied — 7 nouveaux domaines, 5 approfondissements, 5 programmes complets.

**Architecture :** Chaque chantier suit un pipeline standard — recherche Perplexity 3-angles → synthèse → rédaction markdown 3-couches → indexation YAML → validation. Les chantiers sont groupés en 4 vagues de priorité décroissante.

**Stack :** Perplexity Sonar Pro (recherche), markdown (contenu), YAML (index), Python (validation `load_concept()`).

**Prérequis :** `PPLX_API_KEY` configurée dans `~/.claude/settings.json`. Skill `perplexity-research` disponible.

---

## Structure des fichiers

```
knowledge/
  domains/
    biomecanique-course.md          [NOUVEAU — Vague 1]
    techniques-drills-course.md     [NOUVEAU — Vague 1]
    physiopathologie-coureur.md     [NOUVEAU — Vague 1]
    echauffement-retour-au-calme.md [MODIFIÉ — Vague 1, approfondi]
    gestion-course.md               [NOUVEAU — Vague 2]
    force-pour-coureur.md           [NOUVEAU — Vague 2]
    preparation-mentale-avancee.md  [NOUVEAU — Vague 2]
    populations-specifiques.md      [MODIFIÉ — Vague 2, approfondi]
    environnement-et-conditions.md  [MODIFIÉ — Vague 2, approfondi]
    equipement-running.md           [NOUVEAU — Vague 3]
    materiel-et-equipement.md       [MODIFIÉ — Vague 3, approfondi]
    entrainement-croise.md          [MODIFIÉ — Vague 3, approfondi]
  programmes/
    programme-5km.md                [NOUVEAU — Vague 3]
    programme-10km.md               [NOUVEAU — Vague 3]
    programme-semi-marathon.md      [NOUVEAU — Vague 3]
    programme-marathon.md           [NOUVEAU — Vague 4]
    programme-remise-en-forme.md    [NOUVEAU — Vague 4]
  index.yaml                        [MODIFIÉ — chaque chantier]
```

---

## Chunk 1: Vague 1 — Fondamentaux (chantiers 1-4)

### Process standard pour chaque chantier

Chaque chantier de nouveau domaine suit ce processus en 8 étapes. Pour les approfondissements, les étapes 1-2 sont adaptées (focalisées sur les manques identifiés).

- [ ] **Étape A : Recherche Perplexity 3-angles**
  - Lancer 3 appels curl Perplexity Sonar Pro en parallèle (fondamental, appliqué, critique)
  - Sauvegarder les résultats bruts dans `/tmp/research-<domaine>-angle-*.json`
  - Coût par chantier : ~0.015€

- [ ] **Étape B : Synthèse des résultats**
  - Extraire les affirmations clés avec au moins 3 sources par affirmation
  - Vérifier les DOIs (format valide `10.xxxx/...`)
  - Identifier le niveau de preuve (consensus / émergent / controversé)
  - Structurer en plan 3-couches + mythes + biblio

- [ ] **Étape C : Rédaction du fichier domaine**
  - Écrire le markdown complet dans `knowledge/domaines/<nom>.md`
  - Format : sections 1 à 5 (Concepts 3-couches, Méthodologies, Métriques, Mythes, Biblio)
  - 5-8 concepts par domaine
  - Style français, métaphores niveau 1, précision scientifique niveau 3

- [ ] **Étape D : Mise à jour de `index.yaml`**
  - Ajouter le domaine dans `domains`
  - Ajouter chaque concept avec `lines` (layer1/2/3), `keywords`, `triggers`, `connects_to`
  - Ajouter les `intent_rules` pour les nouveaux concepts
  - Mettre à jour `cross_domain_overlaps` si pertinent

- [ ] **Étape E : Validation technique**
  - Vérifier que `load_concept()` fonctionne pour chaque nouveau concept
  - Vérifier que les `line_ranges` sont corrects (pas de décalage)
  - Vérifier les liens `connects_to` (les concepts référencés existent)

- [ ] **Étape F : Commit**
  ```bash
  git add knowledge/domains/<nom>.md knowledge/index.yaml
  git commit -m "knowledge: ajout domaine <nom> — Phase 1 course à pied"
  ```

---

### Chantier 1 : Biomécanique de la course [NOUVEAU]

**Fichier :** `knowledge/domains/biomecanique-course.md`

**Concepts attendus (6) :**
1. Économie de course (RE — running economy) : VO2, coût énergétique, rendement
2. Cinématique de la foulée : cadence, longueur, oscillation verticale, temps de contact
3. Cinétique et forces : force de réaction au sol (GRF), raideur musculaire
4. Posture et alignement : tronc, bassin, chaine postérieure, bras
5. Types de foulée : attaque talon/médio-pied/avant-pied, débats scientifiques
6. Variabilité et individualisation : pourquoi il n'y a pas de foulée "parfaite"

- [ ] **1.1 Recherche Perplexity 3-angles**
  - Fondamental : "What are the biomechanical determinants of running economy? Based on peer-reviewed research with DOIs."
  - Appliqué : "What running form interventions actually improve performance? Protocols from elite coaches."
  - Critique : "Is changing running form beneficial or risky? Contradictory evidence, injury risk of gait retraining."

- [ ] **1.2 Synthèse et rédaction** → `biomecanique-course.md`
- [ ] **1.3 Indexation** → `index.yaml` (6 concepts)
- [ ] **1.4 Validation** `load_concept()` + DOIs
- [ ] **1.5 Commit**

---

### Chantier 2 : Techniques et drills de course [NOUVEAU]

**Fichier :** `knowledge/domains/techniques-drills-course.md`

**Concepts attendus (7) :**
1. Gammes d'échauffement (drills dynamiques) : montées genoux, talons-fesses, pas de l'oie
2. Éducatifs techniques : skipping, griffé, foulées bondissantes, pas chassés
3. Technique de côte : montée (posture, bras, foulée) et descente (freinage, impact)
4. Travail de vélocité : sprints courts, descentes rapides, sur-vitesse
5. Respiration et coordination : synchronisation foulée-respiration, respiration abdominale
6. Renforcement technique : pieds nus, surfaces variées, proprioception cheville
7. Analyse vidéo et feedback : points clés à observer, angles, corrections prioritaires

- [ ] **2.1 Recherche Perplexity 3-angles**
- [ ] **2.2 Synthèse et rédaction** → `techniques-drills-course.md`
- [ ] **2.3 Indexation** → `index.yaml` (7 concepts)
- [ ] **2.4 Validation** `load_concept()` + DOIs
- [ ] **2.5 Commit**

---

### Chantier 3 : Physiopathologie du coureur [NOUVEAU]

**Fichier :** `knowledge/domains/physiopathologie-coureur.md`

**Concepts attendus (6) :**
1. Syndrome de la bandelette ilio-tibiale : causes, diagnostic différentiel, retour à la course
2. Périostite tibiale (shin splints) : mécanisme, facteurs de risque, progression de charge
3. Aponévrosite plantaire : biomécanique, étirements, renforcement intrinsèque du pied
4. Tendinopathie d'Achille : continuum pathologique, protocole de rééducation (lourd/excentrique)
5. Syndrome fémoro-patellaire : dysfonction hanche/genou, renforcement ciblé
6. Fracture de stress : détection précoce, facteurs RED-S, retour progressif

- [ ] **3.1 Recherche Perplexity 3-angles**
- [ ] **3.2 Synthèse et rédaction** → `physiopathologie-coureur.md`
- [ ] **3.3 Indexation** → `index.yaml` (6 concepts)
- [ ] **3.4 Validation** `load_concept()` + DOIs
- [ ] **3.5 Commit**

---

### Chantier 4 : Échauffement et retour au calme [APPROFONDIR]

**Fichier existant :** `knowledge/domains/echauffement-retour-au-calme.md` (78 lignes → 250 lignes cible)

**Manques identifiés :** routines spécifiques course à pied, activation neuromusculaire, strides/accélérations progressives, retour au calme et étirements post-course, protocoles de récupération active.

**Concepts à ajouter/approfondir :**
- Activation spécifique running (7-10 min) : mobilité hanche, activation fessiers, drills dynamiques, strides
- Routine standardisée avant compétition (vs entraînement)
- Retour au calme : footing léger, étirements statiques vs dynamiques (débat scientifique), respiration

- [ ] **4.1 Recherche Perplexity ciblée** (angles : physiologique, appliqué running, débats stretching)
- [ ] **4.2 Rédaction** des sections manquantes, extension des concepts existants
- [ ] **4.3 Mise à jour** `index.yaml` (nouveaux concepts, révision line_ranges)
- [ ] **4.4 Validation** `load_concept()` pour tous les concepts du domaine
- [ ] **4.5 Commit**

---

## Chunk 2: Vague 2 — Appliqués (chantiers 5-9)

### Chantier 5 : Gestion de course [NOUVEAU]

**Fichier :** `knowledge/domains/gestion-course.md`

**Concepts attendus (6) :**
1. Stratégies de pacing : négative split, positive split, even pacing, quand utiliser chaque stratégie
2. Ravitaillement en course : hydratation, glucides, électrolytes, timing, protocoles par distance
3. Gestion de l'allure par RPE et FC : utilisation des zones, ajustement conditions réelles
4. Aspects tactiques : départ (foule, adrénaline), gestion des relances, fin de course
5. Gestion mentale en course : dissociation/association, segmentation, mantras, visualisation
6. Conditions spécifiques : chaleur, pluie, vent, dénivelé, altitude en compétition

- [ ] **5.1 Recherche Perplexity 3-angles**
- [ ] **5.2 Rédaction** → `gestion-course.md`
- [ ] **5.3 Indexation** → `index.yaml`
- [ ] **5.4 Validation**
- [ ] **5.5 Commit**

---

### Chantier 6 : Entraînement de la force pour coureur [NOUVEAU]

**Fichier :** `knowledge/domains/force-pour-coureur.md`

**Concepts attendus (7) :**
1. Fondamentaux : pourquoi la force est essentielle pour le coureur — économie, puissance, blessures
2. Pliométrie pour coureur : bonds, skipping intense, drop jumps, progressions
3. Renforcement charge lourde : squat, deadlift, presse — protocoles et périodisation
4. Gainage et stabilité : core, planches, anti-rotation, lien avec la posture de course
5. Mobilité et souplesse : hanches, chevilles, colonne thoracique — exercices clés
6. Périodisation de la force dans le plan running : quand faire la muscu, concilier avec les séances clés
7. PPG à domicile sans matériel : bandes élastiques, poids de corps, exercices minimalistes

- [ ] **6.1 Recherche Perplexity 3-angles**
- [ ] **6.2 Rédaction** → `force-pour-coureur.md`
- [ ] **6.3 Indexation** → `index.yaml`
- [ ] **6.4 Validation**
- [ ] **6.5 Commit**

---

### Chantier 7 : Préparation mentale avancée [NOUVEAU]

**Fichier :** `knowledge/domains/preparation-mentale-avancee.md`

**Concepts attendus (6) :**
1. Visualisation et imagerie mentale : protocoles, études d'efficacité, scripts types
2. Routines pré-compétition : construction, test, adaptation, exemples d'élites
3. Gestion de la douleur et de l'inconfort : techniques cognitivo-comportementales, dissociation
4. Fixation d'objectifs : processus vs résultat, SMART, réévaluation dynamique
5. Résilience et gestion de l'échec : contre-performance, blessure, DNF
6. Flow state en course : conditions d'entrée, caractéristiques, témoignages

- [ ] **7.1 Recherche Perplexity 3-angles**
- [ ] **7.2 Rédaction** → `preparation-mentale-avancee.md`
- [ ] **7.3 Indexation** → `index.yaml`
- [ ] **7.4 Validation**
- [ ] **7.5 Commit**

---

### Chantier 8 : Populations spécifiques [APPROFONDIR]

**Fichier existant :** `knowledge/domains/populations-specifiques.md` (127 → 300 lignes)

**Manques :** coureurs masters (50+), coureuses (cycle menstruel et performance, grossesse et reprise), jeunes coureurs (développement, précautions), reprise après longue pause, coureurs avec surpoids.

- [ ] **8.1 Recherche Perplexity ciblée** (angles vétérans, femmes, jeunes, obésité/reprise)
- [ ] **8.2 Rédaction** sections manquantes
- [ ] **8.3 Mise à jour** `index.yaml`
- [ ] **8.4 Validation**
- [ ] **8.5 Commit**

---

### Chantier 9 : Environnement et conditions [APPROFONDIR]

**Fichier existant :** `knowledge/domains/environnement-et-conditions.md` (78 → 200 lignes)

**Manques :** acclimatation chaleur (protocoles, timing, hydratation), course par froid (vêtements, respiration, risque hypothermie), altitude (acclimatation, charge, hypoxie), pollution (impact, adaptation).

- [ ] **9.1 Recherche Perplexity ciblée**
- [ ] **9.2 Rédaction** sections manquantes
- [ ] **9.3 Mise à jour** `index.yaml`
- [ ] **9.4 Validation**
- [ ] **9.5 Commit**

---

## Chunk 3: Vague 3 — Support + Programmes (chantiers 10-15)

### Chantier 10 : Équipement running [NOUVEAU]

**Fichier :** `knowledge/domains/equipement-running.md`

**Concepts attendus (5) :**
1. Chaussures de running : types, drop, amorti, stabilité, durée de vie, rotation de paires
2. Capteurs et montres : GPS, cardio poignet vs ceinture, puissance, cadence, précision
3. Vêtements techniques : tissus, thermorégulation, couches, anti-frottement
4. Équipement spécifique : ceinture hydratation, lampes frontales, bâtons (trail)
5. Analyse des données : interprétation charge, TSB, ratio charge aiguë/chronique

- [ ] **10.1 Recherche Perplexity 3-angles**
- [ ] **10.2 Rédaction** → `equipement-running.md`
- [ ] **10.3 Indexation** → `index.yaml`
- [ ] **10.4 Validation**
- [ ] **10.5 Commit**

---

### Chantier 11 : Matériel et équipement [APPROFONDIR]

**Fichier existant :** `knowledge/domains/materiel-et-equipement.md` (96 → 200 lignes)

**Manques :** approfondir montres et capteurs, ajouter tapis de course, home-trainer, applications.

- [ ] **11.1 Recherche Perplexity ciblée**
- [ ] **11.2 Rédaction** sections manquantes
- [ ] **11.3 Mise à jour** `index.yaml`
- [ ] **11.4 Validation**
- [ ] **11.5 Commit**

---

### Chantier 12 : Entraînement croisé [APPROFONDIR]

**Fichier existant :** `knowledge/domains/entrainement-croise.md` (80 → 200 lignes)

**Manques :** vélo pour coureur (spécificités, positions, transfert), natation, PPG, planification du croisé dans une semaine running.

- [ ] **12.1 Recherche Perplexity ciblée**
- [ ] **12.2 Rédaction** sections manquantes
- [ ] **12.3 Mise à jour** `index.yaml`
- [ ] **12.4 Validation**
- [ ] **12.5 Commit**

---

### Programme 5km [NOUVEAU]

**Fichier :** `knowledge/programmes/programme-5km.md`

**3 niveaux :** Débutant (objectif <30 min), Intermédiaire (<22 min), Avancé (<18 min)
**Durée :** 8-12 semaines
**Structure :** 3 séances/sem débutant, 4 intermédiaire, 5 avancé

- [ ] **13.1 Recherche Perplexity** (méthodologies 5km, protocoles VMA, programmes éprouvés)
- [ ] **13.2 Rédaction** programme complet (semaine type, progression, séances clés)
- [ ] **13.3 Indexation** `index.yaml` (concepts liés au 5km, intent rules)
- [ ] **13.4 Validation**
- [ ] **13.5 Commit**

---

### Programme 10km [NOUVEAU]

**Fichier :** `knowledge/programmes/programme-10km.md`

**3 niveaux :** Débutant (<60 min), Intermédiaire (<45 min), Avancé (<38 min)
**Durée :** 10-12 semaines
**Structure :** 3-4-5 séances selon niveau, accent VMA + seuil

- [ ] **14.1-14.5** (même processus que chantier 13)

---

### Programme Semi-marathon [NOUVEAU]

**Fichier :** `knowledge/programmes/programme-semi-marathon.md`

**3 niveaux :** Débutant (<2h), Intermédiaire (<1h35), Avancé (<1h20)
**Durée :** 12-16 semaines
**Structure :** 4-5 séances, accent endurance + allure spécifique

- [ ] **15.1-15.5** (même processus)

---

## Chunk 4: Vague 4 — Finalisation (chantiers 16-18)

### Programme Marathon [NOUVEAU]

**Fichier :** `knowledge/programmes/programme-marathon.md`

**3 niveaux :** Débutant (<4h), Intermédiaire (<3h15), Avancé (<2h50)
**Durée :** 16-20 semaines
**Structure :** 4-5-6 séances, volume progressif, sorties longues structurées

- [ ] **16.1-16.5** (même processus)

---

### Programme Remise en forme [NOUVEAU]

**Fichier :** `knowledge/programmes/programme-remise-en-forme.md`

**Public :** Sédentaires, reprise après longue pause, post-blessure
**Durée :** 6-8 semaines
**Structure :** 2-3 séances, alternance marche/course, progression très graduelle

- [ ] **17.1-17.5** (même processus)

---

### Chantier 18 : Relecture croisée et validation qualité

- [ ] **18.1 Vérification cohérence inter-domaines**
  - Tous les `connects_to` sont valides (pas de référence à un concept inexistant)
  - Pas de contradictions entre domaines sur les mêmes sujets

- [ ] **18.2 Vérification des line_ranges**
  - Script Python pour vérifier que chaque `layer1/2/3` du `index.yaml` correspond au contenu réel

- [ ] **18.3 Vérification des DOIs**
  - Tous les DOIs sont au format `10.xxxx/...`
  - Pas de DOIs dupliqués ou manifestement invalides

- [ ] **18.4 Test de bout en bout**
  - `load_concept()` pour 10 concepts aléatoires
  - Simulation d'une conversation type (selector → prompt builder)
  - Vérification que les nouvelles `intent_rules` capturent bien les questions course à pied

- [ ] **18.5 Commit final de la Phase 1**
  ```bash
  git add -A knowledge/
  git commit -m "knowledge: Phase 1 course à pied complète — 7 domaines, 5 approfondissements, 5 programmes"
  ```

---

## Récapitulatif

| Vague | Chantiers | Nouveaux domaines | Approf. | Programmes | Appels Perplexity |
|-------|-----------|-------------------|---------|------------|-------------------|
| 1     | 1-4       | 3                 | 1       | 0          | 12                |
| 2     | 5-9       | 3                 | 2       | 0          | 15                |
| 3     | 10-15     | 1                 | 2       | 3          | 18                |
| 4     | 16-18     | 0                 | 0       | 2          | 6                 |
| **Total** | **18** | **7**         | **5**   | **5**      | **51**            |

**Budget Perplexity estimé :** ~0.78€ / 10€ (7.8% du budget)
**Durée estimée :** 8-12 sessions de travail
