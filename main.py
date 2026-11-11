# -*- coding: utf-8 -*-
"""
Telegram Content + Referral Bot
Python 3.11+
Railway-ready single file.

Install: pip install -U aiogram aiosqlite
Run: BOT_TOKEN=... ADMIN_ID=... python main.py
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
    BotCommand,
)
from aiogram.client.default import DefaultBotProperties

=
# ====================== CONFIG ======================
BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
ADMIN_ID_RAW = os.getenv("ADMIN_ID", "8942851703").strip()
DB_PATH = os.getenv("DB_PATH", "bot_data.sqlite3").strip()
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "JOKWRHUB18").strip().lstrip("@")

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN environment variable is missing")

try:
    ADMIN_ID = int(ADMIN_ID_RAW)
except (ValueError, TypeError):
    raise RuntimeError(
        f"ADMIN_ID дұрыс емес: '{ADMIN_ID_RAW}'. "
        "Railway Variables-қа тек сан қойыңыз (мысалы: 8942851703)"
    )

# ====================== TEXT ======================
CATEGORIES = ("kz", "kids", "ru", "us")

CATEGORY_LABELS = {
    "kz":   {"kk": "🇰🇿 Қазақша", "ru": "🇰🇿 Казахские"},
    "kids": {"kk": "🧸 Детские", "ru": "🧸 Детские"},
    "ru":   {"kk": "🇷🇺 Орысша", "ru": "🇷🇺 Русские"},
    "us":   {"kk": "🇺🇸 Американша", "ru": "🇺🇸 Американские"},
}

TEXT = {
    "kk": {
        "choose": "Тілді таңдаңыз:",
        "welcome": "🔥 ҚОШ КЕЛДІҢІЗ!\n\nҚалаған бөлімді таңдаңыз.",
        "channels": "📂 Каналдар",
        "free": "🎁 Тегін канал",
        "help": "ℹ️ Көмек",
        "contact": "💬 Админге жазу",
        "back": "⬅️ Артқа",
        "home": "🏠 Басты меню",
        "preview": "👁 Алдын ала көру",
        "buy": "🔞 Сатып алу",
        "no_preview": "Бұл бөлімде әзірге материал жоқ.",
        "buy_text": "Сатып алу туралы ақпарат алу үшін админге жазыңыз.",
        "contact_text": "Хабарламаңызды жазыңыз. Админге жіберіледі.",
        "sent": "✅ Хабарламаңыз жіберілді.",
        "blocked": "🚫 Ботты пайдалану шектелген.",
        "help_text": (
            "💡 НҰСҚАУЛЫҚ\n\n"
            "📂 Каналдар — категорияны таңдап, материалды көріңіз.\n"
            "🎁 Тегін канал — достарыңызды шақырып, тегін қол жеткізіңіз.\n"
            "💬 Админге жазу — сұрақтарыңыз болса жазыңыз."
        ),
        "ref_text": (
            "🎁 ТЕГІН КАНАЛ\n\n"
            "Жеке сілтемеңізді достарыңызға жіберіңіз.\n\n"
            "Сілтеме:\n{link}\n\n"
            "Шақырылған: {count} / {required}"
        ),
        "share": "Досыңа жіберу",
        "reward": "🎉 Құттықтаймыз!\nТегін канал:\n{link}",
        "admin_contact": "Админ: @{username}",
    },
    "ru": {
        "choose": "Выберите язык:",
        "welcome": "🔥 ДОБРО ПОЖАЛОВАТЬ!\n\nВыберите нужный раздел.",
        "channels": "📂 Каналы",
        "free": "🎁 Бесплатный канал",
        "help": "ℹ️ Помощь",
        "contact": "💬 Написать админу",
        "back": "⬅️ Назад",
        "home": "🏠 Главное меню",
        "preview": "👁 Предпросмотр",
        "buy": "🔞 Купить",
        "no_preview": "В этом разделе пока нет материалов.",
        "buy_text": "Напишите администратору для покупки.",
        "contact_text": "Напишите сообщение. Оно будет передано админу.",
        "sent": "✅ Ваше сообщение отправлено.",
        "blocked": "🚫 Доступ ограничен.",
        "help_text": (
            "💡 ИНСТРУКЦИЯ\n\n"
            "📂 Каналы — выберите категорию и посмотрите материалы.\n"
            "🎁 Бесплатный канал — приглашайте друзей и получите доступ.\n"
            "💬 Написать админу — если есть вопросы."
        ),
        "ref_text": (
            "🎁 БЕСПЛАТНЫЙ КАНАЛ\n\n"
            "Отправьте ссылку друзьям.\n\n"
            "Ваша ссылка:\n{link}\n\n"
            "Приглашено: {count} / {required}"
        ),
        "share": "Отправить другу",
        "reward": "🎉 Поздравляем!\nБесплатный канал:\n{link}",
        "admin_contact": "Админ: @{username}",
    },
}

# ====================== DATABASE ======================
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
CREATE TABLE IF NOT EXISTS settings (
  key TEXT PRIMARY KEY,
  value TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS content (
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
  category TEXT
);
CREATE TABLE IF NOT EXISTS broadcast_jobs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  status TEXT NOT NULL,
  file_type TEXT NOT NULL,
  file_id TEXT,
  caption TEXT,
  created_at INTEGER NOT NULL,
  sent_count INTEGER NOT NULL DEFAULT 0,
  failed_count INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS broadcast_recipients (
  job_id INTEGER NOT NULL,
  user_id INTEGER NOT NULL,
  status TEXT NOT NULL DEFAULT 'pending',
  PRIMARY KEY (job_id, user_id)
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
"""

