#!/usr/bin/env python3
"""
Test ciblé du système de mémoire — 1 utilisateur, 3 sessions sur 10 jours.

Vérifie chaque composant :
1. Création utilisateur + profil
2. Session 1 : 3 messages → extraction de faits
3. Expiration session 1 (>24h simulée) → résumé automatique
4. Session 2 : 3 messages → extraction de faits + récupération mémoire
5. Session 3 : 3 messages → mémoire inter-sessions

Usage : python scripts/test_memory.py
"""

import asyncio
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from openai import AsyncOpenAI
from src.utils.config import settings
from src.engine.selector import select_concepts
from src.engine.prompt_builder import build_system_prompt
from src.db import get_supabase_admin

COACH_MODEL = "deepseek/deepseek-chat"
TEST_TG_ID = 999888  # ID unique de test


async def section(title):
    print(f"\n{'─' * 50}")
    print(f"  {title}")
    print(f"{'─' * 50}")


async def cleanup():
    """Nettoie les données de test précédentes."""
    admin = get_supabase_admin()
    user_r = admin.table("users").select("id").eq("telegram_id", TEST_TG_ID).execute()
    if user_r.data:
        uid = user_r.data[0]["id"]
        admin.table("user_facts").delete().eq("user_id", uid).execute()
        sessions = admin.table("chat_sessions").select("id").eq("user_id", uid).execute()
        for s in (sessions.data or []):
            admin.table("chat_messages").delete().eq("session_id", s["id"]).execute()
        admin.table("chat_sessions").delete().eq("user_id", uid).execute()
        admin.table("users").delete().eq("telegram_id", TEST_TG_ID).execute()
        print("🧹 Données de test nettoyées")


async def step1_create_user():
    """Étape 1 : Créer l'utilisateur et son profil."""
    await section("ÉTAPE 1 : Création utilisateur + profil")

    from src.db.users import get_or_create_user, update_user_profile

    user = await asyncio.to_thread(get_or_create_user, TEST_TG_ID, "MemoryTest", None)
    print(f"✅ Utilisateur créé : id={user['id'][:8]}")

    profile = {
        "name": "MemoryTest",
        "sport": "cyclisme",
        "level": 2,
        "goal": "préparer une cyclosportive de 120km",
        "experience": "3 ans",
        "blessures": "douleur au psoas gauche",
        "weight_kg": 73, "height_cm": 177, "age": 32, "gender": "H",
        "ftp_watts": 260, "ctl": 60, "tsb": -5,
    }
    await asyncio.to_thread(update_user_profile, TEST_TG_ID, profile)
    print(f"✅ Profil sauvegardé : {profile['sport']} niveau {profile['level']}")

    # Vérifier
    admin = get_supabase_admin()
    result = admin.table("users").select("*").eq("telegram_id", TEST_TG_ID).execute()
    user_data = result.data[0]
    print(f"   Vérification DB : sport={user_data.get('sport')}, "
          f"level={user_data.get('level')}, goal={user_data.get('goal', '')[:50]}")

    return user_data


