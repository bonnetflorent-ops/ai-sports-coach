# -*- coding: utf-8 -*-
"""Handler /feedback — collecte le feedback utilisateur sur les réponses du coach."""

import logging
from aiogram import Router, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from src.db.sessions import get_or_create_active_session, save_message

router = Router(name="feedback")
logger = logging.getLogger(__name__)


class FeedbackState(StatesGroup):
    waiting = State()  # Attend le commentaire optionnel


@router.message(Command("feedback"))
async def cmd_feedback(message: types.Message, state: FSMContext):
    """Affiche les boutons de feedback pour la dernière réponse du coach."""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="👍 Utile", callback_data="fb:useful"),
            InlineKeyboardButton(text="👎 Pas utile", callback_data="fb:not_useful"),
        ],
        [
            InlineKeyboardButton(text="❌ Annuler", callback_data="fb:cancel"),
        ],
    ])
    await message.answer(
        "Évalue ma dernière réponse :",
        reply_markup=keyboard,
    )


@router.callback_query(lambda c: c.data and c.data.startswith("fb:"))
async def handle_feedback(callback: types.CallbackQuery, state: FSMContext):
    """Traite le clic sur un bouton de feedback."""
    action = callback.data.split(":", 1)[1]

    if action == "cancel":
        await callback.message.edit_text("Feedback annulé.")
        await callback.answer()
        return

    rating = "useful" if action == "useful" else "not_useful"
    emoji = "👍" if rating == "useful" else "👎"

    # Sauvegarder dans la session comme message system
    try:
        user_id = callback.from_user.id
        session = get_or_create_active_session(user_id)
        save_message(
            session_id=session["id"],
            role="system",
            content=f"FEEDBACK: {rating}",
            tokens_in=0,
            tokens_out=0,
            cost_eur=0.0,
        )
        logger.info(f"Feedback {rating} enregistré pour user={user_id}")
    except Exception as e:
        logger.warning(f"Erreur sauvegarde feedback: {e}")

    await callback.message.edit_text(f"{emoji} Merci pour ton retour !")
    await callback.answer()
