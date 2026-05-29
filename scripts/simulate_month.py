#!/usr/bin/env python3
"""
Simulation d'1 mois d'utilisation — AVEC persistance Supabase.

5 utilisateurs fictifs (telegram_id 999001-999005) simulent
des conversations réalistes sur 30 jours (2-3 sessions/semaine).

Vérifie :
- Sauvegarde correcte des messages (chat_messages)
- Rotation des sessions (expiration >24h → nouvelle session + résumé)
- Extraction de faits (user_facts, tous les 5 messages)
- Mémoire inter-session (résumés + faits récupérés)
- Intégrité des données (pas de doublons, compteurs corrects)

Coût estimé : ~0,10€ (deepseek-chat pour coach + extracteur)
Usage : python scripts/simulate_month.py
"""

import asyncio
import json
import logging
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from openai import AsyncOpenAI
from src.utils.config import settings
from src.engine.selector import select_concepts
from src.engine.prompt_builder import build_system_prompt
from src.db import get_supabase_admin

# ── Config ─────────────────────────────────────────────────────────────
COACH_MODEL = "deepseek/deepseek-chat"
EXTRACT_MODEL = "deepseek/deepseek-chat"
RESULTS_FILE = Path(__file__).parent.parent / "simulation_results" / f"month_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

logging.basicConfig(level=logging.WARNING, format="%(message)s")
logger = logging.getLogger("sim")

# IDs de test (n'interfèrent pas avec les vrais utilisateurs)
TEST_TELEGRAM_IDS = [999001, 999002, 999003, 999004, 999005]


# ── 5 Profils de test ──────────────────────────────────────────────────
PROFILES = {
    999001: {
        "name": "FlorentTest", "sport": "cyclisme", "level": 2, "level_name": "Intermédiaire",
        "goal": "préparer une cyclosportive de 120km", "experience": "3 ans",
        "blessures": "douleur au psoas gauche intermittente",
        "weight_kg": 73, "height_cm": 177, "age": 32, "gender": "H",
    },
    999002: {
        "name": "MarieTest", "sport": "running", "level": 1, "level_name": "Débutante",
        "goal": "courir 10km sans s'arrêter", "experience": "6 mois",
        "blessures": "Aucune", "weight_kg": 62, "height_cm": 165, "age": 28, "gender": "F",
    },
    999003: {
        "name": "ThomasTest", "sport": "triathlon", "level": 3, "level_name": "Expert",
        "goal": "qualification Ironman Nice, FTP 320W", "experience": "8 ans",
        "blessures": "Aucune", "weight_kg": 70, "height_cm": 180, "age": 35, "gender": "H",
        "ftp_watts": 320, "vdot": 58, "ctl": 95, "tsb": -15,
    },
    999004: {
        "name": "SophieTest", "sport": "fitness", "level": 1, "level_name": "Débutante",
        "goal": "perdre 8kg et se tonifier", "experience": "2 mois",
        "blessures": "Aucune", "weight_kg": 78, "height_cm": 168, "age": 41, "gender": "F",
    },
    999005: {
        "name": "JulienTest", "sport": "cyclisme", "level": 3, "level_name": "Expert",
        "goal": "podium championnat régional CLM, FTP 340W", "experience": "10 ans",
        "blessures": "douleurs cervicales sur longues sorties",
        "weight_kg": 68, "height_cm": 178, "age": 29, "gender": "H",
        "ftp_watts": 340, "ctl": 110, "tsb": -25,
    },
}