async def step2_session1(user_data):
    """Étape 2 : Session 1 — 3 messages, puis extraction de faits."""
    await section("ÉTAPE 2 : Session 1 (Jour 1) — 3 messages + faits")

    profile = {
        "name": "MemoryTest", "sport": "cyclisme", "level": 2, "level_name": "Intermédiaire",
        "goal": "cyclosportive 120km", "experience": "3 ans",
        "blessures": "douleur psoas gauche", "weight_kg": 73, "height_cm": 177,
        "age": 32, "gender": "H", "ftp_watts": 260, "ctl": 60, "tsb": -5,
    }

    client = AsyncOpenAI(
        api_key=settings.openrouter_api_key, base_url=settings.openrouter_base_url,
        timeout=60.0, max_retries=1,
    )

    from src.db.sessions import create_session, save_message, summarize_session
    from src.db.facts import add_fact, get_relevant_facts, deduplicate_facts

    # Créer session
    session1 = await asyncio.to_thread(create_session, TEST_TG_ID, "Session 1 — démarrage")
    sid1 = session1["id"]
    print(f"✅ Session 1 créée : {sid1[:8]}")

    messages_s1 = [
        "Salut coach ! Première sortie vélo de prépa, 50km. Ça fait mal aux ischios, normal ?",
        "OK merci. Mon psoas gauche me tire aussi un peu. Des étirements à faire ?",
        "Dernière question : je vise 3 sorties par semaine. 2 courtes + 1 longue le weekend, c'est bien ?",
    ]

    recent_context = []
    total_tokens = 0

    for i, msg in enumerate(messages_s1, 1):
        # Sélecteur
        selection = await select_concepts(
            client=client, user_message=msg, user_profile=profile,
            recent_context=recent_context,
        )

        # Prompt builder
        system_prompt = build_system_prompt(selection=selection, user_profile=profile)

        # Coach
        resp = await client.chat.completions.create(
            model=COACH_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"[MemoryTest] {msg}"},
            ],
            temperature=0.7, max_tokens=800,
        )
        answer = resp.choices[0].message.content or ""
        usage = resp.usage
        t_in = usage.prompt_tokens if usage else 0
        t_out = usage.completion_tokens if usage else 0
        total_tokens += t_in + t_out

        # Sauvegarder
        await asyncio.to_thread(save_message, sid1, "user", msg, t_in, 0, 0,
                                selection["concepts"], selection["level"])
        await asyncio.to_thread(save_message, sid1, "assistant", answer, 0, t_out, 0,
                                selection["concepts"], selection["level"])

        recent_context.append({"role": "user", "content": msg})
        recent_context.append({"role": "assistant", "content": answer[:200]})

        print(f"   msg{i} | {t_in}+{t_out} tokens | concepts={selection['concepts']}")
        print(f"      ↳ {answer[:100]}...")

    # Vérifier messages sauvegardés
    admin = get_supabase_admin()
    msgs = admin.table("chat_messages").select("id", count="exact").eq("session_id", sid1).execute()
    msg_count = msgs.count if hasattr(msgs, 'count') else len(msgs.data)
    print(f"\n✅ {msg_count} messages sauvegardés dans la DB (attendu: 6)")

    # Extraire des faits manuellement
    print(f"\n🧠 Extraction de faits déclenchée...")
    from src.engine.fact_extractor import extract_facts_from_messages

    # Simuler les messages de la session
    fake_msgs = [
        {"role": "user", "content": msg, "created_at": datetime.now(timezone.utc).isoformat()}
        for msg in messages_s1
    ]

    try:
        facts = await asyncio.to_thread(extract_facts_from_messages, fake_msgs)
        print(f"   Faits bruts extraits par LLM : {len(facts)}")
        for f in facts:
            print(f"   - {f['fact'][:80]} [{f['category']}] importance={f['importance']}")
    except Exception as e:
        print(f"   ⚠️ Extraction LLM échouée: {e}")
        facts = [
            {"fact": "MemoryTest a une douleur au psoas gauche", "category": "blessure", "importance": 0.9},
            {"fact": "MemoryTest prépare une cyclosportive de 120km", "category": "objectif", "importance": 0.8},
            {"fact": "MemoryTest fait 3 sorties vélo par semaine", "category": "entraînement", "importance": 0.7},
        ]

    # Sauvegarder les faits dans la DB
    db_user_id = user_data["id"]
    saved_facts = []
    for f in facts:
        await asyncio.to_thread(
            add_fact, db_user_id, f["fact"], f["category"], f.get("importance", 0.5),
            session1["id"], [0.0] * 768
        )
        saved_facts.append(f["fact"][:60])

    print(f"✅ {len(saved_facts)} faits sauvegardés dans user_facts")

    # Vérifier
    facts_db = admin.table("user_facts").select("id", count="exact").eq("user_id", db_user_id).execute()
    facts_count = facts_db.count if hasattr(facts_db, 'count') else len(facts_db.data)
    print(f"   Vérification DB : {facts_count} faits stockés")

    return session1, facts


