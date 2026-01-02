import discord
from discord.ext import commands
from datetime import datetime
import re


BUG_CHANNEL_NAME = "🐞-debug-help"
MILESTONE_CHANNEL_NAME = "🏆・milestones-and-wins"

# in-memory task storage (per guild)
TASKS = {}  # guild_id : [ {id,title,desc,by,assigned,done} ]


class Project(commands.Cog):
    def __init__(self, bot):
        self.bot = bot


    # ============================
    # 🗣️ SAY (STAFF SAFE)
    # ============================
    @commands.has_permissions(manage_messages=True)
    @commands.command()
    async def say(self, ctx, *, text: str):
        # prevent mass pings / abuse
        safe = re.sub(r"(@everyone|@here|<@&\d+>)", "[blocked-mention]", text)

        await ctx.message.delete()
        await ctx.send(safe)


    # ============================
    # 🏆 MILESTONES
    # ============================
    @commands.command()
    async def milestone(self, ctx, *, text: str):
        channel = discord.utils.get(ctx.guild.text_channels, name=MILESTONE_CHANNEL_NAME)
        if not channel:
            return await ctx.reply(f"❌ Milestone channel `{MILESTONE_CHANNEL_NAME}` not found.")

        embed = discord.Embed(
            title="🏆 New Milestone Reached",
            description=text,
            color=0xF1C40F,
            timestamp=datetime.utcnow()
        )
        embed.set_footer(text=f"Logged by {ctx.author}", icon_url=ctx.author.display_avatar.url)

        await channel.send(embed=embed)
        await ctx.reply("🎉 Milestone recorded!")


    # ============================
    # 📌 PROJECT TASK SYSTEM
    # ============================
    def ensure_guild_tasks(self, guild_id: int):
        TASKS.setdefault(guild_id, [])

    @commands.group(invoke_without_command=True)
    async def task(self, ctx):
        await ctx.reply("🧩 Task Commands:\n"
                        "`.task add title | desc`\n"
                        "`.task list`\n"
                        "`.task done <id>`\n"
                        "`.task assign <id> @user`")

    @task.command(name="add")
    async def task_add(self, ctx, *, text: str):
        self.ensure_guild_tasks(ctx.guild.id)

        parts = [p.strip() for p in text.split("|")]
        if len(parts) < 2:
            return await ctx.reply("❌ Format: `.task add title | description`")

        title, desc = parts
        task_list = TASKS[ctx.guild.id]

        task_id = len(task_list) + 1
        task_list.append({
            "id": task_id,
            "title": title,
            "desc": desc,
            "by": str(ctx.author),
            "assigned": None,
            "done": False
        })

        await ctx.reply(f"📝 Task **#{task_id}** created — `{title}`")

    @task.command(name="list")
    async def task_list(self, ctx):
        self.ensure_guild_tasks(ctx.guild.id)
        task_list = TASKS[ctx.guild.id]

        if not task_list:
            return await ctx.reply("📭 No tasks yet.")

        lines = []
        for t in task_list:
            status = "✅ Done" if t["done"] else "🟡 Pending"
            assigned = f"👤 {t['assigned']}" if t["assigned"] else "—"
            lines.append(
                f"**#{t['id']}** — {t['title']} ({status})\n"
                f"↳ {t['desc']}\n"
                f"Assigned: {assigned}\n"
            )

        await ctx.reply("\n".join(lines))

    @task.command(name="done")
    async def task_done(self, ctx, task_id: int):
        self.ensure_guild_tasks(ctx.guild.id)
        task_list = TASKS[ctx.guild.id]

        task = next((t for t in task_list if t["id"] == task_id), None)
        if not task:
            return await ctx.reply("❌ Task not found.")

        task["done"] = True
        await ctx.reply(f"✅ Task **#{task_id}** marked as complete!")

    @task.command(name="assign")
    async def task_assign(self, ctx, task_id: int, member: discord.Member):
        self.ensure_guild_tasks(ctx.guild.id)
        task_list = TASKS[ctx.guild.id]

        task = next((t for t in task_list if t["id"] == task_id), None)
        if not task:
            return await ctx.reply("❌ Task not found.")

        task["assigned"] = str(member)
        await ctx.reply(f"📌 Task **#{task_id}** assigned to **{member.display_name}**")


async def setup(bot):
    existing = bot.get_cog("Project")
    if existing:
        await bot.remove_cog("Project")

    await bot.add_cog(Project(bot))
