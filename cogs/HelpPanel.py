import discord
from discord.ext import commands
from discord import app_commands


HELP_MESSAGE = (
    "✨ Hey there! I’m here to help.\n\n"
    "If you need something, just let the team know or explore the server —\n"
    "I’m always improving and learning new features 💙"
)


class HelpPanel(commands.Cog):
    def __init__(self, bot):
        self.bot = bot


    # =========================
    #  TEXT COMMAND (.help)
    # =========================
    @commands.command(name="help")
    async def help_cmd(self, ctx):
        await ctx.send(HELP_MESSAGE)


    # =========================
    #  SLASH COMMAND (/help)
    # =========================
    @app_commands.command(name="help", description="Get help information")
    async def help_slash(self, interaction: discord.Interaction):
        await interaction.response.send_message(HELP_MESSAGE, ephemeral=True)


    # =========================
    #  BOT MENTION → reply
    # =========================
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return

        # user mentions the bot directly
        if (
            message.content.strip() == f"<@{self.bot.user.id}>"
            or message.content.strip() == f"<@!{self.bot.user.id}>"
        ):
            await message.reply(HELP_MESSAGE)


async def setup(bot):
    await bot.add_cog(HelpPanel(bot))