async def init_db():
    global db
    db = await aiosqlite.connect(DB_PATH)
    db.row_factory = aiosqlite.Row
    await db.execute("PRAGMA journal_mode=WAL")
    await db.executescript(SCHEMA)
    defaults = {
        "referral_required": "3",
        "free_channel_url": "",
        "broadcast_delay": "0.07",
    }
    for k, v in defaults.items():
        await db.execute("INSERT OR IGNORE INTO settings(key,value) VALUES(?,?)", (k, v))
    await db.commit()

async def setting(key: str, default: str = "") -> str:
    cur = await db.execute("SELECT value FROM settings WHERE key=?", (key,))
    row = await cur.fetchone()
    return row["value"] if row else default

async def set_setting(key: str, value: str):
    await db.execute(
        "INSERT INTO settings(key,value) VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
        (key, str(value))
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
            (user.username, user.first_name, user.id)
        )
    else:
        if referrer_id == user.id:
            referrer_id = None
        await db.execute(
            """INSERT INTO users(user_id, username, first_name, language, joined_at, referrer_id)
               VALUES (?, ?, ?, '', ?, ?)""",
            (user.id, user.username, user.first_name, int(time.time()), referrer_id)
        )
        if referrer_id:
            ref = await get_user(referrer_id)
            if ref and not ref["is_blocked"]:
                await db.execute(
                    "INSERT OR IGNORE INTO referrals(invited_id, referrer_id, created_at) VALUES (?,?,?)",
                    (user.id, referrer_id, int(time.time()))
                )
                cur = await db.execute("SELECT changes() AS n")
                if (await cur.fetchone())["n"]:
                    await db.execute(
                        "UPDATE users SET referral_count = referral_count + 1 WHERE user_id=?",
                        (referrer_id,)
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
        "UPDATE users SET last_menu_chat_id=?, last_menu_message_id=? WHERE user_id=?",
        (chat_id, message_id, user_id)
    )
    await db.commit()

# ====================== KEYBOARDS ======================
def ikb(rows):
    return InlineKeyboardMarkup(inline_keyboard=rows)

def btn(text, data):
    return InlineKeyboardButton(text=text, callback_data=data)

def main_kb(lang):
    t = TEXT[lang]
    return ikb([
        [btn(t["channels"], "channels"), btn(t["free"], "free")],
        [btn(t["help"], "help"), btn(t["contact"], "contact")],
    ])

def back_kb(lang, target="home"):
    return ikb([[btn(TEXT[lang]["back"], target)]])

def categories_kb(lang):
    rows = [[btn(CATEGORY_LABELS[c][lang], f"cat:{c}")] for c in CATEGORIES]
    rows.append([btn(TEXT[lang]["back"], "home")])
    return ikb(rows)