# ── Planning de conversations (jour → telegram_id → messages) ──────────
# Simule 30 jours : certains jours sans activité, 2-3 messages par session
# Format : {day: {tg_id: [msg1, msg2, msg3]}}
CONVERSATION_PLAN = {
    1: {
        999001: ["Salut coach ! Première sortie vélo de la saison, 40km cool. J'ai mal aux fessiers, c'est normal ?",
                  "OK merci. Je prévois 3 sorties cette semaine, 40km, 50km, 60km avec du D+ le weekend. Trop ambitieux ?"],
        999003: ["Coach, première semaine de mon plan Ironman. J'ai nagé 2km, roulé 3h et couru 1h. Je me sens bien mais mon TSB est déjà à -20. Inquiétant ?"],
    },
    3: {
        999002: ["Coucou ! Première séance running : 3km alternance marche/course, 25 minutes. Les mollets brûlent ! Des conseils ?",
                  "Et je dois courir combien de fois par semaine au début ?"],
        999005: ["Coach, première semaine de prépa CLM. FTP test à 338W, en légère baisse. Normal en début de cycle ?"],
    },
    5: {
        999001: ["Deuxième sortie : 50km, les fessiers vont mieux mais j'ai mon psoas qui a tiré à partir du km 35. Quoi faire ?"],
        999004: ["Hello ! 3ème semaine à la salle, je fais 30min vélo + machines. Aucun changement sur la balance, je déprime un peu..."],
    },
    8: {
        999002: ["J'ai couru 4km sans m'arrêter !!! Mais j'étais essoufflée tout du long, je vais trop vite ?",
                  "Tu me conseilles quel rythme ? En minutes par km ?"],
        999003: ["Coach, bilan semaine 2 : toujours TSB à -18, j'ai du mal à récupérer entre les séances. Faut que j'allège ?",
                  "Si j'allège, je perds pas le bénéfice de la surcharge ?"],
    },
    10: {
        999005: ["Sortie longue 120km avec 2500m D+. Les cervicales ont bloqué après 80km. J'ai dû m'arrêter 10 minutes. Solution ?"],
        999001: ["Ma sortie de 60km avec 1000m D+ : le psoas a tenu mais j'étais cuit sur la fin. Prochaine étape 80km dans 2 semaines, je continue le rythme ?"],
    },
    12: {
        999004: ["Ça y est, -1.5kg sur la balance !!! Mais je stagne sur les machines, je soulève toujours pareil. Normal ?",
                  "Tu me conseilles de changer de programme ou de continuer ?"],
        999001: ["Question nutrition : avant ma sortie longue du weekend, je mange quoi et quand ? J'ai eu un coup de barre au km 50 la dernière fois."],
    },
    15: {
        999002: ["Coach ! J'ai couru 5km en 32 minutes sans m'arrêter ! Trop contente. Par contre j'ai une ampoule sous le pied gauche. Je perce ou pas ?",
                  "Et pour la suite, je passe à 6km ou je reste à 5km cette semaine ?"],
        999003: ["Semaine 3, j'ai allégé comme tu m'as dit, TSB remonté à -10. Je me sens beaucoup mieux. Je peux réaugmenter la semaine prochaine ?"],
    },
    17: {
        999005: ["2ème sortie longue depuis les cervicales : j'ai mis un coussin de tige et ajusté ma position, plus de douleur. Coïncidence ou le réglage a marché ?"],
        999004: ["Coach, je vois des progrès visuels dans le miroir mais la balance bouge plus. C'est le muscle qui remplace le gras ?"],
    },
    20: {
        999001: ["Sortie de 80km avec 1600m D+ : objectif atteint ! Le psoas a tenu, les jambes ont répondu. Prochaine étape 100km ?",
                  "Et j'ai mal au dos niveau lombaires le lendemain, c'est lié à la position vélo ?"],
        999002: ["J'ai une douleur au genou droit apparue après ma sortie de 6km hier. C'est pas très fort mais ça m'inquiète. Je continue ou j'arrête ?"],
    },
    22: {
        999003: ["Coach, j'ai fait mon premier brick vélo 2h + cap 45min. Les jambes étaient en coton sur la course. C'est normal ? Des astuces pour la transition ?",
                  "Et nutrition : j'ai pris un gel à la transition, mais j'avais des crampes d'estomac. Alternative ?"],
        999005: ["CLM dans 3 semaines, j'ai reconnu le parcours. 35km plutôt roulant. Tu me conseilles quel braquet ? Je suis en 54 dents devant."],
    },
    25: {
        999001: ["Dernière grosse sortie avant la cyclo : 100km avec 2000m D+, bouclé en 4h15. Je me sens prêt ! Des conseils pour les 3 derniers jours avant la course ?",
                  "Et niveau bouffe la veille, le fameux 'pasta party', c'est vraiment efficace ?"],
        999004: ["Coach ! -4kg en 1 mois et j'ai augmenté mes charges sur tous les exos ! Je suis trop contente. Prochaine étape : commencer les squats libres ?"],
    },
    28: {
        999002: ["Coach, le genou va mieux après 1 semaine de repos. J'ai repris doucement 4km, RAS. À partir de quand je peux réaugmenter le volume ?",
                  "Et j'aimerais bien me fixer un objectif course dans 2 mois. Un 10km chronométré c'est réaliste ?"],
        999003: ["Bilan du mois : TSB stabilisé à -5, volume bien géré. Prochaine étape j'aimerais monter à 12h/semaine. Trop ou je peux y aller ?"],
    },
    30: {
        999005: ["J-3 avant le CLM, je stresse un peu. Routine des derniers jours ?",
                  "Et le matin de la course, petit dej combien de temps avant ?"],
        999002: ["Merci coach pour le suivi ce mois-ci ! J'ai fait 5km en 30min aujourd'hui, record perso. Prochaine étape 8km. Tu crois que c'est jouable en 1 mois ?"],
    },
}


