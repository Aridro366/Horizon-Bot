import discord
from discord.ext import commands
import json
import asyncio
from datetime import datetime, timedelta
import time
from dotenv import load_dotenv
import os


# ---- Load .env ----
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    raise ValueError("❌ BOT_TOKEN is missing in .env")


# ---- Load config.json (non-secret settings) ----
with open("config.json") as f:
    config = json.load(f)


intents = discord.Intents.default()
intents.members = True
intents.message_content = True


bot = commands.Bot(
    command_prefix=".",
    intents=intents,
    help_command=None
)


@bot.event
async def setup_hook():
    for ext in [
        "cogs.moderation",
        "cogs.logging",
        "cogs.welcome",
        "cogs.afk",
        "cogs.cmd",
        "cogs.Utility",
        "cogs.projects",
        "cogs.BugPanel",
        "cogs.HelpPanel"
    ]:
        await bot.load_extension(ext)

    await bot.tree.sync(guild=discord.Object(id=config["guild_id"]))
    print("Extensions loaded & commands synced")


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} ({bot.user.id})")


def main():
    bot.run(BOT_TOKEN)


if __name__ == "__main__":
    main()
