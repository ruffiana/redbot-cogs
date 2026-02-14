"""Example cog for Redbot."""

from .cog import ExampleCog


async def setup(bot):
    """Setup function for the cog."""
    await bot.add_cog(ExampleCog(bot))
