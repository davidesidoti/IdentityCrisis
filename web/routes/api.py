"""
API routes for guild and nickname management.
"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import delete, select

from shared import ExcludedChannel, Guild, Nickname, UserSession, get_db
from web.discord_oauth import DiscordOAuth
from web.routes.dependencies import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["api"])


# Pydantic models for request/response
class GuildSettings(BaseModel):
    enabled: bool
    restore_on_leave: bool
    immunity_role_id: Optional[int] = None


class NicknameCreate(BaseModel):
    nickname: str


class ExcludedChannelCreate(BaseModel):
    channel_id: int
    channel_name: str


class MessageResponse(BaseModel):
    message: str


@router.get("/guilds")
async def get_user_guilds(user: UserSession = Depends(get_current_user)):
    """Get all guilds where user has admin permissions and bot is present."""
    from shared import get_config
    
    config = get_config()
    oauth = DiscordOAuth(config)
    
    # Get user's guilds from Discord
    user_guilds = await oauth.get_user_guilds(user.access_token)
    
    # Filter to guilds where user has admin
    admin_guilds = [g for g in user_guilds if oauth.user_has_admin(g)]
    
    # Get guilds where bot is present from database
    db = get_db()
    async with db.async_session() as session:
        result = await session.execute(select(Guild.id))
        bot_guild_ids = {row[0] for row in result.fetchall()}
    
    # Return only guilds where both conditions are true
    guilds = []
    for guild in admin_guilds:
        guild_id = int(guild["id"])
        if guild_id in bot_guild_ids:
            guilds.append({
                "id": str(guild_id),
                "name": guild["name"],
                "icon_url": oauth.get_guild_icon_url(guild),
            })
    
    return {"guilds": guilds}


@router.get("/guilds/{guild_id}")
async def get_guild(
    guild_id: int,
    user: UserSession = Depends(get_current_user)
):
    """Get guild settings."""
    db = get_db()
    async with db.async_session() as session:
        result = await session.execute(
            select(Guild).where(Guild.id == guild_id)
        )
        guild = result.scalar_one_or_none()
        
        if not guild:
            raise HTTPException(status_code=404, detail="Guild not found")
        
        return {
            "id": str(guild.id),
            "name": guild.name,
            "icon_url": guild.icon_url,
            "enabled": guild.enabled,
            "restore_on_leave": guild.restore_on_leave,
            "immunity_role_id": str(guild.immunity_role_id) if guild.immunity_role_id else None,
        }


@router.patch("/guilds/{guild_id}")
async def update_guild_settings(
    guild_id: int,
    settings: GuildSettings,
    user: UserSession = Depends(get_current_user)
):
    """Update guild settings."""
    db = get_db()
    async with db.async_session() as session:
        result = await session.execute(
            select(Guild).where(Guild.id == guild_id)
        )
        guild = result.scalar_one_or_none()
        
        if not guild:
            raise HTTPException(status_code=404, detail="Guild not found")
        
        guild.enabled = settings.enabled
        guild.restore_on_leave = settings.restore_on_leave
        guild.immunity_role_id = settings.immunity_role_id
        
        await session.commit()
        
        return {"message": "Settings updated"}


# Nicknames
@router.get("/guilds/{guild_id}/nicknames")
async def get_nicknames(
    guild_id: int,
    user: UserSession = Depends(get_current_user)
):
    """Get all nicknames for a guild."""
    db = get_db()
    async with db.async_session() as session:
        result = await session.execute(
            select(Nickname).where(Nickname.guild_id == guild_id)
        )
        nicknames = result.scalars().all()
        
        return {
            "nicknames": [
                {"id": n.id, "nickname": n.nickname}
                for n in nicknames
            ]
        }


@router.post("/guilds/{guild_id}/nicknames")
async def add_nickname(
    guild_id: int,
    data: NicknameCreate,
    user: UserSession = Depends(get_current_user)
):
    """Add a nickname to a guild."""
    if len(data.nickname) > 32:
        raise HTTPException(
            status_code=400, 
            detail="Nickname must be 32 characters or less"
        )
    
    db = get_db()
    async with db.async_session() as session:
        # Check guild exists
        result = await session.execute(
            select(Guild).where(Guild.id == guild_id)
        )
        if not result.scalar_one_or_none():
            raise HTTPException(status_code=404, detail="Guild not found")
        
        nickname = Nickname(guild_id=guild_id, nickname=data.nickname)
        session.add(nickname)
        await session.commit()
        await session.refresh(nickname)
        
        return {"id": nickname.id, "nickname": nickname.nickname}


@router.delete("/guilds/{guild_id}/nicknames/{nickname_id}")
async def delete_nickname(
    guild_id: int,
    nickname_id: int,
    user: UserSession = Depends(get_current_user)
):
    """Delete a nickname from a guild."""
    db = get_db()
    async with db.async_session() as session:
        result = await session.execute(
            delete(Nickname).where(
                Nickname.id == nickname_id,
                Nickname.guild_id == guild_id
            )
        )
        await session.commit()
        
        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="Nickname not found")
        
        return {"message": "Nickname deleted"}


# Excluded Channels
@router.get("/guilds/{guild_id}/excluded-channels")
async def get_excluded_channels(
    guild_id: int,
    user: UserSession = Depends(get_current_user)
):
    """Get all excluded channels for a guild."""
    db = get_db()
    async with db.async_session() as session:
        result = await session.execute(
            select(ExcludedChannel).where(ExcludedChannel.guild_id == guild_id)
        )
        channels = result.scalars().all()
        
        return {
            "channels": [
                {
                    "id": c.id,
                    "channel_id": str(c.channel_id),
                    "channel_name": c.channel_name,
                }
                for c in channels
            ]
        }


@router.post("/guilds/{guild_id}/excluded-channels")
async def add_excluded_channel(
    guild_id: int,
    data: ExcludedChannelCreate,
    user: UserSession = Depends(get_current_user)
):
    """Add an excluded channel to a guild."""
    db = get_db()
    async with db.async_session() as session:
        # Check if already excluded
        result = await session.execute(
            select(ExcludedChannel).where(
                ExcludedChannel.guild_id == guild_id,
                ExcludedChannel.channel_id == data.channel_id
            )
        )
        if result.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Channel already excluded")
        
        channel = ExcludedChannel(
            guild_id=guild_id,
            channel_id=data.channel_id,
            channel_name=data.channel_name,
        )
        session.add(channel)
        await session.commit()
        await session.refresh(channel)
        
        return {
            "id": channel.id,
            "channel_id": str(channel.channel_id),
            "channel_name": channel.channel_name,
        }


@router.delete("/guilds/{guild_id}/excluded-channels/{channel_db_id}")
async def remove_excluded_channel(
    guild_id: int,
    channel_db_id: int,
    user: UserSession = Depends(get_current_user)
):
    """Remove an excluded channel from a guild."""
    db = get_db()
    async with db.async_session() as session:
        result = await session.execute(
            delete(ExcludedChannel).where(
                ExcludedChannel.id == channel_db_id,
                ExcludedChannel.guild_id == guild_id
            )
        )
        await session.commit()
        
        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="Channel not found")
        
        return {"message": "Channel removed from exclusion list"}