def category_kb(lang, category):
    t = TEXT[lang]
    return ikb([
        [btn(t["preview"], f"preview:{category}")],
        [btn(t["buy"], f"buy:{category}")],
        [btn(t["back"], "channels")],
    ])

def admin_kb():
    return ikb([
        [btn("📂 Контент", "adm:content"), btn("📊 Статистика", "adm:stats")],
        [btn("📢 Рассылка", "adm:broadcast"), btn("🎁 Реферал", "adm:ref")],
        [btn("🔗 Тегін сілтеме", "adm:freeurl"), btn("🚫 Бұғаттау", "adm:block")],
        [btn("⏹ Рассылканы тоқтату", "adm:stop"), btn("🏠 Жабу", "adm:close")],
    ])

async def show_menu(target, user_id: int, text: str, keyboard):
    if isinstance(target, CallbackQuery):
        msg = target.message
        try:
            await msg.edit_text(text, reply_markup=keyboard)
            await save_menu(user_id, msg.chat.id, msg.message_id)
            return
        except TelegramBadRequest as e:
            if "message is not modified" in str(e).lower():
                return
        sent = await msg.answer(text, reply_markup=keyboard)
    else:
        sent = await target.answer(text, reply_markup=keyboard)
    await save_menu(user_id, sent.chat.id, sent.message_id)

# ====================== USER FLOW ======================
@router.message(CommandStart())
async def cmd_start(message: Message):
    args = (message.text or "").split(maxsplit=1)
    referrer = None
    if len(args) > 1 and args[1].startswith("ref_"):
        with suppress(ValueError):
            referrer = int(args[1][4:])

    await save_user(message.from_user, referrer)
    if referrer:
        await check_referral_reward(referrer)

    if await is_blocked(message.from_user.id):
        lang = await get_lang(message.from_user.id)
        await message.answer(TEXT[lang]["blocked"])
        return

    row = await get_user(message.from_user.id)
    if not row or not row["language"]:
        sent = await message.answer(
            TEXT["kk"]["choose"],
            reply_markup=ikb([
                [btn("🇰🇿 Қазақша", "lang:kk"), btn("🇷🇺 Русский", "lang:ru")]
            ])
        )
        await save_menu(message.from_user.id, sent.chat.id, sent.message_id)
    else:
        lang = row["language"]
        await show_menu(message, message.from_user.id, TEXT[lang]["welcome"], main_kb(lang))

@router.callback_query(F.data.startswith("lang:"))
async def set_lang(call: CallbackQuery):
    lang = call.data.split(":")[1]
    if lang not in ("kk", "ru"):
        return await call.answer()
    await set_language(call.from_user.id, lang)
    await call.answer()
    await show_menu(call, call.from_user.id, TEXT[lang]["welcome"], main_kb(lang))

@router.callback_query(F.data == "home")
async def home(call: CallbackQuery):
    lang = await get_lang(call.from_user.id)
    await call.answer()
    await show_menu(call, call.from_user.id, TEXT[lang]["welcome"], main_kb(lang))

@router.callback_query(F.data == "channels")
async def channels(call: CallbackQuery):
    lang = await get_lang(call.from_user.id)
    await call.answer()
    await show_menu(call, call.from_user.id, TEXT[lang]["channels"], categories_kb(lang))

@router.callback_query(F.data.startswith("cat:"))
async def category(call: CallbackQuery):
    cat = call.data.split(":")[1]
    if cat not in CATEGORIES:
        return await call.answer()
    lang = await get_lang(call.from_user.id)
    await call.answer()
    await show_menu(call, call.from_user.id, CATEGORY_LABELS[cat][lang], category_kb(lang, cat))

@router.callback_query(F.data.startswith("preview:"))
async def preview(call: CallbackQuery):
    cat = call.data.split(":")[1]
    if cat not in CATEGORIES:
        return await call.answer()
    lang = await get_lang(call.from_user.id)

    cur = await db.execute(
        "SELECT file_type, file_id, caption FROM content WHERE category=? ORDER BY id DESC LIMIT 8",
        (cat,)
    )
    items = await cur.fetchall()
    if not items:
        return await call.answer(TEXT[lang]["no_preview"], show_alert=True)

    await call.answer()
    for item in reversed(items):
        await send_content(call.from_user.id, item)

    await show_menu(call, call.from_user.id, CATEGORY_LABELS[cat][lang], category_kb(lang, cat))

