import discord
from discord.ext import commands
import json

with open("config.json") as f:
    config = json.load(f)

class Welcome(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @property
    def channel(self):
        return self.bot.get_channel(config["welcome_channel_id"])

    @commands.Cog.listener()
    async def on_member_join(self, member):

        divider = "━━━━━━━━━━━━━━━━━━🌅━━━━━━━━━━━━━━━━━━"

        message = (
            f"{divider}\n"
            f"🌟 **Welcome to _Horizon Devs_ — {member.mention}!**\n\n"
            "We’re really glad to have you here 🤝\n"
            "This community is for **motivated, ambitious developers** who believe in\n"
            "learning together, building meaningful projects, and supporting one another.\n\n"
            "💬 Join conversations, share ideas, ask questions, or showcase your progress —\n"
            "everyone here grows together.\n\n"
            "🌱 Stay kind • Stay curious • Keep improving\n"
            "🌠 **Dream big. Build consistently. Rise together.** 🚀\n\n"
            "Once again — **welcome to the journey!**\n"
            f"{divider}"
        )

        await self.channel.send(message)

async def setup(bot):
    await bot.add_cog(Welcome(bot))
