import discord
from discord.ext import commands
from datetime import datetime
import io


BUG_CHANNEL_NAME = "🐞・bug-reports"
BUG_PANEL_CHANNEL = "🛠️・bug-panel"
BUG_ARCHIVE_CHANNEL = "📦・bug-archive"
DEV_ROLE_NAME = "Developers"   # change if needed

BUG_INDEX = {}          # guild_id -> bug counter
THREAD_MAP = {}         # bug_message_id -> thread_id
ASSIGNED_MAP = {}       # bug_message_id -> user_id
PING_MAP = {}           # bug_message_id -> ping_message_id

SEVERITY_SCORES = {
    "LOW": 1,
    "MEDIUM": 2,
    "HIGH": 3,
    "CRITICAL": 5
}


def next_bug_id(gid: int):
    BUG_INDEX.setdefault(gid, 1)
    bug = BUG_INDEX[gid]
    BUG_INDEX[gid] += 1
    return bug


# ============================
# BUG REPORT FORM (5-FIELD UI)
# ============================
class BugReportModal(discord.ui.Modal, title="🐞 Submit Bug Report"):

    title_input = discord.ui.TextInput(label="Bug Title", max_length=80)

    project_input = discord.ui.TextInput(
        label="Project / Module",
        max_length=60
    )

    priority_input = discord.ui.TextInput(
        label="Priority (Low / Medium / High / Critical)",
        placeholder="High"
    )

    steps_input = discord.ui.TextInput(
        label="Steps to Reproduce",
        style=discord.TextStyle.paragraph
    )

    outcome_input = discord.ui.TextInput(
        label="Expected vs Actual",
        style=discord.TextStyle.paragraph,
        placeholder="Expected: ...\nActual: ..."
    )

    def __init__(self, author, target_channel):
        super().__init__()
        self.author = author
        self.target_channel = target_channel

    async def on_submit(self, interaction: discord.Interaction):

        # respond immediately to avoid timeout
        await interaction.response.send_message(
            "📨 Bug submitted — creating thread...",
            ephemeral=True
        )

        guild = interaction.guild
        bug_id = next_bug_id(guild.id)

        priority = self.priority_input.value.upper()
        if priority not in SEVERITY_SCORES:
            priority = "MEDIUM"

        severity = SEVERITY_SCORES[priority]

        embed = discord.Embed(
            title=f"🐞 BUG-{bug_id} — {self.title_input.value}",
            color=0xE74C3C,
            timestamp=datetime.utcnow()
        )

        embed.add_field(name="👤 Reporter", value=self.author.mention, inline=False)
        embed.add_field(name="📁 Project", value=self.project_input.value, inline=False)

        embed.add_field(name="📌 Priority", value=f"`{priority}`", inline=True)
        embed.add_field(name="🧮 Severity", value=f"`{severity}`", inline=True)

        embed.add_field(name="📝 Steps", value=self.steps_input.value, inline=False)
        embed.add_field(name="📌 Outcome", value=self.outcome_input.value, inline=False)

        view = BugReviewButtons(reporter=self.author)

        # post bug entry
        msg = await self.target_channel.send(embed=embed, view=view)

        # create public discussion thread
        thread = await msg.create_thread(
            name=f"BUG-{bug_id} • {self.title_input.value[:40]}",
            auto_archive_duration=1440
        )

        THREAD_MAP[msg.id] = thread.id

        await thread.send(
            f"🧵 Thread created for **BUG-{bug_id}**\n"
            f"Reporter: {self.author.mention}\n"
            f"Use this thread for investigation & discussion."
        )

        # notify dev team (ping message is tracked so we can delete it later)
        dev_role = discord.utils.get(guild.roles, name=DEV_ROLE_NAME)
        if dev_role:
            ping_msg = await self.target_channel.send(
                f"🔔 {dev_role.mention} — New bug reported: **BUG-{bug_id}**"
            )
            PING_MAP[msg.id] = ping_msg.id


