"""
Configuration module for IdentityCrisis bot.
Loads settings from environment variables.
"""

import os
from dataclasses import dataclass


@dataclass
class Config:
    """Bot configuration loaded from environment variables."""

    token: str
    prefix: str = "!"
    restore_on_leave: bool = True  # Restore original nickname when leaving voice

    @classmethod
    def from_env(cls) -> "Config":
        """Load configuration from environment variables."""
        token = os.getenv("DISCORD_TOKEN")
        if not token:
            raise ValueError(
                "DISCORD_TOKEN environment variable is required. "
                "Create a .env file with DISCORD_TOKEN=your_token_here"
            )

        return cls(
            token=token,
            prefix=os.getenv("BOT_PREFIX", "!"),
            restore_on_leave=os.getenv(
                "RESTORE_ON_LEAVE", "true").lower() == "true",
        )


def load_config() -> Config:
    """Load and return the bot configuration."""
    return Config.from_env()
