#!/usr/bin/env python3
"""
Simulateur de conversations AI Sports Coach.

10 profils × 3-4 messages chacun, pipeline réel complet :
sélecteur → prompt builder → coach LLM → évaluation qualité.

Objectif : détecter les réponses faibles, incohérences, markdown cassé,
et itérer sur le prompt builder / sélecteur en fonction des résultats.

Budget estimé : ~0,35€ (deepseek-chat pour le coach ET l'évaluateur).

Usage : python scripts/simulate_conversations.py [--full]
  --full : utilise deepseek-v4-pro (plus cher, ~1,50€, qualité maximale)
"""

import asyncio
import json
import re
import sys
import time
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from openai import AsyncOpenAI
from src.utils.config import settings
from src.engine.selector import select_concepts
from src.engine.prompt_builder import build_system_prompt

# ── Config ─────────────────────────────────────────────────────────────
USE_FULL_MODEL = "--full" in sys.argv
COACH_MODEL = "deepseek/deepseek-v4-pro" if USE_FULL_MODEL else "deepseek/deepseek-chat"
EVAL_MODEL = "deepseek/deepseek-chat"
RESULTS_DIR = Path(__file__).parent.parent / "simulation_results"
RESULTS_DIR.mkdir(exist_ok=True)

# ── 10 Profils Réalistes ───────────────────────────────────────────────
PROFILES = [
    {
        "id": "p1", "name": "Florent", "sport": "cyclisme", "level": 2, "level_name": "Intermédiaire",
        "goal": "être affûté pour le vélo et avoir un physique athlétique",
        "experience": "3 ans", "blessures": "douleur au psoas gauche intermittente",
        "weight_kg": 73, "height_cm": 177, "age": 32, "gender": "H", "ctl": 60, "tsb": -8,
    },
    {
        "id": "p2", "name": "Marie", "sport": "running", "level": 1, "level_name": "Débutante",
        "goal": "courir son premier 10km sans s'arrêter d'ici 3 mois",
        "experience": "6 mois", "blessures": "Aucune",
        "weight_kg": 62, "height_cm": 165, "age": 28, "gender": "F",
    },
    {
        "id": "p3", "name": "Thomas", "sport": "triathlon", "level": 3, "level_name": "Expert",
        "goal": "qualification pour l'Ironman de Nice, FTP 320W, VMA 19km/h",
        "experience": "8 ans", "blessures": "Aucune",
        "weight_kg": 70, "height_cm": 180, "age": 35, "gender": "H", "ftp_watts": 320, "vdot": 58, "ctl": 95, "tsb": -15,
    },
    {
        "id": "p4", "name": "Sophie", "sport": "fitness", "level": 1, "level_name": "Débutante",
        "goal": "perdre 8 kg et se tonifier, 3 séances/semaine à la salle",
        "experience": "2 mois", "blessures": "Aucune",
        "weight_kg": 78, "height_cm": 168, "age": 41, "gender": "F",
    },
    {
        "id": "p5", "name": "Julien", "sport": "cyclisme", "level": 3, "level_name": "Expert",
        "goal": "podium au championnat régional contre-la-montre, FTP 340W",
        "experience": "10 ans", "blessures": "ancienne fracture clavicule, parfois douleurs cervicales sur longues sorties",
        "weight_kg": 68, "height_cm": 178, "age": 29, "gender": "H", "ftp_watts": 340, "ctl": 110, "tsb": -25,
    },
    {
        "id": "p6", "name": "Emma", "sport": "running", "level": 2, "level_name": "Intermédiaire",
        "goal": "marathon dans 4 mois, objectif 3h45",
        "experience": "3 ans", "blessures": "syndrome de l'essuie-glace au genou droit, sous contrôle",
        "weight_kg": 55, "height_cm": 163, "age": 31, "gender": "F", "vdot": 42,
    },
    {
        "id": "p7", "name": "Lucas", "sport": "crossfit", "level": 2, "level_name": "Intermédiaire",
        "goal": "maîtriser les muscle-ups et améliorer son conditionnement général",
        "experience": "2 ans", "blessures": "tendinite au coude droit (epicondylite) en rémission",
        "weight_kg": 82, "height_cm": 183, "age": 26, "gender": "H",
    },
    {
        "id": "p8", "name": "Nadia", "sport": "cyclisme", "level": 1, "level_name": "Débutante",
        "goal": "reprise du sport après grossesse, faire une sortie de 50km sans être épuisée",
        "experience": "1 an avant pause", "blessures": "Aucune, mais diastasis abdominal résiduel",
        "weight_kg": 68, "height_cm": 170, "age": 34, "gender": "F",
    },
    {
        "id": "p9", "name": "Antoine", "sport": "triathlon", "level": 2, "level_name": "Intermédiaire",
        "goal": "terminer son premier half Ironman en moins de 5h30",
        "experience": "2 ans", "blessures": "Aucune",
        "weight_kg": 75, "height_cm": 182, "age": 38, "gender": "H", "ftp_watts": 240, "vdot": 48,
    },
    {
        "id": "p10", "name": "Camille", "sport": "running", "level": 3, "level_name": "Experte",
        "goal": "ultra-trail de 80km avec 4000m D+, top 10 féminin",
        "experience": "6 ans", "blessures": "entorse cheville gauche récurrente, porte une chevillère",
        "weight_kg": 57, "height_cm": 167, "age": 33, "gender": "F", "vdot": 54, "ctl": 85, "tsb": 5,
    },
]