@router.callback_query(F.data.startswith("buy:"))
async def buy(call: CallbackQuery):
    cat = call.data.split(":")[1]
    if cat not in CATEGORIES:
        return await call.answer()
    lang = await get_lang(call.from_user.id)

    await db.execute(
        "INSERT INTO purchases(user_id, category, created_at) VALUES (?,?,?)",
        (call.from_user.id, cat, int(time.time()))
    )
    await db.commit()

    await call.answer()
    await bot.send_message(
        ADMIN_ID,
        f"🛒 Сатып алу өтініші\n"
        f"ID: `{call.from_user.id}`\n"
        f"Username: @{call.from_user.username or 'жоқ'}\n"
        f"Категория: {CATEGORY_LABELS[cat]['kk']}\n\n"
        f"Жауап беру үшін осы хабарламаға Reply жасаңыз.",
        parse_mode=ParseMode.MARKDOWN
    )
    await bot.send_message(call.from_user.id, TEXT[lang]["buy_text"])
    await bot.send_message(call.from_user.id, f"💬 @{ADMIN_USERNAME}")
    await show_menu(call, call.from_user.id, CATEGORY_LABELS[cat][lang], category_kb(lang, cat))

@router.callback_query(F.data == "help")
async def help_h(call: CallbackQuery):
    lang = await get_lang(call.from_user.id)
    await call.answer()
    await show_menu(call, call.from_user.id, TEXT[lang]["help_text"], back_kb(lang))

@router.callback_query(F.data == "contact")
async def contact(call: CallbackQuery):
    lang = await get_lang(call.from_user.id)
    await call.answer()
    await bot.send_message(call.from_user.id, TEXT[lang]["contact_text"])
    await bot.send_message(call.from_user.id, f"💬 @{ADMIN_USERNAME}")
    await show_menu(
        call, call.from_user.id,
        TEXT[lang]["admin_contact"].format(username=ADMIN_USERNAME),
        back_kb(lang)
    )

@router.callback_query(F.data == "free")
async def free(call: CallbackQuery):
    lang = await get_lang(call.from_user.id)
    row = await get_user(call.from_user.id)
    me = await bot.get_me()
    link = f"https://t.me/{me.username}?start=ref_{call.from_user.id}"
    required = await setting("referral_required", "3")
    count = row["referral_count"] if row else 0

    text = TEXT[lang]["ref_text"].format(link=link, count=count, required=required)
    reward = await setting("free_channel_url", "")
    if row and row["reward_sent"] and reward:
        text += "\n\n" + TEXT[lang]["reward"].format(link=reward)

    kb = ikb([
        [InlineKeyboardButton(text=TEXT[lang]["share"], url=f"https://t.me/share/url?url={link}")],
        [btn(TEXT[lang]["back"], "home")],
    ])
    await call.answer()
    await show_menu(call, call.from_user.id, text, kb)

# ====================== CONTENT ======================
async def send_content(user_id: int, item):
    typ = item["file_type"]
    file_id = item["file_id"]
    caption = item["caption"] or None
    try:
        if typ == "text":
            await bot.send_message(user_id, caption or "")
        elif typ == "photo":
            await bot.send_photo(user_id, file_id, caption=caption)
        elif typ == "video":
            await bot.send_video(user_id, file_id, caption=caption)
        elif typ == "document":
            await bot.send_document(user_id, file_id, caption=caption)
        elif typ == "animation":
            await bot.send_animation(user_id, file_id, caption=caption)
    except Exception as e:
        log.warning("send_content failed for %s: %s", user_id, e)

async def check_referral_reward(user_id: int):
    row = await get_user(user_id)
    if not row or row["reward_sent"]:
        return
    required = int(await setting("referral_required", "3"))
    if row["referral_count"] >= required:
        link = await setting("free_channel_url", "")
        if link:
            lang = row["language"] or "kk"
            await bot.send_message(user_id, TEXT[lang]["reward"].format(link=link))
            await db.execute("UPDATE users SET reward_sent=1 WHERE user_id=?", (user_id,))
            await db.commit()

