import discord
from discord.ext import commands
from discord import app_commands
import json
from datetime import timedelta

# ---------------- CONFIG ----------------

with open("config.json") as f:
    config = json.load(f)

# ---------------- COG ----------------

class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # ---------------- HELPERS ----------------

    def can_moderate(self, moderator: discord.Member, target: discord.Member) -> bool:
        if moderator == target:
            return False
        if target.bot:
            return False
        if target == target.guild.owner:
            return False
        return moderator.top_role > target.top_role

    async def log(self, guild: discord.Guild, embed: discord.Embed):
        channel = guild.get_channel(config["mod_log_channel_id"])
        if channel:
            await channel.send(embed=embed)

    # ---------------- MOD COMMANDS ----------------

    @app_commands.command(name="mute", description="Timeout a user")
    @app_commands.checks.has_role(config["staff_role_id"])
    async def mute(self, interaction: discord.Interaction, user: discord.Member, minutes: int, reason: str):
        if not self.can_moderate(interaction.user, user):
            await interaction.response.send_message(
                embed=discord.Embed(description="❌ You cannot moderate this user.", color=discord.Color.red()),
                ephemeral=True
            )
            return

        await user.timeout(timedelta(minutes=minutes), reason=reason)

        embed = discord.Embed(title="🔇 User Muted", color=discord.Color.orange())
        embed.add_field(name="User", value=str(user), inline=False)
        embed.add_field(name="Duration", value=f"{minutes} minutes", inline=False)
        embed.add_field(name="Reason", value=reason, inline=False)
        embed.add_field(name="Moderator", value=interaction.user.mention, inline=False)

        await interaction.response.send_message(embed=embed, ephemeral=True)
        await self.log(interaction.guild, embed)

    @app_commands.command(name="unmute", description="Remove timeout")
    @app_commands.checks.has_role(config["staff_role_id"])
    async def unmute(self, interaction: discord.Interaction, user: discord.Member):
        await user.timeout(None)

        embed = discord.Embed(title="🔊 User Unmuted", color=discord.Color.green())
        embed.add_field(name="User", value=str(user), inline=False)
        embed.add_field(name="Moderator", value=interaction.user.mention, inline=False)

        await interaction.response.send_message(embed=embed, ephemeral=True)
        await self.log(interaction.guild, embed)

    @app_commands.command(name="kick", description="Kick a user")
    @app_commands.checks.has_role(config["staff_role_id"])
    async def kick(self, interaction: discord.Interaction, user: discord.Member, reason: str):
        if not self.can_moderate(interaction.user, user):
            await interaction.response.send_message(
                embed=discord.Embed(description="❌ You cannot kick this user.", color=discord.Color.red()),
                ephemeral=True
            )
            return

        await user.kick(reason=reason)

        embed = discord.Embed(title="👢 User Kicked", color=discord.Color.red())
        embed.add_field(name="User", value=str(user), inline=False)
        embed.add_field(name="Reason", value=reason, inline=False)
        embed.add_field(name="Moderator", value=interaction.user.mention, inline=False)

        await interaction.response.send_message(embed=embed, ephemeral=True)
        await self.log(interaction.guild, embed)

    @app_commands.command(name="ban", description="Ban a user")
    @app_commands.checks.has_role(config["staff_role_id"])
    async def ban(self, interaction: discord.Interaction, user: discord.Member, reason: str):
        if not self.can_moderate(interaction.user, user):
            await interaction.response.send_message(
                embed=discord.Embed(description="❌ You cannot ban this user.", color=discord.Color.red()),
                ephemeral=True
            )
            return

        await user.ban(reason=reason, delete_message_days=1)

        embed = discord.Embed(title="⛔ User Banned", color=discord.Color.dark_red())
        embed.add_field(name="User", value=str(user), inline=False)
        embed.add_field(name="Reason", value=reason, inline=False)
        embed.add_field(name="Moderator", value=interaction.user.mention, inline=False)

        await interaction.response.send_message(embed=embed, ephemeral=True)
        await self.log(interaction.guild, embed)

    @app_commands.command(name="unban", description="Unban a user by ID")
    @app_commands.checks.has_role(config["staff_role_id"])
    async def unban(self, interaction: discord.Interaction, user_id: str, reason: str = "Ban revoked"):
        try:
            user = discord.Object(id=int(user_id))
        except ValueError:
            await interaction.response.send_message(
                embed=discord.Embed(description="❌ Invalid user ID.", color=discord.Color.red()),
                ephemeral=True
            )
            return

        await interaction.guild.unban(user, reason=reason)

        embed = discord.Embed(title="🔓 User Unbanned", color=discord.Color.green())
        embed.add_field(name="User ID", value=user_id, inline=False)
        embed.add_field(name="Reason", value=reason, inline=False)
        embed.add_field(name="Moderator", value=interaction.user.mention, inline=False)

        await interaction.response.send_message(embed=embed, ephemeral=True)
        await self.log(interaction.guild, embed)

    @app_commands.command(name="purge", description="Delete recent messages in this channel")
    @app_commands.checks.has_role(config["staff_role_id"])
    async def purge(self, interaction: discord.Interaction, amount: int):
        if amount < 1 or amount > 100:
            await interaction.response.send_message(
                embed=discord.Embed(description="❌ Amount must be between 1 and 100.", color=discord.Color.red()),
                ephemeral=True
            )
            return

        deleted = await interaction.channel.purge(limit=amount)

        embed = discord.Embed(title="🧹 Messages Purged", color=discord.Color.orange())
        embed.add_field(name="Channel", value=interaction.channel.mention, inline=False)
        embed.add_field(name="Deleted", value=len(deleted), inline=False)
        embed.add_field(name="Moderator", value=interaction.user.mention, inline=False)

        await interaction.response.send_message(embed=embed, ephemeral=True)
        await self.log(interaction.guild, embed)

    @app_commands.command(name="purge_user", description="Delete messages from a specific user")
    @app_commands.checks.has_role(config["staff_role_id"])
    async def purge_user(self, interaction: discord.Interaction, user: discord.Member, amount: int):
        if amount < 1 or amount > 100:
            await interaction.response.send_message(
                embed=discord.Embed(description="❌ Amount must be between 1 and 100.", color=discord.Color.red()),
                ephemeral=True
            )
            return

        def is_target(m: discord.Message):
            return m.author.id == user.id

        deleted = await interaction.channel.purge(limit=amount, check=is_target)

        embed = discord.Embed(title="🧹 User Messages Purged", color=discord.Color.orange())
        embed.add_field(name="User", value=str(user), inline=False)
        embed.add_field(name="Channel", value=interaction.channel.mention, inline=False)
        embed.add_field(name="Deleted", value=len(deleted), inline=False)
        embed.add_field(name="Moderator", value=interaction.user.mention, inline=False)

        await interaction.response.send_message(embed=embed, ephemeral=True)
        await self.log(interaction.guild, embed)

    # ---------------- ERROR HANDLER ----------------

    async def cog_app_command_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        embed = discord.Embed(color=discord.Color.red())

        if isinstance(error, app_commands.MissingRole):
            embed.description = "❌ You do not have permission to use this command."
        elif isinstance(error, app_commands.BotMissingPermissions):
            embed.description = "❌ I lack the required permissions."
        elif isinstance(error, app_commands.CommandInvokeError):
            embed.description = "❌ Action failed due to role hierarchy or Discord permissions."
        else:
            embed.description = "⚠️ An unexpected error occurred."

        if interaction.response.is_done():
            await interaction.followup.send(embed=embed, ephemeral=True)
        else:
            await interaction.response.send_message(embed=embed, ephemeral=True)

# ---------------- SETUP ----------------

async def setup(bot):
    await bot.add_cog(Moderation(bot))

