# -*- coding: utf-8 -*-
from aiohttp import web
import signal
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
WEBHOOK_URL = "https://panuspambothh.onrender.com"
BOT_TOKEN = "8357978062:AAFSgY1JFtoIjpwmh2juWvojfaMwg2rlMhM"
OWNER_ID = "7450385463"
PORT = "10000"
if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN environment variable is missing.")

# In-memory data and limits
SUDO_USERS = {OWNER_ID}
is_raiding = False
MAX_SPAM_LIMIT = 100000
MAX_RAID_LIMIT = 100000
MAX_SHAYARI_LIMIT = 20
ABUSE_WORDS = [
    "MADARCHOD TERI MAA KI CHUT ME GHUTKA KHAAKE THOOK DUNGA 🤣🤣",
    "TERE BEHEN K CHUT ME CHAKU DAAL KAR CHUT KA KHOON KAR DUGA",
    "TERI VAHEEN NHI HAI KYA? 9 MAHINE RUK SAGI VAHEEN DETA HU 🤣🤣🤩",
    "TERI MAA K BHOSDE ME AEROPLANEPARK KARKE UDAAN BHAR DUGA ✈️🛫",
    "TERI MAA KI CHUT ME SUTLI BOMB FOD DUNGA TERI MAA KI JHAATE JAL KE KHAAK HO JAYEGI💣",
    "TERI MAAKI CHUT ME SCOOTER DAAL DUGA👅",
    "TERE BEHEN K CHUT ME CHAKU DAAL KAR CHUT KA KHOON KAR DUGA",
    "TERE BEHEN K CHUT ME CHAKU DAAL KAR CHUT KA KHOON KAR DUGA",
    "TERI MAA KI CHUT KAKTE 🤱 GALI KE KUTTO 🦮 ME BAAT DUNGA PHIR 🍞 BREAD KI TARH KHAYENGE WO TERI MAA KI CHUT",
    "DUDH HILAAUNGA TERI VAHEEN KE UPR NICHE 🆙🆒😙",
    "TERI MAA KI CHUT ME ✋ HATTH DALKE 👶 BACCHE NIKAL DUNGA 😍",
    "TERI BEHN KI CHUT ME KELE KE CHILKE 🍌🍌😍",
    "TERI BHEN KI CHUT ME USERBOT LAGAAUNGA SASTE SPAM KE CHODE",
    "TERI VAHEEN DHANDHE VAALI 😋😛",
    "TERI MAA KE BHOSDE ME AC LAGA DUNGA SAARI GARMI NIKAL JAAYEGI",
    "TERI VAHEEN KO HORLICKS PEELAUNGA MADARCHOD😚",
    "TERI MAA KI GAAND ME SARIYA DAAL DUNGA MADARCHOD USI SARIYE PR TANG KE BACHE PAIDA HONGE 😱😱",
    "TERI MAA KO KOLKATA VAALE JITU BHAIYA KA LUND MUBARAK 🤩🤩",
    "TERI MUMMY KI FANTASY HU LAWDE, TU APNI BHEN KO SMBHAAL 😈😈",
    "TERA PEHLA BAAP HU MADARCHOD ",
    "TERI VAHEEN KE BHOSDE ME XVIDEOS.COM CHALA KE MUTH MAARUNGA 🤡😹",
    "TERI MAA KA GROUP VAALON SAATH MILKE GANG BANG KRUNGA🙌🏻☠️ ",
    "TERI ITEM KI GAAND ME LUND DAALKE,TERE JAISA EK OR NIKAAL DUNGA MADARCHOD🤘🏻🙌🏻☠️ ",
    "AUKAAT ME REH VRNA GAAND ME DANDA DAAL KE MUH SE NIKAAL DUNGA SHARIR BHI DANDE JESA DIKHEGA 🙄🤭🤭",
    "TERI MUMMY KE SAATH LUDO KHELTE KHELTE USKE MUH ME APNA LODA DE DUNGA☝🏻☝🏻😬",
    "TERI VAHEEN KO APNE LUND PR ITNA JHULAAUNGA KI JHULTE JHULTE HI BACHA PAIDA KR DEGI👀👯 ",
    "TERI MAA KI CHUT MEI BATTERY LAGA KE POWERBANK BANA DUNGA 🔋 🔥🤩",
    "TERI MAA KI CHUT MEI C++ STRING ENCRYPTION LAGA DUNGA BAHTI HUYI CHUT RUK JAYEGIIII😈🔥😍",
    "TERI MAA KE GAAND MEI JHAADU DAL KE MOR 🦚 BANA DUNGAA 🤩🥵😱",
    "TERI CHUT KI CHUT MEI SHOULDERING KAR DUNGAA HILATE HUYE BHI DARD HOGAAA😱🤮👺",
    "TERI MAA KO REDI PE BAITHAL KE USSE USKI CHUT BILWAUNGAA 💰 😵🤩",
    "BHOSDIKE TERI MAA KI CHUT MEI 4 HOLE HAI UNME MSEAL LAGA BAHUT BAHETI HAI BHOFDIKE👊🤮🤢🤢",
    "TERI BAHEN KI CHUT MEI BARGAD KA PED UGA DUNGAA CORONA MEI SAB OXYGEN LEKAR JAYENGE🤢🤩🥳",
    "TERI MAA KI CHUT MEI SUDO LAGA KE BIGSPAM LAGA KE 9999 FUCK LAGAA DU 🤩🥳🔥",
    "TERI VAHEN KE BHOSDIKE MEI BESAN KE LADDU BHAR DUNGA🤩🥳🔥😈",
    "TERI MAA KI CHUT KHOD KE USME CYLINDER ⛽️ FIT KARKE USMEE DAL MAKHANI BANAUNGAAA🤩👊🔥",
    "TERI MAA KI CHUT MEI SHEESHA DAL DUNGAAA AUR CHAURAHE PE TAANG DUNGA BHOSDIKE😈😱🤩",
    "TERI MAA KI CHUT MEI CREDIT CARD DAL KE AGE SE 500 KE KAARE KAARE NOTE NIKALUNGAA BHOSDIKE💰💰🤩",
    "TERI MAA KE SATH SUAR KA SEX KARWA DUNGAA EK SATH 6-6 BACHE DEGI💰🔥😱",
    "TERI BAHEN KI CHUT MEI APPLE KA 18W WALA CHARGER 🔥🤩",
    "TERI BAHEN KI GAAND MEI ONEPLUS KA WRAP CHARGER 30W HIGH POWER 💥😂😎",
    "TERI BAHEN KI CHUT KO AMAZON SE ORDER KARUNGA 10 rs MEI AUR FLIPKART PE 20 RS MEI BECH DUNGA🤮👿😈🤖",
    "TERI MAA KI BADI BHUND ME ZOMATO DAL KE SUBWAY KA BFF VEG SUB COMBO [15cm , 16 inches ] ORDER COD KRVAUNGA OR TERI MAA JAB DILIVERY DENE AYEGI TAB USPE JAADU KRUNGA OR FIR 9 MONTH BAAD VO EK OR FREE DILIVERY DEGI🙀👍🥳🔥",
    "TERI BHEN KI CHUT KAALI🙁🤣💥",
    "TERI MAA KI CHUT ME CHANGES COMMIT KRUGA FIR TERI BHEEN KI CHUT AUTOMATICALLY UPDATE HOJAAYEGI🤖🙏🤔",
    "TERI MAUSI KE BHOSDE MEI INDIAN RAILWAY 🚂💥😂",
    "TU TERI BAHEN TERA KHANDAN SAB BAHEN KE LAWDE RANDI HAI RANDI 🤢✅🔥",
    "TERI BAHEN KI CHUT MEI IONIC BOND BANA KE VIRGINITY LOOSE KARWA DUNGA USKI 📚 😎🤩",
    "TERI RANDI MAA SE PUCHNA BAAP KA NAAM BAHEN KE LODEEEEE 🤩🥳😳",
    "TU AUR TERI MAA DONO KI BHOSDE MEI METRO CHALWA DUNGA MADARXHOD 🚇🤩😱🥶",
    "TERI MAA KO ITNA CHODUNGA TERA BAAP BHI USKO PAHCHANANE SE MANA KAR DEGA😂👿🤩",
    "TERI BAHEN KE BHOSDE MEI HAIR DRYER CHALA DUNGAA💥🔥🔥",
    "TERI MAA KI CHUT MEI TELEGRAM KI SARI RANDIYON KA RANDI KHANA KHOL DUNGAA👿🤮😎",
    "TERI MAA KI CHUT ALEXA DAL KEE DJ BAJAUNGAAA 🎶 ⬆️🤩💥",
    "TERI MAA KE BHOSDE MEI GITHUB DAL KE APNA BOT HOST KARUNGAA 🤩👊👤😍",
    "TERI BAHEN KA VPS BANA KE 24*7 BASH CHUDAI COMMAND DE DUNGAA 🤩💥🔥🔥",
    "TERI MUMMY KI CHUT MEI TERE LAND KO DAL KE KAAT DUNGA MADARCHOD 🔪😂🔥",
    "SUN TERI MAA KA BHOSDA AUR TERI BAHEN KA BHI BHOSDA 👿😎👊",
    "TUJHE DEKH KE TERI RANDI BAHEN PE TARAS ATA HAI MUJHE BAHEN KE LODEEEE 👿💥🤩🔥",
    "SUN MADARCHOD JYADA NA UCHAL MAA CHOD DENGE EK MIN MEI ✅🤣🔥🤩",
    "APNI AMMA SE PUCHNA USKO US KAALI RAAT MEI KAUN CHODNEE AYA THAAA! TERE IS PAPA KA NAAM LEGI 😂👿😳",
    "TOHAR BAHIN CHODU BBAHEN KE LAWDE USME MITTI DAL KE CEMENT SE BHAR DU 🏠🤢🤩💥",
    "TUJHE AB TAK NAHI SMJH AYA KI MAI HI HU TUJHE PAIDA KARNE WALA BHOSDIKEE APNI MAA SE PUCH RANDI KE BACHEEEE 🤩👊👤😍",
    "TERI MAA KE BHOSDE MEI SPOTIFY DAL KE LOFI BAJAUNGA DIN BHAR 😍🎶🎶💥",
    "TERI MAA KA NAYA RANDI KHANA KHOLUNGA CHINTA MAT KAR 👊🤣🤣😳",
    "TERA BAAP HU BHOSDIKE TERI MAA KO RANDI KHANE PE CHUDWA KE US PAISE KI DAARU PEETA HU 🍷🤩🔥",
    "TERI BAHEN KI CHUT MEI APNA BADA SA LODA GHUSSA DUNGAA KALLAAP KE MAR JAYEGI 🤩😳😳🔥",
    "TOHAR MUMMY KI CHUT MEI PURI KI PURI KINGFISHER KI BOTTLE DAL KE TOD DUNGA ANDER HI 😱😂🤩",
    "TERI MAA KO ITNA CHODUNGA KI SAPNE MEI BHI MERI CHUDAI YAAD KAREGI RANDI 🥳😍👊💥",
    "TERI MUMMY AUR BAHEN KO DAUDA DAUDA NE CHODUNGA UNKE NO BOLNE PE BHI LAND GHUSA DUNGA ANDER TAK 😎😎🤣🔥",
    "TERI MUMMY KI CHUT KO ONLINE OLX PE BECHUNGA AUR PAISE SE TERI BAHEN KA KOTHA KHOL DUNGA 😎🤩😝😍",
    "TERI MAA KE BHOSDA ITNA CHODUNGA KI TU CAH KE BHI WO MAST CHUDAI SE DUR NHI JA PAYEGAA 😏😏🤩😍",
    "SUN BE RANDI KI AULAAD TU APNI BAHEN SE SEEKH KUCH KAISE GAAND MARWATE HAI😏🤬🔥💥",
    "TERI MAA KA YAAR HU MEI AUR TERI BAHEN KA PYAAR HU MEI AJA MERA LAND CHOOS LE 🤩🤣💥",
    "MADARCHOD",
    "BHOSDIKE",
    "LAAAWEEE KE BAAAAAL",
    "MAAAAR KI JHAAAAT KE BBBBBAAAAALLLLL",
    "MADRCHOD..",
    "TERI MA KI CHUT..",
    "LWDE KE BAAALLL.",
    "MACHAR KI JHAAT KE BAAALLLL",
    "TERI MA KI CHUT M DU TAPA TAP?",
    "TERI MA KA BHOSDAA",
    "TERI BHN SBSBE BDI RANDI.",
    "TERI MA OSSE BADI RANDDDDD",
    "TERA BAAP CHKAAAA",
    "KITNI CHODU TERI MA AB OR..",
    "TERI MA CHOD DI HM NE",
    "TERI MA KE STH REELS BNEGA ROAD PEE",
    "TERI MA KI CHUT EK DAM TOP SEXY",
    "MALUM NA PHR KESE LETA HU M TERI MA KI CHUT TAPA TAPPPPP",
    "LUND KE CHODE TU KEREGA TYPIN",
    "SPEED PKD LWDEEEE",
    "@ur_alpha_baby BAAP KI SPEED MTCH KRRR",
    "LWDEEE",
    "PAPA KI SPEED MTCH NHI HO RHI KYA",
    "ALE ALE MELA BCHAAAA",
    "CHUD GYA PAPA @ur_alpha_baby SEEE",
    "KISAN KO KHODNA OR",
    "SALE RAPEKL KRDKA TERA",
    "HAHAHAAAAA",
    "KIDSSSS",
    "TERI MA CHUD GYI AB FRAR MT HONA",
    "YE LDNGE BAPP SE",
    "KIDSSS FRAR HAHAHH",
    "BHEN KE LWDE SHRM KR",
    "KITNI GLIYA PDWEGA APNI MA KO",
    "NALLEE",
    "SHRM KR",
    "MERE LUND KE BAAAAALLLLL",
    "KITNI GLIYA PDWYGA APNI MA BHEN KO",
    "RNDI KE LDKEEEEEEEEE",
    "KIDSSSSSSSSSSSS",
    "Apni gaand mein muthi daal",
    "Apni lund choos",
    "Apni ma ko ja choos",
    "Bhen ke laude",
    "Bhen ke takke",
    "Abla TERA KHAN DAN CHODNE KI BARIII",
    "BETE TERI MA SBSE BDI RAND",
    "LUND KE BAAAL JHAT KE PISSSUUUUUUU",
    "LUND PE LTKIT MAAALLLL KI BOND H TUUU",
    "KASH OS DIN MUTH MRKE SOJTA M TUN PAIDA NA HOTAA",
    "GLTI KRDI TUJW PAIDA KRKE",
    "SPEED PKDDD",
    "Gaand main LWDA DAL LE APNI MERAAA",
    "Gaand mein bambu DEDUNGAAAAAA",
    "GAND FTI KE BALKKK",
    "Gote kitne bhi bade ho, lund ke niche hi rehte hai",
    "Hazaar lund teri gaand main",
    "Jhaant ke pissu-",
    "TERI MA KI KALI CHUT",
    "Khotey ki aulda",
    "Kutte ka awlat",
    "Kutte ki jat",
    "Kutte ke tatte",
    "TETI MA KI.CHUT , tERI MA RNDIIIIIIIIIIIIIIIIIIII",
    "Lavde ke bal",
    "muh mei lele",
    "Lund Ke Pasine",
    "MERE LWDE KE BAAAAALLL",
    "HAHAHAAAAAA",
    "CHUD GYAAAAA",
    "Randi khanE KI ULADDD",
    "Sadi hui gaand",
    "Teri gaand main kute ka lund",
    "Teri maa ka bhosda",
    "Teri maa ki chut",
    "Tere gaand mein keede paday",
    "Ullu ke pathe",
    "SUNN MADERCHOD",
    "TERI MAA KA BHOSDA",
    "BEHEN K LUND",
    "TERI MAA KA CHUT KI CHTNIIII",
    "MERA LAWDA LELE TU AGAR CHAIYE TOH",
    "GAANDU",
    "CHUTIYA",
    "TERI MAA KI CHUT PE JCB CHADHAA DUNGA",
    "SAMJHAA LAWDE",
    "YA DU TERE GAAND ME TAPAA TAP��",
    "TERI BEHEN MERA ROZ LETI HAI",
    "TERI GF K SAATH MMS BANAA CHUKA HU���不�不",
    "TU CHUTIYA TERA KHANDAAN CHUTIYA",
    "AUR KITNA BOLU BEY MANN BHAR GAYA MERA�不",
    "TERIIIIII MAAAA KI CHUTTT ME ABCD LIKH DUNGA MAA KE LODE",
    "TERI MAA KO LEKAR MAI FARAR",
    "RANIDIII",
    "BACHEE",
    "CHODU",
    "RANDI",
    "RANDI KE PILLE",
    "TERIIIII MAAA KO BHEJJJ",
    "TERAA BAAAAP HU",
    "teri MAA KI CHUT ME HAAT DAALLKE BHAAG JAANUGA",
    "Teri maa KO SARAK PE LETAA DUNGA",
    "TERI MAA KO GB ROAD PE LEJAKE BECH DUNGA",
    "Teri maa KI CHUT MÉ KAALI MITCH",
    "TERI MAA SASTI RANDI HAI",
    "TERI MAA KI CHUT ME KABUTAR DAAL KE SOUP BANAUNGA MADARCHOD",
    "TERI MAAA RANDI HAI",
    "TERI MAAA KI CHUT ME DETOL DAAL DUNGA MADARCHOD",
    "TERI MAA KAAA BHOSDAA",
    "TERI MAA KI CHUT ME LAPTOP",
    "Teri maa RANDI HAI",
    "TERI MAA KO BISTAR PE LETAAKE CHODUNGA",
    "TERI MAA KO AMERICA GHUMAAUNGA MADARCHOD",
    "TERI MAA KI CHUT ME NAARIYAL PHOR DUNGA",
    "TERI MAA KE GAND ME DETOL DAAL DUNGA",
    "TERI MAAA KO HORLICKS PILAUNGA MADARCHOD",
    "TERI MAA KO SARAK PE LETAAA DUNGAAA",
    "TERI MAA KAA BHOSDA",
    "MERAAA LUND PAKAD LE MADARCHOD",
    "CHUP TERI MAA AKAA BHOSDAA",
    "TERIII MAA CHUF GEYII KYAAA LAWDEEE",
    "TERIII MAA KAA BJSODAAA",
    "MADARXHODDD",
    "TERIUUI MAAA KAA BHSODAAA",
    "TERIIIIII BEHENNNN KO CHODDDUUUU MADARXHODDDD",
    "NIKAL MADARCHOD",
    "RANDI KE BACHE",
    "TERA MAA MERI FAN",
    "TERI SEXY BAHEN KI CHUT OP",
]

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