# ====================== USER → ADMIN ======================
@router.message(F.from_user.id != ADMIN_ID)
async def user_message(message: Message):
    if await is_blocked(message.from_user.id):
        return

    caption = (
        f"📩 Қолданушыдан\n"
        f"ID: `{message.from_user.id}`\n"
        f"Username: @{message.from_user.username or 'жоқ'}\n"
        f"Аты: {message.from_user.full_name}\n\n"
        f"Жауап беру үшін Reply жасаңыз."
    )
    try:
        if message.photo:
            fwd = await bot.send_photo(ADMIN_ID, message.photo[-1].file_id, caption=caption, parse_mode=ParseMode.MARKDOWN)
        elif message.video:
            fwd = await bot.send_video(ADMIN_ID, message.video.file_id, caption=caption, parse_mode=ParseMode.MARKDOWN)
        elif message.document:
            fwd = await bot.send_document(ADMIN_ID, message.document.file_id, caption=caption, parse_mode=ParseMode.MARKDOWN)
        elif message.voice:
            fwd = await bot.send_voice(ADMIN_ID, message.voice.file_id, caption=caption, parse_mode=ParseMode.MARKDOWN)
        elif message.text:
            fwd = await bot.send_message(ADMIN_ID, caption + "\n\n" + message.text, parse_mode=ParseMode.MARKDOWN)
        else:
            fwd = await bot.send_message(ADMIN_ID, caption + "\n\n[қолдау көрсетілмейтін формат]", parse_mode=ParseMode.MARKDOWN)

        await db.execute(
            "INSERT OR REPLACE INTO admin_message_map(admin_message_id, user_id, created_at) VALUES (?,?,?)",
            (fwd.message_id, message.from_user.id, int(time.time()))
        )
        await db.commit()
        lang = await get_lang(message.from_user.id)
        await message.answer(TEXT[lang]["sent"])
    except Exception:
        log.exception("forward failed")

# ====================== ADMIN ======================
@router.message(Command("admin"))
async def admin_panel(message: Message):
    if message.from_user.id != ADMIN_ID:
        return
    await message.answer("🛠 ӘКІМШІ ПАНЕЛІ", reply_markup=admin_kb())