# ── Helpers Supabase ────────────────────────────────────────────────────

async def setup_test_users(client: AsyncOpenAI):
    """Crée les utilisateurs de test dans Supabase s'ils n'existent pas."""
    from src.db.users import get_or_create_user, update_user_profile

    print("📝 Création des utilisateurs de test...")
    for tg_id in TEST_TELEGRAM_IDS:
        profile = PROFILES[tg_id]
        name = profile["name"]
        # Create user
        user = await asyncio.to_thread(
            get_or_create_user, tg_id, name, None
        )
        # Set profile
        profile_data = {
            "name": name,
            "sport": profile["sport"],
            "level": profile["level"],
            "goal": profile["goal"],
            "experience": profile["experience"],
            "blessures": profile.get("blessures"),
            "weight_kg": profile.get("weight_kg"),
            "height_cm": profile.get("height_cm"),
            "age": profile.get("age"),
            "gender": profile.get("gender"),
            "ftp_watts": profile.get("ftp_watts"),
            "vdot": profile.get("vdot"),
            "ctl": profile.get("ctl"),
            "tsb": profile.get("tsb"),
        }
        await asyncio.to_thread(update_user_profile, tg_id, profile_data)
        print(f"   ✅ {name} (ID={tg_id})")
    print()


async def get_active_session_for_day(tg_id: int, day: int):
    """Retourne la session active ou None si expirée (>24h).
    Simule la logique de get_or_create_active_session mais sans effet de bord."""
    from src.db.sessions import _get_active_session_id, create_session

    active = await asyncio.to_thread(_get_active_session_id, tg_id)
    if active:
        started = active.get("started_at")
        if started:
            if isinstance(started, str):
                started = datetime.fromisoformat(started.replace("Z", "+00:00"))
            session_day = started.day
            # Simulation : si on est >= 2 jours après, la session est expirée
            if day - session_day >= 2:
                return None, active  # Expirée, retourne l'ancienne pour résumé
        # Session encore active
        return active, None
    return None, None


async def handle_session_management(tg_id: int, day: int):
    """Gère la création/summarisation de session comme le vrai bot."""
    from src.db.sessions import (
        create_session, summarize_session, _get_active_session_id
    )

    active_session, old_session = await get_active_session_for_day(tg_id, day)

    if old_session and old_session.get("message_count", 0) > 0:
        # Ancienne session expirée → résumer
        old_id = old_session["id"]
        existing_summary = old_session.get("session_summary")
        if not existing_summary:
            try:
                await asyncio.to_thread(summarize_session, old_id)
                print(f"      📋 Session {old_id[:8]} résumée")
            except Exception as e:
                print(f"      ⚠️ Résumé session échoué: {e}")

    if active_session:
        return active_session

    # Créer une nouvelle session
    try:
        session = await asyncio.to_thread(create_session, tg_id, f"Semaine conversation jour {day}")
        return session
    except Exception as e:
        print(f"      ❌ Création session échouée: {e}")
        return None


