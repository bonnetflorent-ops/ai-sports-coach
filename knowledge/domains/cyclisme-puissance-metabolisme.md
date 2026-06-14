# Cyclisme — Puissance et Metabolisme

## 1. Concepts cles — 3 couches de profondeur

### 1.1 FTP et zones de puissance (modele Coggan)

**Couche 1 — Debutant (metaphores, essentiel)**
Le FTP (Functional Threshold Power), c'est la puissance que tu peux tenir pendant environ une heure a effort maximal. Imagine que c'est la vitesse de croisiere de ton moteur — quand tu depasses cette puissance, tu brules vite et tu dois ralentir sous peine de caler. Tout l'entrainement cycliste s'articule autour de ce chiffre, defini en watts, et des zones d'intensite qu'on en deduit.

**Couche 2 — Intermediaire (protocoles, applications)**
Le modele Coggan (2003) definit 7 zones basees sur le pourcentage du FTP :
- **Zone 1 (Actif, < 55 % FTP)** : recuperation active, pedaler sans force
- **Zone 2 (Endurance, 56-75 % FTP)** : endurance fondamentale, conversationnel, le gros du volume
- **Zone 3 (Tempo, 76-90 % FTP)** : rythme soutenu, travail sweet spot (88-94 %)
- **Zone 4 (Seuil, 91-105 % FTP)** : effort a la limite, duree max 60 min
- **Zone 5 (VO2max, 106-120 % FTP)** : intervalles 3-8 min, puissance maximale aerobie
- **Zone 6 (Capacite anaerobie, 121-150 % FTP)** : 30 sec-3 min, accumulation lactate
- **Zone 7 (Puissance neuromusculaire, > 150 % FTP)** : sprints 5-15 sec

**Protocole test FTP 20 min** (le plus courant) : apres 20 min d'echauffement progressif, pedaler a fond pendant 20 min. La puissance moyenne de ces 20 min multipliee par 0,95 donne une estimation du FTP. Attention : les 20 min doivent etre un effort maximal et regulier, pas un sprint de fin.

**Limites du FTP** : le FTP est une simplification pratique, pas un reflet exact de la physiologie. La duree soutenable a la puissance seuil critique peut varier de 35 a 75 min selon le profil du cycliste (fibres musculaires, entrainement, fatigue).

**Couche 3 — Avance (mecanismes, nuances)**
Le modele de la **puissance critique (CP)** affiné par les travaux de Skiba, Jones et Vanhatalo (2012) propose une alternative plus fondee physiologiquement. La CP est l'intensite maximale que le corps peut soutenir sans atteindre son VO2max — elle peut correspondre approximativement au FTP mais est theoriquement plus stable.

