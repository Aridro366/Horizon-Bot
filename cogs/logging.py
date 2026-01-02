import discord
from discord.ext import commands
import json

with open("config.json") as f:
    config = json.load(f)

class Logging(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def log_embed(self, title, desc, color=0x4A5568):
        return discord.Embed(title=title, description=desc, color=color)\
            .set_footer(text="Horizon Devs • Logs")

    @property
    def log_channel(self):
        return self.bot.get_channel(config["log_channel_id"])


    @commands.Cog.listener()
    async def on_message_delete(self, message):
        if message.author.bot: return
        await self.log_channel.send(
            embed=self.log_embed("🗑️ Message Deleted",
                                 f"**Author:** {message.author.mention}\n**Channel:** {message.channel.mention}\n\n{message.content}")
        )

    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        if before.author.bot or before.content == after.content: return
        await self.log_channel.send(
            embed=self.log_embed("✏️ Message Edited",
                                 f"**Author:** {before.author.mention}\n**Channel:** {before.channel.mention}\n\n**Before:** {before.content}\n**After:** {after.content}")
        )

async def setup(bot):
    await bot.add_cog(Logging(bot))
