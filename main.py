# -*- coding: utf-8 -*-
"""
Telegram Content + Referral Bot
Полностью на русском для пользователей
Админ-панель на казахском
Обязательная подписка на канал + второй бот
"""

import asyncio
import logging
import time
from contextlib import suppress
from typing import Optional
from collections import defaultdict

import aiosqlite
from aiogram import Bot, Dispatcher, F, Router
from aiogram.enums import ParseMode, ChatMemberStatus
from aiogram.exceptions import (
    TelegramBadRequest, TelegramForbiddenError, TelegramRetryAfter, TelegramAPIError
)
from aiogram.filters import CommandStart, Command
from aiogram.types import (
    Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton,
    ReplyKeyboardMarkup, KeyboardButton, BotCommand, ReplyKeyboardRemove,
)
from aiogram.client.default import DefaultBotProperties

# ====================== CONFIG ======================
BOT_TOKEN = "9012314155:AAEODB1q2AAZRVYNUWAOOKHINL_WVSMF4Ryk"
ADMIN_ID = 8942851703
ADMIN_USERNAME = "JOKWRHUB18"
DB_PATH = "/data/bot.sqlite3"

# ========== ӨЗГЕРТУ КЕРЕК ==========
CHANNEL_ID = -3887449033                    # Канал ID (санмен)
CHANNEL_LINK = "https://t.me/jokerHubkz     # Канал сілтемесі
SECOND_BOT_USERNAME = "@qozdirushibot"          # Екінші бот username (@сыз)
SECOND_BOT_LINK = f"https://t.me/{qozdirushibot}"
# ===================================

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
log = logging.getLogger("bot")

router = Router()
dp = Dispatcher()
dp.include_router(router)
bot: Optional[Bot] = None
db: Optional[aiosqlite.Connection] = None

# Антиспам
user_message_times = defaultdict(list)
SPAM_LIMIT = 9
SPAM_WINDOW = 15

# ====================== ТЕКСТЫ (орысша) ======================
CATEGORIES = ("kz", "ru", "us")

CATEGORY_LABELS = {
    "kz": "🇰🇿 Казахские",
    "ru": "🇷🇺 Русские",
    "us": "🇺🇸 Американские",
}

TEXT = {
    "welcome": "🔥 ДОБРО ПОЖАЛОВАТЬ!\n\nВыберите нужный раздел.",
    "channels": "📂 Каналы",
    "free": "🎁 Бесплатный канал",
    "help": "ℹ️ Помощь",
    "contact": "💬 Написать админу",
    "home": "🏠 Главное меню",
    "preview": "👁 Предпросмотр",
    "buy": "🔞 Купить",
    "submit": "📤 Отправить видео",
    "no_preview": "В этом разделе пока нет материалов.",
    "buy_text": "Для покупки напишите администратору.",
    "contact_text": "Напишите сообщение. Оно будет передано администратору.",
    "sent": "✅ Ваше сообщение отправлено.",
    "blocked": "🚫 Доступ к боту ограничен.",
    "must_join": "⚠️ Для использования бота необходимо подписаться на канал:",
    "must_start_bot": "⚠️ Теперь нажмите Start в нашем втором боте:",
    "join_btn": "📢 Подписаться на канал",
    "check_sub_btn": "✅ Я подписался",
    "start_bot_btn": "🤖 Перейти в бота",
    "check_bot_btn": "✅ Готово",
    "not_joined": "❌ Вы ещё не подписаны на канал. Подпишитесь и нажмите «Я подписался».",
    "not_started": "❌ Сначала нажмите Start во втором боте, затем вернитесь и нажмите «Готово».",
    "help_text": (
        "💡 ИНСТРУКЦИЯ\n\n"
        "📂 Каналы — выберите категорию и посмотрите материалы.\n"
        "🎁 Бесплатный канал — приглашайте друзей и получите доступ.\n"
        "💬 Написать админу — если есть вопросы.\n"
        "📤 Отправить видео — выберите категорию и отправьте свои видео/фото."
    ),
    "ref_text": (
        "🎁 БЕСПЛАТНЫЙ КАНАЛ\n\n"
        "Отправьте свою ссылку друзьям.\n\n"
        "Ваша ссылка:\n{link}\n\n"
        "Приглашено: {count} / {required}"
    ),
    "reward": "🎉 Поздравляем!\nБесплатный канал:\n{link}",
    "submit_prompt": "Отправьте видео или фото в эту категорию.\nМожно отправлять несколько.\nЧтобы закончить — нажмите «Главное меню».",
    "submit_saved": "✅ Сохранено. Можете отправить ещё.",
}

