# Redbot Cogs Development Environment

This directory contains custom cogs for the Redbot Discord bot framework.

## Setup Instructions

### Prerequisites
- Python 3.9 or higher
- Windows (or adapt commands for your OS)

### Initial Setup (One-time)

1. **Create the virtual environment** (already done):
   ```powershell
   python -m venv .venv
   ```

2. **Activate the virtual environment**:
   ```powershell
   .\.venv\Scripts\python -m pip install --upgrade pip
   .\.venv\Scripts\pip install -r requirements.txt
   ```

### Daily Usage

To use the environment in VS Code or any terminal:
```powershell
.\.venv\Scripts\python   # Run Python from the virtual environment
.\.venv\Scripts\pip      # Install packages
```

## Project Structure

```
redbot_cogs/
├── .venv/               # Virtual environment (ignored in git)
├── cogs/                # Your custom cogs
│   ├── example_cog/
│   │   ├── __init__.py
│   │   └── cog.py
│   └── ...
├── requirements.txt     # Python dependencies
└── README.md           # This file
```

## Creating a New Cog

### Basic Cog Template

Create a new folder in `cogs/` with the following structure:

```
cogs/my_cog/
├── __init__.py
└── cog.py
```

**__init__.py** (minimal):
```python
from .cog import MyCog

async def setup(bot):
    await bot.add_cog(MyCog(bot))
```

**cog.py** (basic example):
```python
import discord
from redbot.core import commands

class MyCog(commands.Cog):
    """My custom cog for Redbot."""

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def hello(self, ctx):
        """Say hello!"""
        await ctx.send(f"Hello {ctx.author.mention}!")

    @commands.Cog.listener()
    async def on_message(self, message):
        """Listen to all messages."""
        if message.author == self.bot.user:
            return
        # Your logic here
```

## Installing Red-DiscordBot Locally

To use Redbot utilities locally for testing:

```powershell
.\.venv\Scripts\python -m pip install red-discordbot[voice]
```

## Useful Resources

- **Redbot Documentation**: https://docs.discord.red/en/stable/
- **Discord.py Documentation**: https://discordpy.readthedocs.io/
- **Redbot Repo**: https://github.com/Cog-Creators/Red-DiscordBot

## Tips

- Always activate `.venv` in your terminal before developing
- Use `redbot --help` to test your bot setup
- Test cogs locally before deploying
- Use type hints and docstrings for better code quality

## Troubleshooting

**Module not found errors?**
- Ensure `.venv` is activated: `.\.venv\Scripts\python`
- Reinstall dependencies: `.\.venv\Scripts\pip install -r requirements.txt`

**Bot not loading cogs?**
- Check cog folder structure and `__init__.py` files
- Verify the `setup()` function in `__init__.py`
- Check bot logs for detailed error messages
