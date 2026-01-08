"""
Shared configuration for IdentityCrisis.
Loads settings from environment variables.
"""

import os
from dataclasses import dataclass
from typing import Optional


@dataclass
class Config:
    """Application configuration."""
    
    # Discord Bot
    discord_token: str
    bot_prefix: str = "!"
    
    # Database
    database_url: str = "postgresql://localhost/identitycrisis"
    
    # Discord OAuth2 (for web dashboard)
    discord_client_id: str = ""
    discord_client_secret: str = ""
    discord_redirect_uri: str = "http://localhost:8000/auth/callback"
    
    # Web
    secret_key: str = "change-me-in-production"
    web_host: str = "0.0.0.0"
    web_port: int = 8000
    base_url: str = "http://localhost:8000"
    
    @classmethod
    def from_env(cls) -> "Config":
        """Load configuration from environment variables."""
        discord_token = os.getenv("DISCORD_TOKEN")
        if not discord_token:
            raise ValueError(
                "DISCORD_TOKEN environment variable is required."
            )
        
        database_url = os.getenv("DATABASE_URL")
        if not database_url:
            raise ValueError(
                "DATABASE_URL environment variable is required."
            )
        
        return cls(
            # Discord Bot
            discord_token=discord_token,
            bot_prefix=os.getenv("BOT_PREFIX", "!"),
            
            # Database
            database_url=database_url,
            
            # Discord OAuth2
            discord_client_id=os.getenv("DISCORD_CLIENT_ID", ""),
            discord_client_secret=os.getenv("DISCORD_CLIENT_SECRET", ""),
            discord_redirect_uri=os.getenv(
                "DISCORD_REDIRECT_URI", 
                "http://localhost:8000/auth/callback"
            ),
            
            # Web
            secret_key=os.getenv("SECRET_KEY", "change-me-in-production"),
            web_host=os.getenv("WEB_HOST", "0.0.0.0"),
            web_port=int(os.getenv("WEB_PORT", "8000")),
            base_url=os.getenv("BASE_URL", "http://localhost:8000"),
        )
    
    @property
    def discord_oauth_url(self) -> str:
        """Generate Discord OAuth2 authorization URL."""
        scopes = "identify guilds"
        return (
            f"https://discord.com/api/oauth2/authorize"
            f"?client_id={self.discord_client_id}"
            f"&redirect_uri={self.discord_redirect_uri}"
            f"&response_type=code"
            f"&scope={scopes}"
        )


# Global config instance
_config: Optional[Config] = None


def load_config() -> Config:
    """Load and cache the configuration."""
    global _config
    if _config is None:
        _config = Config.from_env()
    return _config


def get_config() -> Config:
    """Get the cached configuration."""
    if _config is None:
        raise RuntimeError("Config not loaded. Call load_config() first.")
    return _config