@router.callback_query(F.data.startswith("adm:"))
async def admin_actions(call: CallbackQuery):
    if call.from_user.id != ADMIN_ID:
        return await call.answer("Рұқсат жоқ", show_alert=True)

    action = call.data.split(":")[1]
    await call.answer()

    if action == "close":
        with suppress(TelegramAPIError):
            await call.message.delete()
        return

    if action == "content":
        rows = [[btn(CATEGORY_LABELS[c]["kk"], f"admcat:{c}")] for c in CATEGORIES]
        rows.append([btn("⬅️ Артқа", "adm:back")])
        await call.message.edit_text("Контент жүктейтін категорияны таңдаңыз:", reply_markup=ikb(rows))

    elif action == "stats":
        cur = await db.execute("SELECT COUNT(*) n FROM users")
        total = (await cur.fetchone())["n"]
        cur = await db.execute("SELECT COUNT(*) n FROM users WHERE is_blocked=0")
        active = (await cur.fetchone())["n"]
        cur = await db.execute("SELECT COUNT(*) n FROM users WHERE is_blocked=1")
        blocked = (await cur.fetchone())["n"]
        cur = await db.execute("SELECT COUNT(*) n FROM referrals")
        refs = (await cur.fetchone())["n"]
        cur = await db.execute("SELECT COUNT(*) n FROM users WHERE reward_sent=1")
        rewards = (await cur.fetchone())["n"]
        cur = await db.execute("SELECT COUNT(*) n FROM purchases")
        buys = (await cur.fetchone())["n"]
        cur = await db.execute("SELECT language, COUNT(*) n FROM users GROUP BY language")
        langs = await cur.fetchall()
        lang_txt = "\n".join(f"  {r['language'] or '—'}: {r['n']}" for r in langs) or "  —"

        text = (
            f"📊 СТАТИСТИКА\n\n"
            f"👥 Барлығы: {total}\n"
            f"🟢 Белсенді: {active}\n"
            f"🚫 Бұғатталған: {blocked}\n"
            f"🔗 Шақырылған: {refs}\n"
            f"🎁 Тегін алған: {rewards}\n"
            f"🛒 Сатып алу: {buys}\n\n"
            f"🌐 Тілдер:\n{lang_txt}"
        )
        await call.message.edit_text(text, reply_markup=ikb([[btn("⬅️ Артқа", "adm:back")]]))

    elif action == "broadcast":
        await db.execute(
            "INSERT INTO admin_state(admin_id, state, category) VALUES (?,?,NULL) "
            "ON CONFLICT(admin_id) DO UPDATE SET state=excluded.state, category=NULL",
            (ADMIN_ID, "broadcast_draft")
        )
        await db.commit()
        await call.message.answer("📢 Рассылкаға мәтін / фото / видео жіберіңіз.\nТоқтату: /cancel")

    elif action == "ref":
        req = await setting("referral_required", "3")
        await call.message.edit_text(
            f"Қазіргі талап: {req} адам\nӨзгерту: /setref 5",
            reply_markup=ikb([[btn("⬅️ Артқа", "adm:back")]])
        )

    elif action == "freeurl":
        url = await setting("free_channel_url", "")
        await call.message.edit_text(
            f"Қазіргі сілтеме:\n{url or 'орнатылмаған'}\n\nЖаңа: /setfree https://t.me/...",
            reply_markup=ikb([[btn("⬅️ Артқа", "adm:back")]])
        )

    elif action == "block":
        await call.message.edit_text(
            "Бұғаттау: /block 123456789\nШығару: /unblock 123456789",
            reply_markup=ikb([[btn("⬅️ Артқа", "adm:back")]])
        )

    elif action == "stop":
        await stop_broadcast()
        await call.message.answer("⏹ Белсенді рассылка тоқтатылды.")

    elif action == "back":
        await call.message.edit_text("🛠 ӘКІМШІ ПАНЕЛІ", reply_markup=admin_kb())

@router.callback_query(F.data.startswith("admcat:"))
async def admin_cat(call: CallbackQuery):
    if call.from_user.id != ADMIN_ID:
        return
    cat = call.data.split(":")[1]
    if cat not in CATEGORIES:
        return
    await db.execute(
        "INSERT INTO admin_state(admin_id, state, category) VALUES (?,?,?) "
        "ON CONFLICT(admin_id) DO UPDATE SET state=excluded.state, category=excluded.category",
        (ADMIN_ID, "add_content", cat)
    )
    await db.commit()
    await call.answer()
    await call.message.answer(
        f"{CATEGORY_LABELS[cat]['kk']} бөліміне фото/видео/мәтін жіберіңіз.\n"
        f"Тоқтату: /cancel"
    )

# ====================== ADMIN UPLOAD & REPLY ======================
@router.message(F.from_user.id == ADMIN_ID)
async def admin_message(message: Message):
    if message.text and message.text.startswith("/"):
        return

    # Admin state
    cur = await db.execute("SELECT * FROM admin_state WHERE admin_id=?", (ADMIN_ID,))
    state = await cur.fetchone()

    if state:
        if state["state"] == "broadcast_draft":
            await create_broadcast(message)
            return
        if state["state"] == "add_content":
            await process_upload(message, state["category"])
            return

    # Reply to user
    if message.reply_to_message:
        cur = await db.execute(
            "SELECT user_id FROM admin_message_map WHERE admin_message_id=?",
            (message.reply_to_message.message_id,)
        )
        mapped = await cur.fetchone()
        if mapped:
            try:
                await bot.copy_message(
                    chat_id=mapped["user_id"],
                    from_chat_id=message.chat.id,
                    message_id=message.message_id
                )
                await message.reply("✅ Жауап жіберілді")
            except TelegramForbiddenError:
                await message.reply("Қолданушы ботты бұғаттаған")
            except Exception as e:
                await message.reply(f"Қате: {e}")
            return

    await message.answer("Админ панелі: /admin")

