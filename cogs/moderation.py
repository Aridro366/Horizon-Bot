import discord
from discord.ext import commands
from discord import app_commands
from datetime import timedelta
import json

with open("config.json") as f:
    config = json.load(f)


class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # ------------ Embed Helper ------------
    def mod_embed(self, title, description, color=0x2B6CB0):
        return (
            discord.Embed(title=title, description=description, color=color)
            .set_footer(text="Horizon Devs • Moderation")
        )

    # ------------ Safety Helpers ----------
    def hierarchy_safe(self, actor, target):
        return target.top_role < actor.top_role

    async def send_error_interaction(self, interaction, message):
        await interaction.response.send_message(
            embed=self.mod_embed("⚠️ Action Blocked", message, 0xE53E3E),
            ephemeral=True,
        )

    async def send_error_ctx(self, ctx, message):
        await ctx.reply(
            embed=self.mod_embed("⚠️ Action Blocked", message, 0xE53E3E),
            mention_author=False,
        )

    def admin_only():
        async def predicate(interaction: discord.Interaction):
            if not interaction.user.guild_permissions.manage_guild:
                raise app_commands.CheckFailure("Admin only.")
            return True

        return app_commands.check(predicate)

    # ======================================================
    # PREFIX COMMAND — PURGE
    # ======================================================

    @commands.command(name="purge", aliases=["clear"])
    @commands.has_permissions(manage_messages=True)
    @commands.guild_only()
    async def purge(self, ctx, amount: int):
        """Deletes a number of recent messages in the channel."""

        if amount < 1 or amount > 200:
            return await self.send_error_ctx(
                ctx, "Please choose a number between **1 and 200**."
            )

        deleted = await ctx.channel.purge(limit=amount + 1)

        confirm = await ctx.send(
            embed=self.mod_embed(
                "🧹 Messages Purged",
                f"Deleted **{len(deleted)-1} messages** in {ctx.channel.mention}.",
            )
        )

        await confirm.delete(delay=5)

        log_channel = self.bot.get_channel(config["log_channel_id"])
        if log_channel:
            await log_channel.send(
                embed=self.mod_embed(
                    "🧹 Channel Purge Logged",
                    f"**Moderator:** {ctx.author.mention}\n"
                    f"**Channel:** {ctx.channel.mention}\n"
                    f"**Messages Removed:** {len(deleted)-1}",
                )
            )

    @purge.error
    async def purge_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await self.send_error_ctx(
                ctx, "You need **Manage Messages** permission to use this command."
            )
        elif isinstance(error, commands.BadArgument):
            await self.send_error_ctx(
                ctx, "Please provide a **valid number** of messages."
            )
        else:
            await self.send_error_ctx(
                ctx, "Something went wrong while running this command."
            )

    # ======================================================
    # SLASH COMMANDS — KICK / BAN / TIMEOUT
    # ======================================================

    @app_commands.command(name="kick", description="Kick a member")
    @admin_only()
    async def kick(
        self,
        interaction: discord.Interaction,
        member: discord.Member,
        reason: str = "No reason provided",
    ):
        if not self.hierarchy_safe(interaction.user, member):
            return await self.send_error_interaction(
                interaction,
                "You cannot moderate someone with equal or higher role.",
            )

        await member.kick(reason=reason)

        await interaction.response.send_message(
            embed=self.mod_embed(
                "👢 Member Kicked", f"{member.mention}\n**Reason:** {reason}"
            )
        )

    @app_commands.command(name="ban", description="Ban a member")
    @admin_only()
    async def ban(
        self,
        interaction: discord.Interaction,
        member: discord.Member,
        reason: str = "No reason provided",
    ):
        if not self.hierarchy_safe(interaction.user, member):
            return await self.send_error_interaction(
                interaction,
                "You cannot moderate someone with equal or higher role.",
            )

        await member.ban(reason=reason)

        await interaction.response.send_message(
            embed=self.mod_embed(
                "⛔ Member Banned", f"{member.mention}\n**Reason:** {reason}"
            )
        )

    @app_commands.command(name="timeout", description="Timeout a member (minutes)")
    @admin_only()
    async def timeout(
        self,
        interaction: discord.Interaction,
        member: discord.Member,
        minutes: int,
        reason: str = "No reason provided",
    ):
        if not self.hierarchy_safe(interaction.user, member):
            return await self.send_error_interaction(
                interaction,
                "You cannot moderate someone with equal or higher role.",
            )

        duration = timedelta(minutes=minutes)
        await member.timeout(duration, reason=reason)

        await interaction.response.send_message(
            embed=self.mod_embed(
                "⌛ Member Timed Out",
                f"{member.mention}\n**Duration:** {minutes}m\n**Reason:** {reason}",
            )
        )


async def setup(bot):
    await bot.add_cog(Moderation(bot))