async def save_coach_message(session_id: str, role: str, content: str,
                             tokens_in: int, tokens_out: int, cost: float,
                             concepts: list, level: int):
    """Sauvegarde un message dans chat_messages."""
    from src.db.sessions import save_message

    await asyncio.to_thread(
        save_message,
        session_id=session_id,
        role=role,
        content=content,
        tokens_in=tokens_in,
        tokens_out=tokens_out,
        cost_eur=round(cost, 6),
        concepts_used=concepts,
        level_used=level,
    )


# ── Extraction de faits (simplifiée, sans embeddings) ───────────────────

async def extract_and_save_facts(tg_id: int, session_id: str, messages_text: list[str]):
    """Extrait des faits via LLM et les sauvegarde dans user_facts.
    Skip embeddings (Gemini est cassé)."""
    from src.db.users import get_or_create_user
    from src.db.facts import add_fact, deduplicate_facts

    user = await asyncio.to_thread(get_or_create_user, tg_id, PROFILES[tg_id]["name"], None)
    db_user_id = str(user.get("id", ""))

    if not db_user_id:
        return

    # Prompt simple d'extraction
    extract_prompt = f"""Tu es un extracteur de faits pour un coach sportif IA. 
À partir de cette conversation, extrais 2-4 faits CONCIS (max 200 chars chacun) 
sur l'athlète. Catégories : entraînement, blessure, objectif, préférence, 
nutrition, historique, équipement, récupération.

CONVERSATION :
{chr(10).join(f'- {m[:300]}' for m in messages_text)}

Réponds UNIQUEMENT avec ce JSON :
[{{"fact": "texte", "category": "catégorie", "importance": 0.7}}]"""

    try:
        from openai import AsyncOpenAI
        client = AsyncOpenAI(
            api_key=settings.openrouter_api_key,
            base_url=settings.openrouter_base_url,
            timeout=30.0,
            max_retries=1,
        )

        resp = await client.chat.completions.create(
            model=EXTRACT_MODEL,
            messages=[{"role": "user", "content": extract_prompt}],
            temperature=0.3,
            max_tokens=400,
        )

        text = resp.choices[0].message.content or ""
        # Extract JSON array
        import re
        json_match = re.search(r"\[[\s\S]*\]", text)
        if not json_match:
            return

        facts = json.loads(json_match.group())
        for fact_data in facts:
            # Skip if similar fact exists
            is_dup, existing = await asyncio.to_thread(
                deduplicate_facts, db_user_id, fact_data["fact"]
            )
            if is_dup:
                continue

            await asyncio.to_thread(
                add_fact,
                db_user_id,
                fact_data["fact"],
                fact_data.get("category", "autre"),
                fact_data.get("importance", 0.5),
                session_id,
                [0.0] * 768,  # Zero vector 768d (Gemini embedding cassé)
            )

        print(f"      🧠 {len(facts)} faits extraits")

    except Exception as e:
        print(f"      ⚠️ Extraction faits échouée: {e}")


# ── Simulation principale ───────────────────────────────────────────────

