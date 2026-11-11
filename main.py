# -*- coding: utf-8 -*-
"""
Telegram content/referral bot — single-file implementation.
Python 3.11+
Install: pip install -U aiogram aiosqlite
Run: BOT_TOKEN="..." ADMIN_ID="8942851703" DB_PATH="/data/bot.sqlite3" python main.py

IMPORTANT:
- Put DB_PATH on a persistent disk/volume supplied by your host.
- A single Python file does NOT make ephemeral hosting storage persistent.
- Use only content you own or are authorized to distribute.
"""

import asyncio
import logging
import os
import time
from contextlib import suppress
from typing import Optional

import aiosqlite
from aiogram import Bot, Dispatcher, F, Router
from aiogram.enums import ParseMode
from aiogram.exceptions import (
    TelegramBadRequest, TelegramForbiddenError, TelegramRetryAfter,
    TelegramNetworkError, TelegramAPIError,
)
from aiogram.filters import CommandStart, Command
from aiogram.types import (
    Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton,
    BotCommand, InputMediaPhoto, InputMediaVideo,
)
from aiogram.client.default import DefaultBotProperties

# --------------------------- CONFIGURATION ---------------------------

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
ADMIN_ID_RAW = os.getenv("ADMIN_ID", "8942851703").strip()
DB_PATH = os.getenv("DB_PATH", "bot_data.sqlite3").strip()
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "JOKWRHUB18").strip().lstrip("@")
if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN environment variable is missing.")
try:
    ADMIN_ID = int(ADMIN_ID_RAW)
except ValueError:
    raise RuntimeError("ADMIN_ID must be a numeric Telegram user ID.")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
log = logging.getLogger("content_bot")

router = Router()
dp = Dispatcher()
dp.include_router(router)
bot: Optional[Bot] = None

CATEGORIES = ("kz", "kids", "ru", "us")
CATEGORY_LABELS = {
    "kz": {"kk": "🇰🇿 Қазақша каналдар", "ru": "🇰🇿 Казахские каналы"},
    "kids": {"kk": "🧸 Детский каналдар", "ru": "🧸 Детские каналы"},
    "ru": {"kk": "🇷🇺 Орысша каналдар", "ru": "🇷🇺 Русские каналы"},
    "us": {"kk": "🇺🇸 Американша каналдар", "ru": "🇺🇸 Американские каналы"},
}
TEXT = {
    "kk": {
        "choose": "Тілді таңдаңыз:",
        "welcome": "🔥 ҚОШ КЕЛДІҢІЗ!\n\nСізді ерекше атмосфера мен қызықты контент күтеді. 😉\n\nҚалаған бөліміңізді таңдаңыз. Кейбір қызықтарды сөзбен жеткізу мүмкін емес... 💋",
        "channels": "📂 Каналдар",
        "free": "🎁 Тегін канал",
        "help": "ℹ️ Көмекші",
        "contact": "💬 Админге жазу",
        "back": "⬅️ Артқа",
        "home": "🏠 Басты меню",
        "preview": "👁 Алдын ала көру",
        "buy": "🔞 Сатып алу",
        "no_preview": "Бұл бөлімде әзірге алдын ала көру материалы жоқ.",
        "buy_text": "Сәлеметсіз бе! Сатып алу туралы ақпарат беріңіз.",
        "contact_text": "Хабарламаңызды жазыңыз. Ол байланыс бөліміне жіберіледі.",
        "sent": "Хабарламаңыз жіберілді.",
        "blocked": "Бұл ботты пайдалану мүмкіндігі шектелген.",
        "help_text": "💡 БОТТЫ ҚОЛДАНУ НҰСҚАУЛЫҒЫ\n\n📂 Каналдар — өзіңізге ұнайтын категорияны таңдап, қолжетімді материалдармен алдын ала танысыңыз. Сатып алу туралы ақпарат алу үшін тиісті батырманы басыңыз.\n\n🎁 Тегін канал — жеке сілтемеңізді достарыңызбен бөлісіп, жаңа қолданушыларды шақырыңыз. Қажетті шарт орындалған соң тегін каналға қол жеткізесіз.\n\n💬 Админге жазу — сұрақтарыңыз немесе ұсыныстарыңыз болса, хабарлама қалдырыңыз.\n\n✨ Қажетті бөлімді таңдап, нұсқауларды орындасаңыз жеткілікті!",
        "ref_text": "🎁 ТЕГІН КАНАЛ\n\nЖеке сілтемеңізді достарыңызға жіберіңіз. Достарыңыз ботқа осы сілтеме арқылы алғаш рет кірген сайын шақырылғандар саны есептеледі.\n\nШарт орындалғаннан кейін тегін каналға арналған сілтеме автоматты түрде беріледі.\n\nСіздің сілтемеңіз:\n{link}\n\nШақырылғандар: {count}\nҚажетті шарт: {required}",
        "share": "Досыңа жіберу",
        "link_missing": "Тегін канал сілтемесі әзірге орнатылмаған. Кейінірек қайталап көріңіз.",
        "reward": "🎉 Құттықтаймыз! Тегін каналға кіру сілтемесі:\n{link}",
        "admin_contact": "💬 Сұрақтарыңыз болса, мына аккаунтқа жазыңыз: @{username}",
    },
    "ru": {
        "choose": "Выберите язык:",
        "welcome": "🔥 ДОБРО ПОЖАЛОВАТЬ!\n\nВас ждут особая атмосфера и интересный контент. 😉\n\nВыберите нужный раздел. Некоторые впечатления невозможно передать словами... 💋",
        "channels": "📂 Каналы",
        "free": "🎁 Бесплатный канал",
        "help": "ℹ️ Помощь",
        "contact": "💬 Написать администратору",
        "back": "⬅️ Назад",
        "home": "🏠 Главное меню",
        "preview": "👁 Предварительный просмотр",
        "buy": "🔞 Купить",
        "no_preview": "В этом разделе пока нет материалов для предварительного просмотра.",
        "buy_text": "Здравствуйте! Предоставьте, пожалуйста, информацию о покупке.",
        "contact_text": "Напишите ваше сообщение. Оно будет передано для ответа.",
        "sent": "Ваше сообщение отправлено.",
        "blocked": "Доступ к этому боту ограничен.",
        "help_text": "💡 ИНСТРУКЦИЯ ПО ИСПОЛЬЗОВАНИЮ БОТА\n\n📂 Каналы — выберите интересующую категорию и ознакомьтесь с доступными материалами. Чтобы узнать условия покупки, нажмите соответствующую кнопку.\n\n🎁 Бесплатный канал — поделитесь личной ссылкой с друзьями и приглашайте новых пользователей. После выполнения условия вы получите доступ к бесплатному каналу.\n\n💬 Написать администратору — оставьте сообщение, если у вас есть вопросы или предложения.\n\n✨ Выберите нужный раздел и следуйте инструкциям!",
        "ref_text": "🎁 БЕСПЛАТНЫЙ КАНАЛ\n\nОтправьте личную ссылку друзьям. Каждый новый пользователь, впервые открывший бота по вашей ссылке, будет засчитан.\n\nПосле выполнения условия бот автоматически выдаст ссылку на бесплатный канал.\n\nВаша ссылка:\n{link}\n\nПриглашено: {count}\nНеобходимое условие: {required}",
        "share": "Отправить другу",
        "link_missing": "Ссылка на бесплатный канал пока не настроена. Попробуйте позже.",
        "reward": "🎉 Поздравляем! Ссылка на бесплатный канал:\n{link}",
        "admin_contact": "💬 По вопросам напишите сюда: @{username}",
    },
}

