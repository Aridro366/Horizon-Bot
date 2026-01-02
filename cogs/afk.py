import discord
from discord.ext import commands
from discord import app_commands
import time

AFK_ROLE_NAME = "AFK"   # rename if you want


class Fun(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        # prevent crash if anti-spam uses on_message
        self.msg_cache = {}
        # afk_data[guild][user] = { time, reason, old_nick }
        self.afk_data: dict[int, dict[int, dict]] = {}

    # ---------------- Helpers ----------------
    def format_duration(self, seconds: float):
        mins, secs = divmod(int(seconds), 60)
        hrs, mins = divmod(mins, 60)

        if hrs > 0:
            return f"{hrs}h {mins}m"
        if mins > 0:
            return f"{mins}m {secs}s"
        return f"{secs}s"

    def is_afk(self, guild_id: int, user_id: int):
        return guild_id in self.afk_data and user_id in self.afk_data[guild_id]

    def set_afk(self, guild_id: int, user_id: int, reason: str):
        self.afk_data.setdefault(guild_id, {})[user_id] = {
            "time": time.time(),
            "reason": reason,
            "old_nick": None
        }

    def remove_afk_data(self, guild_id: int, user_id: int):
        if self.is_afk(guild_id, user_id):
            del self.afk_data[guild_id][user_id]
            if not self.afk_data[guild_id]:
                del self.afk_data[guild_id]

    async def get_afk_role(self, guild: discord.Guild):
        role = discord.utils.get(guild.roles, name=AFK_ROLE_NAME)
        if role is None:
            try:
                role = await guild.create_role(
                    name=AFK_ROLE_NAME,
                    reason="AFK system role"
                )
            except discord.Forbidden:
                return None
        return role

    async def set_nick_tag(self, member: discord.Member):
        if not member.guild.me.guild_permissions.manage_nicknames:
            return

        if member.display_name.startswith("[AFK] "):
            return

        self.afk_data[member.guild.id][member.id]["old_nick"] = member.display_name

        try:
            await member.edit(nick=f"[AFK] {member.display_name}")
        except (discord.Forbidden, discord.HTTPException):
            pass

    async def restore_nick(self, member: discord.Member):
        if not member.guild.me.guild_permissions.manage_nicknames:
            return

        entry = self.afk_data.get(member.guild.id, {}).get(member.id)
        if not entry:
            return

        old = entry.get("old_nick")
        if not old:
            return

        try:
            await member.edit(nick=old)
        except (discord.Forbidden, discord.HTTPException):
            pass

    async def enable_afk(self, member: discord.Member, reason: str):
        guild_id = member.guild.id
        self.set_afk(guild_id, member.id, reason)

        await self.set_nick_tag(member)

        role = await self.get_afk_role(member.guild)
        if role:
            try:
                await member.add_roles(role, reason="AFK mode enabled")
            except discord.Forbidden:
                pass

    async def disable_afk(self, member: discord.Member):
        guild_id = member.guild.id

        await self.restore_nick(member)

        role = await self.get_afk_role(member.guild)
        if role:
            try:
                await member.remove_roles(role, reason="AFK mode disabled")
            except discord.Forbidden:
                pass

        self.remove_afk_data(guild_id, member.id)

    # =====================================================
    # PREFIX — !afk
    # =====================================================
    @commands.command(name="afk")
    async def afk_prefix(self, ctx, *, reason: str = "AFK"):
        await self.enable_afk(ctx.author, reason)

        await ctx.send(
            f"🟡 **{ctx.author.display_name}** is now AFK — {reason}"
        )

    # =====================================================
    # SLASH — /afk
    # =====================================================
    @app_commands.command(
        name="afk",
        description="Set your AFK status."
    )
    async def afk_slash(
        self,
        interaction: discord.Interaction,
        reason: str = "AFK"
    ):
        await self.enable_afk(interaction.user, reason)

        await interaction.response.send_message(
            f"🟡 **{interaction.user.display_name}** is now AFK — {reason}",
            ephemeral=False
        )

    # =====================================================
    # MESSAGE LISTENER — ignore afk command, disable on chat
    # =====================================================
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or message.guild is None:
            return

        guild_id = message.guild.id
        user_id = message.author.id

        # --- Do NOT disable AFK while running the AFK command ---
        ctx = await self.bot.get_context(message)
        if ctx.command and ctx.command.name == "afk":
            await self.bot.process_commands(message)
            return

        # --- Disable AFK when sending a normal message ---
        if self.is_afk(guild_id, user_id):
            start = self.afk_data[guild_id][user_id]["time"]
            reason = self.afk_data[guild_id][user_id]["reason"]
            duration = self.format_duration(time.time() - start)

            await self.disable_afk(message.author)

            wake = await message.channel.send(
                f"🟢 **{message.author.display_name}** is back!\n"
                f"⏱ AFK Duration: **{duration}**\n"
                f"📌 Previous reason: {reason}"
            )

            try:
                await wake.delete(delay=5)
            except discord.HTTPException:
                pass

        # --- Notify when tagging AFK users ---
        if message.mentions:
            for user in message.mentions:
                if self.is_afk(guild_id, user.id):
                    data = self.afk_data[guild_id][user.id]
                    duration = self.format_duration(time.time() - data["time"])

                    await message.reply(
                        f"⚠️ **{user.display_name}** is AFK\n"
                        f"📌 Reason: **{data['reason']}**\n"
                        f"⏱ AFK for **{duration}**",
                        mention_author=False
                    )

        # allow other prefix commands to work
        await self.bot.process_commands(message)

    async def cog_load(self):
        # optional: guild-bind slash here if you want
        pass


# ✅ FIXED — load the *Fun* cog (not AFK)
async def setup(bot):
    await bot.add_cog(Fun(bot))