# ============================
# BUTTON CONTROL PANEL
# ============================
class BugReviewButtons(discord.ui.View):
    def __init__(self, reporter):
        super().__init__(timeout=None)
        self.reporter = reporter

    async def get_thread(self, interaction):
        tid = THREAD_MAP.get(interaction.message.id)
        return interaction.guild.get_thread(tid) if tid else None

    # 👤 Assign Developer
    @discord.ui.button(label="Assign to Me", style=discord.ButtonStyle.secondary)
    async def assign(self, interaction, button):
        ASSIGNED_MAP[interaction.message.id] = interaction.user.id

        embed = interaction.message.embeds[0]
        embed.add_field(
            name="👥 Assigned Developer",
            value=interaction.user.mention,
            inline=False
        )

        await interaction.message.edit(embed=embed, view=self)

        thread = await self.get_thread(interaction)
        if thread:
            await thread.send(f"👤 Assigned to {interaction.user.mention}")

        await interaction.response.send_message("Assigned to you.", ephemeral=True)

    # 🟡 Mark In-Progress
    @discord.ui.button(label="Mark In-Progress", style=discord.ButtonStyle.primary)
    async def inprogress(self, interaction, button):
        thread = await self.get_thread(interaction)
        if thread:
            await thread.send(
                f"⚙️ Bug marked **In-Progress** by {interaction.user.mention}"
            )

        await interaction.response.send_message("Status updated.", ephemeral=True)

    # 🟢 Resolve → export + archive + delete + remove ping
    @discord.ui.button(label="Resolve & Archive", style=discord.ButtonStyle.success)
    async def resolve(self, interaction, button):
        thread = await self.get_thread(interaction)
        embed = interaction.message.embeds[0]

        # build TXT export
        report_text = (
            f"{embed.title}\n"
            f"Reporter: {embed.fields[0].value}\n"
            f"Project: {embed.fields[1].value}\n"
            f"Priority: {embed.fields[2].value}\n"
            f"Severity: {embed.fields[3].value}\n\n"
            f"Steps:\n{embed.fields[4].value}\n\n"
            f"Outcome:\n{embed.fields[5].value}\n"
        )

        file = discord.File(
            io.BytesIO(report_text.encode()),
            filename=f"{embed.title.replace(' ', '_')}.txt"
        )

        archive = discord.utils.get(
            interaction.guild.text_channels,
            name=BUG_ARCHIVE_CHANNEL
        )

        if archive:
            await archive.send("📦 **Resolved Bug Export**", file=file)

        # post resolution & archive thread
        if thread:
            await thread.send(f"🟢 Bug marked **Resolved** by {interaction.user.mention}")
            await thread.edit(archived=True, locked=True)

        # delete dev-ping message if it exists
        ping_id = PING_MAP.get(interaction.message.id)
        if ping_id:
            try:
                ping_msg = await interaction.channel.fetch_message(ping_id)
                await ping_msg.delete()
            except:
                pass

        # delete original bug entry
        try:
            await interaction.message.delete()
        except:
            pass

        await interaction.response.send_message(
            "Bug resolved — archived, exported, and cleaned from bug-reports.",
            ephemeral=True
        )


# ============================
# PANEL COMMAND
# ============================
class BugPanel(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.has_permissions(manage_messages=True)
    @commands.command()
    async def bugpanel(self, ctx):
        panel = discord.utils.get(ctx.guild.text_channels, name=BUG_PANEL_CHANNEL)
        if not panel:
            return await ctx.reply("❌ Panel channel not found.")

        embed = discord.Embed(
            title="🐞 Bug Report Panel",
            description="Click below to submit a bug report.",
            color=0x3498DB
        )

        view = discord.ui.View()
        view.add_item(discord.ui.Button(
            label="Submit Bug Report",
            style=discord.ButtonStyle.blurple,
            custom_id="open_bug_modal"
        ))

        await panel.send(embed=embed, view=view)
        await ctx.reply("✅ Bug panel created.")

    @commands.Cog.listener()
    async def on_interaction(self, interaction: discord.Interaction):
        if (
            interaction.type == discord.InteractionType.component
            and interaction.data.get("custom_id") == "open_bug_modal"
        ):
            bug_channel = discord.utils.get(
                interaction.guild.text_channels,
                name=BUG_CHANNEL_NAME
            )

            await interaction.response.send_modal(
                BugReportModal(interaction.user, bug_channel)
            )


async def setup(bot):
    if bot.get_cog("BugPanel"):
        await bot.remove_cog("BugPanel")
    await bot.add_cog(BugPanel(bot))
