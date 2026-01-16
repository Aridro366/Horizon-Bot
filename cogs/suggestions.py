import discord
from discord.ext import commands
from discord import app_commands
import json

# ---------------- CONFIG ----------------

with open("config.json", "r", encoding="utf-8") as f:
    config = json.load(f)

SUGGESTION_CHANNEL_ID = config["suggestion_channel_id"]
STAFF_ROLE_ID = config["staff_role_id"]

# ---------------- PUBLIC VIEW (EVERYONE) ----------------

class SuggestionPublicView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.upvotes: set[int] = set()
        self.downvotes: set[int] = set()

    def update_embed(self, embed: discord.Embed):
        embed.set_field_at(
            2,
            name="Results",
            value=f"✅ {len(self.upvotes)} ❌ {len(self.downvotes)}",
            inline=False
        )

    @discord.ui.button(label="Approve", style=discord.ButtonStyle.success, emoji="✅")
    async def approve(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id in self.upvotes:
            await interaction.response.send_message(
                "You already approved this suggestion.",
                ephemeral=True
            )
            return

        self.downvotes.discard(interaction.user.id)
        self.upvotes.add(interaction.user.id)

        embed = interaction.message.embeds[0]
        self.update_embed(embed)
        await interaction.message.edit(embed=embed, view=self)
        await interaction.response.defer()

    @discord.ui.button(label="Reject", style=discord.ButtonStyle.danger, emoji="❌")
    async def reject(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id in self.downvotes:
            await interaction.response.send_message(
                "You already rejected this suggestion.",
                ephemeral=True
            )
            return

        self.upvotes.discard(interaction.user.id)
        self.downvotes.add(interaction.user.id)

        embed = interaction.message.embeds[0]
        self.update_embed(embed)
        await interaction.message.edit(embed=embed, view=self)
        await interaction.response.defer()

    @discord.ui.button(label="View Votes", style=discord.ButtonStyle.secondary, emoji="👁️")
    async def view_votes(self, interaction: discord.Interaction, button: discord.ui.Button):
        voters = (
            "✅ Upvotes:\n" +
            ("\n".join(f"<@{u}>" for u in self.upvotes) or "None") +
            "\n\n❌ Downvotes:\n" +
            ("\n".join(f"<@{d}>" for d in self.downvotes) or "None")
        )

        embed = discord.Embed(
            title="📊 Vote Breakdown",
            description=voters,
            color=discord.Color.blurple()
        )

        await interaction.response.send_message(embed=embed, ephemeral=True)

# ---------------- STAFF VIEW (THREAD ONLY) ----------------

class SuggestionStaffView(discord.ui.View):
    def __init__(self, public_message: discord.Message, public_view: SuggestionPublicView):
        super().__init__(timeout=None)
        self.public_message = public_message
        self.public_view = public_view

    def is_staff(self, member: discord.Member) -> bool:
        return any(role.id == STAFF_ROLE_ID for role in member.roles)

    @discord.ui.button(label="Accept", style=discord.ButtonStyle.success, emoji="✔️")
    async def accept(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self.is_staff(interaction.user):
            await interaction.response.send_message(
                "❌ Only staff can accept suggestions.",
                ephemeral=True
            )
            return

        embed = discord.Embed(
            title="Status: ACCEPTED",
            color=discord.Color.green()
        )
        embed.add_field(
            name="Suggestion",
            value=self.public_message.embeds[0].description,
            inline=False
        )
        embed.add_field(
            name="Results",
            value=f"✅ {len(self.public_view.upvotes)} ❌ {len(self.public_view.downvotes)}",
            inline=False
        )
        embed.add_field(
            name="Approved By",
            value=interaction.user.mention,
            inline=False
        )

        await self.public_message.edit(embed=embed, view=None)
        await interaction.response.send_message(
            "✅ Suggestion accepted.",
            ephemeral=True
        )

    @discord.ui.button(label="Deny", style=discord.ButtonStyle.danger, emoji="⛔")
    async def deny(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self.is_staff(interaction.user):
            await interaction.response.send_message(
                "❌ Only staff can reject suggestions.",
                ephemeral=True
            )
            return

        await interaction.response.send_modal(
            DenyModal(self.public_message, self.public_view)
        )

# ---------------- DENY MODAL ----------------

class DenyModal(discord.ui.Modal, title="Reject Suggestion"):
    reason = discord.ui.TextInput(
        label="Reason for rejection",
        style=discord.TextStyle.paragraph,
        max_length=400,
        required=True
    )

    def __init__(self, public_message: discord.Message, public_view: SuggestionPublicView):
        super().__init__()
        self.public_message = public_message
        self.public_view = public_view

    async def on_submit(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="Status: REJECTED",
            color=discord.Color.red()
        )
        embed.add_field(
            name="Suggestion",
            value=self.public_message.embeds[0].description,
            inline=False
        )
        embed.add_field(
            name="Reason",
            value=self.reason.value,
            inline=False
        )
        embed.add_field(
            name="Results",
            value=f"✅ {len(self.public_view.upvotes)} ❌ {len(self.public_view.downvotes)}",
            inline=False
        )
        embed.add_field(
            name="Rejected By",
            value=interaction.user.mention,
            inline=False
        )

        await self.public_message.edit(embed=embed, view=None)
        await interaction.response.send_message(
            "⛔ Suggestion rejected.",
            ephemeral=True
        )

# ---------------- COG ----------------

class Suggestions(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="suggest", description="Submit a server suggestion")
    async def suggest(self, interaction: discord.Interaction, suggestion: str):
        channel = interaction.guild.get_channel(SUGGESTION_CHANNEL_ID)

        if not channel:
            await interaction.response.send_message(
                "❌ Suggestion channel not configured.",
                ephemeral=True
            )
            return

        embed = discord.Embed(
            title="📌 New Suggestion",
            description=suggestion,
            color=discord.Color.dark_purple()
        )
        embed.add_field(name="Submitted By", value=interaction.user.mention, inline=False)
        embed.add_field(name="Status", value="⏳ Pending", inline=False)
        embed.add_field(name="Results", value="✅ 0 ❌ 0", inline=False)

        public_view = SuggestionPublicView()
        public_message = await channel.send(embed=embed, view=public_view)

        # -------- CREATE STAFF THREAD (SAFE) --------
        staff_thread = None
        try:
            staff_thread = await public_message.create_thread(
                name="Staff Review",
                auto_archive_duration=1440
            )
        except Exception:
            staff_thread = None

        if staff_thread:
            for member in interaction.guild.members:
                if any(role.id == STAFF_ROLE_ID for role in member.roles):
                    await staff_thread.add_user(member)

            await staff_thread.send(
                "🔐 **Staff-only controls for this suggestion**",
                view=SuggestionStaffView(public_message, public_view)
            )

        await interaction.response.send_message(
            "✅ Your suggestion has been posted.",
            ephemeral=True
        )

# ---------------- SETUP ----------------

async def setup(bot):
    await bot.add_cog(Suggestions(bot))