# ====================== БАЗА ДАННЫХ ======================
SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
  user_id INTEGER PRIMARY KEY,
  username TEXT,
  first_name TEXT,
  language TEXT NOT NULL DEFAULT 'ru',
  joined_at INTEGER NOT NULL,
  referrer_id INTEGER,
  referral_count INTEGER NOT NULL DEFAULT 0,
  reward_sent INTEGER NOT NULL DEFAULT 0,
  is_blocked INTEGER NOT NULL DEFAULT 0,
  second_bot_checked INTEGER NOT NULL DEFAULT 0,
  submit_category TEXT
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
CREATE TABLE IF NOT EXISTS submissions (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL,
  category TEXT NOT NULL,
  file_type TEXT NOT NULL,
  file_id TEXT,
  caption TEXT,
  created_at INTEGER NOT NULL,
  status TEXT NOT NULL DEFAULT 'pending'
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
CREATE INDEX IF NOT EXISTS idx_submissions_cat ON submissions(category, status);
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
        "broadcast_delay": "0.08",
    }
    for k, v in defaults.items():
        await db.execute("INSERT OR IGNORE INTO settings(key, value) VALUES (?, ?)", (k, v))
    await db.commit()

async def setting(key: str, default: str = "") -> str:
    cur = await db.execute("SELECT value FROM settings WHERE key=?", (key,))
    row = await cur.fetchone()
    return row["value"] if row else default

async def set_setting(key: str, value: str):
    await db.execute(
        "INSERT INTO settings(key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
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
            """INSERT INTO users (user_id, username, first_name, language, joined_at, referrer_id)
               VALUES (?, ?, ?, 'ru', ?, ?)""",
            (user.id, user.username, user.first_name, int(time.time()), referrer_id)
        )
        if referrer_id:
            ref = await get_user(referrer_id)
            if ref and not ref["is_blocked"]:
                await db.execute(
                    "INSERT OR IGNORE INTO referrals (invited_id, referrer_id, created_at) VALUES (?, ?, ?)",
                    (user.id, referrer_id, int(time.time()))
                )
                cur = await db.execute("SELECT changes() AS n")
                if (await cur.fetchone())["n"]:
                    await db.execute(
                        "UPDATE users SET referral_count = referral_count + 1 WHERE user_id=?",
                        (referrer_id,)
                    )
    await db.commit()

async def set_submit_category(user_id: int, category: Optional[str]):
    await db.execute("UPDATE users SET submit_category=? WHERE user_id=?", (category, user_id))
    await db.commit()

# ====================== ПРОВЕРКА ПОДПИСКИ ======================
async def is_subscribed(user_id: int) -> bool:
    try:
        member = await bot.get_chat_member(chat_id=CHANNEL_ID, user_id=user_id)
        return member.status in {
            ChatMemberStatus.MEMBER,
            ChatMemberStatus.ADMINISTRATOR,
            ChatMemberStatus.CREATOR
        }
    except Exception as e:
        log.warning(f"Subscribe check failed: {e}")
        return False

async def check_access(message_or_call, user_id: int) -> bool:
    """Проверяет подписку на канал и второй бот. Возвращает True если всё ок."""
    # 1. Канал
    if not await is_subscribed(user_id):
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=TEXT["join_btn"], url=CHANNEL_LINK)],
            [InlineKeyboardButton(text=TEXT["check_sub_btn"], callback_data="check_sub")]
        ])
        text = TEXT["must_join"]
        if isinstance(message_or_call, CallbackQuery):
            await message_or_call.message.answer(text, reply_markup=kb)
            await message_or_call.answer()
        else:
            await message_or_call.answer(text, reply_markup=kb)
        return False

    # 2. Второй бот
    row = await get_user(user_id)
    if not row or not row["second_bot_checked"]:
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=TEXT["start_bot_btn"], url=SECOND_BOT_LINK)],
            [InlineKeyboardButton(text=TEXT["check_bot_btn"], callback_data="check_second_bot")]
        ])
        text = TEXT["must_start_bot"]
        if isinstance(message_or_call, CallbackQuery):
            await message_or_call.message.answer(text, reply_markup=kb)
            await message_or_call.answer()
        else:
            await message_or_call.answer(text, reply_markup=kb)
        return False

    return True

