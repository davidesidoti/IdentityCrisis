"""
Voice Handler Cog for IdentityCrisis.
Listens to voice state updates and renames users on join.
"""

import logging
import random
from typing import Optional

import discord
from discord.ext import commands
from sqlalchemy import select

from bot.data import DEFAULT_NICKNAMES, apply_rules
from shared import IncludedChannel, Guild, Nickname, get_db

logger = logging.getLogger(__name__)


class VoiceHandler(commands.Cog):
    """Handles voice channel events and nickname chaos."""
    
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        # Store original nicknames: {guild_id: {user_id: original_nick}}
        self.original_nicknames: dict[int, dict[int, Optional[str]]] = {}
    
    async def _get_guild_settings(self, guild_id: int) -> Optional[Guild]:
        """Get guild settings from database."""
        db = get_db()
        async with db.async_session() as session:
            result = await session.execute(
                select(Guild).where(Guild.id == guild_id)
            )
            return result.scalar_one_or_none()
    
    async def _get_guild_nicknames(self, guild_id: int) -> list[str]:
        """Get nicknames for a guild (custom or default)."""
        db = get_db()
        async with db.async_session() as session:
            result = await session.execute(
                select(Nickname.nickname).where(Nickname.guild_id == guild_id)
            )
            custom_nicknames = [row[0] for row in result.fetchall()]
            
            if custom_nicknames:
                return custom_nicknames
            return DEFAULT_NICKNAMES.copy()
    
    async def _is_channel_allowed(self, guild_id: int, channel_id: int) -> bool:
        """
        Check if the bot is allowed to work in this channel.
        - If no included channels AND no custom channels: ALL channels are allowed
        - If included channels or custom channels exist: ONLY those channels are allowed
        - Custom channels are always implicitly included
        """
        from shared import IncludedChannel, CustomChannel
        
        db = get_db()
        async with db.async_session() as session:
            # Check if this is a custom channel (always allowed)
            result = await session.execute(
                select(CustomChannel).where(
                    CustomChannel.guild_id == guild_id,
                    CustomChannel.channel_id == channel_id
                )
            )
            if result.scalar_one_or_none():
                return True
            
            # Get included channels
            result = await session.execute(
                select(IncludedChannel).where(IncludedChannel.guild_id == guild_id)
            )
            included_channels = result.scalars().all()
            
            # Get custom channels (to check if any exist)
            result = await session.execute(
                select(CustomChannel).where(CustomChannel.guild_id == guild_id)
            )
            custom_channels = result.scalars().all()
            
            # If no included channels AND no custom channels, all channels are allowed
            if not included_channels and not custom_channels:
                return True
            
            # If we have included channels, check if this channel is in the list
            if included_channels:
                return any(ch.channel_id == channel_id for ch in included_channels)
            
            # If we only have custom channels (but this isn't one of them), not allowed
            return False
        
    async def _get_custom_channel_rules(self, guild_id: int, channel_id: int) -> list[dict] | None:
        """Get custom rules for a channel, if any."""
        from shared import CustomChannel
        
        db = get_db()
        async with db.async_session() as session:
            result = await session.execute(
                select(CustomChannel).where(
                    CustomChannel.guild_id == guild_id,
                    CustomChannel.channel_id == channel_id
                )
            )
            custom_channel = result.scalar_one_or_none()
            
            if custom_channel and custom_channel.rules:
                return custom_channel.rules
            return None
        
    async def _is_custom_channel(self, guild_id: int, channel_id: int) -> bool:
        """Check if a channel has custom rules."""
        from shared import CustomChannel
        
        db = get_db()
        async with db.async_session() as session:
            result = await session.execute(
                select(CustomChannel).where(
                    CustomChannel.guild_id == guild_id,
                    CustomChannel.channel_id == channel_id
                )
            )
            return result.scalar_one_or_none() is not None

    async def _ensure_guild_exists(self, guild: discord.Guild) -> Guild:
        """Ensure guild exists in database, create if not."""
        db = get_db()
        async with db.async_session() as session:
            result = await session.execute(
                select(Guild).where(Guild.id == guild.id)
            )
            db_guild = result.scalar_one_or_none()
            
            if db_guild is None:
                db_guild = Guild(
                    id=guild.id,
                    name=guild.name,
                    icon_url=str(guild.icon.url) if guild.icon else None,
                )
                session.add(db_guild)
                await session.commit()
                await session.refresh(db_guild)
                logger.info(f"Created guild entry for {guild.name} ({guild.id})")
            
            return db_guild
    
    def _store_original_nickname(
        self, 
        guild_id: int, 
        user_id: int, 
        nickname: Optional[str],
        display_name: str
    ) -> None:
        """Store the original nickname and display name before changing it."""
        if guild_id not in self.original_nicknames:
            self.original_nicknames[guild_id] = {}
        
        if user_id not in self.original_nicknames[guild_id]:
            # Store both: nick for restoring, display_name for transformations
            self.original_nicknames[guild_id][user_id] = {
                "nick": nickname,  # Can be None, used for restoring
                "display_name": display_name  # Used for transformations
            }
    
    def _pop_original_nickname(
        self, 
        guild_id: int, 
        user_id: int
    ) -> Optional[str]:
        """Retrieve and remove the stored original display name for restoring."""
        if guild_id in self.original_nicknames:
            data = self.original_nicknames[guild_id].pop(user_id, None)
            if data:
                # Return display_name (server nick if existed, otherwise username)
                # This ensures we restore to what they had before, not None
                return data["display_name"]
        return None
    
    def _get_original_display_name(
        self,
        guild_id: int,
        user_id: int
    ) -> Optional[str]:
        """Get the stored original display name for transformations."""
        if guild_id in self.original_nicknames:
            data = self.original_nicknames[guild_id].get(user_id)
            if data:
                return data["display_name"]
        return None
    
    async def _change_nickname(
        self, 
        member: discord.Member, 
        new_nickname: str
    ) -> bool:
        """Attempt to change a member's nickname."""
        try:
            await member.edit(nick=new_nickname)
            logger.info(
                f"Changed nickname for {member.name} to '{new_nickname}' "
                f"in {member.guild.name}"
            )
            return True
        except discord.Forbidden:
            logger.warning(
                f"Cannot change nickname for {member.name} in {member.guild.name}: "
                "Missing permissions or target has higher role"
            )
            return False
        except discord.HTTPException as e:
            logger.error(f"HTTP error changing nickname: {e}")
            return False
    
    async def _restore_nickname(self, member: discord.Member) -> bool:
        """Restore a member's original nickname."""
        original = self._pop_original_nickname(member.guild.id, member.id)
        
        if member.guild.id in self.original_nicknames or original is not None:
            try:
                await member.edit(nick=original)
                logger.info(
                    f"Restored nickname for {member.name} to '{original}' "
                    f"in {member.guild.name}"
                )
                return True
            except discord.Forbidden:
                logger.warning(
                    f"Cannot restore nickname for {member.name}: Missing permissions"
                )
                return False
            except discord.HTTPException as e:
                logger.error(f"HTTP error restoring nickname: {e}")
                return False
        return False
    
    def _user_joined_voice(
        self, 
        before: discord.VoiceState, 
        after: discord.VoiceState
    ) -> bool:
        """Check if this event represents a user joining a voice channel."""
        return before.channel is None and after.channel is not None
    
    def _user_left_voice(
        self, 
        before: discord.VoiceState, 
        after: discord.VoiceState
    ) -> bool:
        """Check if this event represents a user leaving voice entirely."""
        return before.channel is not None and after.channel is None
    
    def _user_changed_channel(
        self,
        before: discord.VoiceState,
        after: discord.VoiceState
    ) -> bool:
        """Check if user moved from one channel to another."""
        return (
            before.channel is not None 
            and after.channel is not None 
            and before.channel.id != after.channel.id
        )
    
    def _can_rename_member(self, member: discord.Member) -> bool:
        """Check if the bot can rename this member."""
        if member.id == self.bot.user.id:
            return False
        
        if member.id == member.guild.owner_id:
            return False
        
        bot_member = member.guild.me
        if bot_member.top_role <= member.top_role:
            return False
        
        return True
    
    async def _has_immunity(
        self, 
        member: discord.Member, 
        guild_settings: Guild
    ) -> bool:
        """Check if member has the immunity role."""
        if guild_settings.immunity_role_id is None:
            return False
        
        return any(
            role.id == guild_settings.immunity_role_id 
            for role in member.roles
        )
    
    @commands.Cog.listener()
    async def on_guild_join(self, guild: discord.Guild) -> None:
        """Create guild entry when bot joins a server."""
        await self._ensure_guild_exists(guild)
    
    @commands.Cog.listener()
    async def on_voice_state_update(
        self,
        member: discord.Member,
        before: discord.VoiceState,
        after: discord.VoiceState
    ) -> None:
        """Handle voice state changes."""
        
        # Get or create guild settings
        guild_settings = await self._ensure_guild_exists(member.guild)
        
        # Check if bot is enabled for this guild
        if not guild_settings.enabled:
            return
        
        # Check if leaving a custom channel (always restore, regardless of settings)
        if before.channel is not None:
            was_custom_channel = await self._is_custom_channel(member.guild.id, before.channel.id)
        else:
            was_custom_channel = False
        
        # User left voice entirely
        if self._user_left_voice(before, after):
            # Always restore if leaving custom channel, or if restore_on_leave is enabled
            if was_custom_channel or guild_settings.restore_on_leave:
                await self._restore_nickname(member)
            return
        
        # User joined a voice channel OR changed channel
        if self._user_joined_voice(before, after) or self._user_changed_channel(before, after):
            # If leaving a custom channel, restore first
            if was_custom_channel and self._user_changed_channel(before, after):
                await self._restore_nickname(member)
            
            # Check if new channel is allowed (whitelist logic)
            if not await self._is_channel_allowed(member.guild.id, after.channel.id):
                # If changing from an allowed channel to a non-allowed one, restore nickname
                if self._user_changed_channel(before, after):
                    if guild_settings.restore_on_leave and not was_custom_channel:
                        await self._restore_nickname(member)
                return
            
            if not self._can_rename_member(member):
                logger.debug(f"Cannot rename {member.name}: permission check failed")
                return
            
            # Check immunity
            if await self._has_immunity(member, guild_settings):
                logger.debug(f"Skipping {member.name}: has immunity role")
                return
            
            # Store original nickname only if first time joining (not when changing channels)
            if self._user_joined_voice(before, after):
                self._store_original_nickname(
                    member.guild.id, 
                    member.id, 
                    member.nick,
                    member.display_name
                )
            
            # Check for custom channel rules first
            custom_rules = await self._get_custom_channel_rules(
                member.guild.id, 
                after.channel.id
            )
            
            if custom_rules:
                # Apply transformation rules to the user's ORIGINAL display name
                original_name = self._get_original_display_name(member.guild.id, member.id)
                if not original_name:
                    original_name = member.display_name
                new_nickname = apply_rules(original_name, custom_rules)
            else:
                # Standard random nickname
                nicknames = await self._get_guild_nicknames(member.guild.id)
                new_nickname = random.choice(nicknames)
            
            await self._change_nickname(member, new_nickname)


async def setup(bot: commands.Bot) -> None:
    """Setup function for loading the cog."""
    await bot.add_cog(VoiceHandler(bot))
