"""
Main bot class for IdentityCrisis.
"""

import logging

import discord
from discord.ext import commands

from bot.cogs import EXTENSIONS
from shared import Config

logger = logging.getLogger(__name__)


class IdentityCrisisBot(commands.Bot):
    """
    The IdentityCrisis Discord Bot.
    Brings chaos to voice channels by randomizing nicknames.
    """
    
    def __init__(self, config: Config) -> None:
        intents = discord.Intents.default()
        intents.voice_states = True
        intents.guilds = True
        intents.members = True
        
        super().__init__(
            command_prefix=config.bot_prefix,
            intents=intents,
            help_command=commands.DefaultHelpCommand(),
        )
        
        self.config = config
    
    async def setup_hook(self) -> None:
        """Load all extensions/cogs."""
        logger.info("Loading extensions...")
        
        for extension in EXTENSIONS:
            try:
                await self.load_extension(extension)
                logger.info(f"Loaded extension: {extension}")
            except Exception as e:
                logger.error(f"Failed to load extension {extension}: {e}")
                raise
        
        logger.info("All extensions loaded!")
    
    async def on_ready(self) -> None:
        """Called when the bot is fully ready."""
        logger.info(f"Logged in as {self.user} (ID: {self.user.id})")
        logger.info(f"Connected to {len(self.guilds)} guild(s)")
        logger.info("=" * 50)
        logger.info("IdentityCrisis is ready to cause chaos!")
        logger.info("=" * 50)
        
        await self.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.watching,
                name="your identity crisis"
            )
        )
    
    async def on_guild_join(self, guild: discord.Guild) -> None:
        """Called when the bot joins a new guild."""
        logger.info(f"Joined new guild: {guild.name} (ID: {guild.id})")
        
        if guild.system_channel is not None:
            try:
                await guild.system_channel.send(
                    "🎭 **IdentityCrisis has arrived!**\n\n"
                    "Join a voice channel and watch your identity disappear. "
                    "Who will you become today? Nobody knows.\n\n"
                    "_Configure me at the web dashboard!_"
                )
            except discord.Forbidden:
                logger.warning(f"Cannot send welcome message in {guild.name}")
    
    async def on_command_error(
        self, 
        ctx: commands.Context, 
        error: commands.CommandError
    ) -> None:
        """Global error handler for commands."""
        if isinstance(error, commands.CommandNotFound):
            return
        
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("You don't have permission to do that.")
            return
        
        if isinstance(error, commands.BotMissingPermissions):
            await ctx.send(
                "I'm missing some permissions to do that. "
                "Make sure I have 'Manage Nicknames' permission!"
            )
            return
        
        logger.error(f"Unhandled command error: {error}", exc_info=error)
        await ctx.send("Something went wrong. The chaos has backfired.")