# ====================== КЛАВИАТУРЫ ======================
def main_kb():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=TEXT["channels"]), KeyboardButton(text=TEXT["free"])],
            [KeyboardButton(text=TEXT["help"]), KeyboardButton(text=TEXT["contact"])],
        ],
        resize_keyboard=True
    )

def categories_kb():
    buttons = [[KeyboardButton(text=CATEGORY_LABELS[c])] for c in CATEGORIES]
    buttons.append([KeyboardButton(text=TEXT["home"])])
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

def category_kb():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=TEXT["preview"]), KeyboardButton(text=TEXT["buy"])],
            [KeyboardButton(text=TEXT["submit"])],
            [KeyboardButton(text=TEXT["channels"]), KeyboardButton(text=TEXT["home"])],
        ],
        resize_keyboard=True
    )

def admin_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📂 Контент", callback_data="adm:content"),
         InlineKeyboardButton(text="📊 Статистика", callback_data="adm:stats")],
        [InlineKeyboardButton(text="📢 Рассылка", callback_data="adm:broadcast"),
         InlineKeyboardButton(text="🎁 Реферал", callback_data="adm:ref")],
        [InlineKeyboardButton(text="🔗 Тегін сілтеме", callback_data="adm:freeurl"),
         InlineKeyboardButton(text="🚫 Бұғаттау", callback_data="adm:block")],
        [InlineKeyboardButton(text="📥 Жіберілгендер", callback_data="adm:subs")],
        [InlineKeyboardButton(text="⏹ Рассылканы тоқтату", callback_data="adm:stop"),
         InlineKeyboardButton(text="🏠 Жабу", callback_data="adm:close")],
    ])

# ====================== АНТИСПАМ ======================
async def check_spam(user_id: int) -> bool:
    now = time.time()
    times = user_message_times[user_id]
    times.append(now)
    user_message_times[user_id] = [t for t in times if now - t < SPAM_WINDOW]
    return len(user_message_times[user_id]) >= SPAM_LIMIT

async def notify_admin_spam(user_id: int, username: str, full_name: str):
    text = (
        f"⚠️ СПАМ / ФЛУД анықталды\n\n"
        f"ID: `{user_id}`\n"
        f"Username: @{username or 'жоқ'}\n"
        f"Аты: {full_name}\n\n"
        f"Бұғаттайын ба?"
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Иә, бұғатта", callback_data=f"spamblock:{user_id}"),
            InlineKeyboardButton(text="❌ Жоқ", callback_data=f"spamignore:{user_id}"),
        ]
    ])
    try:
        await bot.send_message(ADMIN_ID, text, parse_mode=ParseMode.MARKDOWN, reply_markup=kb)
    except Exception:
        log.exception("spam notify failed")

# ====================== START ======================
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
        await message.answer(TEXT["blocked"], reply_markup=ReplyKeyboardRemove())
        return

    if not await check_access(message, message.from_user.id):
        return

    await message.answer(TEXT["welcome"], reply_markup=main_kb())

@router.callback_query(F.data == "check_sub")
async def cb_check_sub(call: CallbackQuery):
    if await is_subscribed(call.from_user.id):
        await call.answer("Подписка подтверждена ✅", show_alert=True)
        # Екінші ботты тексереміз
        if not await check_access(call, call.from_user.id):
            return
        await call.message.answer(TEXT["welcome"], reply_markup=main_kb())
    else:
        await call.answer(TEXT["not_joined"], show_alert=True)

@router.callback_query(F.data == "check_second_bot")
async def cb_check_second_bot(call: CallbackQuery):
    await db.execute("UPDATE users SET second_bot_checked=1 WHERE user_id=?", (call.from_user.id,))
    await db.commit()
    await call.answer("Принято ✅", show_alert=True)
    await call.message.answer(TEXT["welcome"], reply_markup=main_kb())

@router.callback_query(F.data.startswith("spamblock:"))
async def spam_block(call: CallbackQuery):
    if call.from_user.id != ADMIN_ID:
        return
    uid = int(call.data.split(":")[1])
    await db.execute("UPDATE users SET is_blocked=1 WHERE user_id=?", (uid,))
    await db.commit()
    await call.answer("Бұғатталды", show_alert=True)
    await call.message.edit_text(call.message.text + "\n\n✅ Бұғатталды")

@router.callback_query(F.data.startswith("spamignore:"))
async def spam_ignore(call: CallbackQuery):
    if call.from_user.id != ADMIN_ID:
        return
    await call.answer("Өткізілді", show_alert=True)
    await call.message.edit_text(call.message.text + "\n\n❌ Өткізілді")