async def handle(request):
    return web.Response(text="✅ Bot is alive!")

async def webhook_handler(request):
    try:
        data = await request.json()
        update = Update.de_json(data, application.bot)
        application.update_queue.put_nowait(update)
    except Exception as e:
        logger.error(f"Webhook error: {e}")
    return web.Response(text="OK")

async def start_web():
    app = web.Application()
    app.router.add_get("/", handle)
    app.router.add_post("/webhook", webhook_handler)

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", PORT)
    await site.start()
    logger.info(f"🌍 Web server started on port {PORT}")
    return runner

def run_web():
    asyncio.run(start_web())

# ─── Main ────────────────────────────────
async def main():
    load_data()
    logger.info("🤖 Bot starting in webhook mode...")

    # Start aiohttp server
    await start_web()

    # Initialize and start application
    await application.initialize()
    await application.start()

    # Set webhook
    WEBHOOK_URL = os.getenv("WEBHOOK_URL")  # e.g. https://your-app.onrender.com
    if not WEBHOOK_URL:
        logger.error("❌ WEBHOOK_URL not set in environment variables")
        sys.exit(1)

    await application.bot.set_webhook(WEBHOOK_URL + "/webhook")
    logger.info(f"🤖 Webhook set to {WEBHOOK_URL}/webhook")

    # Keep running forever
    await asyncio.Event().wait()


def handle_exit(signum, frame):
    print("🛑 Shutting down...")
    sys.exit(0)


if __name__ == "__main__":
    signal.signal(signal.SIGINT, handle_exit)
    signal.signal(signal.SIGTERM, handle_exit)
    asyncio.run(main())