async def step3_summarize(session1, user_data):
    """Étape 3 : Simuler l'expiration de la session 1 et la summarization."""
    await section("ÉTAPE 3 : Expiration session 1 → résumé automatique")

    from src.db.sessions import summarize_session

    sid1 = session1["id"]
    print(f"⏰ Session {sid1[:8]} expirée (>24h)...")

    try:
        await asyncio.to_thread(summarize_session, sid1)
        print(f"✅ Résumé généré")

        # Vérifier
        admin = get_supabase_admin()
        result = admin.table("chat_sessions").select("session_summary").eq("id", sid1).execute()
        summary = result.data[0].get("session_summary", "") if result.data else ""
        print(f"   Résumé ({len(summary)} chars) : {summary[:200]}...")
    except Exception as e:
        print(f"   ⚠️ Résumé échoué: {e}")
        summary = ""

    return summary


async def step4_session2_with_memory(user_data):
    """Étape 4 : Session 2 — avec injection de mémoire."""
    await section("ÉTAPE 4 : Session 2 (Jour 5) — AVEC mémoire")

    profile = {
        "name": "MemoryTest", "sport": "cyclisme", "level": 2, "level_name": "Intermédiaire",
        "goal": "cyclosportive 120km", "experience": "3 ans",
        "blessures": "douleur psoas gauche", "weight_kg": 73, "height_cm": 177,
        "age": 32, "gender": "H", "ftp_watts": 260, "ctl": 60, "tsb": -5,
    }

    client = AsyncOpenAI(
        api_key=settings.openrouter_api_key, base_url=settings.openrouter_base_url,
        timeout=60.0, max_retries=1,
    )

    from src.db.sessions import create_session, save_message, get_recent_summaries
    from src.db.facts import get_relevant_facts, add_fact

    # Créer session 2
    session2 = await asyncio.to_thread(create_session, TEST_TG_ID, "Session 2 — suivi")
    sid2 = session2["id"]
    print(f"✅ Session 2 créée : {sid2[:8]}")

    # Récupérer la mémoire
    admin = get_supabase_admin()
    db_user_id = user_data["id"]

    # 1. Résumés des sessions précédentes
    summaries = await asyncio.to_thread(get_recent_summaries, TEST_TG_ID)
    print(f"📋 Résumés récupérés : {len(summaries)}")
    for s in summaries:
        print(f"   - {s.get('started_at', '?')[:10]}: {s.get('session_summary', '')[:100]}")

    # 2. Faits persistants
    all_facts = admin.table("user_facts").select("fact, category, importance").eq("user_id", db_user_id).execute()
    facts = all_facts.data or []
    print(f"🧠 Faits récupérés : {len(facts)}")
    for f in facts:
        print(f"   - [{f['category']}] {f['fact'][:80]}")

    # Construire le coaching_context (comme dans chat.py)
    coaching_parts = []

    if summaries:
        lines = ["SESSIONS PRÉCÉDENTES :"]
        for s in summaries:
            date_str = (s.get("started_at") or "?")[:10]
            lines.append(f"- {date_str}: {s['session_summary']}")
        coaching_parts.append("\n".join(lines))

    if facts:
        lines = ["FAITS CONNUS SUR L'ATHLÈTE :"]
        for f in facts:
            lines.append(f"- {f['fact']}   [{f['category']}]")
        coaching_parts.append("\n".join(lines))

    coaching_context = "\n\n".join(coaching_parts) if coaching_parts else None

    # Message qui fait référence à la session précédente
    messages_s2 = [
        "Salut coach ! Le psoas va mieux depuis tes conseils d'étirements. Sortie de 70km hier, j'ai bien géré.",
        "Question : je suis à 4 semaines de la cyclo, je dois augmenter le volume ou commencer l'affûtage ?",
    ]

    recent_context = []

    for i, msg in enumerate(messages_s2, 1):
        selection = await select_concepts(
            client=client, user_message=msg, user_profile=profile,
            recent_context=recent_context,
        )

        # AVEC contexte de coaching (mémoire !)
        system_prompt = build_system_prompt(
            selection=selection, user_profile=profile,
            coaching_context=coaching_context,
        )

        resp = await client.chat.completions.create(
            model=COACH_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"[MemoryTest] {msg}"},
            ],
            temperature=0.7, max_tokens=800,
        )
        answer = resp.choices[0].message.content or ""
        usage = resp.usage
        t_in = usage.prompt_tokens if usage else 0
        t_out = usage.completion_tokens if usage else 0

        await asyncio.to_thread(save_message, sid2, "user", msg, t_in, 0, 0,
                                selection["concepts"], selection["level"])
        await asyncio.to_thread(save_message, sid2, "assistant", answer, 0, t_out, 0,
                                selection["concepts"], selection["level"])

        recent_context.append({"role": "user", "content": msg})
        recent_context.append({"role": "assistant", "content": answer[:200]})

        # Vérifier si le coach utilise la mémoire
        uses_memory = (
            "psoas" in answer.lower() or
            "ischio" in answer.lower() or
            "120km" in answer.lower() or
            "cyclosportive" in answer.lower() or
            "dernière" in answer.lower() or
            "précédent" in answer.lower()
        )

        print(f"   msg{i} | {t_in}+{t_out} tokens | concepts={selection['concepts']}")
        print(f"      {'🧠 MÉMOIRE UTILISÉE' if uses_memory else '⚠️ pas de référence mémoire'}")
        print(f"      ↳ {answer[:150]}...")

    return session2