# ====================== ПОЛЬЗОВАТЕЛЬСКОЕ МЕНЮ ======================
@router.message(F.text)
async def text_handler(message: Message):
    if message.from_user.id == ADMIN_ID:
        return

    if await is_blocked(message.from_user.id):
        return

    if not await check_access(message, message.from_user.id):
        return

    if await check_spam(message.from_user.id):
        await notify_admin_spam(message.from_user.id, message.from_user.username, message.from_user.full_name)
        return

    text = message.text.strip()

    if text == TEXT["home"]:
        await set_submit_category(message.from_user.id, None)
        await message.answer(TEXT["welcome"], reply_markup=main_kb())
        return

    if text == TEXT["channels"]:
        await set_submit_category(message.from_user.id, None)
        await message.answer("Выберите категорию:", reply_markup=categories_kb())
        return

    # Категория таңдау
    for cat, label in CATEGORY_LABELS.items():
        if text == label:
            await set_submit_category(message.from_user.id, f"view:{cat}")
            await message.answer(label, reply_markup=category_kb())
            return

    row = await get_user(message.from_user.id)
    current = row["submit_category"] if row else None

    if current and current.startswith("view:"):
        cat = current[5:]

        if text == TEXT["preview"]:
            cur = await db.execute(
                "SELECT file_type, file_id, caption FROM content WHERE category=? ORDER BY id DESC LIMIT 10",
                (cat,)
            )
            items = await cur.fetchall()
            if not items:
                await message.answer(TEXT["no_preview"])
            else:
                for item in reversed(items):
                    await send_content(message.from_user.id, item)
            return

        if text == TEXT["buy"]:
            await db.execute(
                "INSERT INTO purchases (user_id, category, created_at) VALUES (?, ?, ?)",
                (message.from_user.id, cat, int(time.time()))
            )
            await db.commit()
            await bot.send_message(
                ADMIN_ID,
                f"🛒 Сатып алу өтініші\n"
                f"ID: `{message.from_user.id}`\n"
                f"Username: @{message.from_user.username or 'жоқ'}\n"
                f"Категория: {CATEGORY_LABELS[cat]}\n\n"
                f"Жауап беру үшін Reply жасаңыз.",
                parse_mode=ParseMode.MARKDOWN
            )
            await message.answer(TEXT["buy_text"])
            await message.answer(f"💬 @{ADMIN_USERNAME}")
            return

        if text == TEXT["submit"]:
            await set_submit_category(message.from_user.id, cat)
            await message.answer(TEXT["submit_prompt"], reply_markup=ReplyKeyboardMarkup(
                keyboard=[[KeyboardButton(text=TEXT["home"])]], resize_keyboard=True
            ))
            return

    if text == TEXT["free"]:
        await set_submit_category(message.from_user.id, None)
        row = await get_user(message.from_user.id)
        me = await bot.get_me()
        link = f"https://t.me/{me.username}?start=ref_{message.from_user.id}"
        required = await setting("referral_required", "3")
        count = row["referral_count"] if row else 0
        txt = TEXT["ref_text"].format(link=link, count=count, required=required)
        reward = await setting("free_channel_url", "")
        if row and row["reward_sent"] and reward:
            txt += "\n\n" + TEXT["reward"].format(link=reward)
        await message.answer(txt, reply_markup=main_kb())
        return

    if text == TEXT["help"]:
        await set_submit_category(message.from_user.id, None)
        await message.answer(TEXT["help_text"], reply_markup=main_kb())
        return

    if text == TEXT["contact"]:
        await set_submit_category(message.from_user.id, None)
        await message.answer(TEXT["contact_text"])
        await message.answer(f"💬 @{ADMIN_USERNAME}", reply_markup=main_kb())
        return

    # Қалыпты мәтін — админге
    await forward_to_admin(message)

@router.message(F.content_type.in_({"photo", "video", "document", "animation"}))
async def media_handler(message: Message):
    if message.from_user.id == ADMIN_ID:
        return

    if await is_blocked(message.from_user.id):
        return

    if not await check_access(message, message.from_user.id):
        return

    if await check_spam(message.from_user.id):
        await notify_admin_spam(message.from_user.id, message.from_user.username, message.from_user.full_name)
        return

    row = await get_user(message.from_user.id)
    submit_cat = row["submit_category"] if row else None

    if submit_cat and submit_cat in CATEGORIES:
        typ, file_id, caption = None, None, message.caption or ""
        if message.photo:
            typ, file_id = "photo", message.photo[-1].file_id
        elif message.video:
            typ, file_id = "video", message.video.file_id
        elif message.document:
            typ, file_id = "document", message.document.file_id
        elif message.animation:
            typ, file_id = "animation", message.animation.file_id

        if typ:
            await db.execute(
                "INSERT INTO submissions (user_id, category, file_type, file_id, caption, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                (message.from_user.id, submit_cat, typ, file_id, caption, int(time.time()))
            )
            await db.commit()
            await message.answer(TEXT["submit_saved"])
            return

    await forward_to_admin(message)

