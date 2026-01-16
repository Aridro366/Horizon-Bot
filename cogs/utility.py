import discord
from discord.ext import commands
import time
from datetime import timedelta

class Utility(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.start_time = time.time()

    # ---------- GLOBAL STAFF CHECK ----------

    async def cog_check(self, ctx: commands.Context):
        if not ctx.author.guild_permissions.manage_guild:
            await ctx.send("❌ Staff only command.")
            return False
        return True

    # ---------- HELPERS ----------

    def get_uptime(self) -> str:
        return str(timedelta(seconds=int(time.time() - self.start_time)))

    # ---------- BASIC ----------

    @commands.command(name="ping")
    async def ping(self, ctx: commands.Context):
        await ctx.send(
            embed=discord.Embed(
                title="🏓 Pong",
                description=f"Latency: `{round(self.bot.latency * 1000)} ms`",
                color=discord.Color.green()
            )
        )

    @commands.command(name="bot_info")
    async def info_cmd(self, ctx: commands.Context):
        embed = discord.Embed(
            title="🤖 Bot Information",
            color=discord.Color.blurple()
        )
        embed.add_field(name="Uptime", value=self.get_uptime(), inline=False)
        embed.add_field(name="Latency", value=f"{round(self.bot.latency * 1000)} ms", inline=False)
        embed.add_field(name="Servers", value=len(self.bot.guilds), inline=True)
        embed.add_field(
            name="Users",
            value=len({m.id for g in self.bot.guilds for m in g.members}),
            inline=True
        )
        embed.set_footer(text=f"Bot ID: {self.bot.user.id}")
        await ctx.send(embed=embed)

    @commands.command(name="bot_status")
    async def status_cmd(self, ctx: commands.Context):
        perms = ctx.guild.me.guild_permissions

        embed = discord.Embed(
            title="🧠 Bot Status",
            color=discord.Color.teal()
        )
        embed.add_field(name="Online", value="✅ Yes", inline=True)
        embed.add_field(name="Manage Roles", value="✅" if perms.manage_roles else "❌", inline=True)
        embed.add_field(name="Manage Threads", value="✅" if perms.manage_threads else "❌", inline=True)
        embed.add_field(name="Latency", value=f"{round(self.bot.latency * 1000)} ms", inline=True)

        await ctx.send(embed=embed)

    # ---------- USER ----------

    @commands.command(name="user_info")
    async def user_info(self, ctx: commands.Context, member: discord.Member | None = None):
        member = member or ctx.author
        roles = ", ".join(r.mention for r in member.roles if r.name != "@everyone") or "None"

        embed = discord.Embed(
            title="👤 User Information",
            color=discord.Color.orange()
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.add_field(name="User", value=f"{member} ({member.id})", inline=False)
        embed.add_field(
            name="Account Created",
            value=member.created_at.strftime("%d %b %Y"),
            inline=True
        )
        embed.add_field(
            name="Joined Server",
            value=member.joined_at.strftime("%d %b %Y"),
            inline=True
        )
        embed.add_field(name="Roles", value=roles, inline=False)

        await ctx.send(embed=embed)

    # ---------- ROLE MANAGEMENT ----------

    @commands.command(name="add_role")
    async def add_role(self, ctx: commands.Context, member: discord.Member, role: discord.Role):
        if role >= ctx.author.top_role:
            await ctx.send("❌ You cannot assign this role.")
            return

        await member.add_roles(role, reason=f"Added by {ctx.author}")
        await ctx.send(
            embed=discord.Embed(
                description=f"✅ Added {role.mention} to {member.mention}",
                color=discord.Color.green()
            )
        )

    @commands.command(name="remove_role")
    async def remove_role(self, ctx: commands.Context, member: discord.Member, role: discord.Role):
        if role >= ctx.author.top_role:
            await ctx.send("❌ You cannot remove this role.")
            return

        await member.remove_roles(role, reason=f"Removed by {ctx.author}")
        await ctx.send(
            embed=discord.Embed(
                description=f"🗑 Removed {role.mention} from {member.mention}",
                color=discord.Color.red()
            )
        )

    # ---------- HELP ----------

    @commands.command(name="util_help")
    async def util_help(self, ctx: commands.Context):
        embed = discord.Embed(
            title="🛠 Utility Commands (Staff Only)",
            color=discord.Color.dark_gray()
        )
        embed.description = (
            "`.ping` – Bot latency\n"
            "`.bot_info` – Bot stats & uptime\n"
            "`.bot_status` – Bot permissions\n"
            "`.user_info [user]` – User info\n"
            "`.add_role @user @role` – Add role\n"
            "`.remove_role @user @role` – Remove role"
        )
        await ctx.send(embed=embed)
        
@commands.command(name="say")
async def say(self, ctx: commands.Context, *, message: str):
    if not ctx.author.guild_permissions.manage_guild:
        await ctx.send("❌ Staff only command.")
        return

    # Prevent mass mentions
    if "@everyone" in message or "@here" in message:
        await ctx.send("❌ Mass mentions are not allowed.", delete_after=5)
        return

    await ctx.message.delete()
    await ctx.send(message)


# ---------- SETUP ----------

async def setup(bot):
    await bot.add_cog(Utility(bot))
