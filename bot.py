# bot.py
import os
import asyncio
from datetime import datetime
import pytz
import nest_asyncio

from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.tl.functions.users import GetFullUserRequest

from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# --- ENV ---
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
SESSION = os.getenv("SESSION")
BOT_TOKEN = os.getenv("BOT_TOKEN")  # BotFather token
TIMEZONE = os.getenv("TIMEZONE", "Asia/Dhaka")
BOT_NAME = os.getenv("BOT_NAME", "InfoGram BOT")
DEVELOPER = os.getenv("DEVELOPER", "@Luizzsec")
DESCRIPTION = os.getenv("DESCRIPTION", "A Telegram bot that shows public profile details of any user.")
LANG = os.getenv("LANG", "English")

# --- Telethon client for lookups ---
tele_client = TelegramClient(StringSession(SESSION), API_ID, API_HASH)

# --- Helpers ---
def fmt_name(user_obj):
    first = getattr(user_obj, "first_name", "") or ""
    last = getattr(user_obj, "last_name", "") or ""
    return ((first + (" " + last if last else "")).strip()) or "N/A"

def format_user_card(u):
    """
    Return nicely formatted profile card string for a Telethon user object `u`.
    Works whether `u` is a User or a UserFull (safely extracts the inner User).
    """
    # if u is a UserFull (has attribute 'user'), use that inner user object
    user_obj = getattr(u, "user", u)

    tz = pytz.timezone(TIMEZONE)
    now = datetime.now(tz).strftime("%Y-%m-%d %H:%M")

    # safe attribute getters from the actual user object
    uid = getattr(user_obj, "id", "N/A")
    username = getattr(user_obj, "username", None)
    photo = getattr(user_obj, "photo", None)
    premium = "Yes" if getattr(user_obj, "premium", False) else "No"
    scam = "Yes" if getattr(user_obj, "scam", False) else "No"
    fake = "Yes" if getattr(user_obj, "fake", False) else "No"
    dc = getattr(getattr(user_obj, "photo", None), "dc_id", "N/A")

    status = "Hidden"
    try:
        st = getattr(user_obj, "status", None)
        status = type(st).__name__ if st else "Hidden"
    except Exception:
        status = "Hidden"

    # Registered On / Account Age: NOT reliably available via Telegram API -> N/A / best-effort
    registered_on = "N/A"
    account_age = "N/A"

    card_lines = [
        f"ID: `{uid}`",
        f"Name: {fmt_name(user_obj)}",
        f"Username: @{username if username else 'Not set'}",
        f"Premium: {premium}",
        f"Fake Label: {fake}",
        f"Scam Label: {scam}",
        f"Photos: {'Set' if photo else 'No'}",
        f"Status: {status}",
        f"DC: {dc}",
        f"Account Age: {account_age}",
        f"Registered On: {registered_on}",
        f"Language: {LANG}",
        f"Date: {now} ({TIMEZONE})",
    ]
    return "\n".join(f"- {line}" for line in card_lines)

# --- Bot handlers (python-telegram-bot async) ---
async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    # Try to get more details about the requester via telethon (best-effort)
    try:
        full = await tele_client(GetFullUserRequest(user.id))
        u = getattr(full, "user", full)
    except Exception:
        # fallback to basic info from the incoming update
        class Simple:
            id = user.id
            first_name = user.first_name
            last_name = getattr(user, "last_name", None)
            username = user.username
            photo = None
        u = Simple()

    card = format_user_card(u)

    text = (
        f"👋 Hello {user.first_name or 'User'}!\n\n"
        f"Welcome to *{BOT_NAME}* 🕵️‍♂️\n\n"
        f"📋 *User Information*\n\n"
        f"{card}\n\n"
        f"🧠 *How to use:*\n"
        f"• Send a username like `@example` or `t.me/example`\n"
        f"• Or forward a user's message to this bot\n\n"
        f"💻 Developer: {DEVELOPER}\n\n"
        f"⚠️ This bot only displays *public* information available on Telegram."
    )

    # Help text included in start message as requested
    await update.message.reply_text(text, parse_mode="Markdown")

async def lookup_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    m = update.message
    if not m:
        return
    text = (m.text or "").strip()

    # handle forwarded message (prefer forwarded sender)
    query = None
    if m.forward_from or m.forward_from_message_id:
        target = m.forward_from or m.forward_from_chat
        if hasattr(target, "id"):
            query = str(target.id)
        else:
            await m.reply_text("Could not determine forwarded user.")
            return
    else:
        # Accept @username or t.me/username or numeric ID
        if text.startswith("@"):
            query = text[1:].split()[0]
        elif "t.me/" in text:
            query = text.split("t.me/")[-1].split()[0]
        elif text.isdigit():
            query = text
        else:
            # ignore other messages
            return

    # --- perform telethon lookup (inside async handler) ---
    try:
        full = await tele_client(GetFullUserRequest(query))
        u = getattr(full, "user", full)

        card = format_user_card(u)
        await m.reply_text(f"📋 *User Information*\n\n{card}", parse_mode="Markdown")
    except Exception as e:
        # send a readable error message (don't leak internal stack)
        await m.reply_text(f"❌ Error: {str(e)}")

# --- main: start telethon and PTB application ---
async def main():
    # start telethon
    await tele_client.start()
    print("Telethon client started.")

    # start python-telegram-bot Application
    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start_handler))
    # message handler: text messages (excluding commands)
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), lookup_handler))

    print("Starting Telegram Bot (Bot API)...")
    # run polling (async)
    await application.run_polling()

if __name__ == "__main__":
    # prevent "Cannot close a running event loop" on hosting platforms
    nest_asyncio.apply()
    asyncio.get_event_loop().run_until_complete(main())
