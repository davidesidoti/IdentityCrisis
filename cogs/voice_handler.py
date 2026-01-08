"""
Voice Handler Cog for IdentityCrisis.
Listens to voice state updates and renames users on join.
"""

import random
import logging
from typing import Optional

import discord
from discord.ext import commands

from data import DEFAULT_NICKNAMES

logger = logging.getLogger(__name__)


class VoiceHandler(commands.Cog):
    """Handles voice channel events and nickname chaos."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.nicknames = DEFAULT_NICKNAMES.copy()
        # Store original nicknames: {guild_id: {user_id: original_nick}}
        self.original_nicknames: dict[int, dict[int, Optional[str]]] = {}
        # Config flag (will be loaded from bot config later)
        self.restore_on_leave = True

    def _get_random_nickname(self) -> str:
        """Get a random nickname from the pool."""
        return random.choice(self.nicknames)

    def _store_original_nickname(
        self,
        guild_id: int,
        user_id: int,
        nickname: Optional[str]
    ) -> None:
        """Store the original nickname before changing it."""
        if guild_id not in self.original_nicknames:
            self.original_nicknames[guild_id] = {}

        # Only store if we don't already have one (first join)
        if user_id not in self.original_nicknames[guild_id]:
            self.original_nicknames[guild_id][user_id] = nickname

    def _pop_original_nickname(
        self,
        guild_id: int,
        user_id: int
    ) -> Optional[str]:
        """Retrieve and remove the stored original nickname."""
        if guild_id in self.original_nicknames:
            return self.original_nicknames[guild_id].pop(user_id, None)
        return None

    async def _change_nickname(
        self,
        member: discord.Member,
        new_nickname: str
    ) -> bool:
        """
        Attempt to change a member's nickname.
        Returns True if successful, False otherwise.
        """
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
        """
        Restore a member's original nickname.
        Returns True if successful, False otherwise.
        """
        original = self._pop_original_nickname(member.guild.id, member.id)

        # original can be None (meaning they had no nickname)
        # We need to check if we actually had a stored value
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
        # User was not in voice before, now they are
        return before.channel is None and after.channel is not None

    def _user_left_voice(
        self,
        before: discord.VoiceState,
        after: discord.VoiceState
    ) -> bool:
        """Check if this event represents a user leaving voice entirely."""
        # User was in voice before, now they're not
        return before.channel is not None and after.channel is None

    def _can_rename_member(self, member: discord.Member) -> bool:
        """Check if the bot can rename this member."""
        # Can't rename the bot itself
        if member.id == self.bot.user.id:
            return False

        # Can't rename the server owner
        if member.id == member.guild.owner_id:
            return False

        # Check if bot's highest role is above member's highest role
        bot_member = member.guild.me
        if bot_member.top_role <= member.top_role:
            return False

        return True

    @commands.Cog.listener()
    async def on_voice_state_update(
        self,
        member: discord.Member,
        before: discord.VoiceState,
        after: discord.VoiceState
    ) -> None:
        """Handle voice state changes - the main chaos entry point."""

        # User joined a voice channel
        if self._user_joined_voice(before, after):
            if not self._can_rename_member(member):
                logger.debug(
                    f"Cannot rename {member.name}: permission check failed")
                return

            # Store original nickname
            self._store_original_nickname(
                member.guild.id,
                member.id,
                member.nick
            )

            # Assign chaos
            new_nickname = self._get_random_nickname()
            await self._change_nickname(member, new_nickname)

        # User left voice entirely
        elif self._user_left_voice(before, after):
            if self.restore_on_leave:
                await self._restore_nickname(member)


async def setup(bot: commands.Bot) -> None:
    """Setup function for loading the cog."""
    await bot.add_cog(VoiceHandler(bot))
