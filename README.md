🤖 Horizon 2.0 — Developer Community Discord Bot

Horizon 2.0 is a feature-rich Discord bot designed specifically for developer communities.
It focuses on structured discussions, staff workflows, community feedback, and clean moderation UX — without spammy or gimmicky systems.

✨ Core Features
🧠 Community-Focused

Structured Suggestion System with voting & staff review

Clean community announcements

Polls, events, highlights, and reviews

Designed for developer collaboration, not noise

🛡️ Staff-First Design

Staff-only controls where required

Private staff threads for sensitive actions

Clear separation between public interaction and moderation

⚡ Hybrid Command Support

Slash commands (/) for modern interactions

Prefix commands (.) for fast staff actions

📌 Suggestion System

A full feedback workflow inspired by large professional servers.

How it works

Members submit suggestions

Community votes publicly

Staff review privately

Final decision is posted cleanly

Features

Public voting (Approve / Reject)

Vote count tracking

Vote breakdown view

Private staff review thread

Staff-only Accept / Deny

Reasoned rejection support

Automatic status update

Command
/suggest <suggestion>

🛠 Staff Prefix Commands (.)

All prefix commands are staff-only.

🔧 Utility & Bot Management
.ping

Checks the bot’s current latency and responsiveness.

.bot_info

Displays bot uptime, latency, server count, and user count.

.bot_status

Shows the bot’s operational status and important permissions.

.user_info [@user]

Displays detailed information about a user (account age, join date, roles).

🎭 Role Management
.add_role @user @role

Assigns a role to a user safely (permission-checked).

.remove_role @user @role

Removes a role from a user safely (permission-checked).

🗣️ Message Control
.say <message>

Makes the bot send a message on behalf of staff.
(The original command message is deleted automatically.)

📋 Help
.util_help

Shows a list of all available staff prefix commands.


🔐 Permissions Required

The bot requires the following permissions to function correctly:
View Channels
Send Messages
Manage Roles
Create Threads
Msnage Threads
Send Messages in Threads
Additionally, Message Content Intent must be enabled for prefix commands.

⚙️ Configuration
.env
DISCORD_TOKEN=your_bot_token
GUILD_ID=your_server_id   # optional but recommended

config.json
{
  "staff_role_id": 123456789012345678,
  "suggestion_channel_id": 987654321098765432
}

🚀 Getting Started

Install dependencies
=
pip install -r requirements.txt
Configure .env and config.json
Start the bot
python main.py


Use /suggest or staff prefix commands

🧩 Design Philosophy

No XP grinding
No spam automation
No fake engagement systems
Clean UX over flashy features
Built for real developer communities

🛣️ Future-Ready

Horizon 2.0 is structured to easily support:

Moderation audit logs
Knowledge bases
Project collaboration boards

📜 License
for private use , no copy and reuse..