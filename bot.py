import os
import asyncio
from datetime import datetime
import pytz
from telethon import TelegramClient, events
from telethon.sessions import StringSession
from telethon.tl.functions.users import GetFullUserRequest

# --- Environment Variables ---
api_id = int(os.getenv("API_ID"))
api_hash = os.getenv("API_HASH")
session = os.getenv("SESSION")
timezone = os.getenv("TIMEZONE", "Asia/Dhaka")
bot_name = os.getenv("BOT_NAME", "InfoGram BOT")
developer = os.getenv("DEVELOPER", "@Luizzsec")
description = os.getenv("DESCRIPTION", "A Telegram bot that shows public profile details of any user.")

# --- Initialize client ---
client = TelegramClient(StringSession(session), api_id, api_hash)

# --- /start Command ---
@client.on(events.NewMessage(pattern='/start'))
async def start(event):
    user = await event.get_sender()
    tz = pytz.timezone(timezone)
    now = datetime.now(tz).strftime("%Y-%m-%d %H:%M")

    info = f"""
👋 Hello {user.first_name or 'User'}!
Welcome to **{bot_name}** 🕵️‍♂️

📋 **Your Profile Info:**
- ID: `{user.id}`
- Name: {user.first_name or ''} {user.last_name or ''}
- Username: @{user.username or 'Not set'}
- Premium: {'Yes' if getattr(user, 'premium', False) else 'No'}
- Language: English
- Date: {now}
- Photos: {'Set' if user.photo else 'No'}
- Scam Label: {'Yes' if getattr(user, 'scam', False) else 'No'}
- Fake Label: {'Yes' if getattr(user, 'fake', False) else 'No'}

🧠 **How to use:**
• Send a username like `@example` or `t.me/example`
• Or forward a user’s message to this chat

💻 Developer: {developer}
"""
    await event.respond(info)

# --- /help Command ---
@client.on(events.NewMessage(pattern='/help'))
async def help_cmd(event):
    text = f"""
📖 **Help Menu**

Usage:
• Send @username or t.me/username
• Or forward a user's message

I will show all public information of that Telegram account.

💡 Tips:
- Some info may be hidden due to privacy settings.
- This bot does NOT store or share any data.

👨‍💻 Developer: {developer}
"""
    await event.respond(text)

# --- /about Command ---
@client.on(events.NewMessage(pattern='/about'))
async def about(event):
    text = f"""
ℹ️ **About This Bot**

Name: {bot_name}
Developer: {developer}
Language: English
Timezone: {timezone}

Description:
{description}

⚠️ This bot only shows **public information** from Telegram.
It does not access any private data or violate privacy.

"""
    await event.respond(text)

# --- Username Lookup ---
@client.on(events.NewMessage)
async def lookup(event):
    text = event.text.strip()
    if not text.startswith("@") and "t.me/" not in text:
        return

    username = text.replace("t.me/", "").replace("@", "")
    try:
        full = await client(GetFullUserRequest(username))
        u = full.user

        info = f"""
📋 **User Information**

- ID: `{u.id}`
- Name: {u.first_name or ''} {u.last_name or ''}
- Username: @{u.username or 'Not set'}
- Premium: {'Yes' if getattr(u, 'premium', False) else 'No'}
- Scam Label: {'Yes' if getattr(u, 'scam', False) else 'No'}
- Fake Label: {'Yes' if getattr(u, 'fake', False) else 'No'}
- Photos: {'Set' if u.photo else 'No'}
- Status: {type(u.status).__name__ if hasattr(u, 'status') else 'Hidden'}

✅ Lookup complete.
"""
        await event.respond(info)
    except Exception as e:
        await event.respond(f"❌ Error: {str(e)}")

print("🚀 InfoGram BOT is now running...")
client.start()
client.run_until_disconnected()