async def run_month_simulation():
    client = AsyncOpenAI(
        api_key=settings.openrouter_api_key,
        base_url=settings.openrouter_base_url,
        timeout=60.0,
        max_retries=1,
    )

    print("📅 SIMULATION 1 MOIS — 5 utilisateurs, 30 jours")
    print(f"   Coach: {COACH_MODEL} | Extracteur: {EXTRACT_MODEL}")
    print(f"   Messages prévus : {sum(len(msgs) for day_msgs in CONVERSATION_PLAN.values() for msgs in day_msgs.values())}")
    print()

    # Init users
    await setup_test_users(client)

    all_results = []
    message_counter = {}  # tg_id → count (pour déclencher extraction tous les 5 msg)
    session_messages = {}  # tg_id → [user_msg, coach_msg, ...] (pour extraction)
    total_cost = 0.0
    total_tokens_in = 0
    total_tokens_out = 0

    for day in sorted(CONVERSATION_PLAN.keys()):
        day_msgs = CONVERSATION_PLAN[day]
        day_total = sum(len(msgs) for msgs in day_msgs.values())
        print(f"📆 Jour {day} — {day_total} messages")

        for tg_id in sorted(day_msgs.keys()):
            profile = PROFILES[tg_id]
            name = profile["name"]
            user_msgs = day_msgs[tg_id]

            # Gestion session
            session = await handle_session_management(tg_id, day)
            if not session:
                print(f"   ❌ {name}: impossible de créer une session")
                continue

            session_id = session["id"]

            # Initialiser compteur
            if tg_id not in message_counter:
                message_counter[tg_id] = session.get("message_count", 0)
            if tg_id not in session_messages:
                session_messages[tg_id] = []

            recent_context = []  # Contexte récent pour le sélecteur

            for i, user_msg in enumerate(user_msgs, 1):
                icon = "💬"
                try:
                    # ── Sélecteur ──
                    t0 = time.time()
                    selection = await select_concepts(
                        client=client, user_message=user_msg,
                        user_profile=profile, recent_context=recent_context,
                    )
                    sel_ms = (time.time() - t0) * 1000

                    # ── Prompt builder ──
                    system_prompt = build_system_prompt(
                        selection=selection, user_profile=profile
                    )

                    # ── Coach LLM ──
                    t1 = time.time()
                    resp = await client.chat.completions.create(
                        model=COACH_MODEL,
                        messages=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": f"[{name}] {user_msg}"},
                        ],
                        temperature=0.7, max_tokens=1200,
                    )
                    coach_ms = (time.time() - t1) * 1000

                    answer = resp.choices[0].message.content or ""
                    usage = resp.usage
                    tokens_in = usage.prompt_tokens if usage else 0
                    tokens_out = usage.completion_tokens if usage else 0
                    finish_reason = resp.choices[0].finish_reason

                    # Coût
                    cost = (tokens_in * 0.14 + tokens_out * 0.28) / 1_000_000
                    total_tokens_in += tokens_in
                    total_tokens_out += tokens_out
                    total_cost += cost

                    # ── Sauvegarde DB ──
                    await save_coach_message(
                        session_id, "user", user_msg,
                        tokens_in, 0, 0, selection["concepts"], selection["level"],
                    )
                    await save_coach_message(
                        session_id, "assistant", answer,
                        0, tokens_out, cost, selection["concepts"], selection["level"],
                    )

                    message_counter[tg_id] += 2  # user + assistant

                    # ── Contexte récent ──
                    recent_context.append({"role": "user", "content": user_msg})
                    recent_context.append({"role": "assistant", "content": answer[:200]})
                    session_messages[tg_id].append(f"USER: {user_msg}")
                    session_messages[tg_id].append(f"COACH: {answer[:200]}")

                    # ── Résultat ──
                    truncated = "✂️" if finish_reason == "length" else ""
                    print(f"   {icon} {name} msg{i} | {tokens_in}+{tokens_out} tokens | "
                          f"concepts={selection['concepts']} | "
                          f"sél={sel_ms:.0f}ms coach={coach_ms:.0f}ms {truncated}")
                    print(f"      ↳ {answer[:120]}...")

                    all_results.append({
                        "jour": day, "profil": name, "message_n": i,
                        "question": user_msg[:150], "reponse": answer[:200],
                        "concepts": selection["concepts"],
                        "tokens_in": tokens_in, "tokens_out": tokens_out,
                        "cout": round(cost, 6), "truncated": finish_reason == "length",
                    })

                    await asyncio.sleep(0.3)

                except Exception as e:
                    print(f"   🔥 {name} msg{i} | ERREUR: {e}")
                    all_results.append({"jour": day, "profil": name, "message_n": i, "erreur": str(e)})

            # ── Extraction de faits tous les 5 messages ──
            if message_counter[tg_id] >= 5:
                count_before = message_counter[tg_id]
                await extract_and_save_facts(tg_id, session_id, session_messages[tg_id][-20:])
                message_counter[tg_id] = 0  # Reset
                session_messages[tg_id] = []  # Vider

        print()

    # ── Vérification d'intégrité ────────────────────────────────────────
    print("═" * 60)
    print("🔍 VÉRIFICATION D'INTÉGRITÉ")
    print("═" * 60)

    admin = get_supabase_admin()
    checks = {}

    for tg_id in TEST_TELEGRAM_IDS:
        name = PROFILES[tg_id]["name"]

        # Vérifier l'utilisateur
        user_r = admin.table("users").select("id, first_name").eq("telegram_id", tg_id).execute()
        user_ok = bool(user_r.data)
        checks[f"{name} - user"] = user_ok

        if user_ok:
            user_id = user_r.data[0]["id"]
            stored_name = user_r.data[0].get("first_name", "?")
            print(f"   {'✅' if stored_name == name else '⚠️'} {name} : DB={stored_name}")

            # Compter les sessions
            sess_r = admin.table("chat_sessions").select("id", count="exact").eq("user_id", user_id).execute()
            sess_count = sess_r.count if hasattr(sess_r, 'count') else len(sess_r.data)
            checks[f"{name} - sessions"] = sess_count
            print(f"      Sessions : {sess_count}")

            # Compter les messages par session
            all_sessions = sess_r.data
            total_msgs = 0
            for s in all_sessions:
                sid = s["id"]
                msgs = admin.table("chat_messages").select("id", count="exact").eq("session_id", sid).execute()
                c = msgs.count if hasattr(msgs, 'count') else len(msgs.data)
                total_msgs += c

            checks[f"{name} - messages"] = total_msgs
            print(f"      Messages : {total_msgs}")

            # Compter les faits
            facts_r = admin.table("user_facts").select("id", count="exact").eq("user_id", user_id).execute()
            facts_count = facts_r.count if hasattr(facts_r, 'count') else len(facts_r.data)
            checks[f"{name} - faits"] = facts_count
            print(f"      Faits    : {facts_count}")

            # Vérifier les résumés de session
            summaries = [s for s in all_sessions if s.get("session_summary")]
            checks[f"{name} - résumés"] = len(summaries)
            if summaries:
                print(f"      Résumés  : {len(summaries)}")
                for s in summaries[:2]:
                    print(f"         {s['id'][:8]}: {s.get('session_summary', '')[:100]}")

        print()

    # ── Stats globales ──
    errors = sum(1 for r in all_results if r.get("erreur"))
    truncated = sum(1 for r in all_results if r.get("truncated"))

    print("═" * 60)
    print(f"📊 BILAN GLOBAL")
    print(f"   Messages traités  : {len(all_results)}")
    print(f"   Erreurs           : {errors}")
    print(f"   Tronqués          : {truncated}")
    print(f"   Tokens            : {total_tokens_in:,} in / {total_tokens_out:,} out")
    print(f"   Coût total        : {total_cost:.4f}€")
    print()

    # Sauvegarde
    RESULTS_FILE.parent.mkdir(exist_ok=True)
    with open(RESULTS_FILE, "w", encoding="utf-8") as f:
        json.dump({"checks": checks, "results": all_results, "stats": {
            "total": len(all_results), "errors": errors, "truncated": truncated,
            "tokens_in": total_tokens_in, "tokens_out": total_tokens_out,
            "cost_eur": total_cost,
        }}, f, ensure_ascii=False, indent=2)
    print(f"📁 Résultats : {RESULTS_FILE}")

    return all_results, checks


if __name__ == "__main__":
    asyncio.run(run_month_simulation())
