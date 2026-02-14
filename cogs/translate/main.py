"""
Main Translation cog for Discord bot.

This module contains the Discord commands and event listeners for the Translation cog.
All translation logic is delegated to the translator.py module.
All error messages come from strings.py.

Provides:
- Text and slash commands for manual translation
- Context menu commands for quick translation
- User preference system (preferred language)
- Ephemeral response system (translations only visible to requester)
"""

import logging
import re
from typing import Optional, Union

import discord
from redbot.core import commands, app_commands, Config
from redbot.core.bot import Red

from .translator import Translator, TranslationAPIError, LanguageNotFoundError
from .cache import TranslationCache
from . import strings

logger = logging.getLogger(__name__)

# Matches Discord custom emojis: <:name:id> or <a:name:id>
CUSTOM_EMOJI_PATTERN = re.compile(r"<a?:\w+:\d+>")


class Translation(commands.Cog):
    """Translate messages using Google Translate. Supports slash commands and context menus."""

    def __init__(self, bot: Red):
        """
        Initialize the Translation cog.

        Args:
            bot: The Red Discord bot instance
        """
        self.bot = bot
        self.logger = logging.getLogger("red.unicornia-cogs.translate")

        # Initialize translator and cache
        self.translator = Translator(timeout=10)
        self.cache = TranslationCache(max_size=5000, default_ttl=604800)  # 7 days

        # Initialize config
        self.config = Config.get_conf(
            self, identifier=1234567890, force_registration=True
        )
        self.config.register_user(preferred_language="english")

        # Add context menu command
        self.context_menu = app_commands.ContextMenu(
            name="Translate", callback=self.translate_context_menu
        )
        self.bot.tree.add_command(self.context_menu)

    async def cog_unload(self):
        """
        Clean up when cog is unloaded.

        Removes context menu and clears cache.
        """
        self.bot.tree.remove_command(
            self.context_menu.name, type=self.context_menu.type
        )
        await self.cache.clear()
        self.logger.info("Translation cog unloaded")

    async def red_delete_data_for_user(self, requester: str, user_id: int):
        """
        Delete user data when requested (GDPR compliance).

        Args:
            requester: The request source (who is requesting deletion)
            user_id: The user ID to delete data for
        """
        await self.config.user_from_id(user_id).clear()

    # ========================================================================
    # AUTOCOMPLETE CALLBACKS (must be before decorators that reference them)
    # ========================================================================

    @staticmethod
    async def _autocomplete_language(
        interaction: discord.Interaction, current: str = ""
    ) -> list[app_commands.Choice[str]]:
        """
        Autocomplete for language selection in slash commands.

        Returns available languages matching the user's input.

        Args:
            interaction: The interaction context
            current: Current text the user has typed

        Returns:
            List of language choices (max 25)
        """
        available_langs = list(Translator.LANGUAGE_CODES.values())
        available_langs.sort()
        current = current.strip().lower()

        if not current:
            # Show first 25 languages
            return [
                app_commands.Choice(name=lang.title(), value=lang)
                for lang in available_langs[:25]
            ]

        # Prioritize languages that start with the current input
        choices = []
        remaining = available_langs.copy()

        # Starting matches first
        for lang in available_langs:
            if lang.lower().startswith(current):
                choices.append(app_commands.Choice(name=lang.title(), value=lang))
                remaining.remove(lang)

        # Then partial matches
        for lang in remaining:
            if current in lang.lower():
                choices.append(app_commands.Choice(name=lang.title(), value=lang))

        return choices[:25]

    # ========================================================================
    # HELPER METHODS
    # ========================================================================

    @staticmethod
    def _clean_text(text: str) -> str:
        """
        Clean text for translation.

        Removes Discord custom emojis but preserves regular text and Unicode emojis.

        Args:
            text: Raw text possibly containing Discord markdown

        Returns:
            Cleaned text ready for translation
        """
        # Remove Discord custom emojis
        cleaned = CUSTOM_EMOJI_PATTERN.sub("", text)
        return cleaned.strip()

    async def _respond_ephemeral(
        self,
        ctx: Union[commands.Context, discord.Interaction],
        embed: discord.Embed,
        message: Optional[discord.Message] = None,
    ) -> None:
        """
        Send a response in the appropriate format for the context.

        For slash commands: Always ephemeral
        For context menus: Always ephemeral
        For text commands: Reply to message if available, otherwise send ephemeral

        Args:
            ctx: Command context (User or Interaction)
            embed: Embed to send
            message: Optional original message to reply to
        """
        if isinstance(ctx, discord.Interaction):
            # Slash command or context menu - always ephemeral
            await ctx.response.send_message(embed=embed, ephemeral=True)
        elif isinstance(ctx, commands.Context):
            # Text command
            if message:
                # Reply to the original message
                await message.reply(embed=embed, mention_author=False)
            else:
                # Send as ephemeral if possible, otherwise regular message
                try:
                    await ctx.send(embed=embed, ephemeral=True)
                except (discord.Forbidden, discord.NotFound):
                    # Fallback to regular message if ephemeral fails
                    await ctx.send(embed=embed)

    # ========================================================================
    # TRANSLATION LOGIC
    # ========================================================================

    async def _do_translate(
        self,
        text: str,
        target_language: str,
        source_language: str = "auto",
    ) -> Optional[str]:
        """
        Translate text, checking cache first.

        Args:
            text: Text to translate
            target_language: Target language (will be normalized)
            source_language: Source language code or "auto" for detection

        Returns:
            Translated text, or None if translation failed

        Raises:
            LanguageNotFoundError: If target language is invalid
            TranslationAPIError: If translation API fails
        """
        if not text or not text.strip():
            return None

        # Clean the text
        text = self._clean_text(text)
        if not text:
            return None

        # Check cache first
        cached = await self.cache.get(text, target_language)
        if cached:
            self.logger.debug(f"Cache hit: {text[:50]}... → {target_language}")
            return cached.translated_text

        # Not in cache - translate via API
        translated = await self.translator.translate(
            text, target_language, source_language
        )

        # Cache the result
        await self.cache.set(text, target_language, translated, source_language)

        return translated

    # ========================================================================
    # COMMANDS - PREFIX TEXT COMMANDS
    # ========================================================================

    @commands.bot_has_permissions(embed_links=True)
    @commands.group(name="translate", invoke_without_command=True)
    async def translate_group(self, ctx: commands.Context, *, text: str = ""):
        """
        Translate text to your preferred language.

        You can provide text directly, or reply to a message to translate it.
        First, set your preferred language with [p]setmylanguage.

        Example:
            [p]translate Hello, how are you?
            (replies to a message): [p]translate
        """
        try:
            # Get user's preferred language
            preferred_lang = await self.config.user(ctx.author).preferred_language()
            if not preferred_lang:
                await ctx.send(strings.NO_LANGUAGE_PREFERENCE, ephemeral=True)
                return

            # Determine what to translate
            if text:
                # User provided text directly
                source_message = None
                content = text
            elif ctx.message.reference:
                # User replied to a message
                try:
                    source_message = await ctx.channel.fetch_message(
                        ctx.message.reference.message_id
                    )
                    content = source_message.content
                    # Also include embed descriptions if present
                    for embed in source_message.embeds:
                        if embed.description:
                            content += "\n" + embed.description
                except (discord.NotFound, discord.Forbidden):
                    await ctx.send(strings.MISSING_MESSAGE, ephemeral=True)
                    return
            else:
                await ctx.send(strings.MISSING_INPUTS, ephemeral=True)
                return

            # Translate
            try:
                translated = await self._do_translate(content, preferred_lang)
                if not translated:
                    await ctx.send(strings.MISSING_MESSAGE, ephemeral=True)
                    return

                # Build and send embed
                embed = strings.build_translation_embed(
                    translated,
                    "original",  # Would need detected language from translator
                    preferred_lang,
                    original_author=source_message.author if source_message else None,
                    color=await self.bot.get_embed_color(ctx.channel),
                )
                await self._respond_ephemeral(ctx, embed, source_message)

            except LanguageNotFoundError:
                await ctx.send(strings.LANGUAGE_NOT_FOUND, ephemeral=True)
            except TranslationAPIError as e:
                self.logger.error(f"Translation error: {e}")
                await ctx.send(strings.TRANSLATION_FAILED, ephemeral=True)

        except Exception as e:
            self.logger.exception(f"Unexpected error in translate_group: {e}")
            await ctx.send(strings.TRANSLATION_FAILED, ephemeral=True)

    @commands.bot_has_permissions(embed_links=True)
    @translate_group.command(name="to")
    async def translate_to(
        self, ctx: commands.Context, language: str, *, text: str = ""
    ):
        """
        Translate text to a specific language.

        You can provide text directly, or reply to a message to translate it.

        Example:
            [p]translate to spanish Hello world
            (replies to a message): [p]translate to french
        """
        try:
            # Normalize language
            target_lang = self.translator.normalize_language(language)
            if not target_lang:
                await ctx.send(strings.LANGUAGE_NOT_FOUND, ephemeral=True)
                return

            # Determine what to translate
            if text:
                source_message = None
                content = text
            elif ctx.message.reference:
                try:
                    source_message = await ctx.channel.fetch_message(
                        ctx.message.reference.message_id
                    )
                    content = source_message.content
                    for embed in source_message.embeds:
                        if embed.description:
                            content += "\n" + embed.description
                except (discord.NotFound, discord.Forbidden):
                    await ctx.send(strings.MISSING_MESSAGE, ephemeral=True)
                    return
            else:
                await ctx.send(strings.MISSING_INPUTS, ephemeral=True)
                return

            # Translate
            try:
                translated = await self._do_translate(content, target_lang)
                if not translated:
                    await ctx.send(strings.MISSING_MESSAGE, ephemeral=True)
                    return

                embed = strings.build_translation_embed(
                    translated,
                    "original",
                    target_lang,
                    original_author=source_message.author if source_message else None,
                    color=await self.bot.get_embed_color(ctx.channel),
                )
                await self._respond_ephemeral(ctx, embed, source_message)

            except TranslationAPIError as e:
                self.logger.error(f"Translation error: {e}")
                await ctx.send(strings.TRANSLATION_FAILED, ephemeral=True)

        except Exception as e:
            self.logger.exception(f"Unexpected error in translate_to: {e}")
            await ctx.send(strings.TRANSLATION_FAILED, ephemeral=True)

    # ========================================================================
    # COMMANDS - HYBRID COMMANDS (text + slash)
    # ========================================================================

    @commands.hybrid_command(name="setmylanguage")
    @app_commands.autocomplete(language=_autocomplete_language)
    async def set_language(self, ctx: commands.Context, *, language: str):
        """
        Set your preferred language for translations.

        After setting this, [p]translate will automatically translate to your preferred language.

        Example:
            [p]setmylanguage spanish
            [p]setmylanguage english
        """
        # Normalize the language
        target_lang = self.translator.normalize_language(language)
        if not target_lang:
            await ctx.send(strings.LANGUAGE_NOT_FOUND, ephemeral=True)
            return

        # Save preference
        await self.config.user(ctx.author).preferred_language.set(target_lang)

        # Respond with success message in target language
        try:
            success_msg = strings.LANGUAGE_SET.format(language=target_lang.title())
            translated = await self._do_translate(success_msg, target_lang)

            embed = strings.build_success_embed(translated or success_msg)
            await ctx.send(embed=embed, ephemeral=True)
        except Exception as e:
            self.logger.error(f"Error translating success message: {e}")
            embed = strings.build_success_embed(
                strings.LANGUAGE_SET.format(language=target_lang.title())
            )
            await ctx.send(embed=embed, ephemeral=True)

    # ========================================================================
    # COMMANDS - SLASH COMMANDS
    # ========================================================================

    @app_commands.command(name="translate")
    @app_commands.autocomplete(to=_autocomplete_language)
    async def translate_slash(
        self, interaction: discord.Interaction, to: str, text: str
    ):
        """
        Translate text to a specific language.

        Args:
            to: Target language (e.g., 'english', 'spanish', 'es', 'fr')
            text: Text to translate
        """
        await interaction.response.defer(ephemeral=True)

        try:
            # Normalize language
            target_lang = self.translator.normalize_language(to)
            if not target_lang:
                embed = strings.build_error_embed(strings.LANGUAGE_NOT_FOUND)
                await interaction.followup.send(embed=embed, ephemeral=True)
                return

            # Translate
            try:
                translated = await self._do_translate(text, target_lang)
                if not translated:
                    await interaction.followup.send(
                        strings.MISSING_MESSAGE, ephemeral=True
                    )
                    return

                embed = strings.build_translation_embed(
                    translated,
                    "original",
                    target_lang,
                    original_author=interaction.user,
                    color=await self.bot.get_embed_color(interaction.guild),
                )
                await interaction.followup.send(embed=embed, ephemeral=True)

            except TranslationAPIError as e:
                self.logger.error(f"Translation error: {e}")
                embed = strings.build_error_embed(strings.TRANSLATION_FAILED)
                await interaction.followup.send(embed=embed, ephemeral=True)

        except Exception as e:
            self.logger.exception(f"Unexpected error in translate_slash: {e}")
            embed = strings.build_error_embed(strings.TRANSLATION_FAILED)
            await interaction.followup.send(embed=embed, ephemeral=True)

    # ========================================================================
    # CONTEXT MENU COMMANDS
    # ========================================================================

    async def translate_context_menu(
        self, interaction: discord.Interaction, message: discord.Message
    ):
        """
        Translate a message using the context menu.

        Right-click a message → Apps → Translate
        """
        await interaction.response.defer(ephemeral=True)

        try:
            # Get user's preferred language
            preferred_lang = await self.config.user(
                interaction.user
            ).preferred_language()
            if not preferred_lang:
                embed = strings.build_error_embed(strings.NO_LANGUAGE_PREFERENCE)
                await interaction.followup.send(embed=embed, ephemeral=True)
                return

            # Get message content
            content = message.content
            for embed in message.embeds:
                if embed.description:
                    content += "\n" + embed.description

            # Translate
            try:
                translated = await self._do_translate(content, preferred_lang)
                if not translated:
                    await interaction.followup.send(
                        strings.MISSING_MESSAGE, ephemeral=True
                    )
                    return

                embed = strings.build_translation_embed(
                    translated,
                    "original",
                    preferred_lang,
                    original_author=message.author,
                    color=await self.bot.get_embed_color(interaction.channel),
                )
                await interaction.followup.send(embed=embed, ephemeral=True)

            except TranslationAPIError as e:
                self.logger.error(f"Translation error: {e}")
                embed = strings.build_error_embed(strings.TRANSLATION_FAILED)
                await interaction.followup.send(embed=embed, ephemeral=True)

        except Exception as e:
            self.logger.exception(f"Unexpected error in context menu: {e}")
            embed = strings.build_error_embed(strings.TRANSLATION_FAILED)
            await interaction.followup.send(embed=embed, ephemeral=True)