async def process_upload(message: Message, category: str):
    if message.text and message.text.startswith("/cancel"):
        await db.execute("DELETE FROM admin_state WHERE admin_id=?", (ADMIN_ID,))
        await db.commit()
        await message.answer("Тоқтатылды", reply_markup=admin_kb())
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
        await message.answer("Қолдау көрсетілетін формат: мәтін, фото, видео, құжат, GIF")
        return

    await db.execute(
        "INSERT INTO content(category, file_type, file_id, caption, created_at) VALUES (?,?,?,?,?)",
        (category, typ, file_id, caption, int(time.time()))
    )
    await db.commit()
    await message.answer("✅ Сақталды. Тағы жіберіңіз немесе /cancel")

# ====================== ADMIN COMMANDS ======================
@router.message(Command("cancel"))
async def cancel(message: Message):
    if message.from_user.id != ADMIN_ID:
        return
    await db.execute("DELETE FROM admin_state WHERE admin_id=?", (ADMIN_ID,))
    await db.commit()
    await message.answer("Тоқтатылды", reply_markup=admin_kb())

@router.message(Command("setref"))
async def setref(message: Message):
    if message.from_user.id != ADMIN_ID:
        return
    parts = (message.text or "").split()
    if len(parts) != 2 or not parts[1].isdigit() or int(parts[1]) < 1:
        return await message.answer("Қолдану: /setref 3")
    await set_setting("referral_required", parts[1])
    await message.answer(f"✅ Жаңа талап: {parts[1]}")
    # Барлық кім жеткен болса — сыйлық беру
    cur = await db.execute(
        "SELECT user_id FROM users WHERE reward_sent=0 AND referral_count >= ?",
        (int(parts[1]),)
    )
    for row in await cur.fetchall():
        await check_referral_reward(row["user_id"])

@router.message(Command("setfree"))
async def setfree(message: Message):
    if message.from_user.id != ADMIN_ID:
        return
    parts = (message.text or "").split(maxsplit=1)
    if len(parts) != 2 or not parts[1].startswith(("https://t.me/", "https://telegram.me/")):
        return await message.answer("Қолдану: /setfree https://t.me/канал")
    await set_setting("free_channel_url", parts[1].strip())
    await message.answer("✅ Тегін канал сілтемесі сақталды")

@router.message(Command("block"))
async def block(message: Message):
    if message.from_user.id != ADMIN_ID:
        return
    parts = (message.text or "").split()
    if len(parts) != 2 or not parts[1].isdigit():
        return await message.answer("Қолдану: /block 123456789")
    uid = int(parts[1])
    await db.execute("UPDATE users SET is_blocked=1 WHERE user_id=?", (uid,))
    await db.commit()
    await message.answer(f"🚫 {uid} бұғатталды")

@router.message(Command("unblock"))
async def unblock(message: Message):
    if message.from_user.id != ADMIN_ID:
        return
    parts = (message.text or "").split()
    if len(parts) != 2 or not parts[1].isdigit():
        return await message.answer("Қолдану: /unblock 123456789")
    uid = int(parts[1])
    await db.execute("UPDATE users SET is_blocked=0 WHERE user_id=?", (uid,))
    await db.commit()
    await message.answer(f"✅ {uid} шығарылды")

# ====================== BROADCAST ======================
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
        await message.answer("Формат қолдау таппайды")
        return

    cur = await db.execute(
        "INSERT INTO broadcast_jobs(status, file_type, file_id, caption, created_at) VALUES ('queued',?,?,?,?)",
        (typ, file_id, caption, int(time.time()))
    )
    job_id = cur.lastrowid

    cur = await db.execute("SELECT user_id FROM users WHERE is_blocked=0 ORDER BY user_id")
    users = await cur.fetchall()
    await db.executemany(
        "INSERT OR IGNORE INTO broadcast_recipients(job_id, user_id, status) VALUES (?,?, 'pending')",
        [(job_id, r["user_id"]) for r in users]
    )
    await db.commit()

    await message.answer(
        f"📢 Рассылка #{job_id} дайын\n"
        f"Алушылар: {len(users)}\n"
        f"Бастау: /startbroadcast {job_id}"
    )
    await db.execute("DELETE FROM admin_state WHERE admin_id=?", (ADMIN_ID,))
    await db.commit()

