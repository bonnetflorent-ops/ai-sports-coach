# -*- coding: utf-8 -*-
"""Ça reste volontairement en français, c'est un produit français."""

from aiogram import Router, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

router = Router(name="onboarding")


class Onboarding(StatesGroup):
    waiting = State()


@router.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    prenom = message.from_user.first_name

    await message.answer(
        f"Salut {prenom} ! 👋\n\n"
        f"Je suis ton assistant d'entraînement IA. "
        f"Je crée des plans, j'analyse tes séances, et surtout — je dialogue avec toi.\n\n"
        f"Pour commencer, j'ai besoin d'en savoir un peu plus sur toi. "
        f"Réponds à ces 5 questions en une fois :\n\n"
        f"1️⃣ Quel est ton sport principal ?\n"
        f"2️⃣ Quel est ton niveau (débutant / intermédiaire / avancé) ?\n"
        f"3️⃣ Quel est ton objectif actuel ?\n"
        f"4️⃣ Combien de créneaux par semaine as-tu ? Quels jours ?\n"
        f"5️⃣ As-tu des blessures ou contraintes que je dois connaître ?\n\n"
        f"*Numérote tes réponses, je m'occupe du reste.*"
    )
    await state.set_state(Onboarding.waiting)