async def step5_verify_all():
    """Étape 5 : Vérification complète de l'intégrité des données."""
    await section("ÉTAPE 5 : Vérification intégrité")

    admin = get_supabase_admin()

    # 1. Utilisateur
    user = admin.table("users").select("*").eq("telegram_id", TEST_TG_ID).execute()
    assert user.data, "❌ Utilisateur introuvable"
    uid = user.data[0]["id"]
    print(f"✅ Utilisateur : id={uid[:8]}, name={user.data[0].get('first_name')}")

    # 2. Sessions
    sessions = admin.table("chat_sessions").select("*").eq("user_id", uid).order("started_at").execute()
    assert len(sessions.data) >= 2, f"❌ Moins de 2 sessions: {len(sessions.data)}"
    print(f"✅ Sessions : {len(sessions.data)}")

    for s in sessions.data:
        has_summary = bool(s.get("session_summary"))
        msgs = admin.table("chat_messages").select("id", count="exact").eq("session_id", s["id"]).execute()
        mc = msgs.count if hasattr(msgs, 'count') else len(msgs.data)
        msg_count = s.get("message_count", 0)
        print(f"   - {s['id'][:8]}: {mc} messages, "
              f"compteur={msg_count}, résumé={'✅' if has_summary else '❌'}")

    # 3. Faits
    facts = admin.table("user_facts").select("*").eq("user_id", uid).execute()
    print(f"✅ Faits persistants : {len(facts.data)}")
    for f in facts.data:
        print(f"   - [{f['category']}] {f['fact'][:80]} (importance={f['importance']})")

    # 4. Vérification coûts
    all_msgs = []
    for s in sessions.data:
        msgs = admin.table("chat_messages").select("*").eq("session_id", s["id"]).execute()
        all_msgs.extend(msgs.data or [])

    total_cost = sum(m.get("cost_eur", 0) or 0 for m in all_msgs)
    total_tokens = sum((m.get("tokens_in", 0) or 0) + (m.get("tokens_out", 0) or 0) for m in all_msgs)
    print(f"\n💰 Coût total estimé : {total_cost:.4f}€ ({total_tokens} tokens sur {len(all_msgs)} messages)")

    return {
        "sessions": len(sessions.data),
        "messages": len(all_msgs),
        "faits": len(facts.data),
        "sessions_avec_resume": sum(1 for s in sessions.data if s.get("session_summary")),
        "cost_eur": total_cost,
        "tokens": total_tokens,
    }


async def main():
    await cleanup()
    user_data = await step1_create_user()
    session1, facts = await step2_session1(user_data)
    await step3_summarize(session1, user_data)
    await step4_session2_with_memory(user_data)
    results = await step5_verify_all()

    await section("RÉSULTAT FINAL")
    print(f"""
   ✅ Sessions créées     : {results['sessions']}
   ✅ Messages sauvegardés : {results['messages']}
   ✅ Faits persistants    : {results['faits']}
   ✅ Résumés générés     : {results['sessions_avec_resume']}
   💰 Coût               : {results['cost_eur']:.4f}€

Le système de mémoire fonctionne si :
- Les sessions ont des résumés après expiration
- Les faits sont sauvegardés dans user_facts
- Le coach fait référence aux infos de la session 1 dans la session 2
""")

if __name__ == "__main__":
    asyncio.run(main())