async def forward_to_admin(message: Message):
    caption = (
        f"📩 Хабарлама\n"
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
        elif message.text:
            fwd = await bot.send_message(ADMIN_ID, caption + "\n\n" + message.text, parse_mode=ParseMode.MARKDOWN)
        else:
            fwd = await bot.send_message(ADMIN_ID, caption + "\n\n[Формат қолдау таппайды]", parse_mode=ParseMode.MARKDOWN)

        await db.execute(
            "INSERT OR REPLACE INTO admin_message_map (admin_message_id, user_id, created_at) VALUES (?, ?, ?)",
            (fwd.message_id, message.from_user.id, int(time.time()))
        )
        await db.commit()
        await message.answer(TEXT["sent"])
    except Exception:
        log.exception("forward failed")

# ====================== КОНТЕНТ ЖІБЕРУ ======================
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
        log.warning("send_content failed: %s", e)

async def check_referral_reward(user_id: int):
    row = await get_user(user_id)
    if not row or row["reward_sent"]:
        return
    required = int(await setting("referral_required", "3"))
    if row["referral_count"] >= required:
        link = await setting("free_channel_url", "")
        if link:
            await bot.send_message(user_id, TEXT["reward"].format(link=link))
            await db.execute("UPDATE users SET reward_sent=1 WHERE user_id=?", (user_id,))
            await db.commit()

# ====================== АДМИН ПАНЕЛІ ======================
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
        rows = [[InlineKeyboardButton(text=CATEGORY_LABELS[c], callback_data=f"admcat:{c}")] for c in CATEGORIES]
        rows.append([InlineKeyboardButton(text="⬅️ Артқа", callback_data="adm:back")])
        await call.message.edit_text("Контент жүктейтін категорияны таңдаңыз:", reply_markup=InlineKeyboardMarkup(inline_keyboard=rows))

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
        cur = await db.execute("SELECT COUNT(*) n FROM submissions WHERE status='pending'")
        pending_subs = (await cur.fetchone())["n"]

        text = (
            f"📊 СТАТИСТИКА\n\n"
            f"👥 Барлығы: {total}\n"
            f"🟢 Белсенді: {active}\n"
            f"🚫 Бұғатталған: {blocked}\n"
            f"🔗 Шақырылған: {refs}\n"
            f"🎁 Тегін алған: {rewards}\n"
            f"🛒 Сатып алу: {buys}\n"
            f"📥 Күтіп тұрған видео: {pending_subs}"
        )
        await call.message.edit_text(text, reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text="⬅️ Артқа", callback_data="adm:back")]]
        ))

    elif action == "broadcast":
        await db.execute(
            "INSERT INTO admin_state (admin_id, state, category) VALUES (?, 'broadcast_draft', NULL) "
            "ON CONFLICT(admin_id) DO UPDATE SET state='broadcast_draft', category=NULL",
            (ADMIN_ID,)
        )
        await db.commit()
        await call.message.answer("📢 Рассылкаға мәтін / фото / видео жіберіңіз.\nТоқтату: /cancel")

    elif action == "ref":
        req = await setting("referral_required", "3")
        await call.message.edit_text(
            f"Қазіргі талап: {req} адам\nӨзгерту: /setref 5",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="⬅️ Артқа", callback_data="adm:back")]])
        )

    elif action == "freeurl":
        url = await setting("free_channel_url", "")
        await call.message.edit_text(
            f"Қазіргі сілтеме:\n{url or 'орнатылмаған'}\n\nЖаңа: /setfree https://t.me/...",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="⬅️ Артқа", callback_data="adm:back")]])
        )

    elif action == "block":
        await call.message.edit_text(
            "Бұғаттау: /block 123456789\nШығару: /unblock 123456789",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="⬅️ Артқа", callback_data="adm:back")]])
        )

    elif action == "subs":
        rows = [[InlineKeyboardButton(text=CATEGORY_LABELS[c], callback_data=f"subcat:{c}")] for c in CATEGORIES]
        rows.append([InlineKeyboardButton(text="⬅️ Артқа", callback_data="adm:back")])
        await call.message.edit_text("Жіберілген видеоларды қай категориядан көреміз?", reply_markup=InlineKeyboardMarkup(inline_keyboard=rows))

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
        "INSERT INTO admin_state (admin_id, state, category) VALUES (?, 'add_content', ?) "
        "ON CONFLICT(admin_id) DO UPDATE SET state='add_content', category=excluded.category",
        (ADMIN_ID, cat)
    )
    await db.commit()
    await call.answer()
    await call.message.answer(
        f"{CATEGORY_LABELS[cat]} бөліміне фото/видео/мәтін жіберіңіз.\nТоқтату: /cancel"
    )