@router.message(Command("startbroadcast"))
async def start_bc(message: Message):
    global broadcast_task
    if message.from_user.id != ADMIN_ID:
        return
    parts = (message.text or "").split()
    if len(parts) != 2 or not parts[1].isdigit():
        return await message.answer("Қолдану: /startbroadcast JOB_ID")

    job_id = int(parts[1])
    cur = await db.execute("SELECT status FROM broadcast_jobs WHERE id=?", (job_id,))
    job = await cur.fetchone()
    if not job:
        return await message.answer("Табылмады")
    if broadcast_task and not broadcast_task.done():
        return await message.answer("Басқа рассылка жүріп жатыр")

    await db.execute("UPDATE broadcast_jobs SET status='running' WHERE id=?", (job_id,))
    await db.commit()
    broadcast_task = asyncio.create_task(run_broadcast(job_id))
    await message.answer(f"▶️ #{job_id} басталды\nТоқтату: /stopbroadcast")

async def run_broadcast(job_id: int):
    async with broadcast_lock:
        cur = await db.execute("SELECT * FROM broadcast_jobs WHERE id=?", (job_id,))
        job = await cur.fetchone()
        if not job:
            return

        delay = float(await setting("broadcast_delay", "0.07"))

        while True:
            cur = await db.execute(
                """SELECT r.user_id FROM broadcast_recipients r
                   JOIN users u ON u.user_id = r.user_id
                   WHERE r.job_id=? AND r.status='pending' AND u.is_blocked=0
                   ORDER BY r.user_id LIMIT 1""",
                (job_id,)
            )
            recipient = await cur.fetchone()
            if not recipient:
                await db.execute("UPDATE broadcast_jobs SET status='completed' WHERE id=?", (job_id,))
                await db.commit()
                with suppress(Exception):
                    await bot.send_message(ADMIN_ID, f"✅ Рассылка #{job_id} аяқталды")
                return

            # status check
            cur = await db.execute("SELECT status FROM broadcast_jobs WHERE id=?", (job_id,))
            if (await cur.fetchone())["status"] != "running":
                return

            uid = recipient["user_id"]
            try:
                fake = {"file_type": job["file_type"], "file_id": job["file_id"], "caption": job["caption"]}
                await send_content(uid, fake)
                await db.execute(
                    "UPDATE broadcast_recipients SET status='sent' WHERE job_id=? AND user_id=?",
                    (job_id, uid)
                )
                await db.execute(
                    "UPDATE broadcast_jobs SET sent_count = sent_count + 1 WHERE id=?",
                    (job_id,)
                )
            except TelegramRetryAfter as e:
                await db.commit()
                await asyncio.sleep(e.retry_after + 1)
                continue
            except TelegramForbiddenError:
                await db.execute(
                    "UPDATE broadcast_recipients SET status='failed' WHERE job_id=? AND user_id=?",
                    (job_id, uid)
                )
                await db.execute(
                    "UPDATE broadcast_jobs SET failed_count = failed_count + 1 WHERE id=?",
                    (job_id,)
                )
            except Exception:
                log.exception("broadcast fail %s", uid)
                await db.execute(
                    "UPDATE broadcast_recipients SET status='failed' WHERE job_id=? AND user_id=?",
                    (job_id, uid)
                )
                await db.execute(
                    "UPDATE broadcast_jobs SET failed_count = failed_count + 1 WHERE id=?",
                    (job_id,)
                )
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
async def stop_bc(message: Message):
    if message.from_user.id != ADMIN_ID:
        return
    await stop_broadcast()
    await message.answer("⏹ Тоқтатылды")

# ====================== START ======================
async def resume_pending():
    global broadcast_task
    cur = await db.execute("SELECT id FROM broadcast_jobs WHERE status='running' ORDER BY id DESC LIMIT 1")
    row = await cur.fetchone()
    if row:
        log.info("Resuming broadcast %s", row["id"])
        broadcast_task = asyncio.create_task(run_broadcast(row["id"]))

async def main():
    global bot
    await init_db()
    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    await bot.set_my_commands([BotCommand(command="start", description="Ботты бастау")])
    await resume_pending()
    log.info("Bot started | DB=%s", DB_PATH)
    try:
        await dp.start_polling(bot)
    finally:
        await db.close()
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())
