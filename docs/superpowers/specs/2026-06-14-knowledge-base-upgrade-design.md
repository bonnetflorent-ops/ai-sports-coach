# Design d'amélioration de la base de connaissances — Phase 1 Course à pied

**Date :** 2026-06-14
**Statut :** Approuvé
**Objectif :** Élever la base de connaissances du coach IA au niveau d'un coach professionnel d'élite, en commençant par la course à pied.

## Contexte

La base de connaissances actuelle contient 13 domaines et 58 concepts avec 3 niveaux de profondeur. Elle est de bonne qualité scientifique mais présente des déséquilibres importants (4 domaines à 300-500 lignes, 5 domaines à moins de 100 lignes), pas de programmes d'entraînement concrets, et des manques critiques pour la course à pied (biomécanique, technique, gestion de course, préparation mentale).

L'objectif est de faire de cette base la référence pour les sports d'endurance, en commençant par la course à pied — le plus gros marché.

## Approche retenue

**Approche A — Progressive par sport.** Chaque phase produit un résultat autonome et utilisable. La course à pied est la porte d'entrée stratégique (sport le plus pratiqué, le plus accessible, là où un coach IA a le plus de valeur).

Les fondamentaux (physiologie, nutrition, récupération, blessures) étant communs à tous les sports d'endurance, 60-70% du travail sera réutilisable pour les phases suivantes (trail, cyclisme, triathlon).

## Architecture cible

### Phase 1 — Course à pied

- **18-20 domaines** (13 existants + 5-7 nouveaux)
- **80-90 concepts** (58 existants + 22-32 nouveaux)
- **~800-1000 KB** total
- **5 programmes complets** (5km → Marathon + Remise en forme)

### Nouveaux domaines (7)

| # | Domaine | Priorité |
|---|---------|----------|
| 1 | Biomécanique de la course | Critique |
| 2 | Techniques et drills de course | Critique |
| 3 | Gestion de course (pacing, stratégie) | Critique |
| 4 | Préparation mentale avancée | Haute |
| 5 | Entraînement de la force pour coureur | Haute |
| 6 | Équipement running | Moyenne |
| 7 | Physiopathologie du coureur | Haute |

### Domaines existants à approfondir (5)

| Domaine | Lignes actuelles | Cible |
|---------|-----------------|-------|
| Échauffement/retour au calme | 78 | 250 |
| Environnement/conditions | 78 | 200 |
| Matériel/équipement | 96 | 200 |
| Entraînement croisé | 80 | 200 |
| Populations spécifiques | 127 | 300 |

### Programmes d'entraînement (5)

| Programme | Niveaux | Durée |
|-----------|---------|-------|
| 5 km | Débutant/Intermédiaire/Avancé | 8-12 sem |
| 10 km | Débutant/Intermédiaire/Avancé | 10-12 sem |
| Semi-marathon | Débutant/Intermédiaire/Avancé | 12-16 sem |
| Marathon | Débutant/Intermédiaire/Avancé | 16-20 sem |
| Remise en forme | Unique | 6-8 sem |

## Process de recherche

### Pipeline

1. **Recherche Perplexity Sonar Pro** — 3 appels parallèles (fondamental, appliqué, critique)
2. **Vérification croisée** — minimum 3 sources par affirmation, validation DOIs, niveau de preuve
3. **Rédaction 3-niveaux** — format existant (Couche 1/2/3 + Mythes + Biblio)
4. **Intégration technique** — `index.yaml` (keywords, triggers, connects_to), test `load_concept()`

### Budget Perplexity

- 51 appels estimés pour la Phase 1 complète
- ~0.78€ sur un budget de 10€
- Marge confortable de ~9€

## Ordre de bataille

### Vague 1 — Fondamentaux
1. Biomécanique de la course [NOUVEAU]
2. Techniques et drills de course [NOUVEAU]
3. Physiopathologie du coureur [NOUVEAU]
4. Échauffement/retour au calme [APPROFONDIR]

### Vague 2 — Appliqués
5. Gestion de course [NOUVEAU]
6. Force pour coureur [NOUVEAU]
7. Préparation mentale avancée [NOUVEAU]
8. Populations spécifiques [APPROFONDIR]
9. Environnement/conditions [APPROFONDIR]

### Vague 3 — Support + Programmes
10. Équipement running [NOUVEAU]
11. Matériel/équipement [APPROFONDIR]
12. Entraînement croisé [APPROFONDIR]
13. Programme 5km [NOUVEAU]
14. Programme 10km [NOUVEAU]
15. Programme Semi-marathon [NOUVEAU]

### Vague 4 — Finalisation
16. Programme Marathon [NOUVEAU]
17. Programme Remise en forme [NOUVEAU]
18. Relecture croisée + validation qualité

## Format de livrable

Chaque chantier produit :
- Un fichier markdown dans `knowledge/domains/` (format 3-couches + mythes + biblio)
- Une entrée dans `knowledge/index.yaml` (concepts, keywords, triggers, connects_to)
- Pour les programmes : un fichier markdown structuré avec semaines types et séances clés détaillées
- Vérification que `load_concept()` fonctionne pour chaque concept ajouté

## Conventions

- Français pour tout le contenu
- Format 3-couches existant : Couche 1 (débutant, métaphores), Couche 2 (intermédiaire, protocoles), Couche 3 (expert, mécanismes)
- Citations avec DOI, auteurs, revue, année
- Liens transversaux (`connects_to`) entre concepts
- Niveau de preuve explicite pour les affirmations non consensuelles
