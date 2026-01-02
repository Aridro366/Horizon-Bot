import discord
from discord.ext import commands
import time
import random
from datetime import datetime


SUGGESTIONS_CHANNEL_NAME = "💡・suggestions"
VC_ROLE_NAME = "🎧 In Voice"


class Utility(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.start_time = time.time()

    # ===============================
    # 5) PING / UPTIME / BOT INFO
    # ===============================
    @commands.command()
    async def ping(self, ctx):
        latency = round(self.bot.latency * 1000)
        await ctx.reply(f"🏓 Pong! `{latency}ms`")

    @commands.command()
    async def uptime(self, ctx):
        seconds = int(time.time() - self.start_time)
        mins, secs = divmod(seconds, 60)
        hrs, mins = divmod(mins, 60)

        await ctx.reply(f"⏳ Uptime: **{hrs}h {mins}m {secs}s**")

    @commands.command()
    async def botinfo(self, ctx):
        guilds = len(self.bot.guilds)
        users = sum(g.member_count for g in self.bot.guilds)

        await ctx.reply(
            f"🤖 **Bot Info**\n"
            f"• Servers: **{guilds}**\n"
            f"• Users: **{users}**\n"
            f"• Prefix: `.`"
        )

# =========================
    #  VC ROLE HELPERS
    # =========================
    async def get_vc_role(self, guild: discord.Guild):
        """Get or create the VC role."""
        role = discord.utils.get(guild.roles, name=VC_ROLE_NAME)
        if not role:
            role = await guild.create_role(
                name=VC_ROLE_NAME,
                reason="Auto-created VC activity role"
            )
        return role


    # =========================
    #  VC ROLE EVENT HANDLER
    # =========================
    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        # ignore bots
        if member.bot:
            return

        role = await self.get_vc_role(member.guild)

        joined_vc = after.channel is not None
        left_vc = after.channel is None

        # 🎧 Joined a VC → add role
        if joined_vc and role not in member.roles:
            try:
                await member.add_roles(
                    role,
                    reason="User joined a voice channel"
                )
            except discord.Forbidden:
                pass

        # 🚪 Left VC → remove role
        if left_vc and role in member.roles:
            try:
                await member.remove_roles(
                    role,
                    reason="User left voice channel"
                )
            except discord.Forbidden:
                pass


async def setup(bot):
    existing = bot.get_cog("Utility")
    if existing:
        await bot.remove_cog("Utility")

    await bot.add_cog(Utility(bot))
