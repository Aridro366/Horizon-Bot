import discord
from discord.ext import commands, tasks
import os
import asyncio
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_ID = int(os.getenv("GUILD_ID", 0))

# ---------- INTENTS ----------

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

# ---------- BOT ----------

class HorizonBot(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix=".",
            intents=intents,
            help_command=None
        )

        # Status messages
        self.status_messages = [
            discord.Game("Managing Suggestions"),
            discord.Game("Helping Developers"),
            discord.Game("Use /help"),
            discord.Game("Built for Dev Communities"),
            discord.Game("Horizon 2.0")
        ]

    async def setup_hook(self):
        # Load cogs
        await self.load_extension("cogs.suggestions")
        await self.load_extension("cogs.utility")
        await self.load_extension("cogs.welcome")
        await self.load_extension("cogs.moderation")
        await self.load_extension("cogs.qa")
        await self.load_extension("cogs.help_panel")

        # Start rotating status AFTER setup
        self.rotate_status.start()

        # -------- SLASH SYNC --------
        if GUILD_ID:
            guild = discord.Object(id=GUILD_ID)
            self.tree.copy_global_to(guild=guild)
            await self.tree.sync(guild=guild)
        else:
            await self.tree.sync()

    # ---------- ROTATING STATUS ----------

    @tasks.loop(seconds=10)
    async def rotate_status(self):
        activity = self.status_messages.pop(0)
        self.status_messages.append(activity)

        await self.change_presence(
            status=discord.Status.online,
            activity=activity
        )

    @rotate_status.before_loop
    async def before_rotate_status(self):
        # Ensure bot is fully ready
        await self.wait_until_ready()

# ---------- RUN ----------

async def main():
    bot = HorizonBot()
    await bot.start(TOKEN)

asyncio.run(main())