# ── Scénarios de conversation par profil ───────────────────────────────
# Chaque profil a 3-4 messages qui forment une mini-conversation
SCENARIOS = {
    "p1": [  # Florent — cycliste intermédiaire avec douleur psoas
        "Salut coach ! J'ai fait ma sortie vélo lundi comme prévu (60km, 800m D+) mais j'ai senti mon psoas gauche tirer après 40km. C'est normal ou je dois m'inquiéter ?",
        "OK merci. Et pour ma séance muscu de demain (mardi), je fais ma séance A normalement (développé couché, RDL, triceps) ou je lève le pied ?",
        "Dernière question : j'ai une cyclo de 120km dans 3 semaines. Avec cette douleur, est-ce que je peux la faire ou je dois annuler ?",
    ],
    "p2": [  # Marie — débutante running
        "Coucou coach ! J'ai fait ma 3ème sortie running aujourd'hui : 4km en 28 minutes, je suis essoufflée tout le long. C'est normal au début ou je vais trop vite ?",
        "Ah oui j'alternais marche et course avant mais j'ai essayé de courir tout du long cette fois. Je dois revenir au fractionné marche/course alors ?",
        "Et pour les courbatures, j'ai super mal aux mollets le lendemain. Des astuces ?",
    ],
    "p3": [  # Thomas — triathlète expert
        "Coach, analyse ma semaine : lundi 4km natation + 1h vélo zone 2, mardi fractionné cap 8×800m, mercredi 100km vélo avec 2000m D+, jeudi repos, vendredi brick vélo 2h + cap 45min, samedi natation 3km, dimanche sortie longue cap 25km. Trop ou pas assez ?",
        "Mon TSB est à -15 depuis 10 jours. À partir de quel moment c'est dangereux ? Je me sens fatigué mais je dors bien.",
        "OK je vais alléger. Question nutrition : pendant mon Ironman je vise 90g de glucides/heure. C'est cohérent ou je peux monter à 110g ?",
    ],
    "p4": [  # Sophie — débutante fitness
        "Hello ! Ça fait 1 mois que je vais à la salle 3 fois par semaine mais je vois aucun changement sur la balance. Je fais 30min de vélo elliptique + quelques machines. Je fais quoi de travers ?",
        "D'accord, donc je dois ajouter des exercices polyarticulaires. Tu peux me donner 3 exercices à faire absolument ?",
        "Et pour la nutrition, j'ai lu qu'il fallait supprimer les glucides le soir pour maigrir. C'est vrai ?",
    ],
    "p5": [  # Julien — cycliste expert avec TSB très bas
        "Coach, mon TSB est à -25 et ma course CLM est dans 10 jours. Je dois absolument être en forme. Tu me conseilles de continuer à m'entraîner ou de tout couper ?",
        "J'ai du mal à couper... Si je fais juste une sortie de 1h en zone 1 par jour pendant 3 jours, c'est acceptable ?",
        "OK. Et niveau nutrition, un truc qui peut m'aider à récupérer plus vite ces 10 prochains jours ?",
    ],
    "p6": [  # Emma — coureuse intermédiaire, genou
        "Salut ! J'ai fait ma sortie longue de 18km hier et mon genou droit (syndrome essuie-glace) a commencé à me brûler vers le km 14. J'ai fini mais en boitant. Qu'est-ce que je fais pour ma sortie de demain ?",
        "OK repos. Et à plus long terme, il y a des exercices de renforcement qui marchent vraiment pour ce syndrome ? J'en ai marre que ça revienne.",
        "Merci. Dernière chose : je dois changer mes chaussures (800km dessus), tu as des conseils pour le choix du modèle avec ce problème de genou ?",
    ],
    "p7": [  # Lucas — crossfit intermédiaire, coude
        "Salut coach, mon coude droit me fait encore souffrir sur les pull-ups et les cleans. J'ai arrêté 2 semaines mais dès que je reprends ça revient. Je fais quoi ?",
        "Le strap j'ai déjà essayé, ça aide un peu mais pas assez. Tu penses que je dois voir un kiné ou je peux gérer tout seul avec des exos ?",
        "OK je vais prendre RDV kiné. En attendant, quels mouvements de crossfit je PEUX faire sans solliciter le coude ?",
    ],
    "p8": [  # Nadia — débutante cyclisme, post-grossesse
        "Hello coach ! Je reprends le vélo après ma grossesse (bébé a 4 mois). J'ai fait 15km hier et j'étais épuisée, alors qu'avant j'en faisais 50 sans problème. C'est normal ? Combien de temps pour retrouver mon niveau ?",
        "Ah et j'ai encore un petit diastasis (écartement des abdos). Le vélo c'est safe ou je risque d'aggraver ?",
        "Merci pour les conseils ! Tu me recommandes combien de sorties par semaine pour reprendre progressivement ?",
    ],
    "p9": [  # Antoine — triathlète intermédiaire
        "Coach, je prépare mon premier half Ironman (dans 4 mois). J'arrive à caser 8-10h d'entraînement par semaine réparties sur les 3 sports. Est-ce que c'est suffisant pour viser 5h30 ?",
        "OK. Et comment je répartis mes 10h entre natation, vélo et course à pied ? J'ai un bon niveau vélo (FTP 240) mais je nage comme une brique.",
        "Question bête mais... la transition vélo-course, je la bosse comment concrètement ? J'ai jamais fait de brick.",
    ],
    "p10": [  # Camille — coureuse experte ultra
        "Coach, je prépare un ultra de 80km/4000m D+. J'ai fait une sortie de 50km avec 2500m D+ ce weekend, tout s'est bien passé sauf que j'ai roulé la cheville droite 2 fois dans les descentes techniques. Ma chevillère actuelle est trop souple je pense. Des recommandations ?",
        "OK pour la chevillère rigide. Question nutrition sur l'ultra : je vise 60g de glucides/heure mais au bout de 5h j'ai des nausées. Comment gérer ça ?",
        "Et pour la gestion du sommeil la veille d'un ultra ? Je dors jamais bien, trop stressée.",
    ],
}

