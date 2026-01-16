import discord
from discord.ext import commands
from discord import app_commands

# ---------- VIEW (BUTTONS) ----------

class WelcomeView(discord.ui.View):
    def __init__(self):
        # NOT persistent → no timeout=None + no bot.add_view()
        super().__init__()

        # Link buttons (safe, no callbacks)
        self.add_item(discord.ui.Button(
            label="Permanent Invite",
            style=discord.ButtonStyle.link,
            url="https://discord.gg/CdzEc3x3Ft",
            emoji="🔗"
        ))

        self.add_item(discord.ui.Button(
            label="GitHub",
            style=discord.ButtonStyle.link,
            url="https://github.com/Aridro366",
            emoji="🐙"
        ))

        self.add_item(discord.ui.Button(
            label="Website",
            style=discord.ButtonStyle.link,
            url="https://aridrosportfolio.netlify.app/",
            emoji="🌐"
        ))

    # -------- INTERACTION BUTTONS --------

    @discord.ui.button(label="How to share code", style=discord.ButtonStyle.primary, emoji="💻")
    async def share_code(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title="💻 How to Share Code",
            description=(
                "Use **code blocks**:\n"
                "```python\nprint('Hello World')\n```\n"
                "Use GitHub or Pastebin for large files.\n"
                "Always mention **language + error**."
            ),
            color=discord.Color.blurple()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(label="How to ask for help", style=discord.ButtonStyle.danger, emoji="❓")
    async def ask_help(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title="❓ How to Ask for Help",
            description=(
                "Good questions include:\n"
                "• What you’re trying to do\n"
                "• What happened\n"
                "• Error message\n"
                "• Code snippet\n"
                "• go to Command channel and type /ask and your can submit a help request!!\n\n"
                "❌ Avoid: *pls help*"
            ),
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(label="Learn a new language", style=discord.ButtonStyle.success, emoji="📘")
    async def learn_lang(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title="📘 Learning Resources",
            description=(
                "Python → docs.python.org\n"
                "Web → developer.mozilla.org\n"
                "Java → docs.oracle.com\n"
                "Git → git-scm.com"
            ),
            color=discord.Color.green()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)


    @discord.ui.button(label="How XP works", style=discord.ButtonStyle.success, emoji="⭐")
    async def xp(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title="⭐ XP System",
            description=(
                "Earn XP by helping others.\n"
                "Quality answers > spam.\n"
                "XP is moderated."
            ),
            color=discord.Color.gold()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)


# ---------- COG ----------

class Welcome(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="setup_welcome", description="Post the server welcome panel")
    @app_commands.checks.has_permissions(administrator=True)
    async def setup_welcome(self, interaction: discord.Interaction):

        embed = discord.Embed(
            title="⭐ About the Server ⭐",
            description=(
                "**Welcome to the Horizon devs!**\n\n"
                "We’re a community of programmers who love sharing knowledge.\n\n"
                "**Need help?** Ask in support channels.\n"
                "**Show projects?** Use the showcase channel.\n"
                "**Just chat?** Join general or tech-talk."
            ),
            color=discord.Color.dark_purple()
        )

        embed.set_footer(text="Developer Den")

        await interaction.channel.send(embed=embed, view=WelcomeView())
        await interaction.response.send_message(
            "✅ Welcome panel created.",
            ephemeral=True
        )


# ---------- SETUP ----------

async def setup(bot):
    await bot.add_cog(Welcome(bot))
