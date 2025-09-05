# -*- coding: utf-8 -*-
import subprocess
import sys
import os
import importlib
import asyncio
import time
import random
import json
import logging
import threading
from flask import Flask, request
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    CommandHandler,
    MessageHandler,
    filters,
)

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Configuration
BOT_TOKEN = "8357978062:AAFFiCH_jsnynvnhTWmoH3SSYburEekjWSI"
OWNER_ID = os.getenv("OWNER_ID")
if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN environment variable is missing.")

# In-memory data and limits
SUDO_USERS = {OWNER_ID}
is_raiding = False
MAX_SPAM_LIMIT = 100000
MAX_RAID_LIMIT = 100000
MAX_SHAYARI_LIMIT = 20

# Load persisted data
def load_data():
    global SUDO_USERS, ABUSE_WORDS
    try:
        with open("bot_data.json", "r") as f:
            data = json.load(f)
            SUDO_USERS = set(data.get("sudo_users", [OWNER_ID]))
            ABUSE_WORDS = data.get("abuse_words", ABUSE_WORDS)
    except FileNotFoundError:
        pass

# Save data to file
def save_data():
    try:
        with open("bot_data.json", "w") as f:
            json.dump({"sudo_users": list(SUDO_USERS), "abuse_words": ABUSE_WORDS}, f)
    except Exception as e:
        logger.error(f"Failed to save data: {str(e)}")

