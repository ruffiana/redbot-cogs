"""Example cog demonstrating basic Redbot cog structure."""

import discord
from redbot.core import commands


class ExampleCog(commands.Cog):
    """
    Example cog for Redbot.
    
    This is a template cog showing how to create basic commands
    and listeners in Redbot.
    """
    
    def __init__(self, bot):
        """Initialize the cog.
        
        Args:
            bot: The Redbot instance.
        """
        self.bot = bot
    
    @commands.command()
    async def hello(self, ctx):
        """Greet the user who invoked the command."""
        await ctx.send(f"Hello {ctx.author.mention}! 👋")
    
    @commands.command()
    async def echo(self, ctx, *, message: str):
        """Echo back what the user says.
        
        Args:
            message: The message to echo.
        """
        await ctx.send(f"{ctx.author.mention} says: {message}")
    
    @commands.Cog.listener()
    async def on_message(self, message):
        """Listen to all messages in the server.
        
        Args:
            message: The Discord message object.
        """
        # Don't respond to bot messages to avoid loops
        if message.author == self.bot.user:
            return
        
        # Example: Log messages with more than 100 characters
        if len(message.content) > 100:
            print(f"Long message from {message.author}: {len(message.content)} chars")
    
    @commands.Cog.listener()
    async def on_member_join(self, member):
        """Welcome new members when they join.
        
        Args:
            member: The member who joined.
        """
        print(f"{member} joined the server!")
        # You could send a welcome message to a specific channel here