@router.callback_query(F.data.startswith("subcat:"))
async def show_submissions(call: CallbackQuery):
    if call.from_user.id != ADMIN_ID:
        return
    cat = call.data.split(":")[1]
    cur = await db.execute(
        "SELECT id, user_id, file_type, file_id, caption, created_at FROM submissions "
        "WHERE category=? AND status='pending' ORDER BY id DESC LIMIT 20",
        (cat,)
    )
    items = await cur.fetchall()
    if not items:
        await call.answer("Бұл категорияда жіберілген видео жоқ", show_alert=True)
        return

    await call.answer()
    await call.message.answer(f"📥 {CATEGORY_LABELS[cat]} — соңғы жіберілгендер:")

    for item in items:
        caption = f"ID: {item['id']} | User: {item['user_id']}\n{item['caption'] or ''}"
        try:
            if item["file_type"] == "photo":
                await bot.send_photo(ADMIN_ID, item["file_id"], caption=caption)
            elif item["file_type"] == "video":
                await bot.send_video(ADMIN_ID, item["file_id"], caption=caption)
            elif item["file_type"] == "document":
                await bot.send_document(ADMIN_ID, item["file_id"], caption=caption)
            elif item["file_type"] == "animation":
                await bot.send_animation(ADMIN_ID, item["file_id"], caption=caption)
        except Exception:
            pass
        await asyncio.sleep(0.3)

# ====================== АДМИН ХАБАРЛАМАЛАРЫ ======================
@router.message(F.from_user.id == ADMIN_ID)
async def admin_message(message: Message):
    if message.text and message.text.startswith("/"):
        return

    cur = await db.execute("SELECT * FROM admin_state WHERE admin_id=?", (ADMIN_ID,))
    state = await cur.fetchone()

    if state:
        if state["state"] == "broadcast_draft":
            await create_broadcast(message)
            return
        if state["state"] == "add_content":
            await process_upload(message, state["category"])
            return

    # Reply арқылы жауап
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
        "INSERT INTO content (category, file_type, file_id, caption, created_at) VALUES (?, ?, ?, ?, ?)",
        (category, typ, file_id, caption, int(time.time()))
    )
    await db.commit()
    await message.answer("✅ Сақталды. Тағы жіберіңіз немесе /cancel")

# ====================== АДМИН КОМАНДАЛАРЫ ======================
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
async def block_cmd(message: Message):
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
async def unblock_cmd(message: Message):
    if message.from_user.id != ADMIN_ID:
        return
    parts = (message.text or "").split()
    if len(parts) != 2 or not parts[1].isdigit():
        return await message.answer("Қолдану: /unblock 123456789")
    uid = int(parts[1])
    await db.execute("UPDATE users SET is_blocked=0 WHERE user_id=?", (uid,))
    await db.commit()
    await message.answer(f"✅ {uid} шығарылды")

# ====================== РАССЫЛКА ======================
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
        "INSERT INTO broadcast_jobs (status, file_type, file_id, caption, created_at) VALUES ('queued', ?, ?, ?, ?)",
        (typ, file_id, caption, int(time.time()))
    )
    job_id = cur.lastrowid

    cur = await db.execute("SELECT user_id FROM users WHERE is_blocked=0 ORDER BY user_id")
    users = await cur.fetchall()
    await db.executemany(
        "INSERT OR IGNORE INTO broadcast_recipients (job_id, user_id, status) VALUES (?, ?, 'pending')",
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

        delay = float(await setting("broadcast_delay", "0.08"))

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

# ====================== ІСКЕ ҚОСУ ======================
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
    await bot.set_my_commands([BotCommand(command="start", description="Запустить бота")])
    await resume_pending()
    log.info("Bot started | DB=%s", DB_PATH)
    try:
        await dp.start_polling(bot)
    finally:
        await db.close()
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())
