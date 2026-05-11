# -*- coding: utf-8 -*-
"""Handler principal : envoie les messages à DeepSeek avec contexte minimal."""

from aiogram import Router, types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from src.engine.llm import chat as llm_chat
from src.bot.handlers.start import Onboarding

router = Router(name="chat")


class Chat(StatesGroup):
    active = State()


SYSTEM_PROMPT = """Tu es un assistant d'entraînement IA, spécialisé en sport.

Ton rôle :
- Conseiller, planifier, expliquer les principes d'entraînement
- Poser des questions précises et groupées (pas de ping-pong infini)
- Justifier tes recommandations scientifiquement
- Adapter tes réponses au niveau de l'athlète

Sécurité :
- Si l'utilisateur signale une douleur → recommander de consulter un médecin 
  ET proposer une adaptation concrète de l'entraînement
- JAMAIS de diagnostic médical

Reste concis, pédagogue, et encourageant."""


@router.message()
async def handle_message(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    prenom = message.from_user.first_name

    # Si onboarding en cours, traiter la réponse d'onboarding
    current_state = await state.get_state()
    if current_state == Onboarding.waiting.state:
        await state.clear()
        await message.answer(
            f"Parfait {prenom}, j'ai bien noté tout ça ! 🎯\n\n"
            f"Je te prépare un plan d'entraînement adapté. "
            f"En attendant, tu peux me poser toutes tes questions — "
            f"entraînement, nutrition, récupération, matériel..."
        )
        # TODO: sauvegarder le profil et générer un premier plan
        return

    # Conversation normale
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"[{prenom}] {message.text}"},
    ]

    try:
        response = await llm_chat(messages)
        await message.answer(response)
    except Exception as e:
        await message.answer(
            "Désolé, je rencontre un problème technique. Réessaie dans un instant."
        )
        raise