# ── Évaluateur de qualité ──────────────────────────────────────────────

EVAL_PROMPT = """Tu es un évaluateur de coaching sportif IA. Analyse cette réponse et attribue UNIQUEMENT des notes de 1 à 5 sur ces 6 critères. Sois EXIGEANT — une réponse générique ou passe-partout doit avoir des notes basses.

PROFIL DE L'ATHLÈTE :
- Prénom : {name}
- Sport : {sport}
- Niveau : {level_name}
- Objectif : {goal}
- Blessures : {blessures}
- Question : {question}

RÉPONSE DU COACH :
{response}

CRITÈRES (1=très mauvais, 5=excellent) :

1. PERTINENCE : La réponse répond-elle directement à la question posée ?
   - 5 : réponse parfaitement ciblée sur la question
   - 1 : réponse hors-sujet ou à côté de la plaque

2. PERSONNALISATION : Utilise le prénom, le sport, le niveau, l'objectif ?
   - 5 : réponse impossible à donner à un autre athlète (ultra-personnalisée)
   - 1 : réponse générique qui conviendrait à n'importe qui

3. PRÉCISION SCIENTIFIQUE : Les concepts cités sont-ils corrects ? Pas de conseils dangereux ?
   - 5 : concepts précis, zones d'entraînement correctes, données crédibles
   - 1 : contenu scientifiquement faux ou dangereux

4. ACTIONNABILITÉ : Propose des actions concrètes (pas juste des généralités) ?
   - 5 : plan d'action détaillé, exercices spécifiques, chiffré
   - 1 : que des généralités ("écoute ton corps", "fais attention")

5. TON & ADAPTATION : Le ton correspond-il au niveau de l'athlète ?
   - 5 : parfaitement adapté (pédagogue pour débutant, technique pour expert)
   - 1 : jargon incompréhensible pour un débutant, ou niveau bébé pour un expert

6. SÉCURITÉ : Si blessure/douleur mentionnée → avertissement médical présent ?
   - 5 : avertissement médical présent ET pertinent
   - 1 : pas d'avertissement alors qu'il y a une blessure/douleur, OU conseil dangereux
   - Note : si aucune blessure, mets 5 par défaut

IMPORTANT : Réponds UNIQUEMENT avec ce JSON (pas de markdown, pas de commentaires) :
{{"pertinence": N, "personnalisation": N, "precision": N, "actionnabilité": N, "ton": N, "securite": N, "commentaire_bref": "1 phrase max en français"}}"""


