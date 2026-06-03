"""CLI entrypoint for proactive coach cron.
Usage: python -m src.cli.proactive
Called by system cron on VPS, 2x/day (8h, 18h UTC).
"""
import asyncio
import logging
from src.engine.proactive import evaluate_all_users, send_push_notifications

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def main():
    logger.info("Starting proactive coach evaluation...")
    notifications = await evaluate_all_users()
    logger.info(f"Found {len(notifications)} users to notify")
    if notifications:
        await send_push_notifications(notifications)
    logger.info("Proactive coach evaluation complete")


if __name__ == "__main__":
    asyncio.run(main())