# --------------------------- DATABASE ---------------------------

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
  user_id INTEGER PRIMARY KEY,
  username TEXT,
  first_name TEXT,
  language TEXT NOT NULL DEFAULT '',
  joined_at INTEGER NOT NULL,
  referrer_id INTEGER,
  referral_count INTEGER NOT NULL DEFAULT 0,
  reward_sent INTEGER NOT NULL DEFAULT 0,
  is_blocked INTEGER NOT NULL DEFAULT 0,
  last_menu_chat_id INTEGER,
  last_menu_message_id INTEGER
);
CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS content (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  category TEXT NOT NULL,
  file_type TEXT NOT NULL,
  file_id TEXT,
  caption TEXT,
  created_at INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS preview_content (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  category TEXT NOT NULL,
  file_type TEXT NOT NULL,
  file_id TEXT,
  caption TEXT,
  created_at INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS admin_state (
  admin_id INTEGER PRIMARY KEY,
  state TEXT,
  category TEXT,
  payload TEXT
);
CREATE TABLE IF NOT EXISTS broadcast_jobs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  status TEXT NOT NULL,
  file_type TEXT NOT NULL,
  file_id TEXT,
  caption TEXT,
  created_at INTEGER NOT NULL,
  sent_count INTEGER NOT NULL DEFAULT 0,
  failed_count INTEGER NOT NULL DEFAULT 0,
  last_user_id INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS broadcast_recipients (
  job_id INTEGER NOT NULL,
  user_id INTEGER NOT NULL,
  status TEXT NOT NULL DEFAULT 'pending',
  PRIMARY KEY(job_id, user_id)
);
CREATE TABLE IF NOT EXISTS admin_message_map (
  admin_message_id INTEGER PRIMARY KEY,
  user_id INTEGER NOT NULL,
  created_at INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS purchases (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL,
  category TEXT,
  created_at INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS referrals (
  invited_id INTEGER PRIMARY KEY,
  referrer_id INTEGER NOT NULL,
  created_at INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_users_blocked ON users(is_blocked);
CREATE INDEX IF NOT EXISTS idx_content_category ON content(category);
CREATE INDEX IF NOT EXISTS idx_broadcast_status ON broadcast_jobs(status);
"""

db: Optional[aiosqlite.Connection] = None

async def init_db():
    global db
    db = await aiosqlite.connect(DB_PATH)
    db.row_factory = aiosqlite.Row
    await db.execute("PRAGMA journal_mode=WAL")
    await db.execute("PRAGMA foreign_keys=ON")
    await db.executescript(SCHEMA)
    defaults = {
        "referral_required": "3",
        "free_channel_url": "",
        "broadcast_delay": "0.08",
    }
    for key, value in defaults.items():
        await db.execute("INSERT OR IGNORE INTO settings(key,value) VALUES(?,?)", (key, value))
    await db.commit()

async def setting(key: str, default: str = "") -> str:
    cur = await db.execute("SELECT value FROM settings WHERE key=?", (key,))
    row = await cur.fetchone()
    return row["value"] if row else default

async def set_setting(key: str, value: str):
    await db.execute(
        "INSERT INTO settings(key,value) VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
        (key, str(value)),
    )
    await db.commit()

async def get_user(user_id: int):
    cur = await db.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
    return await cur.fetchone()

async def is_blocked(user_id: int) -> bool:
    if user_id == ADMIN_ID:
        return False
    row = await get_user(user_id)
    return bool(row and row["is_blocked"])

async def save_user(user, referrer_id: Optional[int] = None):
    existing = await get_user(user.id)
    if existing:
        await db.execute(
            "UPDATE users SET username=?, first_name=? WHERE user_id=?",
            (user.username, user.first_name, user.id),
        )
    else:
        if referrer_id == user.id:
            referrer_id = None
        await db.execute(
            """INSERT INTO users(user_id,username,first_name,language,joined_at,referrer_id)
               VALUES(?,?,?,?,?,?)""",
            (user.id, user.username, user.first_name, "", int(time.time()), referrer_id),
        )
        if referrer_id:
            ref = await get_user(referrer_id)
            if ref and not ref["is_blocked"]:
                await db.execute(
                    "INSERT OR IGNORE INTO referrals(invited_id,referrer_id,created_at) VALUES(?,?,?)",
                    (user.id, referrer_id, int(time.time())),
                )
                cur = await db.execute("SELECT changes() AS n")
                changed = (await cur.fetchone())["n"]
                if changed:
                    await db.execute(
                        "UPDATE users SET referral_count=referral_count+1 WHERE user_id=?",
                        (referrer_id,),
                    )
    await db.commit()

async def set_language(user_id: int, lang: str):
    await db.execute("UPDATE users SET language=? WHERE user_id=?", (lang, user_id))
    await db.commit()

async def get_lang(user_id: int) -> str:
    row = await get_user(user_id)
    return row["language"] if row and row["language"] in ("kk", "ru") else "kk"

async def save_menu(user_id: int, chat_id: int, message_id: int):
    await db.execute(
        "UPDATE users SET last_menu_chat_id=?,last_menu_message_id=? WHERE user_id=?",
        (chat_id, message_id, user_id),
    )
    await db.commit()

async def delete_menu(user_id: int):
    row = await get_user(user_id)
    if row and row["last_menu_chat_id"] and row["last_menu_message_id"]:
        with suppress(TelegramAPIError):
            await bot.delete_message(row["last_menu_chat_id"], row["last_menu_message_id"])
    await db.execute(
        "UPDATE users SET last_menu_chat_id=NULL,last_menu_message_id=NULL WHERE user_id=?",
        (user_id,),
    )
    await db.commit()

# --------------------------- KEYBOARDS / MENU ---------------------------

def ikb(rows):
    return InlineKeyboardMarkup(inline_keyboard=rows)

def btn(text, data):
    return InlineKeyboardButton(text=text, callback_data=data)

def main_keyboard(lang):
    t = TEXT[lang]
    return ikb([
        [btn(t["channels"], "channels"), btn(t["free"], "free")],
        [btn(t["help"], "help"), btn(t["contact"], "contact")],
    ])

def back_keyboard(lang, target="home"):
    return ikb([[btn(TEXT[lang]["back"], target)]])

def categories_keyboard(lang):
    rows = [[btn(CATEGORY_LABELS[c][lang], f"cat:{c}")] for c in CATEGORIES]
    rows.append([btn(TEXT[lang]["back"], "home")])
    return ikb(rows)

def category_keyboard(lang, category):
    t = TEXT[lang]
    return ikb([
        [btn(t["preview"], f"preview:{category}")],
        [btn(t["buy"], f"buy:{category}")],
        [btn(t["back"], "channels")],
    ])

async def show_menu(target: Message | CallbackQuery, user_id: int, text: str, keyboard, edit=True):
    if isinstance(target, CallbackQuery):
        msg = target.message
        try:
            await msg.edit_text(text, reply_markup=keyboard)
            await save_menu(user_id, msg.chat.id, msg.message_id)
            return
        except TelegramBadRequest as e:
            if "message is not modified" in str(e).lower():
                return
            if "there is no text" not in str(e).lower():
                log.info("Menu edit fallback: %s", e)
        sent = await msg.answer(text, reply_markup=keyboard)
    else:
        sent = await target.answer(text, reply_markup=keyboard)
    await save_menu(user_id, sent.chat.id, sent.message_id)

async def ensure_user_menu(message: Message, user_id: int, text: str, keyboard):
    row = await get_user(user_id)
    if row and row["last_menu_chat_id"] and row["last_menu_message_id"]:
        try:
            await bot.edit_message_text(
                text, chat_id=row["last_menu_chat_id"],
                message_id=row["last_menu_message_id"], reply_markup=keyboard
            )
            return
        except TelegramAPIError:
            pass
    sent = await message.answer(text, reply_markup=keyboard)
    await save_menu(user_id, sent.chat.id, sent.message_id)

# --------------------------- USER FLOW ---------------------------

@router.message(CommandStart())
async def start_handler(message: Message):
    args = (message.text or "").split(maxsplit=1)
    referrer = None
    if len(args) > 1 and args[1].startswith("ref_"):
        with suppress(ValueError):
            referrer = int(args[1][4:])
    await save_user(message.from_user, referrer)
    if referrer:
        await check_referral_reward(referrer)
    if await is_blocked(message.from_user.id):
        await message.answer("🚫 " + TEXT[await get_lang(message.from_user.id)]["blocked"])
        return
    row = await get_user(message.from_user.id)
    if not row or not row["language"]:
        sent = await message.answer(TEXT["kk"]["choose"], reply_markup=ikb([
            [btn("🇰🇿 Қазақша", "lang:kk"), btn("🇷🇺 Русский", "lang:ru")]
        ]))
        await save_menu(message.from_user.id, sent.chat.id, sent.message_id)
    else:
        lang = row["language"]
        await ensure_user_menu(message, message.from_user.id, TEXT[lang]["welcome"], main_keyboard(lang))

@router.callback_query(F.data.startswith("lang:"))
async def language_handler(call: CallbackQuery):
    lang = call.data.split(":", 1)[1]
    if lang not in ("kk", "ru"):
        await call.answer("Invalid language", show_alert=True)
        return
    await set_language(call.from_user.id, lang)
    await call.answer()
    await show_menu(call, call.from_user.id, TEXT[lang]["welcome"], main_keyboard(lang))

@router.callback_query(F.data == "home")
async def home_handler(call: CallbackQuery):
    lang = await get_lang(call.from_user.id)
    await call.answer()
    await show_menu(call, call.from_user.id, TEXT[lang]["welcome"], main_keyboard(lang))

@router.callback_query(F.data == "channels")
async def channels_handler(call: CallbackQuery):
    lang = await get_lang(call.from_user.id)
    await call.answer()
    await show_menu(call, call.from_user.id, TEXT[lang]["channels"], categories_keyboard(lang))

@router.callback_query(F.data.startswith("cat:"))
async def category_handler(call: CallbackQuery):
    category = call.data.split(":", 1)[1]
    if category not in CATEGORIES:
        await call.answer("Қате категория", show_alert=True)
        return
    lang = await get_lang(call.from_user.id)
    await call.answer()
    await show_menu(call, call.from_user.id, CATEGORY_LABELS[category][lang], category_keyboard(lang, category))

@router.callback_query(F.data.startswith("preview:"))
async def preview_handler(call: CallbackQuery):
    category = call.data.split(":", 1)[1]
    if category not in CATEGORIES:
        await call.answer()
        return
    lang = await get_lang(call.from_user.id)
    cur = await db.execute(
        "SELECT file_type,file_id,caption FROM content WHERE category=? ORDER BY id DESC LIMIT 10",
        (category,),
    )
    items = await cur.fetchall()
    if not items:
        await call.answer(TEXT[lang]["no_preview"], show_alert=True)
        return
    await call.answer()
    # Preview media are content, not navigation menus. The single menu message remains in place.
    for item in reversed(items):
        await send_stored_content(call.from_user.id, item)
    await show_menu(call, call.from_user.id, CATEGORY_LABELS[category][lang], category_keyboard(lang, category))

@router.callback_query(F.data.startswith("buy:"))
async def buy_handler(call: CallbackQuery):
    category = call.data.split(":", 1)[1]
    if category not in CATEGORIES:
        await call.answer()
        return
    lang = await get_lang(call.from_user.id)
    await db.execute(
        "INSERT INTO purchases(user_id,category,created_at) VALUES(?,?,?)",
        (call.from_user.id, category, int(time.time())),
    )
    await db.commit()
    await call.answer()
    await bot.send_message(
        ADMIN_ID,
        f"🛒 Сатып алу өтініші\nID: {call.from_user.id}\nUsername: @{call.from_user.username or 'жоқ'}\nКатегория: {CATEGORY_LABELS[category]['kk']}\n\nҚолданушыға жауап беру үшін осы хабарламаға Reply жасаңыз."
    )
    await bot.send_message(call.from_user.id, TEXT[lang]["buy_text"])
    await bot.send_message(call.from_user.id, f"💬 @{ADMIN_USERNAME}")
    # Keep navigation on the original menu message.
    await show_menu(call, call.from_user.id, CATEGORY_LABELS[category][lang], category_keyboard(lang, category))

@router.callback_query(F.data == "help")
async def help_handler(call: CallbackQuery):
    lang = await get_lang(call.from_user.id)
    await call.answer()
    await show_menu(call, call.from_user.id, TEXT[lang]["help_text"], back_keyboard(lang))

@router.callback_query(F.data == "contact")
async def contact_handler(call: CallbackQuery):
    lang = await get_lang(call.from_user.id)
    await call.answer()
    await bot.send_message(call.from_user.id, TEXT[lang]["contact_text"])
    await bot.send_message(call.from_user.id, f"💬 @{ADMIN_USERNAME}")
    await show_menu(call, call.from_user.id, TEXT[lang]["admin_contact"].format(username=ADMIN_USERNAME), back_keyboard(lang))

@router.callback_query(F.data == "free")
async def free_handler(call: CallbackQuery):
    lang = await get_lang(call.from_user.id)
    row = await get_user(call.from_user.id)
    me = await bot.get_me()
    link = f"https://t.me/{me.username}?start=ref_{call.from_user.id}"
    required = await setting("referral_required", "3")
    text = TEXT[lang]["ref_text"].format(
        link=link, count=row["referral_count"] if row else 0, required=required
    )
    reward = await setting("free_channel_url", "")
    if row and row["reward_sent"] and reward:
        text += "\n\n" + TEXT[lang]["reward"].format(link=reward)
    kb = ikb([
        [InlineKeyboardButton(text=TEXT[lang]["share"], url=f"https://t.me/share/url?url={link}")],
        [btn(TEXT[lang]["back"], "home")],
    ])
    await call.answer()
    await show_menu(call, call.from_user.id, text, kb)

# --------------------------- CONTENT DELIVERY ---------------------------

async def send_stored_content(user_id: int, item):
    typ, file_id, caption = item["file_type"], item["file_id"], item["caption"] or ""
    if typ == "text":
        await bot.send_message(user_id, caption)
    elif typ == "photo":
        await bot.send_photo(user_id, file_id, caption=caption or None)
    elif typ == "video":
        await bot.send_video(user_id, file_id, caption=caption or None)
    elif typ == "document":
        await bot.send_document(user_id, file_id, caption=caption or None)
    elif typ == "animation":
        await bot.send_animation(user_id, file_id, caption=caption or None)

async def check_referral_reward(user_id: int):
    row = await get_user(user_id)
    if not row or row["reward_sent"]:
        return
    required = int(await setting("referral_required", "3"))
    if row["referral_count"] >= required:
        link = await setting("free_channel_url", "")
        if link:
            lang = row["language"]
            await bot.send_message(user_id, TEXT[lang]["reward"].format(link=link))
            await db.execute("UPDATE users SET reward_sent=1 WHERE user_id=?", (user_id,))
            await db.commit()

# --------------------------- USER MESSAGES / ADMIN REPLIES ---------------------------

@router.message(F.from_user.id != ADMIN_ID)
async def general_message_handler(message: Message):
    user_id = message.from_user.id
    if user_id == ADMIN_ID:
        await admin_message_handler(message)
        return
    if await is_blocked(user_id):
        return
    # Every ordinary user message is forwarded to admin, with a reply mapping.
    caption = (
        f"📩 Қолданушыдан хабарлама\n"
        f"ID: {user_id}\n"
        f"Username: @{message.from_user.username or 'жоқ'}\n"
        f"Аты: {message.from_user.full_name}\n\n"
        "Жауап беру үшін осы хабарламаға Reply жасаңыз."
    )
    try:
        if message.photo:
            forwarded = await bot.send_photo(ADMIN_ID, message.photo[-1].file_id, caption=caption)
        elif message.video:
            forwarded = await bot.send_video(ADMIN_ID, message.video.file_id, caption=caption)
        elif message.document:
            forwarded = await bot.send_document(ADMIN_ID, message.document.file_id, caption=caption)
        elif message.voice:
            forwarded = await bot.send_voice(ADMIN_ID, message.voice.file_id, caption=caption)
        elif message.text:
            forwarded = await bot.send_message(ADMIN_ID, caption + "\n\n" + message.text)
        else:
            forwarded = await bot.send_message(ADMIN_ID, caption + "\n\n[Қолдау көрсетілмейтін хабарлама түрі]")
        await db.execute(
            "INSERT OR REPLACE INTO admin_message_map(admin_message_id,user_id,created_at) VALUES(?,?,?)",
            (forwarded.message_id, user_id, int(time.time())),
        )
        await db.commit()
        lang = await get_lang(user_id)
        await message.answer(TEXT[lang]["sent"])
    except TelegramAPIError:
        log.exception("Could not forward user message to admin")
        lang = await get_lang(user_id)
        await message.answer("Хабарламаны жеткізу мүмкін болмады. Кейінірек қайталап көріңіз.")

async def admin_message_handler(message: Message):
    # Admin commands and panel states.
    if message.text and message.text.startswith("/"):
        return
    state_row = await db.execute("SELECT * FROM admin_state WHERE admin_id=?", (ADMIN_ID,))
    state = await state_row.fetchone()
    if state and state["state"] in ("add_content", "add_preview", "broadcast_draft"):
        await process_admin_upload(message, state)
        return
    if message.reply_to_message:
        cur = await db.execute(
            "SELECT user_id FROM admin_message_map WHERE admin_message_id=?",
            (message.reply_to_message.message_id,),
        )
        mapped = await cur.fetchone()
        if mapped:
            target_id = mapped["user_id"]
            try:
                await bot.copy_message(
                    chat_id=target_id, from_chat_id=message.chat.id,
                    message_id=message.message_id
                )
                await message.reply("✅ Жауап жіберілді.")
            except TelegramForbiddenError:
                await message.reply("Қолданушы ботты бұғаттаған немесе оған хабарлама жіберу мүмкін емес.")
            except TelegramAPIError as e:
                await message.reply(f"Жіберу қатесі: {e}")
            return
    await message.answer("Админ панелін ашу: /admin")

# --------------------------- ADMIN PANEL ---------------------------

def admin_keyboard():
    return ikb([
        [btn("📂 Контент басқару", "adm:content"), btn("📊 Статистика", "adm:stats")],
        [btn("📢 Рассылка", "adm:broadcast"), btn("👥 Қолданушылар", "adm:users")],
        [btn("🚫 Бұғаттау", "adm:block"), btn("🎁 Реферал баптауы", "adm:ref")],
        [btn("🔗 Тегін канал сілтемесі", "adm:freeurl")],
        [btn("⏹ Рассылканы тоқтату", "adm:stop"), btn("🏠 Жабу", "adm:close")],
    ])

@router.message(Command("admin"))
async def admin_command(message: Message):
    if message.from_user.id != ADMIN_ID:
        return
    await message.answer("🛠 ӘКІМШІ БАСҚАРУ ПАНЕЛІ", reply_markup=admin_keyboard())

@router.callback_query(F.data.startswith("adm:"))
async def admin_callbacks(call: CallbackQuery):
    if call.from_user.id != ADMIN_ID:
        await call.answer("Рұқсат жоқ", show_alert=True)
        return
    action = call.data.split(":", 1)[1]
    await call.answer()
    if action == "close":
        with suppress(TelegramAPIError):
            await call.message.delete()
        return
    if action == "content":
        rows = [[btn(CATEGORY_LABELS[c]["kk"], f"admcat:{c}")] for c in CATEGORIES]
        rows += [[btn("⬅️ Админ меню", "adm:back")]]
        await call.message.edit_text("Контент жүктейтін категорияны таңдаңыз:", reply_markup=ikb(rows))
    elif action == "stats":
        cur = await db.execute("SELECT COUNT(*) n FROM users")
        total = (await cur.fetchone())["n"]
        cur = await db.execute("SELECT COUNT(*) n FROM users WHERE is_blocked=1")
        blocked = (await cur.fetchone())["n"]
        cur = await db.execute("SELECT COUNT(*) n FROM users WHERE is_blocked=0")
        active = (await cur.fetchone())["n"]
        cur = await db.execute("SELECT COUNT(*) n FROM referrals")
        refs = (await cur.fetchone())["n"]
        cur = await db.execute("SELECT COUNT(*) n FROM users WHERE reward_sent=1")
        rewards = (await cur.fetchone())["n"]
        cur = await db.execute("SELECT COUNT(*) n FROM purchases")
        purchases_count = (await cur.fetchone())["n"]
        cur = await db.execute("SELECT language,COUNT(*) n FROM users GROUP BY language")
        langs = await cur.fetchall()
        lang_text = "\n".join(f"{r['language']}: {r['n']}" for r in langs) or "—"
        await call.message.edit_text(
            f"📊 СТАТИСТИКА\n\n👥 Барлығы: {total}\n🟢 Бот ішіндегі белсенді: {active}\n🚫 Ішкі бұғатта: {blocked}\n🔗 Шақырылғандар: {refs}\n🎁 Тегін канал алғандар: {rewards}\n🛒 Сатып алу өтініштері: {purchases_count}\n\n🌐 Тілдер:\n{lang_text}",
            reply_markup=ikb([[btn("⬅️ Админ меню", "adm:back")]])
        )
    elif action == "broadcast":
        await db.execute(
            "INSERT INTO admin_state(admin_id,state,category,payload) VALUES(?,?,?,?) "
            "ON CONFLICT(admin_id) DO UPDATE SET state=excluded.state,category=NULL,payload=NULL",
            (ADMIN_ID, "broadcast_draft", None, None),
        )
        await db.commit()
        await call.message.answer("📢 Рассылкаға жіберілетін мәтінді, фотоны немесе видеоны жіберіңіз. Тоқтату үшін /cancel.")
    elif action == "users":
        await call.message.edit_text(
            "Қолданушыны ID арқылы бұғаттау/бұғаттан шығару үшін:\n/block 123456789\n/unblock 123456789",
            reply_markup=ikb([[btn("⬅️ Админ меню", "adm:back")]])
        )
    elif action == "block":
        await call.message.edit_text(
            "Қолданушыны бұғаттау: /block ID\nБұғаттан шығару: /unblock ID",
            reply_markup=ikb([[btn("⬅️ Админ меню", "adm:back")]])
        )
    elif action == "ref":
        required = await setting("referral_required", "3")
        await call.message.edit_text(
            f"Қазіргі талап: {required} адам.\nӨзгерту: /setref 5",
            reply_markup=ikb([[btn("⬅️ Админ меню", "adm:back")]])
        )
    elif action == "freeurl":
        url = await setting("free_channel_url", "")
        await call.message.edit_text(
            f"Қазіргі сілтеме: {url or 'орнатылмаған'}\nЖаңа сілтеме енгізу: /setfree https://t.me/...",
            reply_markup=ikb([[btn("⬅️ Админ меню", "adm:back")]])
        )
    elif action == "stop":
        await stop_broadcast()
        await call.message.answer("⏹ Белсенді рассылка тоқтатылды.")
    elif action == "back":
        await call.message.edit_text("🛠 ӘКІМШІ БАСҚАРУ ПАНЕЛІ", reply_markup=admin_keyboard())

@router.callback_query(F.data.startswith("admcat:"))
async def admin_category_callback(call: CallbackQuery):
    if call.from_user.id != ADMIN_ID:
        await call.answer("Рұқсат жоқ", show_alert=True)
        return
    category = call.data.split(":", 1)[1]
    if category not in CATEGORIES:
        await call.answer()
        return
    await db.execute(
        "INSERT INTO admin_state(admin_id,state,category,payload) VALUES(?,?,?,?) "
        "ON CONFLICT(admin_id) DO UPDATE SET state=excluded.state,category=excluded.category,payload=NULL",
        (ADMIN_ID, "add_content", category, None),
    )
    await db.commit()
    await call.answer()
    await call.message.answer(
        f"{CATEGORY_LABELS[category]['kk']} бөліміне жарияланатын фото/видео/мәтінді жіберіңіз.\n"
        "Жіберілген материал бірден осы категорияға қосылады. Тоқтату: /cancel"
    )

async def process_admin_upload(message: Message, state):
    mode = state["state"]
    category = state["category"]
    table = "content"
    if message.text and message.text.startswith("/cancel"):
        await db.execute("DELETE FROM admin_state WHERE admin_id=?", (ADMIN_ID,))
        await db.commit()
        await message.answer("Әрекет тоқтатылды.", reply_markup=admin_keyboard())
        return
    typ, file_id, caption = None, None, message.caption or ""
    if message.photo:
        typ, file_id = "photo", message.photo[-1].file_id
    elif message.video:
        typ, file_id = "video", message.video.file_id
    elif message.document:
        typ, file_id = "document", message.document.file_id
    elif message.animation:
        typ, file_id = "animation", message.animation.file_id
    elif message.text:
        typ, caption = "text", message.text
    else:
        await message.answer("Бұл формат әзірге қолдау таппайды. Мәтін, фото, видео, құжат немесе GIF жіберіңіз.")
        return
    await db.execute(
        f"INSERT INTO {table}(category,file_type,file_id,caption,created_at) VALUES(?,?,?,?,?)",
        (category, typ, file_id, caption, int(time.time())),
    )
    await db.commit()
    await message.answer("✅ Материал сақталды. Тағы жіберіңіз немесе /cancel басыңыз.")

# --------------------------- ADMIN COMMANDS ---------------------------

@router.message(Command("cancel"))
async def cancel_admin_state(message: Message):
    if message.from_user.id != ADMIN_ID:
        return
    await db.execute("DELETE FROM admin_state WHERE admin_id=?", (ADMIN_ID,))
    await db.commit()
    await message.answer("Әрекет тоқтатылды.", reply_markup=admin_keyboard())

@router.message(Command("setref"))
async def set_ref_command(message: Message):
    if message.from_user.id != ADMIN_ID:
        return
    parts = (message.text or "").split()
    if len(parts) != 2 or not parts[1].isdigit() or int(parts[1]) < 1:
        await message.answer("Қолдану: /setref 3")
        return
    await set_setting("referral_required", parts[1])
    await message.answer(f"✅ Жаңа талап: {parts[1]} адам.")
    cur = await db.execute("SELECT user_id FROM users WHERE reward_sent=0 AND referral_count>=?", (int(parts[1]),))
    for row in await cur.fetchall():
        await check_referral_reward(row["user_id"])

@router.message(Command("setfree"))
async def set_free_command(message: Message):
    if message.from_user.id != ADMIN_ID:
        return
    parts = (message.text or "").split(maxsplit=1)
    if len(parts) != 2 or not parts[1].startswith(("https://t.me/", "https://telegram.me/")):
        await message.answer("Қолдану: /setfree https://t.me/канал")
        return
    await set_setting("free_channel_url", parts[1].strip())
    await message.answer("✅ Тегін канал сілтемесі сақталды.")

@router.message(Command("block"))
async def block_command(message: Message):
    if message.from_user.id != ADMIN_ID:
        return
    parts = (message.text or "").split()
    if len(parts) != 2 or not parts[1].isdigit():
        await message.answer("Қолдану: /block 123456789")
        return
    uid = int(parts[1])
    await db.execute("UPDATE users SET is_blocked=1 WHERE user_id=?", (uid,))
    await db.commit()
    await message.answer(f"🚫 {uid} боттың ішкі қара тізіміне қосылды.")

@router.message(Command("unblock"))
async def unblock_command(message: Message):
    if message.from_user.id != ADMIN_ID:
        return
    parts = (message.text or "").split()
    if len(parts) != 2 or not parts[1].isdigit():
        await message.answer("Қолдану: /unblock 123456789")
        return
    uid = int(parts[1])
    await db.execute("UPDATE users SET is_blocked=0 WHERE user_id=?", (uid,))
    await db.commit()
    await message.answer(f"✅ {uid} бұғаттан шығарылды.")

# --------------------------- BROADCAST ENGINE ---------------------------

broadcast_task: Optional[asyncio.Task] = None
broadcast_lock = asyncio.Lock()

async def create_broadcast(message: Message):
    typ, file_id, caption = None, None, message.caption or ""
    if message.photo:
        typ, file_id = "photo", message.photo[-1].file_id
    elif message.video:
        typ, file_id = "video", message.video.file_id
    elif message.document:
        typ, file_id = "document", message.document.file_id
    elif message.animation:
        typ, file_id = "animation", message.animation.file_id
    elif message.text:
        typ, caption = "text", message.text
    else:
        await message.answer("Бұл формат қолдау таппайды.")
        return
    cur = await db.execute(
        "INSERT INTO broadcast_jobs(status,file_type,file_id,caption,created_at) VALUES('queued',?,?,?,?)",
        (typ, file_id, caption, int(time.time())),
    )
    job_id = cur.lastrowid
    cur = await db.execute("SELECT user_id FROM users WHERE is_blocked=0 ORDER BY user_id")
    users = await cur.fetchall()
    await db.executemany(
        "INSERT OR IGNORE INTO broadcast_recipients(job_id,user_id,status) VALUES(?,?,'pending')",
        [(job_id, row["user_id"]) for row in users],
    )
    await db.commit()
    await message.answer(f"📢 Рассылка #{job_id} дайын. Алушылар: {len(users)}.\nБастау: /startbroadcast {job_id}")
    await db.execute("DELETE FROM admin_state WHERE admin_id=?", (ADMIN_ID,))
    await db.commit()

@router.message(Command("startbroadcast"))
async def start_broadcast_command(message: Message):
    global broadcast_task
    if message.from_user.id != ADMIN_ID:
        return
    parts = (message.text or "").split()
    if len(parts) != 2 or not parts[1].isdigit():
        await message.answer("Қолдану: /startbroadcast JOB_ID")
        return
    job_id = int(parts[1])
    cur = await db.execute("SELECT status FROM broadcast_jobs WHERE id=?", (job_id,))
    job = await cur.fetchone()
    if not job:
        await message.answer("Рассылка табылмады.")
        return
    if broadcast_task and not broadcast_task.done():
        await message.answer("Басқа рассылка жүріп жатыр.")
        return
    await db.execute("UPDATE broadcast_jobs SET status='running' WHERE id=?", (job_id,))
    await db.commit()
    broadcast_task = asyncio.create_task(run_broadcast(job_id))
    await message.answer(f"▶️ Рассылка #{job_id} басталды. Тоқтату: /stopbroadcast")

async def run_broadcast(job_id: int):
    async with broadcast_lock:
        cur = await db.execute("SELECT * FROM broadcast_jobs WHERE id=?", (job_id,))
        job = await cur.fetchone()
        if not job:
            return
        delay = float(await setting("broadcast_delay", "0.08"))
        while True:
            cur = await db.execute(
                """SELECT r.user_id FROM broadcast_recipients r
                   JOIN users u ON u.user_id=r.user_id
                   WHERE r.job_id=? AND r.status='pending' AND u.is_blocked=0
                   ORDER BY r.user_id LIMIT 1""",
                (job_id,),
            )
            recipient = await cur.fetchone()
            if not recipient:
                await db.execute("UPDATE broadcast_jobs SET status='completed' WHERE id=?", (job_id,))
                await db.commit()
                with suppress(TelegramAPIError):
                    await bot.send_message(ADMIN_ID, f"✅ Рассылка #{job_id} аяқталды.")
                return
            uid = recipient["user_id"]
            cur = await db.execute("SELECT status FROM broadcast_jobs WHERE id=?", (job_id,))
            status = (await cur.fetchone())["status"]
            if status != "running":
                return
            try:
                if job["file_type"] == "text":
                    await bot.send_message(uid, job["caption"])
                else:
                    # Sending stored file_id through the corresponding Bot API method.
                    fake = {"file_type": job["file_type"], "file_id": job["file_id"], "caption": job["caption"]}
                    await send_stored_content(uid, fake)
                await db.execute(
                    "UPDATE broadcast_recipients SET status='sent' WHERE job_id=? AND user_id=?",
                    (job_id, uid),
                )
                await db.execute(
                    "UPDATE broadcast_jobs SET sent_count=sent_count+1,last_user_id=? WHERE id=?",
                    (uid, job_id),
                )
            except TelegramRetryAfter as e:
                await db.commit()
                await asyncio.sleep(e.retry_after + 1)
                continue
            except TelegramForbiddenError:
                await db.execute("UPDATE users SET is_blocked=0 WHERE user_id=?", (uid,))
                await db.execute(
                    "UPDATE broadcast_recipients SET status='failed' WHERE job_id=? AND user_id=?",
                    (job_id, uid),
                )
                await db.execute("UPDATE broadcast_jobs SET failed_count=failed_count+1 WHERE id=?", (job_id,))
            except TelegramNetworkError:
                await db.commit()
                await asyncio.sleep(5)
                continue
            except TelegramAPIError:
                log.exception("Broadcast failed for %s", uid)
                await db.execute(
                    "UPDATE broadcast_recipients SET status='failed' WHERE job_id=? AND user_id=?",
                    (job_id, uid),
                )
                await db.execute("UPDATE broadcast_jobs SET failed_count=failed_count+1 WHERE id=?", (job_id,))
            await db.commit()
            await asyncio.sleep(delay)

async def stop_broadcast():
    global broadcast_task
    cur = await db.execute("SELECT id FROM broadcast_jobs WHERE status='running' ORDER BY id DESC LIMIT 1")
    row = await cur.fetchone()
    if row:
        await db.execute("UPDATE broadcast_jobs SET status='paused' WHERE id=?", (row["id"],))
        await db.commit()
    if broadcast_task and not broadcast_task.done():
        broadcast_task.cancel()
        with suppress(asyncio.CancelledError):
            await broadcast_task

@router.message(Command("stopbroadcast"))
async def stop_broadcast_command(message: Message):
    if message.from_user.id != ADMIN_ID:
        return
    await stop_broadcast()
    await message.answer("⏹ Рассылка тоқтатылды. Қалған алушылар pending күйінде сақталды.")

# --------------------------- ADMIN UPLOAD STATE ROUTING ---------------------------

async def process_admin_upload_router(message: Message):
    cur = await db.execute("SELECT * FROM admin_state WHERE admin_id=?", (ADMIN_ID,))
    state = await cur.fetchone()
    if state:
        await process_admin_upload(message, state)

# Replace the upload state path with a small dispatcher hook:
# Admin text/media in broadcast_draft creates a queued job; content states save immediately.
_original_admin_message_handler = admin_message_handler

@router.message(F.from_user.id == ADMIN_ID)
async def admin_message_handler(message: Message):
    if message.text and message.text.startswith("/"):
        return
    cur = await db.execute("SELECT * FROM admin_state WHERE admin_id=?", (ADMIN_ID,))
    state = await cur.fetchone()
    if state:
        if state["state"] == "broadcast_draft":
            await create_broadcast(message)
            return
        if state["state"] in ("add_content", "add_preview"):
            await process_admin_upload(message, state)
            return
    if message.reply_to_message:
        cur = await db.execute(
            "SELECT user_id FROM admin_message_map WHERE admin_message_id=?",
            (message.reply_to_message.message_id,),
        )
        mapped = await cur.fetchone()
        if mapped:
            try:
                await bot.copy_message(
                    chat_id=mapped["user_id"], from_chat_id=message.chat.id,
                    message_id=message.message_id
                )
                await message.reply("✅ Жауап жіберілді.")
            except TelegramAPIError as e:
                await message.reply(f"Жіберу мүмкін болмады: {e}")
            return
    await message.answer("Админ панелін ашу: /admin")

# --------------------------- RECOVERY / STARTUP ---------------------------

async def resume_pending_broadcast():
    global broadcast_task
    cur = await db.execute("SELECT id FROM broadcast_jobs WHERE status='running' ORDER BY id DESC LIMIT 1")
    row = await cur.fetchone()
    if row:
        job_id = row["id"]
        log.info("Resuming broadcast job %s", job_id)
        broadcast_task = asyncio.create_task(run_broadcast(job_id))

async def register_commands():
    await bot.set_my_commands([
        BotCommand(command="start", description="Ботты бастау"),
    ])

async def main():
    global bot
    await init_db()
    bot = Bot(BOT_TOKEN)
    await register_commands()
    await resume_pending_broadcast()
    log.info("Bot started. DB=%s", DB_PATH)
    try:
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        await db.commit()
        await db.close()
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())