async def evaluate_response(client: AsyncOpenAI, profile: dict, question: str, response: str) -> dict:
    """Évalue une réponse coaching avec deepseek-chat."""
    prompt = EVAL_PROMPT.format(
        name=profile["name"],
        sport=profile["sport"],
        level_name=profile["level_name"],
        goal=profile.get("goal", "non spécifié"),
        blessures=profile.get("blessures", "Aucune"),
        question=question,
        response=response,
    )

    try:
        result = await client.chat.completions.create(
            model=EVAL_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=200,
        )
        text = result.choices[0].message.content.strip()

        # Extract JSON (handle markdown code blocks)
        json_match = re.search(r"\{[\s\S]*\}", text)
        if json_match:
            scores = json.loads(json_match.group())
            return scores
        return {"error": "JSON parse failed", "raw": text[:200]}
    except Exception as e:
        return {"error": str(e)}


def check_markdown_balance(text: str) -> dict:
    """Vérifie que les entités markdown sont équilibrées (le bug principal)."""
    entities = {"**": 0, "*": 0, "__": 0, "_": 0}
    # Count simple * (not part of **)
    i = 0
    while i < len(text):
        if text[i:i+2] == "**":
            entities["**"] += 1
            i += 2
            continue
        elif text[i] == "*" and (i == 0 or text[i-1] != "\\"):
            entities["*"] += 1
        elif text[i:i+2] == "__":
            entities["__"] += 1
            i += 2
            continue
        elif text[i] == "_" and (i == 0 or text[i-1] != "\\"):
            entities["_"] += 1
        i += 1

    issues = []
    for entity, count in entities.items():
        if count % 2 != 0:
            issues.append(f"{entity}: {count} occurrences (impair)")

    return {"balanced": len(issues) == 0, "issues": issues}


# ── Simulation principale ───────────────────────────────────────────────

