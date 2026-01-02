import discord
from discord.ext import commands, tasks
from discord import app_commands
from datetime import timedelta
import time
import re


# ==========================
# CONFIG
# ==========================
TARGET_CHANNEL_ID = 1419004086216298710   # voting channel
STARBOARD_CHANNEL_NAME = "⭐・top-likes"

UP_EMOJI = "👍"
DOWN_EMOJI = "👎"
UPVOTE_THRESHOLD = 6

SPAM_WINDOW = 5
SPAM_THRESHOLD = 5

BLOCKED_PHRASES = [
    "free nitro",
    "discord.gg/",
    "steam giveaway",
    "crypto scam"
]

REMINDER_MAX_HOURS = 24


# ==========================
# HELPERS
# ==========================
TIME_REGEX = r"^(\d+)(s|m|h|d)$"
def parse_time(string):
    m = re.match(TIME_REGEX, string)
    if not m:
        return None
    v = int(m.group(1))
    return {
        "s": timedelta(seconds=v),
        "m": timedelta(minutes=v),
        "h": timedelta(hours=v),
        "d": timedelta(days=v)
    }[m.group(2)]


# Track which messages already reached starboard
POSTED_MESSAGES = set()


# ==========================
# MAIN COG
# ==========================
class Fun(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        # anti-spam cache
        self.msg_cache = {}

        # temp actions
        self.active_actions = []
        self.check_actions.start()

        # reminders
        self.reminders = []
        self.reminder_loop.start()


    # -------- starboard helpers --------
    def get_starboard(self, guild: discord.Guild):
        return discord.utils.get(guild.text_channels, name=STARBOARD_CHANNEL_NAME)


    # =====================================================
    # 📨 MESSAGE LISTENER (vote auto-react + spam + filter)
    # =====================================================
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or message.guild is None:
            return

        # ---------- VOTE CHANNEL AUTO-REACTIONS ----------
        if message.channel.id == TARGET_CHANNEL_ID:
            try:
                await message.add_reaction(UP_EMOJI)
                await message.add_reaction(DOWN_EMOJI)
            except (discord.Forbidden, discord.HTTPException):
                pass

        # ---------- ANTI-SPAM ----------
        uid = message.author.id
        now = time.time()

        self.msg_cache.setdefault(uid, [])
        self.msg_cache[uid] = [t for t in self.msg_cache[uid] if now - t < SPAM_WINDOW]
        self.msg_cache[uid].append(now)

        if len(self.msg_cache[uid]) >= SPAM_THRESHOLD:
            try:
                await message.author.timeout(
                    discord.utils.utcnow() + timedelta(minutes=5),
                    reason="Auto anti-spam timeout"
                )
            except Exception:
                pass

            await message.channel.send(
                f"⚠️ {message.author.mention} was rate-limited for spamming."
            )

        # ---------- WORD FILTER ----------
        content = message.content.lower()
        for phrase in BLOCKED_PHRASES:
            if phrase in content:
                try:
                    await message.delete()
                except Exception:
                    pass

                await message.channel.send(
                    "⛔ Message blocked — filtered content detected."
                )
                break


    # =====================================================
    # ⭐ HANDLE VOTE REACTIONS → SEND TO STARBOARD
    # =====================================================
    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        if str(payload.emoji) not in (UP_EMOJI, DOWN_EMOJI):
            return

        if payload.channel_id != TARGET_CHANNEL_ID:
            return

        guild = self.bot.get_guild(payload.guild_id)
        channel = guild.get_channel(payload.channel_id)
        message = await channel.fetch_message(payload.message_id)

        if message.author.bot:
            return

        if message.id in POSTED_MESSAGES:
            return

        up_count = 0
        for r in message.reactions:
            if str(r.emoji) == UP_EMOJI:
                up_count = r.count

        if up_count < UPVOTE_THRESHOLD:
            return

        starboard = self.get_starboard(guild)
        if not starboard:
            return

        embed = discord.Embed(
            description=message.content or "(no text)",
            color=0xFFD700
        )
        embed.set_author(
            name=message.author,
            icon_url=message.author.display_avatar.url
        )
        embed.add_field(name="Jump to message", value=f"[Open]({message.jump_url})")
        embed.set_footer(text=f"👍 {up_count} upvotes")

        if message.attachments:
            embed.set_image(url=message.attachments[0].url)

        await starboard.send(embed=embed)

        POSTED_MESSAGES.add(message.id)


    # =====================================================
    # ⏳ TEMP MUTE / TEMP BAN  (PREFIX)
    # =====================================================
    @commands.command()
    @commands.has_permissions(moderate_members=True)
    async def tempmute(self, ctx, member: discord.Member, duration: str, *, reason="No reason"):
        delta = parse_time(duration)
        if not delta:
            return await ctx.reply("❌ Invalid time. Use `10m`, `2h`, `1d`")

        until = discord.utils.utcnow() + delta
        await member.timeout(until, reason=reason)

        self.active_actions.append({
            "user": member.id,
            "guild": ctx.guild.id,
            "until": until,
            "type": "mute"
        })

        await ctx.send(f"🔇 {member.mention} muted for **{duration}** — {reason}")

    @commands.command()
    @commands.has_permissions(ban_members=True)
    async def tempban(self, ctx, member: discord.Member, duration: str, *, reason="No reason"):
        delta = parse_time(duration)
        if not delta:
            return await ctx.reply("❌ Invalid time. Use `10m`, `2h`, `1d`")

        until = discord.utils.utcnow() + delta
        await ctx.guild.ban(member, reason=reason)

        self.active_actions.append({
            "user": member.id,
            "guild": ctx.guild.id,
            "until": until,
            "type": "ban"
        })

        await ctx.send(f"⛔ {member.mention} banned for **{duration}** — {reason}")

    @tasks.loop(seconds=15)
    async def check_actions(self):
        now = discord.utils.utcnow()

        for action in self.active_actions[:]:
            if now >= action["until"]:
                guild = self.bot.get_guild(action["guild"])

                if action["type"] == "mute":
                    user = guild.get_member(action["user"])
                    if user:
                        await user.timeout(None, reason="Temp mute expired")

                elif action["type"] == "ban":
                    try:
                        await guild.unban(discord.Object(id=action["user"]))
                    except Exception:
                        pass

                self.active_actions.remove(action)


    # =====================================================
    # ⏰ REMINDER — PREFIX COMMAND (NEW)
    # =====================================================
    @commands.command(name="remind")
    async def remind_prefix(self, ctx, time_value: str, *, text: str):
        delta = parse_time(time_value)
        if not delta:
            return await ctx.reply("❌ Invalid time. Use `10m`, `1h`, `2d`.")

        if delta > timedelta(hours=REMINDER_MAX_HOURS):
            return await ctx.reply(
                f"❌ Max reminder time is {REMINDER_MAX_HOURS}h."
            )

        remind_at = time.time() + delta.total_seconds()

        self.reminders.append({
            "user": ctx.author.id,
            "guild": ctx.guild.id,
            "channel": ctx.channel.id,
            "time": remind_at,
            "text": text
        })

        await ctx.reply(
            f"⏳ Reminder set for **{time_value}** — `{text}`"
        )


    # =====================================================
    # ⏰ REMINDER — SLASH (still available)
    # =====================================================
    @app_commands.command(name="remind", description="Set a reminder")
    async def remind(self, interaction: discord.Interaction, time_value: str, *, text: str):
        delta = parse_time(time_value)
        if not delta:
            return await interaction.response.send_message(
                "❌ Invalid time. Use `10m`, `1h`, `2d`.",
                ephemeral=True
            )

        if delta > timedelta(hours=REMINDER_MAX_HOURS):
            return await interaction.response.send_message(
                f"❌ Max reminder time is {REMINDER_MAX_HOURS}h.",
                ephemeral=True
            )

        remind_at = time.time() + delta.total_seconds()

        self.reminders.append({
            "user": interaction.user.id,
            "guild": interaction.guild.id,
            "channel": interaction.channel.id,
            "time": remind_at,
            "text": text
        })

        await interaction.response.send_message(
            f"⏳ Reminder set for **{time_value}** — `{text}`"
        )


    @tasks.loop(seconds=10)
    async def reminder_loop(self):
        now = time.time()

        for r in self.reminders[:]:
            if now >= r["time"]:
                guild = self.bot.get_guild(r["guild"])
                channel = guild.get_channel(r["channel"])

                await channel.send(
                    f"🔔 <@{r['user']}> **Reminder:** {r['text']}"
                )

                self.reminders.remove(r)


async def setup(bot):
    existing = bot.get_cog("Fun")
    if existing:
        await bot.remove_cog("Fun")

    await bot.add_cog(Fun(bot))
