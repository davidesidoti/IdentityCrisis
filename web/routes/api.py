"""
API routes for guild and nickname management.
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

import httpx
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import delete, func, select

from shared import CustomChannel, Guild, IncludedChannel, MemberNickname, Nickname, UserSession, get_config, get_db
from web.discord_oauth import DiscordOAuth
from web.routes.dependencies import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["api"])

STALE_MEMBER_DAYS = 30
DEFAULT_PAGE_SIZE = 25
MAX_PAGE_SIZE = 100


# Pydantic models for request/response
class GuildSettings(BaseModel):
    enabled: bool
    restore_on_leave: bool
    immunity_role_id: Optional[int] = None


class NicknameCreate(BaseModel):
    nickname: str


class IncludedChannelCreate(BaseModel):
    channel_id: str
    channel_name: str
    

class RuleCreate(BaseModel):
    type: str
    value: Optional[str] = None


class CustomChannelCreate(BaseModel):
    channel_id: str
    channel_name: str
    rules: list[RuleCreate] = []


class CustomChannelUpdate(BaseModel):
    rules: list[RuleCreate]


class MessageResponse(BaseModel):
    message: str


class MemberNicknameUpdate(BaseModel):
    reset_nickname: Optional[str] = None
    manual: bool = True


async def _apply_member_nickname(
    guild_id: int,
    user_id: int,
    nickname: Optional[str]
) -> tuple[bool, Optional[str]]:
    config = get_config()
    headers = {"Authorization": f"Bot {config.discord_token}"}
    payload = {"nick": nickname}
    url = f"{DiscordOAuth.API_BASE}/guilds/{guild_id}/members/{user_id}"

    async with httpx.AsyncClient() as client:
        response = await client.patch(url, json=payload, headers=headers)

    if response.status_code in (200, 204):
        return True, None
    return False, response.text


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


# Member reset nicknames
@router.get("/guilds/{guild_id}/member-nicknames")
async def get_member_nicknames(
    guild_id: int,
    page: int = 1,
    page_size: int = DEFAULT_PAGE_SIZE,
    user: UserSession = Depends(get_current_user)
):
    """Get paginated member reset nicknames for a guild."""
    if page < 1:
        raise HTTPException(status_code=400, detail="Page must be >= 1")
    if page_size < 1 or page_size > MAX_PAGE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"Page size must be between 1 and {MAX_PAGE_SIZE}"
        )

    db = get_db()
    async with db.async_session() as session:
        cutoff = datetime.now(timezone.utc) - timedelta(days=STALE_MEMBER_DAYS)
        await session.execute(
            delete(MemberNickname).where(
                MemberNickname.guild_id == guild_id,
                MemberNickname.last_seen_at < cutoff
            )
        )
        await session.commit()

        total_result = await session.execute(
            select(func.count()).select_from(MemberNickname).where(
                MemberNickname.guild_id == guild_id
            )
        )
        total = total_result.scalar_one()

        result = await session.execute(
            select(MemberNickname)
            .where(MemberNickname.guild_id == guild_id)
            .order_by(MemberNickname.last_seen_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        members = result.scalars().all()

        return {
            "members": [
                {
                    "id": m.id,
                    "user_id": str(m.user_id),
                    "username": m.username,
                    "display_name": m.display_name,
                    "reset_nickname": m.reset_nickname,
                    "reset_nickname_manual": m.reset_nickname_manual,
                    "last_seen_at": m.last_seen_at.isoformat() if m.last_seen_at else None,
                }
                for m in members
            ],
            "page": page,
            "page_size": page_size,
            "total": total,
            "stale_days": STALE_MEMBER_DAYS,
        }


@router.patch("/guilds/{guild_id}/member-nicknames/{member_id}")
async def update_member_nickname(
    guild_id: int,
    member_id: int,
    data: MemberNicknameUpdate,
    user: UserSession = Depends(get_current_user)
):
    """Update a member's reset nickname and apply immediately."""
    nickname = data.reset_nickname
    if nickname is not None:
        nickname = nickname.strip()
        if nickname == "":
            nickname = None
        if nickname is not None and len(nickname) > 32:
            raise HTTPException(
                status_code=400,
                detail="Nickname must be 32 characters or less"
            )

    db = get_db()
    async with db.async_session() as session:
        result = await session.execute(
            select(MemberNickname).where(
                MemberNickname.guild_id == guild_id,
                MemberNickname.user_id == member_id
            )
        )
        member = result.scalar_one_or_none()

        if not member:
            raise HTTPException(status_code=404, detail="Member not found")

        if data.manual:
            member.reset_nickname_manual = True
            member.reset_nickname = nickname
        else:
            member.reset_nickname_manual = False
            member.reset_nickname = nickname if nickname is not None else member.last_seen_nick

        await session.commit()

        applied, error = await _apply_member_nickname(
            guild_id,
            member_id,
            member.reset_nickname
        )

        if not applied:
            logger.warning(
                "Failed to apply nickname update for %s in guild %s: %s",
                member_id,
                guild_id,
                error
            )

        return {
            "message": "Member nickname updated",
            "applied": applied,
            "reset_nickname": member.reset_nickname,
            "reset_nickname_manual": member.reset_nickname_manual,
        }