async def run_simulation():
    client = AsyncOpenAI(
        api_key=settings.openrouter_api_key,
        base_url=settings.openrouter_base_url,
        timeout=60.0,
        max_retries=1,
    )

    print(f"🔬 Simulateur AI Sports Coach — {len(PROFILES)} profils, {sum(len(v) for v in SCENARIOS.values())} messages")
    print(f"   Modèle coach : {COACH_MODEL}")
    print(f"   Modèle éval  : {EVAL_MODEL}")
    print()

    all_results = []
    total_cost = 0
    total_tokens_in = 0
    total_tokens_out = 0

    for profile in PROFILES:
        pid = profile["id"]
        name = profile["name"]
        sport = profile["sport"]
        messages = SCENARIOS[pid]

        print(f"━ {name} ({sport}, {profile['level_name']}) — {len(messages)} messages")

        profile_results = []
        recent_context = []

        for i, user_msg in enumerate(messages, 1):
            icon = "💬"
            try:
                # ── Étape 1 : Sélecteur de concepts ──
                t0 = time.time()
                selection = await select_concepts(
                    client=client,
                    user_message=user_msg,
                    user_profile=profile,
                    recent_context=recent_context,
                )
                selector_ms = (time.time() - t0) * 1000

                # ── Étape 2 : Prompt builder ──
                system_prompt = build_system_prompt(
                    selection=selection,
                    user_profile=profile,
                    coaching_context=None,  # Pas de contexte mémoire en simulation
                )

                # ── Étape 3 : Coach LLM ──
                t1 = time.time()
                response = await client.chat.completions.create(
                    model=COACH_MODEL,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": f"[{name}] {user_msg}"},
                    ],
                    temperature=0.7,
                    max_tokens=1500,
                )
                coach_ms = (time.time() - t1) * 1000

                answer = response.choices[0].message.content or ""
                usage = response.usage
                tokens_in = usage.prompt_tokens if usage else 0
                tokens_out = usage.completion_tokens if usage else 0
                finish_reason = response.choices[0].finish_reason

                # Coût estimé (deepseek-chat: $0.14/$0.28, v4-pro: $0.55/$2.19 per 1M)
                if "v4-pro" in COACH_MODEL:
                    cost = (tokens_in * 0.55 + tokens_out * 2.19) / 1_000_000
                else:
                    cost = (tokens_in * 0.14 + tokens_out * 0.28) / 1_000_000

                total_tokens_in += tokens_in
                total_tokens_out += tokens_out
                total_cost += cost

                # ── Étape 4 : Évaluation ──
                eval_start = time.time()
                scores = await evaluate_response(client, profile, user_msg, answer)
                eval_ms = (time.time() - eval_start) * 1000

                # Coût évaluation (deepseek-chat, ~200 tokens out)
                eval_cost = (tokens_in * 0.14 + 200 * 0.28) / 1_000_000  # rough estimate
                total_cost += eval_cost

                # ── Étape 5 : Vérification markdown ──
                md_check = check_markdown_balance(answer)

                # ── Alimenter le contexte récent ──
                recent_context.append({"role": "user", "content": user_msg})
                recent_context.append({"role": "assistant", "content": answer[:200]})

                # ── Résultat ──
                result = {
                    "profil": name,
                    "sport": sport,
                    "niveau": profile["level_name"],
                    "message_n": i,
                    "question": user_msg[:100],
                    "reponse": answer[:300] + ("..." if len(answer) > 300 else ""),
                    "reponse_complete": answer,
                    "concepts": selection["concepts"],
                    "niveau_selection": selection["level"],
                    "raison": selection["reasoning"],
                    "tokens_in": tokens_in,
                    "tokens_out": tokens_out,
                    "finish_reason": finish_reason,
                    "cout_eur": round(cost, 6),
                    "score_pertinence": scores.get("pertinence", "?"),
                    "score_personnalisation": scores.get("personnalisation", "?"),
                    "score_precision": scores.get("precision", "?"),
                    "score_actionnabilite": scores.get("actionnabilité", "?"),
                    "score_ton": scores.get("ton", "?"),
                    "score_securite": scores.get("securite", "?"),
                    "commentaire": scores.get("commentaire_bref", ""),
                    "markdown_ok": md_check["balanced"],
                    "markdown_issues": md_check["issues"],
                    "timing_selector_ms": round(selector_ms),
                    "timing_coach_ms": round(coach_ms),
                    "timing_eval_ms": round(eval_ms),
                }

                # Score moyen
                numeric_scores = [
                    scores.get(k, 0) for k in
                    ["pertinence", "personnalisation", "precision", "actionnabilité", "ton", "securite"]
                    if isinstance(scores.get(k), (int, float))
                ]
                result["score_moyen"] = round(sum(numeric_scores) / len(numeric_scores), 1) if numeric_scores else 0

                # Icône selon qualité
                if result["score_moyen"] >= 4:
                    icon = "✅"
                elif result["score_moyen"] >= 3:
                    icon = "⚠️"
                elif result["score_moyen"] >= 2:
                    icon = "🔶"
                else:
                    icon = "❌"

                if finish_reason == "length":
                    icon = "✂️"  # Tronqué

                if not md_check["balanced"]:
                    icon = "💥" + icon  # Markdown cassé (bug principal !)

                profile_results.append(result)

                print(f"   {icon} msg{i} | score={result['score_moyen']}/5 | "
                      f"tokens={tokens_in}+{tokens_out} | "
                      f"concepts={selection['concepts']} | "
                      f"sél={selector_ms}ms coach={coach_ms}ms eval={eval_ms}ms")

                if scores.get("commentaire_bref"):
                    print(f"      💬 {scores['commentaire_bref']}")
                if not md_check["balanced"]:
                    print(f"      💥 MARKDOWN CASSÉ : {md_check['issues']}")
                if finish_reason == "length":
                    print(f"      ✂️ RÉPONSE TRONQUÉE (max_tokens atteint)")

                # Petit délai pour éviter de spammer l'API
                await asyncio.sleep(0.5)

            except Exception as e:
                icon = "🔥"
                result = {
                    "profil": name, "message_n": i, "question": user_msg[:100],
                    "erreur": str(e), "score_moyen": 0,
                }
                profile_results.append(result)
                print(f"   {icon} msg{i} | ERREUR: {e}")

        all_results.extend(profile_results)
        print()

    # ── Rapport final ───────────────────────────────────────────────────
    print("═" * 60)
    print(f"📊 RAPPORT FINAL")
    print(f"═" * 60)

    # Stats globales
    scores = [r.get("score_moyen", 0) for r in all_results if not r.get("erreur")]
    markdown_ok = sum(1 for r in all_results if r.get("markdown_ok", False))
    markdown_bad = sum(1 for r in all_results if not r.get("markdown_ok", True) and not r.get("erreur"))
    truncated = sum(1 for r in all_results if r.get("finish_reason") == "length")
    errors = sum(1 for r in all_results if r.get("erreur"))

    avg_score = round(sum(scores) / len(scores), 1) if scores else 0

    print(f"   Messages traités   : {len(all_results)}")
    print(f"   Score moyen        : {avg_score}/5 {'✅' if avg_score >= 3.5 else '⚠️' if avg_score >= 2.5 else '❌'}")
    print(f"   Markdown OK        : {markdown_ok}/{len(all_results)}")
    print(f"   Markdown CASSÉ 💥  : {markdown_bad}/{len(all_results)} {'⚠️ À CORRIGER' if markdown_bad > 0 else '✅'}")
    print(f"   Réponses tronquées : {truncated}/{len(all_results)}")
    print(f"   Erreurs            : {errors}/{len(all_results)}")
    print(f"   Tokens (in/out)    : {total_tokens_in:,} / {total_tokens_out:,}")
    print(f"   Coût estimé        : {total_cost:.4f}€")
    print()

    # Par critère
    criteria = ["pertinence", "personnalisation", "precision", "actionnabilite", "ton", "securite"]
    criteria_labels = ["Pertinence", "Personnalisation", "Précision", "Actionnabilité", "Ton", "Sécurité"]
    for crit, label in zip(criteria, criteria_labels):
        vals = [r.get(f"score_{crit}", 0) for r in all_results
                if isinstance(r.get(f"score_{crit}"), (int, float))]
        avg = round(sum(vals) / len(vals), 1) if vals else 0
        bar = "█" * int(avg) + "░" * (5 - int(avg))
        print(f"   {label:20s} {bar} {avg}/5")

    print()

    # Pire réponses (score < 3)
    bad = [r for r in all_results if r.get("score_moyen", 0) < 3 and not r.get("erreur")]
    if bad:
        print(f"⚠️  RÉPONSES FAIBLES (score < 3/5) : {len(bad)}")
        for r in bad[:5]:
            print(f"   - {r['profil']} msg{r['message_n']}: score={r['score_moyen']}")
            print(f"     Q: {r['question'][:120]}")
            print(f"     R: {r['reponse'][:150]}")
            if r.get("commentaire"):
                print(f"     💬 {r['commentaire']}")
            print()

    # Sauvegarde JSON
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    json_path = RESULTS_DIR / f"simulation_{timestamp}.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(all_results, f, ensure_ascii=False, indent=2)
    print(f"📁 Résultats sauvegardés : {json_path}")
    print(f"   ({len(json.dumps(all_results)):,} bytes)")

    return all_results


if __name__ == "__main__":
    asyncio.run(run_simulation())
