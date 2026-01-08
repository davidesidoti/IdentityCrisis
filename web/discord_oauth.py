"""
Discord OAuth2 service for web authentication.
"""

from datetime import datetime, timedelta, timezone
from typing import Any, Optional

import httpx

from shared import Config


class DiscordOAuth:
    """Discord OAuth2 client."""
    
    API_BASE = "https://discord.com/api/v10"
    
    def __init__(self, config: Config):
        self.client_id = config.discord_client_id
        self.client_secret = config.discord_client_secret
        self.redirect_uri = config.discord_redirect_uri
    
    async def exchange_code(self, code: str) -> dict[str, Any]:
        """Exchange authorization code for access token."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.API_BASE}/oauth2/token",
                data={
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "grant_type": "authorization_code",
                    "code": code,
                    "redirect_uri": self.redirect_uri,
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
            response.raise_for_status()
            return response.json()
    
    async def refresh_token(self, refresh_token: str) -> dict[str, Any]:
        """Refresh an access token."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.API_BASE}/oauth2/token",
                data={
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "grant_type": "refresh_token",
                    "refresh_token": refresh_token,
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
            response.raise_for_status()
            return response.json()
    
    async def get_user(self, access_token: str) -> dict[str, Any]:
        """Get the current user's info."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.API_BASE}/users/@me",
                headers={"Authorization": f"Bearer {access_token}"},
            )
            response.raise_for_status()
            return response.json()
    
    async def get_user_guilds(self, access_token: str) -> list[dict[str, Any]]:
        """Get the current user's guilds."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.API_BASE}/users/@me/guilds",
                headers={"Authorization": f"Bearer {access_token}"},
            )
            response.raise_for_status()
            return response.json()
    
    @staticmethod
    def calculate_token_expiry(expires_in: int) -> datetime:
        """Calculate token expiry datetime."""
        return datetime.now(timezone.utc) + timedelta(seconds=expires_in)
    
    @staticmethod
    def is_token_expired(expires_at: datetime) -> bool:
        """Check if token is expired (with 5 min buffer)."""
        return datetime.now(timezone.utc) >= (expires_at - timedelta(minutes=5))
    
    @staticmethod
    def user_has_admin(guild: dict[str, Any]) -> bool:
        """Check if user has admin permissions in a guild."""
        permissions = int(guild.get("permissions", 0))
        ADMINISTRATOR = 0x8
        MANAGE_GUILD = 0x20
        return bool(permissions & (ADMINISTRATOR | MANAGE_GUILD))
    
    @staticmethod
    def get_avatar_url(user: dict[str, Any]) -> Optional[str]:
        """Get user avatar URL."""
        avatar = user.get("avatar")
        if avatar:
            user_id = user["id"]
            ext = "gif" if avatar.startswith("a_") else "png"
            return f"https://cdn.discordapp.com/avatars/{user_id}/{avatar}.{ext}"
        return None
    
    @staticmethod
    def get_guild_icon_url(guild: dict[str, Any]) -> Optional[str]:
        """Get guild icon URL."""
        icon = guild.get("icon")
        if icon:
            guild_id = guild["id"]
            ext = "gif" if icon.startswith("a_") else "png"
            return f"https://cdn.discordapp.com/icons/{guild_id}/{icon}.{ext}"
        return None
