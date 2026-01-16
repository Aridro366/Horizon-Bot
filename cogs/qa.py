import discord
from discord.ext import commands
from discord import app_commands
import json

# ---------- CONFIG ----------

with open("config.json") as f:
    config = json.load(f)

QA_CHANNEL_ID = config.get("qa_channel_id")
STAFF_ROLE_ID = config["staff_role_id"]

# ---------- VIEW ----------

class SolvedView(discord.ui.View):
    def __init__(self, author_id: int):
        super().__init__()
        self.author_id = author_id

    @discord.ui.button(
        label="Mark as Solved",
        style=discord.ButtonStyle.success,
        emoji="✅"
    )
    async def solved(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        is_staff = any(
            role.id == STAFF_ROLE_ID
            for role in interaction.user.roles
        )

        if interaction.user.id != self.author_id and not is_staff:
            await interaction.response.send_message(
                "❌ Only the author or staff can mark this solved.",
                ephemeral=True
            )
            return

        thread = interaction.channel

        if isinstance(thread, discord.Thread):
            await thread.edit(
                name=f"✅ SOLVED | {thread.name}",
                archived=True
            )

        button.disabled = True
        await interaction.message.edit(view=self)

        await interaction.response.send_message(
            "✅ Marked as solved.",
            ephemeral=True
        )

# ---------- COG ----------

class QASystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="ask",
        description="Ask a programming question (creates a thread)"
    )
    @app_commands.describe(
        title="Short problem summary",
        language="Programming language or tech",
        description="Explain the issue clearly",
        code="Optional code or error"
    )
    async def ask(
        self,
        interaction: discord.Interaction,
        title: str,
        language: str,
        description: str,
        code: str | None = None
    ):
        channel = interaction.guild.get_channel(QA_CHANNEL_ID)

        if not channel:
            await interaction.response.send_message(
                "❌ Q&A channel is not configured.",
                ephemeral=True
            )
            return

        embed = discord.Embed(
            title=title,
            description=description,
            color=discord.Color.blurple()
        )
        embed.add_field(name="Language / Tech", value=language, inline=False)
        embed.add_field(name="Asked by", value=interaction.user.mention, inline=False)

        if code:
            embed.add_field(
                name="Code / Error",
                value=f"```{code[:1000]}```",
                inline=False
            )

        embed.set_footer(text="Please continue discussion in the thread")

        message = await channel.send(embed=embed)

        thread = await message.create_thread(
            name=f"❓ {language} | {title[:80]}"
        )

        await thread.send(
            "🔍 **Discussion Thread**\n"
            "Use replies here to help solve the problem.",
            view=SolvedView(interaction.user.id)
        )

        await interaction.response.send_message(
            f"✅ Your question has been posted: {thread.mention}",
            ephemeral=True
        )

# ---------- SETUP ----------

async def setup(bot):
    await bot.add_cog(QASystem(bot))