Le modele a 3 parametres (CP, W', et Pmax) offre une vision plus complete :
- **CP** (= FTP theorique) : asymptote de la relation puissance-duree, seuil d'equilibre lactate
- **W'** : travail anaerobie utilisable au-dessus de CP (environ 15-30 kJ), se regenere au repos
- **Pmax** : puissance maximale instantanee

Des travaux recents (Poole et al., Med Sci Sports Exerc, DOI: 10.1249/MSS.0000000000000730) montrent que le FTP tend a surestimer la CP de 5-10 % chez les cyclistes bien entrainees, car l'effort maximal sur 20 min est influence par la capacite anaerobie, pas seulement la composante aerobie.

Le modele Coggan reste tres utilise dans l'entrainement quotidien (TrainingPeaks, WKO, Intervals.icu) car plus simple a implementer, mais les coachs avances integrent les concepts de CP et W' pour affiner la prescription d'intervalles et la gestion des reserves anaerobies en course.

### 1.2 Courbe de puissance et profil

**Couche 1 — Debutant (metaphores, essentiel)**
La courbe de puissance, c'est le graphique qui montre ta puissance maximale pour chaque duree : 5 secondes, 1 minute, 5 minutes, 20 minutes, 1 heure... C'est comme ta carte de visite athletique — elle montre tes points forts (sprinteur ? grimpeur ? rouleur ?) et tes points faibles. En comparant plusieurs courbes dans le temps, tu vois si tu progresses.

**Couche 2 — Intermediaire (protocoles, applications)**
La **courbe de puissance personnelle (CPP)** se construit en extrayant les meilleures puissances enregistrees par duree (5 sec, 15 sec, 30 sec, 1 min, 2 min, 5 min, 10 min, 20 min, 60 min, 90 min). Les logiciels comme WKO, TrainingPeaks ou Strava generent automatiquement cette courbe.

**Profil typique par discipline** :
- **Route sprinteur** : pic 5 sec tres eleve (> 15 W/kg), baisse rapide, CP modeste
- **Route grimpeur** : bon ratio 5-20 min (4-6 W/kg), pic 5 sec modeste
- **VTT XC** : bonne courbe 1-10 min, variabilite elevee, bonne capacite de relance
- **Gravel** : courbe similaire au route mais avec plus d'endurance (60-180 min)

**Normalized Power (NP)** : la puissance normalisee est une moyenne ajustee qui tient compte de la variabilite de l'effort. Contrairement a la puissance moyenne, elle pondere les pics (exponentielle 4e puissance, puis racine 4e). Un NP superieur a la puissance moyenne indique un effort irregulier (typique du VTT, Graval, ou route avec du relief).

**Intensity Factor (IF)** = NP / FTP. Un IF de 1.0 correspond a un effort seuil. Les valeurs guide : Z2 (< 0.75), Tempo (0.75-0.85), Sweet Spot (0.85-0.95), Seuil (0.95-1.05).

**Couche 3 — Avance (mecanismes, nuances)**
La courbe de puissance peut etre modelisee mathematiquement par la relation puissance-duree : **P(t) = W'/t + CP** (modele 2 parametres) ou **P(t) = W'/t + CP + Pmax x exp(-t/tau)** (modele 3 parametres). Le modele 3 parametres colle mieux aux tres courtes durees (< 30 sec).

L'analyse de la courbe permet de detecter des faiblesses specifiques : une courbe qui s'ecroule entre 5 min et 20 min evoque un deficit de puissance aerobie ou une mauvaise gestion du W'. Une courbe plate en dessous de 1 min signale un manque de puissance neuromusculaire.

L'evolution de la CPP est un meilleur indicateur de progression que le seul FTP, car elle reflete l'ensemble des filieres energetiques. Les etudes montrent qu'une amelioration de 10 % du CP (FTP) est associee a une amelioration de 6-8 % du temps sur 40 km contre-la-montre [Jobson et al., Sports Med, DOI: 10.2165/11589190-000000000-00000].

### 1.3 W/kg et performance

**Couche 1 — Debutant (metaphores, essentiel)**
Le rapport poids/puissance (W/kg), c'est ton nombre de watts divisé par ton poids en kilos. C'est le vrai indicateur de performance en cote : un athlete leger avec une puissance modeste peut grimper plus vite qu'un athlete lourd avec beaucoup de puissance. En montagne, chaque kilo compte doublé : 1 kg de moins, c'est 5-8 watts d'economie en cote a 5 %.

**Couche 2 — Intermediaire (protocoles, applications)**
Valeurs references (route, masculin) :
- **Cyclotouriste** : 2.0-2.5 W/kg au seuil
- **Amateur entraine** : 2.8-3.5 W/kg au seuil
- **Amateur performant** : 3.8-4.5 W/kg au seuil
- **Competiteur regional** : 4.0-5.0 W/kg au seuil
- **Elite nationale** : 5.0-5.8 W/kg au seuil
- **WorldTour** : 6.0-6.5 W/kg au seuil (grimpeurs)

(Femmes : environ 15-20 % inferieur, mais les ecarts tendent a se reduire sur les efforts longs > 2h)

Le W/kg est surtout determinant en **cote** : une pente a 8 % demande environ 45-55 W pour deplacer 1 kg supplementaire. Sur le plat, le W absolu (watts bruts) est plus important car la resistance aerodynamique domine, pas le poids.

**Couche 3 — Avance (mecanismes, nuances)**
La relation W/kg-performance n'est pas lineaire : la puissance aerobie maximale (VO2max en W/kg theorique) est limitee par le transport d'oxygene et la capillarisation. A partir de 5.5-6.0 W/kg, les gains sont exponentiellement plus durs a obtenir — ces niveaux requierent des annees d'entrainement structure et un profil genetique favorable.

Le debat W/kg vs W absolu est fondamental en cyclisme :
- **Parcours accidente / montagne** : le W/kg determine le classement
- **Plat / contre-la-montre plat** : le W absolu + l'aerodynamisme dominent
- **Sprint** : puissance neuromusculaire absolue (jusqu'a 1500-2000 W chez les elites) et position aerodynamique

Les transformations corporelles (perte de poids) doivent etre gerees avec une attention aux risques de RED-S (Relative Energy Deficiency in Sport), surtout chez les grimpeurs [Mountjoy et al., Br J Sports Med, DOI: 10.1136/bjsports-2018-099522].

### 1.4 Decouplage aerobie (cardiac drift, Pa:HR)

**Couche 1 — Debutant (metaphores, essentiel)**
Le decouplage aerobie, c'est le phenomene ou ta frequence cardiaque augmente progressivement alors que ta puissance ne change pas, pendant un effort prolonge. C'est normal ! C'est lie a la fatigue, a la chaleur, a la deshydratation. Un petit decouplage (< 5 %) est attendu sur une sortie longue. Un decouplage > 10 % signale un probleme (fatigue, surentrainement, nutrition).

**Couche 2 — Intermediaire (protocoles, applications)**
Le rapport **Pa:HR (Power-to-Heart Rate)** est le ratio de la puissance produite sur la frequence cardiaque. En debut de seance a etat stable, Pa:HR est constant. En milieu de seance, si Pa:HR chute de plus de 10 % (la FC augmente ou la puissance baisse), il y a decouplage.

**Protocole de mesure** : lors d'une sortie de 2-3h en Z2 (65-75 % FTP), comparer le Pa:HR des premieres 30 min a celui des 30 dernieres minutes.
- Decouplage < 5 % : bon etat de forme
- Decouplage 5-10 % : acceptable, surveillance
- Decouplage > 10 % : alerte — peut indiquer deshydratation, deficit energetique ou fatigue accumulee

**Facteurs influencant le decouplage** : chaleur, humidite, altitude, fatigue cumulative, hydratation insuffisante, depletion de glycogene, cafeine.

**Couche 3 — Avance (mecanismes, nuances)**
Le cardiac drift (derive cardiaque) est un phenomene multiparametrique impliquant :
- **Le systeme cardiovasculaire** : baisse du volume d'ejection systolique due a l'augmentation de la temperature corporelle (redistribution sanguine vers la peau) et a la deshydratation → augmentation compensatoire de la FC
- **Le systeme metabolique** : depletion du glycogene hepatique et musculaire entrainant une augmentation de la contribution des graisses et une hausse de la catecholamine
- **Le systeme nerveux autonome** : baisse du tonus parasympathique et augmentation du tonus orthosympathique avec la duree

Le point de decouplage (la duree a partir de laquelle le Pa:HR commence a diverger) est un indicateur de la condition aerobie : plus il est tardif (> 90-120 min), meilleure est la resistance a la fatigue.

Sur le plan pratique, un decouplage eleve en debut de saison est normal et devrait se reduire avec l'augmentation du volume en endurance fondamentale.

### 1.5 Economie de pedalage (efficiency vs economy)

**Couche 1 — Debutant (metaphores, essentiel)**
L'economie de pedalage, c'est la quantite d'energie que tu depenses pour produire ta puissance. Deux cyclistes avec le meme FTP n'auront pas la meme endurance : le plus econome consomme moins d'oxygene pour les memes watts. C'est comme deux voitures, l'une sobre (economique) et l'autre qui boit plus.

**Couche 2 — Intermediaire (protocoles, applications)**
On distingue :
- **Gross Efficiency (GE)** : ratio du travail mecanique sur la depense energetique totale. GE = Puissance (W) x 0.01433 / VO2 (L/min). Valeurs : 20-25 % chez les cyclistes entraine (25-30 % chez les elites).
- **Net Efficiency (NE)** : prend en compte le cout metabolique de base (VO2 de repos). Generalement 2-3 % plus eleve que GE.
- **Delta Efficiency (DE)** : mesure le rendement incremental (variation de travail / variation d'energie). C'est le reflet du rendement intrinsique du muscle.

**Facteurs determinants de l'economie de pedalage** : proportion de fibres lentes (type I), densite mitochondriale, technique de pedalage (fluidite), raideur musculo-tendineuse, fatigue, cadence.

**Couche 3 — Avance (mecanismes, nuances)**
L'economie de pedalage est influencee par la proportion de fibres de type I (plus efficaces pour convertir le substrat en travail mecanique). Les cyclistes avec une forte proportion de fibres I ont generalement une meilleure economie a basse intensite (40-60 % FTP), mais l'avantage s'estompe a haute intensite.

Des etudes en biopsie musculaire montrent que 8-12 semaines d'entrainement en endurance augmentent l'activite des enzymes oxydatives (citrate synthase, SDH) de 20-40 %, ce qui ameliore l'efficience mitochondriale et donc l'economie [Burgomaster et al., J Appl Physiol, DOI: 10.1152/japplphysiol.00137.2006].

Contrairement a la course a pied, l'economie de pedalage varie moins entre cyclistes (coeff. var. ~5-8 % vs 10-15 % pour la course), car le geste est plus contraint mecaniquement. Les gains d'economie viennent surtout de la gestion de la cadence, de la fluidite du couple, et de la reduction des co-contractions antagonistes [Mornieux et al., 2007].

### 1.6 Specificites Gravel et VTT (NP, VI, variabilite)

**Couche 1 — Debutant (metaphores, essentiel)**
En Gravel et VTT, la puissance n'est pas constante comme sur route : tu alternes entre des efforts intenses (relances, montees) et des moments de recuperation (descentes, virages). Cette irregularite est capturee par des metriques specifiques : la Normalized Power (NP) et le Variability Index (VI). Comprendre ces indicateurs t'aide a ne pas sous-estimer la difficulte d'une sortie accidentee.

**Couche 2 — Intermediaire (protocoles, applications)**
Le **Variability Index (VI)** = NP / Puissance moyenne. Plus le VI est eleve, plus l'effort est irregulier :
- Route plat (roulage groupe) : VI < 1.05
- Route vallonné : VI = 1.05-1.15
- Gravel mixte : VI = 1.10-1.20
- VTT XC : VI = 1.20-1.40
- VTT descente : VI > 1.50 (effort tres explosif)

Une sortie Gravel de 4h avec NP = 200W mais VI = 1.25 sera significativement plus epuisante qu'une sortie route de 4h a 200W avec VI = 1.05. Le stress physiologique est mieux represente par NP que par la puissance moyenne.

**Training Stress Score (TSS)** : TSS = (sec x NP x IF) / (FTP x 3600) x 100. Un TSS de 100 correspond a 1h a FTP. En Gravel/VTT, le TSS est souvent plus eleve que ce que la puissance moyenne suggere (car NP > puissance moyenne). Exemple : 4h a NP 180W avec FTP 250W donne TSS = 144 (effort significatif).

**Couche 3 — Avance (mecanismes, nuances)**
L'entrainement pour le Gravel et le VTT doit integrer la **variabilite de puissance** comme variable d'entrainement specifique. Des protocoles d'intervalles irreguliers (stochastic training) simulent mieux les demandes du VTT que les intervalles lisses sur home-trainer.

Le **kilojoule (kJ)** depense pendant une sortie est une autre mesure pertinente : il reflete le travail total effectue. En VTT, pour une meme duree et un meme NP, le travail total (kJ) peut etre inferieur au route (car les descentes ne produisent pas de puissance), mais le cout physiologique est comparable ou superieur du fait du stress technique, des impacts et de la charge neuromusculaire excentrique.

## 2. Methodologies et applications pratiques

**Protocole test FTP 20 min standardise** :
1. 15 min echauffement progressif (Z1-Z2)
2. 2 min a 80 % FTP percu (pour ouvrir les jambes)
3. 3 min de recuperation facile
4. 10 sec sprint a 200 % FTP percu (activation neuromusculaire)
5. 5 min recuperation facile
6. 20 min a effort maximal chronometre (ne pas sprinter le debut, rester regulier)
7. 15 min retour au calme
Resultat : puissance moyenne des 20 min x 0.95 = FTP estime

**Interpretation du decouplage en sortie longue** :
- Si Pa:HR decouple > 10 % apres 60-90 min => besoin de plus d'endurance fondamentale
- Si Pa:HR reste stable > 2h => bon etat de forme
- Si Pa:HR decouple des le debut => fatigue residuelle ou hydratation insuffisante

## 3. Metriques et outils

- **FTP (W)** : reference absolue de la puissance soutenable (60 min theoriques)
- **W/kg** : ratio performance/masse, cle en terrain accidente
- **NP (Normalized Power)** : puissance moyenne ponderee, meilleur reflet du cout physiologique
- **IF (Intensity Factor)** : NP/FTP, charge relative de la seance
- **VI (Variability Index)** : NP/puissance moyenne, irregularite de l'effort
- **TSS (Training Stress Score)** : charge totale de seance (100 = 1h a FTP)
- **Pa:HR (Power-to-Heart Rate)** : ratio puissance/FC, indicateur de fatigue
- **Decouplage (%)** : derive du Pa:HR sur un effort constant
- **kJ (kilojoules)** : travail mecanique total depense
- **CP (Critical Power)** : modele scientifique alternatif au FTP
- **W'** : capacite de travail anaerobie utilisable au-dessus de CP

## 4. Mythes et debats

**"Le FTP mesure vraiment ta puissance soutenable 60 min"** — Vrai approximativement. Le test 20 min x 0.95 est une estimation, pas une valeur absolue. De vrais tests 60 min sont plus rares mais plus precis. Certains coachs preferent un test 8 min x 1.06 ou un test ramp pour estimer le FTP.

**"NP est plus important que la puissance moyenne"** — Vrai pour les efforts irreguliers (VTT, Gravel, route avec relief). Sur un contre-la-montre plat (puissance quasi-constante), NP = puissance moyenne, donc la difference est nulle.

**"Le W/kg est TOUT en cyclisme"** — Faux. Sur le plat, la puissance absolue et l'aerodynamisme prennent le pas. Seuls 20-30 % du parcours d'une cyclosportive typique sont suffisamment pentus pour que le W/kg soit determinant.

**"Un VI eleve est toujours mauvais"** — Pas forcement. L'irregularite est inevitable et meme entrainee (entrainement par intervalles, stochastic training). Le probleme est quand l'irregularite est subie (mauvais pacing) et non choisie.

**"Le test 20 min est le meilleur protocole FTP"** — Le debat persiste : le test 20 min x 0.95 serait moins fiable pour les debutants (qui ne savent pas gerer la duree) et les elites (dont le temps soutenable au seuil peut exceder 60 min). Le test ramp (aerobic power test) est parfois prefere pour sa reproductibilite et son cout en fatigue moindre.

## 5. Bibliographie

- Coggan AR. Training and racing using a power meter. *TrainingPeaks*. 2003.
- Allen H, Coggan AR, McGregor S. Training and Racing with a Power Meter. 3rd ed. Boulder: VeloPress; 2019.
- Poole DC, Burnley M, Vanhatalo A, Rossiter HB, Jones AM. Critical power: an important fatigue threshold in exercise physiology. *Medicine & Science in Sports & Exercise*. 2016;48(11):2320-2334. DOI: `10.1249/MSS.0000000000000730`
- Jobson SA, Nevill AM, Jeukendrup AE, Passfield L. Optimizing cycling performance using pacing strategy and power output. *Sports Medicine*. 2009;39(10):803-826. DOI: `10.2165/11317770-000000000-00000`
- Mountjoy M, Sundgot-Borgen J, Burke L, et al. International Olympic Committee consensus statement on relative energy deficiency in sport (RED-S). *British Journal of Sports Medicine*. 2018;52(11):687-697. DOI: `10.1136/bjsports-2018-099522`
- Burgomaster KA, Howarth KR, Phillips SM, et al. Similar metabolic adaptations during exercise after low-volume sprint interval and traditional endurance training in humans. *Journal of Applied Physiology*. 2008;104(1):104-110. DOI: `10.1152/japplphysiol.00137.2006`
- Mornieux G, Stapelfeldt B, Gollhofer A, Belli A. Effects of pedalling technique on mechanical effectiveness and efficiency in cycling. *Journal of Biomechanics*. 2007;40(4):927-933. DOI: `10.1016/j.jbiomech.2007.02.003`
- Skiba PF, Chidnok W, Vanhatalo A, Jones AM. Modeling the expenditure and reconstitution of work capacity above critical power. *Medicine & Science in Sports & Exercise*. 2012;44(8):1526-1532. DOI: `10.1249/MSS.0b013e3182517a80`
- Impellizzeri FM, Marcora SM. Test validation in sport physiology: lessons learned from clinimetrics. *International Journal of Sports Physiology and Performance*. 2009;4(2):269-277. DOI: `10.1123/ijspp.4.2.269`
- Lucia A, Hoyos J, Carvajal A, Chicharro JL. Heart rate response to professional road cycling: the Tour de France. *International Journal of Sports Medicine*. 1999;20(3):167-172. DOI: `10.1055/s-2007-971130`
