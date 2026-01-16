import discord
from discord.ext import commands
from discord import app_commands

class HelpPanel(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="help", description="Show all bot commands and features")
    async def help_panel(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="🤖 Horizon 2.0 — Help Panel",
            description=(
                "A developer-focused Discord bot built for **structured discussions**, "
                "**clean staff workflows**, and **community feedback**."
            ),
            color=discord.Color.blurple()
        )

        # -------- FEATURES --------
        embed.add_field(
            name="✨ Core Features",
            value=(
                "• Suggestion system with voting\n"
                "• Private staff review threads\n"
                "• Staff-only prefix commands\n"
                "• Hybrid slash + prefix support\n"
                "• Clean, non-spam UX"
            ),
            inline=False
        )

        # -------- SLASH COMMANDS --------
        embed.add_field(
            name="📌 Slash Commands (`/`)",
            value=(
                "`/suggest` — Submit a server suggestion\n"
                "`/help` — Show this help panel"
            ),
            inline=False
        )

        # -------- PREFIX COMMANDS --------
        embed.add_field(
            name="🛠 Staff Prefix Commands (`.`)",
            value=(
                "`.ping` — Bot latency\n"
                "`.bot_info` — Bot stats & uptime\n"
                "`.bot_status` — Bot health & permissions\n"
                "`.user_info` — User details\n"
                "`.add_role` — Assign role\n"
                "`.remove_role` — Remove role\n"
                "`.say` — Bot announcement message\n"
                "`.util_help` — Utility command list"
            ),
            inline=False
        )

        # -------- FOOTER --------
        embed.set_footer(
            text="Horizon 2.0 • Built for developer communities"
        )

        await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(HelpPanel(bot))
