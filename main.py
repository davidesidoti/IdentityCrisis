#!/usr/bin/env python3
"""
IdentityCrisis Discord Bot
Entry point for the application.

Who are you? Who knows. Join a voice channel and find out.
"""

import asyncio
import logging
import sys

from dotenv import load_dotenv

from config import load_config
from bot import IdentityCrisisBot


def setup_logging() -> None:
    """Configure logging for the bot."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[
            logging.StreamHandler(sys.stdout),
        ],
    )

    # Reduce noise from discord.py
    logging.getLogger("discord").setLevel(logging.WARNING)
    logging.getLogger("discord.http").setLevel(logging.WARNING)


async def main() -> None:
    """Main entry point."""
    setup_logging()
    logger = logging.getLogger(__name__)

    # Load environment variables from .env file
    load_dotenv()

    try:
        config = load_config()
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        sys.exit(1)

    logger.info("Starting IdentityCrisis bot...")

    bot = IdentityCrisisBot(config)

    async with bot:
        await bot.start(config.token)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nBot stopped by user. Goodbye!")
