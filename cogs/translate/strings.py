"""
User-facing strings and message templates for the Translation cog.

Contains all Discord embed templates, error messages, and help text.
Centralized here for easy maintenance and localization in the future.

No Discord imports allowed - strings only.
"""

import discord

# ============================================================================
# ERROR MESSAGES (user-facing)
# ============================================================================

MISSING_INPUTS = (
    "Please provide some text to translate, or reply to a message to translate it."
)
"""Shown when user doesn't provide text or reference message."""

MISSING_MESSAGE = "`Nothing to translate.`"
"""Shown when a message reference is broken or unresolvable."""

LANGUAGE_NOT_FOUND = "`That's not a recognized language. Try something like 'english', 'spanish', or 'es'.`"
"""Shown when user provides an invalid language code/name."""

TRANSLATION_FAILED = "`Translation failed. The service might be temporarily unavailable. Try again in a moment.`"
"""Shown when the translation API returns an error."""

TRANSLATION_TIMEOUT = "`Translation took too long to process. Try again in a moment.`"
"""Shown when translation request exceeds timeout."""

API_RATE_LIMITED = (
    "`Translation service is busy right now. Please try again in a few seconds.`"
)
"""Shown when hitting translation service rate limits."""

NO_LANGUAGE_PREFERENCE = (
    "You haven't set a preferred language yet. Use `/translate to` to translate to a specific language, "
    "or use `/setmylanguage` to set your preference."
)
"""Shown when user tries auto-translate without a preference set."""

# ============================================================================
# SUCCESS MESSAGES
# ============================================================================

LANGUAGE_SET = "✅ Your preferred language is now **{language}**."
"""Shown when user successfully sets their language preference."""

LANGUAGE_SET_FOOTER = (
    "When you translate a message, it will be translated to {language}."
)
"""Footer text for language preference confirmation."""

# ============================================================================
# EMBED BUILDERS (return discord.Embed objects)
# ============================================================================


def build_translation_embed(
    translated_text: str,
    source_language: str,
    target_language: str,
    original_author: discord.User = None,
    color: discord.Color = None,
) -> discord.Embed:
    """
    Build a rich embed for displaying a translation.

    Args:
        translated_text: The translated text (will be truncated to 3990 chars for embed limit)
        source_language: Source language name (e.g., "spanish")
        target_language: Target language name (e.g., "english")
        original_author: Optional User object to display in author field
        color: Optional embed color. If None, defaults to Discord's brand color.

    Returns:
        Formatted discord.Embed with translation result.

    Examples:
        >>> embed = build_translation_embed(
        ...     "Hello world",
        ...     "spanish",
        ...     "english",
        ...     original_author=ctx.author
        ... )
        >>> await ctx.send(embed=embed, ephemeral=True)
    """
    if color is None:
        color = discord.Color.blurple()

    # Truncate to embed limits
    display_text = translated_text[:3990] if translated_text else "*[empty]*"

    embed = discord.Embed(description=display_text, color=color)

    # Set author if original message author is provided
    if original_author:
        embed.set_author(
            name=original_author.display_name,
            icon_url=original_author.display_avatar.url,
        )

    # Footer shows language direction
    source_title = source_language.title()
    target_title = target_language.title()
    embed.set_footer(text=f"{source_title} → {target_title}")

    return embed


def build_error_embed(
    message: str,
    title: str = "Translation Error",
    color: discord.Color = None,
) -> discord.Embed:
    """
    Build an error embed for failures.

    Args:
        message: Error message to display
        title: Embed title. Defaults to "Translation Error".
        color: Embed color. Defaults to red.

    Returns:
        Formatted error discord.Embed.
    """
    if color is None:
        color = discord.Color.red()

    embed = discord.Embed(title=title, description=message, color=color)
    return embed


def build_success_embed(
    message: str,
    title: str = "Success",
    color: discord.Color = None,
) -> discord.Embed:
    """
    Build a success embed.

    Args:
        message: Success message to display
        title: Embed title. Defaults to "Success".
        color: Embed color. Defaults to green.

    Returns:
        Formatted success discord.Embed.
    """
    if color is None:
        color = discord.Color.green()

    embed = discord.Embed(title=title, description=message, color=color)
    return embed


# ============================================================================
# HELP TEXT
# ============================================================================

TRANSLATE_COMMAND_HELP = (
    "Translate text to your preferred language.\n\n"
    "You can provide text directly or reply to a message to translate it.\n"
    "First, set your preferred language with `/setmylanguage`."
)

TRANSLATE_TO_COMMAND_HELP = (
    "Translate text to a specific language.\n\n"
    "Provide the target language and the text to translate, "
    "or reply to a message."
)

SETMYLANGUAGE_COMMAND_HELP = (
    "Set your preferred language for translations.\n\n"
    "Use this once, then `/translate` will automatically translate to your preferred language."
)
