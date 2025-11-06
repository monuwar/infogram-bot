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

# === Environment Variables ===
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
SESSION = os.getenv("SESSION")
BOT_TOKEN = os.getenv("BOT_TOKEN")
TIMEZONE = os.getenv("TIMEZONE", "Asia/Dhaka")
BOT_NAME = os.getenv("BOT_NAME", "InfoGram BOT")
DEVELOPER = os.getenv("DEVELOPER", "@Luizzsec")
DESCRIPTION = os.getenv("DESCRIPTION", "A Telegram bot that shows public profile details of any user.")
LANG = os.getenv("LANG", "English")

# === Telethon Client ===
tele_client = TelegramClient(StringSession(SESSION), API_ID, API_HASH)

# === Helper Functions ===
def fmt_name(user_obj):
    first = getattr(user_obj, "first_name", "") or ""
    last = getattr(user_obj, "last_name", "") or ""
    return ((first + (" " + last if last else "")).strip()) or "N/A"


def format_user_card(u):
    """Handles both User and UserFull types safely"""
    user_obj = getattr(u, "user", u)
    tz = pytz.timezone(TIMEZONE)
    now = datetime.now(tz).strftime("%Y-%m-%d %H:%M")

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


# === Handlers ===
async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    try:
        full = await tele_client(GetFullUserRequest(user.id))
        u = getattr(full, "user", full)
    except Exception:
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
        f"📋 *Your Profile Info:*\n\n"
        f"{card}\n\n"
        f"🧠 *How to use:*\n"
        f"• Send a username like `@example` or `t.me/example`\n"
        f"• Or forward a user's message to this bot\n\n"
        f"💻 Developer: {DEVELOPER}\n\n"
        f"⚠️ This bot only displays *public* information available on Telegram."
    )
    await update.message.reply_text(text, parse_mode="Markdown")


async def lookup_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    m = update.message
    if not m:
        return

    text = (m.text or "").strip()
    query = None

    if m.forward_from or m.forward_from_message_id:
        target = m.forward_from or m.forward_from_chat
        if hasattr(target, "id"):
            query = str(target.id)
        else:
            await m.reply_text("Could not determine forwarded user.")
            return
    else:
        if text.startswith("@"):
            query = text[1:].split()[0]
        elif "t.me/" in text:
            query = text.split("t.me/")[-1].split()[0]
        elif text.isdigit():
            query = text
        else:
            return

    try:
        full = await tele_client(GetFullUserRequest(query))
        u = getattr(full, "user", full)
        card = format_user_card(u)
        await m.reply_text(f"📋 *User Information*\n\n{card}", parse_mode="Markdown")
    except Exception as e:
        await m.reply_text(f"❌ Error: {str(e)}")


# === Main Function ===
async def run_bot():
    await tele_client.start()
    print("✅ Telethon client started.")

    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start_handler))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, lookup_handler))

    print("🤖 Telegram Bot running...")
    await application.run_polling(close_loop=False)


if __name__ == "__main__":
    nest_asyncio.apply()
    asyncio.run(run_bot())