# Check sudo
def is_sudo(user_id):
    return user_id in SUDO_USERS

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [
            InlineKeyboardButton("☆𝗖𝗛𝗔𝗡𝗡𝗘𝗟☆", url="https://t.me/ll_YOUR_PANDA"),
            InlineKeyboardButton("☆𝗦𝗨𝗣𝗣𝗢𝗥𝗧☆", url="https://t.me/RADHIKA_YIIOO"),
        ],
        [InlineKeyboardButton("☆_M_Y 𝗟𝗢𝗥𝗗☆", url="tg://openmessage?user_id=7048854228")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    caption = (
        """╭─━─━─━─✧✦✧─━─━─━─╮
🔹 𝙄 𝘼𝙈 𝙏𝙃𝙀 𝙁𝘼𝙎𝙏𝙀𝙎𝙏 𝙎𝙋𝘼𝙈 & 𝙍𝘼𝙄𝘿 𝘽𝙊𝙏 🔹
╰─━─━─━─✧✦✧─━─━─━─╯
➤ X𝐁𝐎𝐓𝐒 𝐕𝐄𝐑𝐒𝐈𝐎𝐍 : M3.3
➤ 𝙋𝙔𝙏𝙃𝙊𝙉 𝙑𝙀𝙍𝙎𝙄𝙊𝙉 : 3.11.3
➤ 𝙏𝙀𝙇𝙀𝙏𝙃𝙊𝙉 𝙑𝙀𝙍𝙎𝙄𝙊𝙉 : 1.40.0
━━━━━━━━━━━━━━━━━━━━━
⚡ POWERED BY » <a href='tg://openmessage?user_id=7048854228'>𓆩꯭𝐀꯭𝛅꯭𓆪꯭ ꯭ꭙ꯭ ꯭𝐒꯭ᴜ꯭ᴘ꯭ʀ꯭፝֠֩ᴇ꯭ᴍ꯭ᴇ꯭ ꯭⌯ ꯭ᴋ꯭꯭𝛊꯭፝֟͠𝛈꯭ɢ꯭💀꯭ ⟪𝑻𝑨𝑩𝑨𝑯𝑰 ⟫</a>
/help ᴄʜᴇᴄᴋ ᴛʜᴇ ʙᴏᴛ ᴄᴏᴍᴍᴀɴᴄs"""
    )

    await update.message.reply_photo(
        photo="https://t.me/METHODS_YI/137",
        caption=caption,
        reply_markup=reply_markup,
        parse_mode=ParseMode.HTML,
    )

# /help
async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_sudo(update.message.from_user.id):
        return await update.message.reply_text("🚫 You are not a sudo user.")
    await update.message.reply_text(
        """┏━━ 📜 BOT COMMANDS ━━┓

             🔹 SPAM / RAID
               • /spam <text> <count>
               • /raid <@user> <count>
               • /stopraid
               • .raid (reply to user) <count>

             🔹 ADMIN CONTROLS
               • /addabuse <word>
               • /addsudo <user_id>
               • /removesudo <user_id>
               • /sudo  (list sudo users)

             🔹 UTILITIES
               • /ping  (check bot is alive)

      ┗━━━━━━━━━━━━━━━━━━━┛"""
    )

async def raid_loop(message, mention):
    global is_raiding
    while is_raiding:
        await message.reply_html(f"{mention} {random.choice(ABUSE_WORDS)}")
        await asyncio.sleep(0.5)  # Rate limit to avoid flooding

async def dot_raid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global is_raiding
    if not update.message.reply_to_message:
        return await update.message.reply_text("❗Reply to a user with .raid <count> or .raid nonstop.")
    args = update.message.text.split()
    user = update.message.reply_to_message.from_user
    mention = user.mention_html()
    if len(args) >= 2 and args[1].lower() == "nonstop":
        is_raiding = True
        await update.message.reply_text("🚀 Starting nonstop raid...")
        asyncio.create_task(raid_loop(update.message, mention))
    else:
        try:
            count = int(args[1])
            messages = [f"{mention} {random.choice(ABUSE_WORDS)}" for _ in range(count)]
            await asyncio.gather(*(update.message.reply_html(msg) for msg in messages))
        except:
            await update.message.reply_text("❗Count must be number or 'nonstop'.")

# /ping
async def cmd_ping(update: Update, context: ContextTypes.DEFAULT_TYPE):
    start = time.time()
    msg = await update.message.reply_text("⏱ ᴅᴀᴅʏ ɪs ᴄᴏᴍɪɴɢ...")
    latency = (time.time() - start) * 1000
    await msg.edit_text(f"🏓 Pong: `{latency:.2f} ms`𓆩꯭𝐀꯭𝛅꯭𓆪꯭ ꯭ꭙ꯭ ꯭𝐒꯭ᴜ꯭ᴘ꯭ʀ꯭፝֠֩ᴇ꯭ᴍ꯭ᴇ꯭ ꯭⌯ ꯭ᴋ꯭꯭𝛊꯭፝֟͠𝛈꯭ɢ꯭💀꯭ ⟪𝑻𝑨𝑩𝑨𝑯𝑰 ⟫\n\n ɪs ʜᴇʀᴇ ᴛᴏ ʙᴏʟᴏ ᴋɪsᴋᴏ ᴘᴀʟᴇɴᴀ ʜᴀɪ 🤡", parse_mode=ParseMode.MARKDOWN)

# /spam
async def cmd_spam(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_sudo(update.message.from_user.id):
        return await update.message.reply_text("🚫 You are not a sudo user.")
    if len(context.args) < 2:
        return await update.message.reply_text("❗Usage: /spam <text> <count>")
    try:
        count = int(context.args[-1])
        if not (0 < count <= MAX_SPAM_LIMIT):
            return await update.message.reply_text("🚫 Limit is 1 to 20.")
        text = " ".join(context.args[:-1])
        await asyncio.gather(*(update.message.reply_text(text) for _ in range(count)))
    except ValueError:
        await update.message.reply_text("❗Count must be a number.")

# /raid
async def cmd_raid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_sudo(update.message.from_user.id):
        return await update.message.reply_text("🚫 You are not a sudo user.")
    if len(context.args) < 2:
        return await update.message.reply_text("❗Usage: /raid <@username> <count>")
    username = context.args[0] if context.args[0].startswith("@") else f"@{context.args[0]}"
    try:
        count = int(context.args[1])
        if not (0 < count <= MAX_RAID_LIMIT):
            return await update.message.reply_text("🚫 Limit is 1 to 15.")
        messages = [f"{username} {random.choice(ABUSE_WORDS)}" for _ in range(count)]
        await asyncio.gather(*(update.message.reply_text(msg) for msg in messages))
    except ValueError:
        await update.message.reply_text("❗Count must be a number.")

# /stopraid
async def cmd_stopraid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global is_raiding
    if not is_sudo(update.message.from_user.id):
        return await update.message.reply_text("🚫 You are not a sudo user.")
    is_raiding = False
    await update.message.reply_text("🛑 Raid stopped.")

# /addabuse
async def cmd_addabuse(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_sudo(update.message.from_user.id):
        return await update.message.reply_text("🚫 You are not a sudo user.")
    if len(context.args) < 1:
        return await update.message.reply_text("❗Usage: /addabuse <word>")
    word = context.args[0].lower()
    if word in ABUSE_WORDS:
        return await update.message.reply_text("⚠️ Already exists.")
    ABUSE_WORDS.append(word)
    save_data()
    await update.message.reply_text(f"✅ Added: {word}")

# /addsudo
async def cmd_addsudo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id != OWNER_ID:
        return await update.message.reply_text("🚫 Only owner can use this.")
    if len(context.args) < 1:
        return await update.message.reply_text("❗Usage: /addsudo <user_id>")
    try:
        uid = int(context.args[0])
        SUDO_USERS.add(uid)
        save_data()
        await update.message.reply_text(f"✅ Added sudo: {uid}")
    except:
        await update.message.reply_text("❗Invalid user ID.")

# /removesudo
async def cmd_removesudo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id != OWNER_ID:
        return await update.message.reply_text("🚫 Only owner can use this.")
    if len(context.args) < 1:
        return await update.message.reply_text("❗Usage: /removesudo <user_id>")
    try:
        uid = int(context.args[0])
        SUDO_USERS.discard(uid)
        save_data()
        await update.message.reply_text(f"✅ Removed sudo: {uid}")
    except:
        await update.message.reply_text("❗Invalid user ID.")

# /sudo
async def cmd_listsudo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id != OWNER_ID:
        return await update.message.reply_text("🚫 Only owner can use this.")
    await update.message.reply_text("👑 Sudo Users:\n" + "\n".join(map(str, SUDO_USERS)))

# Initialize Telegram application
application = ApplicationBuilder().token(BOT_TOKEN).build()

# Register handlers
application.add_handler(CommandHandler("start", cmd_start))
application.add_handler(CommandHandler("help", cmd_help))
application.add_handler(CommandHandler("ping", cmd_ping))
application.add_handler(CommandHandler("spam", cmd_spam))
application.add_handler(CommandHandler("raid", cmd_raid))
application.add_handler(CommandHandler("stopraid", cmd_stopraid))
application.add_handler(CommandHandler("addabuse", cmd_addabuse))
application.add_handler(CommandHandler("addsudo", cmd_addsudo))
application.add_handler(CommandHandler("removesudo", cmd_removesudo))
application.add_handler(CommandHandler("sudo", cmd_listsudo))
application.add_handler(MessageHandler(filters.TEXT & filters.Regex(r"^\.raid(\s|$)"), dot_raid))

# Flask app
flask_app = Flask(__name__)

@flask_app.route('/webhook', methods=['GET', 'POST'])
def webhook():
    if request.method == 'POST':
        try:
            update_json = request.get_json(force=True)
            update = Update.de_json(update_json, application.bot)
            # Run the processing in the async loop
            asyncio.run_coroutine_threadsafe(application.process_update(update), async_loop)
            return 'OK', 200
        except Exception as e:
            logger.error(f"Error processing update: {e}")
            return 'Error', 500
    return 'OK', 200

# Global async loop
async_loop = None

def start_async_loop():
    global async_loop
    async_loop = asyncio.new_event_loop()
    asyncio.set_event_loop(async_loop)
    async_loop.run_forever()

if __name__ == "__main__":
    load_data()
    logger.info("Bot starting...")

    # Start the async loop in a separate thread
    thread = threading.Thread(target=start_async_loop)
    thread.start()

    # Wait a bit for the loop to start
    time.sleep(1)

    # Set webhook if WEBHOOK_URL is provided
    WEBHOOK_URL = os.environ.get('WEBHOOK_URL')
    if WEBHOOK_URL:
        webhook_url = WEBHOOK_URL + '/webhook'
        set_coro = application.bot.set_webhook(webhook_url)
        future = asyncio.run_coroutine_threadsafe(set_coro, async_loop)
        try:
            future.result()  # Wait for set_webhook to complete
            logger.info(f"Webhook set to {webhook_url}")
        except Exception as e:
            logger.error(f"Failed to set webhook: {e}")

    print("✅ Bot running...")
    port = int(os.environ.get('PORT', 5000))
    flask_app.run(host='0.0.0.0', port=port)
