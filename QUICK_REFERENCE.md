# Redbot Cog Development Quick Reference

## Command Cheat Sheet

### Activate Virtual Environment (PowerShell)
```powershell
.\.venv\Scripts\Activate.ps1
```

If you get an execution policy error, run this once:
```powershell
powershell -NoProfile -ExecutionPolicy Bypass -Command "Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser"
```

### Using the Virtual Environment Directly
```powershell
# Run Python
.\.venv\Scripts\python

# Install packages
.\.venv\Scripts\python -m pip install package_name

# Run a script
.\.venv\Scripts\python script.py
```

### Quick Setup Reminder
```powershell
# Make sure you're in the project root directory
.\.venv\Scripts\python -m pip install -r requirements.txt
```

## Creating a New Cog

1. **Create the cog directory**:
   ```powershell
   mkdir cogs\my_new_cog
   ```

2. **Create `__init__.py`**:
   ```python
   from .cog import MyNewCog

   async def setup(bot):
       await bot.add_cog(MyNewCog(bot))
   ```

3. **Create `cog.py`**:
   ```python
   import discord
   from redbot.core import commands

   class MyNewCog(commands.Cog):
       """Description of your cog."""

       def __init__(self, bot):
           self.bot = bot

       @commands.command()
       async def mycommand(self, ctx):
           """What your command does."""
           await ctx.send("Response!")
   ```

## Common Redbot Decorators

### Commands
```python
@commands.command()                    # Basic command
@commands.command(aliases=["alias1"])  # With aliases
@commands.admin()                      # Admin only
@commands.mod()                        # Moderator only
@commands.has_permissions(ban_members=True)
```

### Listeners
```python
@commands.Cog.listener()
async def on_message(self, message):   # Any message
async def on_member_join(self, member): # Member joins
async def on_message_delete(self, message): # Message deleted
async def on_reaction_add(self, reaction, user): # Reaction added
```

## Testing Your Cog

Create a test script:
```python
import asyncio
from redbot.core import commands
from cogs.example_cog import ExampleCog

# Check imports and basic structure
cog = ExampleCog(None)
print("✓ Cog imports successfully")
```

Run with: `.\.venv\Scripts\python test_script.py`

## Dependencies Management

### Update all packages
```powershell
.\.venv\Scripts\python -m pip install --upgrade -r requirements.txt
```

### Add a new dependency
```powershell
.\.venv\Scripts\python -m pip install new_package
.\.venv\Scripts\python -m pip freeze > requirements.txt
```

### View installed packages
```powershell
.\.venv\Scripts\python -m pip list
```

## Debugging Tips

### Enable debug logging
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Common errors
- **ImportError**: Check `.venv` is activated and package is installed
- **AttributeError on ctx**: Verify you're inheriting from `commands.Cog`
- **Command not found**: Check `setup()` function exists and is called

## IDE Setup

### VS Code
1. Open command palette: `Ctrl+Shift+P`
2. Search for "Python: Select Interpreter"
3. Choose `.\.venv\Scripts\python`

### PyCharm
1. Go to Settings → Project → Python Interpreter
2. Click gear icon → Add
3. Select "Existing Environment"
4. Navigate to `.\.venv\Scripts\python.exe`

## Resources

- **Redbot Documentation**: https://docs.red-discordbot.com/
- **Discord.py Guide**: https://discordpy.readthedocs.io/
- **Example Cogs**: https://github.com/Cog-Creators/Red-DiscordBot/tree/main/cogs

## File Structure
```
redbot_cogs/
├── .venv/                     # Virtual environment
├── cogs/
│   ├── example_cog/          # Example cog (you can delete this)
│   │   ├── __init__.py
│   │   └── cog.py
│   ├── my_first_cog/         # Your custom cogs
│   │   ├── __init__.py
│   │   └── cog.py
│   └── another_cog/
│       ├── __init__.py
│       └── cog.py
├── .gitignore
├── activate_venv.bat          # Quick activation script
├── requirements.txt
└── README.md
```
