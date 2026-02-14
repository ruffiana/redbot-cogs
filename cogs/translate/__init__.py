"""
Translation cog for Red Discord bot.

Translates messages using Google Translate with user preferences and caching.

Setup:
    [p]load translate

Usage:
    [p]setmylanguage <language> - Set your preferred language
    [p]translate [text] - Translate to your preferred language
    [p]translate to <language> [text] - Translate to a specific language
    /translate <language> <text> - Slash command translation

Features:
    - Ephemeral responses (only you see translations)
    - User language preferences
    - Translation caching for performance
    - Context menu quick translate
    - Language autocomplete
"""

from redbot.core import commands
from redbot.core.utils import get_end_user_data_statement

from .main import Translation

__red_end_user_data_statement__ = get_end_user_data_statement(__file__)


async def setup(bot):
    """
    Setup hook called when the cog is loaded.

    Args:
        bot: The Red Discord bot instance
    """
    await bot.add_cog(Translation(bot))
