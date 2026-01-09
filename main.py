#!/usr/bin/env python3
"""
IdentityCrisis - Discord Bot + Web Dashboard
Main entry point for running both services.
"""

import asyncio
import logging
import os
import sys
from contextlib import asynccontextmanager
from logging.handlers import RotatingFileHandler

import uvicorn
from dotenv import load_dotenv

from bot import IdentityCrisisBot
from shared import init_database, load_config
from web import create_app


def setup_logging(log_file_path: str, log_level: str = "INFO") -> None:
    """Configure logging."""
    level_name = log_level.upper()
    level_value = getattr(logging, level_name, logging.INFO)
    handlers: list[logging.Handler] = [logging.StreamHandler(sys.stdout)]

    if log_file_path:
        log_dir = os.path.dirname(log_file_path)
        if log_dir:
            os.makedirs(log_dir, exist_ok=True)
        file_handler = RotatingFileHandler(
            log_file_path,
            maxBytes=5 * 1024 * 1024,
            backupCount=5,
            encoding="utf-8",
        )
        file_handler.setLevel(level_value)
        handlers.append(file_handler)

    logging.basicConfig(
        level=level_value,
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=handlers,
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
    # Load environment variables
    load_dotenv()

    log_level = os.getenv("LOG_LEVEL", "INFO")
    log_file_path = os.getenv("LOG_FILE_PATH", "logs/identitycrisis.log")
    setup_logging(log_file_path, log_level)
    logger = logging.getLogger(__name__)
    
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
