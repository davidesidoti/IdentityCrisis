#!/usr/bin/env python3
"""
IdentityCrisis - Discord Bot + Web Dashboard
Main entry point for running both services.
"""

import asyncio
import logging
import sys
from contextlib import asynccontextmanager

import uvicorn
from dotenv import load_dotenv

from bot import IdentityCrisisBot
from shared import init_database, load_config
from web import create_app


def setup_logging() -> None:
    """Configure logging."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[
            logging.StreamHandler(sys.stdout),
        ],
    )
    
    # Reduce noise
    logging.getLogger("discord").setLevel(logging.WARNING)
    logging.getLogger("discord.http").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)


async def run_bot(config) -> None:
    """Run the Discord bot."""
    logger = logging.getLogger("bot")
    bot = IdentityCrisisBot(config)
    
    try:
        await bot.start(config.discord_token)
    except Exception as e:
        logger.error(f"Bot error: {e}")
        raise


async def run_web(config) -> None:
    """Run the web dashboard."""
    app = create_app()
    
    server_config = uvicorn.Config(
        app,
        host=config.web_host,
        port=config.web_port,
        log_level="info",
    )
    server = uvicorn.Server(server_config)
    await server.serve()


async def main() -> None:
    """Main entry point - runs both bot and web server."""
    setup_logging()
    logger = logging.getLogger(__name__)
    
    # Load environment variables
    load_dotenv()
    
    try:
        config = load_config()
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        sys.exit(1)
    
    # Initialize database
    logger.info("Initializing database...")
    await init_database(config.database_url)
    logger.info("Database initialized!")
    
    logger.info("=" * 50)
    logger.info("Starting IdentityCrisis...")
    logger.info(f"Web dashboard: http://{config.web_host}:{config.web_port}")
    logger.info("=" * 50)
    
    # Run both services concurrently
    await asyncio.gather(
        run_bot(config),
        run_web(config),
    )


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nShutting down. Goodbye!")
