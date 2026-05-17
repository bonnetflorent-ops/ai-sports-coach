# -*- coding: utf-8 -*-
"""AI Sports Coach — Bot Telegram principal."""

import asyncio

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties

from src.utils.config import settings
from src.utils.logging_setup import setup_logging
from src.bot.handlers import start, chat, feedback

import structlog

setup_logging()
logger = structlog.get_logger(__name__)


async def main():
    bot = Bot(
        token=settings.telegram_bot_token,
        default=DefaultBotProperties(parse_mode="Markdown"),
    )
    dp = Dispatcher()

    # Handlers — l'ordre compte : /start en premier, puis fallback chat
    dp.include_router(start.router)
    dp.include_router(chat.router)
    dp.include_router(feedback.router)

    logger.info("bot_started", mode="polling")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())