@router.delete("/guilds/{guild_id}/member-nicknames/{member_id}")
async def delete_member_nickname(
    guild_id: int,
    member_id: int,
    user: UserSession = Depends(get_current_user)
):
    """Delete a member's reset nickname entry."""
    db = get_db()
    async with db.async_session() as session:
        result = await session.execute(
            delete(MemberNickname).where(
                MemberNickname.guild_id == guild_id,
                MemberNickname.user_id == member_id
            )
        )
        await session.commit()

        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="Member not found")

        return {"message": "Member nickname removed"}


# Included Channels (whitelist)
@router.get("/guilds/{guild_id}/included-channels")
async def get_included_channels(
    guild_id: int,
    user: UserSession = Depends(get_current_user)
):
    """Get all included channels for a guild."""
    db = get_db()
    async with db.async_session() as session:
        result = await session.execute(
            select(IncludedChannel).where(IncludedChannel.guild_id == guild_id)
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


@router.post("/guilds/{guild_id}/included-channels")
async def add_included_channel(
    guild_id: int,
    data: IncludedChannelCreate,
    user: UserSession = Depends(get_current_user)
):
    """Add an included channel to a guild."""
    db = get_db()
    async with db.async_session() as session:
        # Check if already included
        result = await session.execute(
            select(IncludedChannel).where(
                IncludedChannel.guild_id == guild_id,
                IncludedChannel.channel_id == int(data.channel_id)
            )
        )
        if result.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Channel already included")
        
        channel = IncludedChannel(
            guild_id=guild_id,
            channel_id=int(data.channel_id),
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


@router.delete("/guilds/{guild_id}/included-channels/{channel_db_id}")
async def remove_included_channel(
    guild_id: int,
    channel_db_id: int,
    user: UserSession = Depends(get_current_user)
):
    """Remove an included channel from a guild."""
    db = get_db()
    async with db.async_session() as session:
        result = await session.execute(
            delete(IncludedChannel).where(
                IncludedChannel.id == channel_db_id,
                IncludedChannel.guild_id == guild_id
            )
        )
        await session.commit()
        
        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="Channel not found")
        
        return {"message": "Channel removed from inclusion list"}


# Custom Channels with Rules
@router.get("/guilds/{guild_id}/custom-channels")
async def get_custom_channels(
    guild_id: int,
    user: UserSession = Depends(get_current_user)
):
    """Get all custom channels for a guild."""
    db = get_db()
    async with db.async_session() as session:
        result = await session.execute(
            select(CustomChannel).where(CustomChannel.guild_id == guild_id)
        )
        channels = result.scalars().all()
        
        return {
            "channels": [
                {
                    "id": c.id,
                    "channel_id": str(c.channel_id),
                    "channel_name": c.channel_name,
                    "rules": c.rules or [],
                }
                for c in channels
            ]
        }


@router.post("/guilds/{guild_id}/custom-channels")
async def add_custom_channel(
    guild_id: int,
    data: CustomChannelCreate,
    user: UserSession = Depends(get_current_user)
):
    """Add a custom channel with rules."""
    db = get_db()
    async with db.async_session() as session:
        # Check if already exists
        result = await session.execute(
            select(CustomChannel).where(
                CustomChannel.guild_id == guild_id,
                CustomChannel.channel_id == int(data.channel_id)
            )
        )
        if result.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Channel already has custom rules")
        
        channel = CustomChannel(
            guild_id=guild_id,
            channel_id=int(data.channel_id),
            channel_name=data.channel_name,
            rules=[{"type": r.type, "value": r.value} for r in data.rules],
        )
        session.add(channel)
        await session.commit()
        await session.refresh(channel)
        
        return {
            "id": channel.id,
            "channel_id": str(channel.channel_id),
            "channel_name": channel.channel_name,
            "rules": channel.rules,
        }


@router.patch("/guilds/{guild_id}/custom-channels/{channel_db_id}")
async def update_custom_channel(
    guild_id: int,
    channel_db_id: int,
    data: CustomChannelUpdate,
    user: UserSession = Depends(get_current_user)
):
    """Update rules for a custom channel."""
    db = get_db()
    async with db.async_session() as session:
        result = await session.execute(
            select(CustomChannel).where(
                CustomChannel.id == channel_db_id,
                CustomChannel.guild_id == guild_id
            )
        )
        channel = result.scalar_one_or_none()
        
        if not channel:
            raise HTTPException(status_code=404, detail="Custom channel not found")
        
        channel.rules = [{"type": r.type, "value": r.value} for r in data.rules]
        await session.commit()
        
        return {"message": "Rules updated"}


@router.delete("/guilds/{guild_id}/custom-channels/{channel_db_id}")
async def delete_custom_channel(
    guild_id: int,
    channel_db_id: int,
    user: UserSession = Depends(get_current_user)
):
    """Delete a custom channel."""
    db = get_db()
    async with db.async_session() as session:
        result = await session.execute(
            delete(CustomChannel).where(
                CustomChannel.id == channel_db_id,
                CustomChannel.guild_id == guild_id
            )
        )
        await session.commit()
        
        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="Custom channel not found")
        
        return {"message": "Custom channel deleted"}


@router.get("/available-rules")
async def get_available_rules():
    """Get list of available transformation rules."""
    from bot.data import TRANSFORMER_NAMES
    
    return {
        "rules": [
            {"type": key, "name": name, "has_value": key in ["prefix", "suffix"]}
            for key, name in TRANSFORMER_NAMES.items()
        ]
    }
