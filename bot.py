# bot.py
import os
import asyncio
from datetime import datetime
import pytz

from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.tl.functions.users import GetFullUserRequest

from telegram import __version__ as PTB_VERS
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Environment
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
SESSION = os.getenv("SESSION")
BOT_TOKEN = os.getenv("BOT_TOKEN")   # BotFather token
TIMEZONE = os.getenv("TIMEZONE", "Asia/Dhaka")
BOT_NAME = os.getenv("BOT_NAME", "InfoGram BOT")
DEVELOPER = os.getenv("DEVELOPER", "@Luizzsec")
DESCRIPTION = os.getenv("DESCRIPTION", "A Telegram bot that shows public profile details of any user.")
LANG = os.getenv("LANG", "English")

# Initialize Telethon client (for lookups)
tele_client = TelegramClient(StringSession(SESSION), API_ID, API_HASH)

# Helper: format user info (from telethon user object)
def format_user_card(u, tz_name=TIMEZONE):
    # Created & DC & Account Age — best-effort (some fields may be missing)
    tz = pytz.timezone(tz_name)
    now = datetime.now(tz)
    # account age: Telethon doesn't expose created date reliably => show N/A if not found
    created = getattr(u, "created", None) or None
    created_str = created.strftime("%Y-%m") if created else "N/A"
    # DC: telethon user.photo.dc_id if available
    dc = getattr(u.photo, "dc_id", "N/A") if u.photo else "N/A"

    # Status name
    status = "Hidden"
    try:
        status = type(u.status).__name__ if hasattr(u, "status") else "Hidden"
    except Exception:
        status = "Hidden"

    info = [
        f"- ID: `{u.id}`",
        f"- Name: { (u.first_name or '') + (' ' + (u.last_name or '') if u.last_name else '') }",
        f"- DC: {dc}",
        f"- Created: {created_str}",
        f"- Username: @{u.username or 'Not set'}",
        f"- Premium: {'Yes' if getattr(u, 'premium', False) else 'Inactive'}",
        f"- Language: {LANG}",
        f"- Date: {now.strftime('%Y-%m-%d %H:%M')} ({tz_name})",
        f"- Photos: {'Set' if u.photo else 'No'}",
        f"- Status: {status}",
        f"- Scam Label: {'Yes' if getattr(u, 'scam', False) else 'No'}",
        f"- Fake Label: {'Yes' if getattr(u, 'fake', False) else 'No'}",
        f"- Paid Message: {'Yes' if getattr(u, 'paid_subscribe', False) else 'No'}"  # best-effort
    ]
    return "\n".join(info)

# Bot command handlers (python-telegram-bot async handlers)
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    # Get Telethon info for the requester (if available)
    try:
        # Telethon requires numeric id or username; use user.id (telegram numeric id)
        full = await tele_client(GetFullUserRequest(user.id))
        u = full.user
        card = format_user_card(u)
    except Exception:
        # If Telethon can't fetch (e.g., privacy), show limited info
        card = f"- ID: `{user.id}`\n- Name: {user.full_name}\n- Username: @{user.username or 'Not set'}\n- (Detailed info may be restricted)"

    text = (
        f"👋 Hello {user.first_name or 'User'}!\n\n"
        f"Welcome to *{BOT_NAME}* 🕵️‍♂️\n\n"
        f"📋 *Your Profile Info:*\n{card}\n\n"
        f"🧠 *How to use:*\n"
        f"• Send a username like `@example` or `t.me/example`\n"
        f"• Or forward a user's message to this bot\n\n"
        f"💻 Developer: {DEVELOPER}"
    )
    await update.message.reply_text(text, parse_mode="Markdown")

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "📖 *Help Menu*\n\n"
        "Usage:\n"
        "• Send `@username` or `t.me/username`\n"
        "• Or forward a user's message\n\n"
        "I will show all *public* information available for that account.\n\n"
        f"Developer: {DEVELOPER}"
    )
    await update.message.reply_text(text, parse_mode="Markdown")

async def about(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        f"ℹ️ *About This Bot*\n\n"
        f"Name: {BOT_NAME}\n"
        f"Developer: {DEVELOPER}\n"
        f"Language: {LANG}\n"
        f"Timezone: {TIMEZONE}\n\n"
        f"Description: {DESCRIPTION}\n\n"
        "⚠️ This bot only shows *public* information from Telegram."
    )
    await update.message.reply_text(text, parse_mode="Markdown")

async def lookup_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    m = update.message
    text = (m.text or "").strip()
    # If forwarded message: lookup forwarded sender
    if m.forward_from or m.forward_from_message_id:
        target = m.forward_from or m.forward_from_chat
        # for forwarded internal complexity, attempt telethon by id if available
        if hasattr(target, "id"):
            query = str(target.id)
        else:
            await m.reply_text("Could not determine forwarded user.")
            return
    else:
        # Accept @username or t.me/username or numeric ID
        if text.startswith("@"):
            query = text[1:]
        elif "t.me/" in text:
            query = text.split("t.me/")[-1].split()[0]
        elif text.isdigit():
            query = text
        else:
            # ignore other messages
            return

    # perform telethon lookup
    try:
        full = await tele_client(GetFullUserRequest(query))
        u = full.user
        card = format_user_card(u)
        await m.reply_text(f"📋 *User Information*\n\n{card}", parse_mode="Markdown")
    except Exception as e:
        await m.reply_text(f"❌ Error: {e}")

async def main():
    # start telethon
    await tele_client.start()
    print("Telethon client started.")

    # start PTB (Application)
    application = Application.builder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_cmd))
    application.add_handler(CommandHandler("about", about))
    # message handler for lookups (text starting with @ or t.me or forwarded)
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), lookup_handler))

    print("Starting Telegram Bot (Bot API)...")
    # run polling (will keep running)
    await application.run_polling()

if __name__ == "__main__":
    import nest_asyncio
    nest_asyncio.apply()
    asyncio.get_event_loop().run_until_complete(main())
