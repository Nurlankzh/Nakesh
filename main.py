#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Толық автоматтандырылған Telegram бот
Бір файл · INLINE-only · Бір негізгі меню · SQLite
Қазақша / Русский · Реферал · Рассылка · Админ панель
"""

import asyncio
import logging
import sqlite3
from datetime import datetime
from typing import Optional, List, Dict

from aiogram import Bot, Dispatcher, F, Router
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup
from aiogram.filters import Command, CommandStart
from aiogram.enums import ParseMode
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.exceptions import TelegramRetryAfter, TelegramForbiddenError, TelegramBadRequest
from aiogram.utils.keyboard import InlineKeyboardBuilder

# ====================== КОНФИГ ======================
BOT_TOKEN = "9012314155:AAEoGUo4q-0KmSZQKJIasyzX_YeK5YXr9fI"
ADMIN_ID = 8942851703
ADMIN_USERNAME = "JOKWRHUB18"
DB_PATH = "bot_database.db"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.FileHandler("bot.log", encoding="utf-8"), logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# ====================== ТІЛДЕР ======================
TEXTS = {
    "kk": {
        "choose_lang": "Тілді таңдаңыз / Выберите язык",
        "welcome": (
            "🔥 <b>ҚОШ КЕЛДІҢІЗ!</b>\n\n"
            "Сізді ерекше атмосфера, қызықты контент және ұмытылмас әсерлер күтеді. 😉\n\n"
            "Мұнда әркім өзіне ұнайтын бөлімді таба алады.\n\n"
            "✨ Қалаған категорияңызды таңдаңыз, алдын ала танысыңыз және өзіңізге ұнайтын контентті ашыңыз.\n\n"
            "💋 Кейбір қызықтарды сөзбен жеткізу мүмкін емес...\n\n"
            "Таңдау өзіңізде!"
        ),
        "main_menu": "🏠 <b>Басты меню</b>\n\nТөмендегі бөлімдердің бірін таңдаңыз:",
        "channels": "📂 <b>Каналдар</b>\n\nКатегорияны таңдаңыз:",
        "cat_kk": "🇰🇿 Қазақша каналдар",
        "cat_kids": "🧸 Детский каналдар",
        "cat_ru": "🇷🇺 Орысша каналдар",
        "cat_en": "🇺🇸 Американша каналдар",
        "preview": "👁 Алдын ала көру",
        "buy": "🔞 Сатып алу",
        "back": "🔙 Артқа",
        "to_main": "🏠 Басты меню",
        "free_channel": (
            "🎁 <b>Тегін канал</b>\n\n"
            "Досыңызды шақырып, тегін каналға қол жеткізіңіз!\n\n"
            "Өз жеке сілтемеңізді достарыңызбен бөлісіңіз. "
            "Қажетті адам санына жеткенде сілтеме автоматты беріледі."
        ),
        "share_link": "🔗 Досыңа жіберу",
        "share_bot": "📤 Ботты тарату",
        "help": (
            "💡 <b>БОТТЫ ҚОЛДАНУ НҰСҚАУЛЫҒЫ</b>\n\n"
            "📂 <b>Каналдар</b> — өзіңізге ұнайтын категорияны таңдаңыз. Қолжетімді контентпен алдын ала танысып, сатып алу туралы ақпарат ала аласыз.\n\n"
            "🎁 <b>Тегін канал</b> — арнайы сілтемеңізді достарыңызбен бөлісіп, жаңа қолданушыларды шақырыңыз. Қажетті шартты орындағаннан кейін тегін каналға қол жеткізе аласыз.\n\n"
            "💬 <b>Админге жазу</b> — сұрақтарыңыз немесе ұсыныстарыңыз болса, хабарлама қалдырыңыз.\n\n"
            "✨ Ботты пайдалану өте оңай. Қажетті бөлімді таңдап, нұсқауларды орындасаңыз жеткілікті!"
        ),
        "write_admin": "💬 <b>Админге жазу</b>\n\nХабарламаңызды жазыңыз. Админ жақын арада жауап береді.",
        "msg_sent": "✅ Хабарламаңыз админге жіберілді!",
        "buy_sent": (
            "🛒 <b>Сатып алу</b>\n\n"
            "Админге тікелей жазыңыз:\n\n"
            f"👉 @{ADMIN_USERNAME}\n\n"
            "Немесе төмендегі батырманы басыңыз."
        ),
        "no_preview": "⚠️ Бұл категорияда әзірге алдын ала көру контенті жоқ.",
        "ref_link": "🔗 Сіздің реферал сілтемеңіз:\n\n<code>{link}</code>\n\nДосыңыз осы сілтеме арқылы кірсе, сізге есептеледі.",
        "ref_progress": "📊 Сіз шақырған адамдар: <b>{count}</b>\nҚажетті: <b>{needed}</b>",
        "ref_done": "🎉 Құттықтаймыз! Тегін канал сілтемесі:\n\n{link}",
        "already_got": "✅ Сіз тегін каналды бұрын алғансыз.",
        "blocked": "🚫 Сіз бұғатталғансыз. Ботты пайдалана алмайсыз.",
        "admin_panel": "⚙️ <b>АДМИН ПАНЕЛІ</b>\n\nБөлімді таңдаңыз:",
    },
    "ru": {
        "choose_lang": "Тілді таңдаңыз / Выберите язык",
        "welcome": (
            "🔥 <b>ДОБРО ПОЖАЛОВАТЬ!</b>\n\n"
            "Вас ждёт особенная атмосфера, интересный контент и незабываемые впечатления. 😉\n\n"
            "Здесь каждый найдёт раздел по душе.\n\n"
            "✨ Выберите желаемую категорию, ознакомьтесь заранее и откройте контент, который вам нравится.\n\n"
            "💋 Некоторые вещи невозможно передать словами...\n\n"
            "Выбор за вами!"
        ),
        "main_menu": "🏠 <b>Главное меню</b>\n\nВыберите один из разделов ниже:",
        "channels": "📂 <b>Каналы</b>\n\nВыберите категорию:",
        "cat_kk": "🇰🇿 Казахские каналы",
        "cat_kids": "🧸 Детские каналы",
        "cat_ru": "🇷🇺 Русские каналы",
        "cat_en": "🇺🇸 Американские каналы",
        "preview": "👁 Предпросмотр",
        "buy": "🔞 Купить",
        "back": "🔙 Назад",
        "to_main": "🏠 Главное меню",
        "free_channel": (
            "🎁 <b>Бесплатный канал</b>\n\n"
            "Пригласите друзей и получите доступ к бесплатному каналу!\n\n"
            "Поделитесь своей личной ссылкой с друзьями. "
            "Когда наберётся нужное количество — ссылка выдастся автоматически."
        ),
        "share_link": "🔗 Отправить другу",
        "share_bot": "📤 Распространить бота",
        "help": (
            "💡 <b>ИНСТРУКЦИЯ ПО ИСПОЛЬЗОВАНИЮ БОТА</b>\n\n"
            "📂 <b>Каналы</b> — выберите понравившуюся категорию. Можете ознакомиться с доступным контентом и получить информацию о покупке.\n\n"
            "🎁 <b>Бесплатный канал</b> — поделитесь своей специальной ссылкой с друзьями и пригласите новых пользователей. После выполнения условия получите доступ к бесплатному каналу.\n\n"
            "💬 <b>Написать админу</b> — если есть вопросы или предложения, оставьте сообщение.\n\n"
            "✨ Пользоваться ботом очень просто. Выберите нужный раздел и следуйте инструкциям!"
        ),
        "write_admin": "💬 <b>Написать админу</b>\n\nНапишите ваше сообщение. Админ ответит в ближайшее время.",
        "msg_sent": "✅ Ваше сообщение отправлено админу!",
        "buy_sent": (
            "🛒 <b>Покупка</b>\n\n"
            "Напишите админу напрямую:\n\n"
            f"👉 @{ADMIN_USERNAME}\n\n"
            "Или нажмите кнопку ниже."
        ),
        "no_preview": "⚠️ В этой категории пока нет контента для предпросмотра.",
        "ref_link": "🔗 Ваша реферальная ссылка:\n\n<code>{link}</code>\n\nЕсли друг зайдёт по этой ссылке — вам засчитается.",
        "ref_progress": "📊 Приглашено вами: <b>{count}</b>\nНужно: <b>{needed}</b>",
        "ref_done": "🎉 Поздравляем! Ссылка на бесплатный канал:\n\n{link}",
        "already_got": "✅ Вы уже получили бесплатный канал.",
        "blocked": "🚫 Вы заблокированы. Не можете пользоваться ботом.",
        "admin_panel": "⚙️ <b>АДМИН-ПАНЕЛЬ</b>\n\nВыберите раздел:",
    }
}

CATEGORIES = {
    "kk": "cat_kk",
    "kids": "cat_kids",
    "ru": "cat_ru",
    "en": "cat_en",
}

# ====================== FSM ======================
class AdminStates(StatesGroup):
    waiting_content = State()
    waiting_broadcast = State()
    waiting_ref_count = State()
    waiting_free_link = State()
    waiting_block_id = State()
    waiting_unblock_id = State()

class UserStates(StatesGroup):
    waiting_admin_msg = State()

# ====================== DATABASE ======================
class Database:
    def __init__(self, path: str = DB_PATH):
        self.path = path
        self._init_db()

    def _conn(self):
        conn = sqlite3.connect(self.path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        conn = self._conn()
        cur = conn.cursor()
        cur.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            language TEXT DEFAULT 'kk',
            referrer_id INTEGER,
            referrals_count INTEGER DEFAULT 0,
            got_free INTEGER DEFAULT 0,
            is_blocked INTEGER DEFAULT 0,
            is_bot_blocked INTEGER DEFAULT 0,
            created_at TEXT,
            last_active TEXT,
            main_message_id INTEGER
        );
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT
        );
        CREATE TABLE IF NOT EXISTS content (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT NOT NULL,
            file_id TEXT,
            file_type TEXT,
            caption TEXT,
            created_at TEXT
        );
        CREATE TABLE IF NOT EXISTS referrals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            referrer_id INTEGER,
            referred_id INTEGER UNIQUE,
            created_at TEXT
        );
        CREATE TABLE IF NOT EXISTS blacklist (
            user_id INTEGER PRIMARY KEY,
            reason TEXT,
            created_at TEXT
        );
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            from_id INTEGER,
            to_id INTEGER,
            text TEXT,
            file_id TEXT,
            file_type TEXT,
            category TEXT,
            is_admin INTEGER DEFAULT 0,
            created_at TEXT
        );
        CREATE TABLE IF NOT EXISTS broadcast_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            total INTEGER,
            success INTEGER,
            failed INTEGER,
            created_at TEXT
        );
        CREATE TABLE IF NOT EXISTS purchases (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            category TEXT,
            status TEXT DEFAULT 'new',
            created_at TEXT
        );
        CREATE TABLE IF NOT EXISTS bot_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            message_id INTEGER NOT NULL,
            created_at TEXT
        );
        """)
        cur.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('ref_needed', '3')")
        cur.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('free_channel_link', '')")
        conn.commit()
        conn.close()

    def get_setting(self, key: str, default: str = "") -> str:
        conn = self._conn()
        row = conn.execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
        conn.close()
        return row["value"] if row else default

    def set_setting(self, key: str, value: str):
        conn = self._conn()
        conn.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, value))
        conn.commit()
        conn.close()

    def add_user(self, user_id: int, username: str = None, first_name: str = None,
                 language: str = "kk", referrer_id: int = None):
        conn = self._conn()
        now = datetime.now().isoformat()
        conn.execute(
            "INSERT OR IGNORE INTO users (user_id, username, first_name, language, referrer_id, created_at, last_active) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (user_id, username, first_name, language, referrer_id, now, now)
        )
        if referrer_id and referrer_id != user_id:
            exists = conn.execute("SELECT 1 FROM referrals WHERE referred_id = ?", (user_id,)).fetchone()
            if not exists:
                conn.execute(
                    "INSERT INTO referrals (referrer_id, referred_id, created_at) VALUES (?, ?, ?)",
                    (referrer_id, user_id, now)
                )
                conn.execute(
                    "UPDATE users SET referrals_count = referrals_count + 1 WHERE user_id = ?",
                    (referrer_id,)
                )
        conn.commit()
        conn.close()

    def update_user(self, user_id: int, **kwargs):
        if not kwargs:
            return
        conn = self._conn()
        sets = ", ".join(f"{k} = ?" for k in kwargs)
        conn.execute(f"UPDATE users SET {sets} WHERE user_id = ?", list(kwargs.values()) + [user_id])
        conn.commit()
        conn.close()

    def get_user(self, user_id: int) -> Optional[Dict]:
        conn = self._conn()
        row = conn.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)).fetchone()
        conn.close()
        return dict(row) if row else None

    def is_blocked(self, user_id: int) -> bool:
        conn = self._conn()
        row = conn.execute("SELECT 1 FROM blacklist WHERE user_id = ?", (user_id,)).fetchone()
        conn.close()
        return bool(row)

    def block_user(self, user_id: int, reason: str = ""):
        conn = self._conn()
        now = datetime.now().isoformat()
        conn.execute(
            "INSERT OR REPLACE INTO blacklist (user_id, reason, created_at) VALUES (?, ?, ?)",
            (user_id, reason, now)
        )
        conn.execute("UPDATE users SET is_blocked = 1 WHERE user_id = ?", (user_id,))
        conn.commit()
        conn.close()

    def unblock_user(self, user_id: int):
        conn = self._conn()
        conn.execute("DELETE FROM blacklist WHERE user_id = ?", (user_id,))
        conn.execute("UPDATE users SET is_blocked = 0 WHERE user_id = ?", (user_id,))
        conn.commit()
        conn.close()

    def get_blacklist(self) -> List[Dict]:
        conn = self._conn()
        rows = conn.execute("SELECT * FROM blacklist ORDER BY created_at DESC").fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def save_bot_message(self, user_id: int, message_id: int):
        conn = self._conn()
        now = datetime.now().isoformat()
        conn.execute(
            "INSERT INTO bot_messages (user_id, message_id, created_at) VALUES (?, ?, ?)",
            (user_id, message_id, now)
        )
        # Соңғы 60 хабарламаны ғана сақтау
        conn.execute("""
            DELETE FROM bot_messages WHERE user_id = ? AND id NOT IN (
                SELECT id FROM bot_messages WHERE user_id = ? ORDER BY id DESC LIMIT 60
            )
        """, (user_id, user_id))
        conn.commit()
        conn.close()

    def get_bot_messages(self, user_id: int) -> List[int]:
        conn = self._conn()
        rows = conn.execute("SELECT message_id FROM bot_messages WHERE user_id = ?", (user_id,)).fetchall()
        conn.close()
        return [r["message_id"] for r in rows]

    def clear_bot_messages(self, user_id: int):
        conn = self._conn()
        conn.execute("DELETE FROM bot_messages WHERE user_id = ?", (user_id,))
        conn.commit()
        conn.close()

    def add_content(self, category: str, file_id: str, file_type: str, caption: str = ""):
        conn = self._conn()
        now = datetime.now().isoformat()
        conn.execute(
            "INSERT INTO content (category, file_id, file_type, caption, created_at) VALUES (?, ?, ?, ?, ?)",
            (category, file_id, file_type, caption, now)
        )
        conn.commit()
        conn.close()

    def get_content(self, category: str) -> List[Dict]:
        conn = self._conn()
        rows = conn.execute("SELECT * FROM content WHERE category = ? ORDER BY id", (category,)).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def clear_content(self, category: str):
        conn = self._conn()
        conn.execute("DELETE FROM content WHERE category = ?", (category,))
        conn.commit()
        conn.close()

    def add_message(self, from_id: int, to_id: int, text: str = "", file_id: str = None,
                    file_type: str = None, category: str = None, is_admin: int = 0):
        conn = self._conn()
        now = datetime.now().isoformat()
        conn.execute(
            "INSERT INTO messages (from_id, to_id, text, file_id, file_type, category, is_admin, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (from_id, to_id, text, file_id, file_type, category, is_admin, now)
        )
        conn.commit()
        conn.close()

    def add_purchase(self, user_id: int, category: str):
        conn = self._conn()
        now = datetime.now().isoformat()
        conn.execute(
            "INSERT INTO purchases (user_id, category, created_at) VALUES (?, ?, ?)",
            (user_id, category, now)
        )
        conn.commit()
        conn.close()

    def mark_got_free(self, user_id: int):
        self.update_user(user_id, got_free=1)

    def get_stats(self) -> Dict:
        conn = self._conn()
        s = {}
        s["total_users"] = conn.execute("SELECT COUNT(*) as c FROM users").fetchone()["c"]
        s["active"] = conn.execute("SELECT COUNT(*) as c FROM users WHERE is_bot_blocked = 0").fetchone()["c"]
        s["bot_blocked"] = conn.execute("SELECT COUNT(*) as c FROM users WHERE is_bot_blocked = 1").fetchone()["c"]
        s["blacklist"] = conn.execute("SELECT COUNT(*) as c FROM blacklist").fetchone()["c"]
        s["kk"] = conn.execute("SELECT COUNT(*) as c FROM users WHERE language = 'kk'").fetchone()["c"]
        s["ru"] = conn.execute("SELECT COUNT(*) as c FROM users WHERE language = 'ru'").fetchone()["c"]
        row = conn.execute("SELECT SUM(referrals_count) as c FROM users").fetchone()
        s["total_refs"] = row["c"] or 0
        s["got_free"] = conn.execute("SELECT COUNT(*) as c FROM users WHERE got_free = 1").fetchone()["c"]
        s["purchases"] = conn.execute("SELECT COUNT(*) as c FROM purchases").fetchone()["c"]
        conn.close()
        return s

    def get_all_user_ids(self, exclude_blocked: bool = True) -> List[int]:
        conn = self._conn()
        if exclude_blocked:
            rows = conn.execute(
                "SELECT user_id FROM users WHERE is_blocked = 0 AND is_bot_blocked = 0"
            ).fetchall()
        else:
            rows = conn.execute("SELECT user_id FROM users").fetchall()
        conn.close()
        return [r["user_id"] for r in rows]

db = Database()

# ====================== KEYBOARDS ======================
def lang_kb() -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="🇰🇿 Қазақша", callback_data="lang:kk")
    b.button(text="🇷🇺 Русский", callback_data="lang:ru")
    b.adjust(2)
    return b.as_markup()

def main_menu_kb(lang: str) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    if lang == "kk":
        b.button(text="📂 Каналдар", callback_data="menu:channels")
        b.button(text="🎁 Тегін канал", callback_data="menu:free")
        b.button(text="ℹ️ Көмекші", callback_data="menu:help")
        b.button(text="💬 Админге жазу", callback_data="menu:admin_chat")
    else:
        b.button(text="📂 Каналы", callback_data="menu:channels")
        b.button(text="🎁 Бесплатный канал", callback_data="menu:free")
        b.button(text="ℹ️ Помощь", callback_data="menu:help")
        b.button(text="💬 Написать админу", callback_data="menu:admin_chat")
    b.adjust(2)
    return b.as_markup()

def channels_kb(lang: str) -> InlineKeyboardMarkup:
    t = TEXTS[lang]
    b = InlineKeyboardBuilder()
    b.button(text=t["cat_kk"], callback_data="cat:kk")
    b.button(text=t["cat_kids"], callback_data="cat:kids")
    b.button(text=t["cat_ru"], callback_data="cat:ru")
    b.button(text=t["cat_en"], callback_data="cat:en")
    b.button(text=t["back"], callback_data="menu:main")
    b.adjust(1)
    return b.as_markup()

def category_kb(lang: str, cat: str) -> InlineKeyboardMarkup:
    t = TEXTS[lang]
    b = InlineKeyboardBuilder()
    b.button(text=t["preview"], callback_data=f"preview:{cat}")
    b.button(text=t["buy"], callback_data=f"buy:{cat}")
    b.button(text=t["back"], callback_data="menu:channels")
    b.button(text=t["to_main"], callback_data="menu:main")
    b.adjust(2)
    return b.as_markup()

def free_kb(lang: str) -> InlineKeyboardMarkup:
    t = TEXTS[lang]
    b = InlineKeyboardBuilder()
    b.button(text=t["share_link"], callback_data="ref:link")
    b.button(text=t["share_bot"], callback_data="ref:share")
    b.button(text=t["back"], callback_data="menu:main")
    b.adjust(1)
    return b.as_markup()

def back_main_kb(lang: str) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text=TEXTS[lang]["to_main"], callback_data="menu:main")
    return b.as_markup()

def admin_panel_kb() -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="📂 Контент басқару", callback_data="admin:content")
    b.button(text="📊 Статистика", callback_data="admin:stats")
    b.button(text="📢 Рассылка", callback_data="admin:broadcast")
    b.button(text="👥 Қолданушылар", callback_data="admin:users")
    b.button(text="🚫 Бұғаттау жүйесі", callback_data="admin:blacklist")
    b.button(text="🎁 Реферал баптаулары", callback_data="admin:ref")
    b.button(text="🔗 Тегін канал сілтемесі", callback_data="admin:free_link")
    b.button(text="💬 Хат алмасу", callback_data="admin:chat")
    b.button(text="⚙️ Бот баптаулары", callback_data="admin:settings")
    b.adjust(1)
    return b.as_markup()

def admin_content_kb() -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    for code, key in CATEGORIES.items():
        b.button(text=TEXTS["kk"][key], callback_data=f"admin_cat:{code}")
    b.button(text="🔙 Админ панель", callback_data="admin:panel")
    b.adjust(1)
    return b.as_markup()

def admin_cat_actions_kb(cat: str) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="➕ Контент қосу", callback_data=f"admin_add:{cat}")
    b.button(text="👁 Көру", callback_data=f"admin_view:{cat}")
    b.button(text="🗑 Тазалау", callback_data=f"admin_clear:{cat}")
    b.button(text="🔙 Артқа", callback_data="admin:content")
    b.adjust(1)
    return b.as_markup()

def admin_ref_kb() -> InlineKeyboardMarkup:
    needed = db.get_setting("ref_needed", "3")
    b = InlineKeyboardBuilder()
    b.button(text=f"Қазіргі: {needed} → Өзгерту", callback_data="admin:set_ref")
    b.button(text="🔙 Админ панель", callback_data="admin:panel")
    b.adjust(1)
    return b.as_markup()

def admin_blacklist_kb() -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="🚫 Бұғаттау (ID)", callback_data="admin:block")
    b.button(text="♻️ Бұғаттан шығару (ID)", callback_data="admin:unblock")
    b.button(text="📋 Қара тізім", callback_data="admin:list_bl")
    b.button(text="🔙 Админ панель", callback_data="admin:panel")
    b.adjust(1)
    return b.as_markup()

def confirm_bc_kb() -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="✅ Жіберу", callback_data="bc:confirm")
    b.button(text="❌ Бас тарту", callback_data="bc:cancel")
    b.adjust(2)
    return b.as_markup()

def stop_bc_kb() -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="⏹ ТОҚТАТУ", callback_data="bc:stop")
    return b.as_markup()

# ====================== HELPERS ======================
async def safe_edit(message: Message, text: str, reply_markup=None):
    try:
        await message.edit_text(text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)
    except TelegramBadRequest as e:
        if "message is not modified" not in str(e).lower():
            try:
                await message.answer(text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)
            except Exception:
                pass

def get_lang(user_id: int) -> str:
    user = db.get_user(user_id)
    return (user["language"] if user else "kk") or "kk"

# ====================== BOT ======================
bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)
router = Router()
dp.include_router(router)

broadcast_stop = False
pending_broadcast: Dict = {}

# ====================== USER HANDLERS ======================
@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    user_id = message.from_user.id
    username = message.from_user.username
    first_name = message.from_user.first_name

    referrer_id = None
    args = message.text.split()
    if len(args) > 1 and args[1].startswith("ref_"):
        try:
            rid = int(args[1].replace("ref_", ""))
            if rid != user_id:
                referrer_id = rid
        except ValueError:
            pass

    if db.is_blocked(user_id):
        await message.answer(TEXTS["kk"]["blocked"])
        return

    user = db.get_user(user_id)
    if not user:
        db.add_user(user_id, username, first_name, "kk", referrer_id)
        msg = await message.answer(TEXTS["kk"]["choose_lang"], reply_markup=lang_kb())
        db.update_user(user_id, main_message_id=msg.message_id)
        db.save_bot_message(user_id, msg.message_id)
    else:
        db.update_user(
            user_id,
            username=username,
            first_name=first_name,
            last_active=datetime.now().isoformat()
        )
        lang = user["language"] or "kk"
        text = TEXTS[lang]["welcome"] + "\n\n" + TEXTS[lang]["main_menu"]
        msg = await message.answer(text, reply_markup=main_menu_kb(lang), parse_mode=ParseMode.HTML)
        db.update_user(user_id, main_message_id=msg.message_id)
        db.save_bot_message(user_id, msg.message_id)

@router.callback_query(F.data.startswith("lang:"))
async def set_language(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    lang = callback.data.split(":")[1]
    user_id = callback.from_user.id
    if db.is_blocked(user_id):
        await safe_edit(callback.message, TEXTS["kk"]["blocked"])
        return
    db.update_user(user_id, language=lang)
    text = TEXTS[lang]["welcome"] + "\n\n" + TEXTS[lang]["main_menu"]
    await safe_edit(callback.message, text, main_menu_kb(lang))

@router.callback_query(F.data == "menu:main")
async def menu_main(callback: CallbackQuery):
    await callback.answer()
    user_id = callback.from_user.id
    if db.is_blocked(user_id):
        await safe_edit(callback.message, TEXTS["kk"]["blocked"])
        return
    lang = get_lang(user_id)
    text = TEXTS[lang]["welcome"] + "\n\n" + TEXTS[lang]["main_menu"]
    await safe_edit(callback.message, text, main_menu_kb(lang))

@router.callback_query(F.data == "menu:channels")
async def menu_channels(callback: CallbackQuery):
    await callback.answer()
    user_id = callback.from_user.id
    if db.is_blocked(user_id):
        return
    lang = get_lang(user_id)
    await safe_edit(callback.message, TEXTS[lang]["channels"], channels_kb(lang))

@router.callback_query(F.data.startswith("cat:"))
async def category_view(callback: CallbackQuery):
    await callback.answer()
    user_id = callback.from_user.id
    if db.is_blocked(user_id):
        return
    cat = callback.data.split(":")[1]
    lang = get_lang(user_id)
    cat_name = TEXTS[lang][CATEGORIES[cat]]
    text = f"{cat_name}\n\n{TEXTS[lang]['preview']} / {TEXTS[lang]['buy']}"
    await safe_edit(callback.message, text, category_kb(lang, cat))

@router.callback_query(F.data.startswith("preview:"))
async def preview_content(callback: CallbackQuery):
    await callback.answer()
    user_id = callback.from_user.id
    if db.is_blocked(user_id):
        return
    cat = callback.data.split(":")[1]
    lang = get_lang(user_id)
    contents = db.get_content(cat)
    if not contents:
        msg = await callback.message.answer(TEXTS[lang]["no_preview"])
        db.save_bot_message(user_id, msg.message_id)
        return

    for c in contents[:5]:
        try:
            sent = None
            if c["file_type"] == "photo":
                sent = await bot.send_photo(user_id, c["file_id"], caption=c["caption"] or None)
            elif c["file_type"] == "video":
                sent = await bot.send_video(user_id, c["file_id"], caption=c["caption"] or None)
            else:
                sent = await bot.send_message(user_id, c["caption"] or c["file_id"])
            if sent:
                db.save_bot_message(user_id, sent.message_id)
            await asyncio.sleep(0.25)
        except Exception as e:
            logger.error(f"Preview error: {e}")

    cat_name = TEXTS[lang][CATEGORIES[cat]]
    text = f"{cat_name}\n\n{TEXTS[lang]['preview']} / {TEXTS[lang]['buy']}"
    try:
        await callback.message.edit_text(text, reply_markup=category_kb(lang, cat), parse_mode=ParseMode.HTML)
    except Exception:
        pass

@router.callback_query(F.data.startswith("buy:"))
async def buy_request(callback: CallbackQuery):
    await callback.answer()
    user_id = callback.from_user.id
    if db.is_blocked(user_id):
        return
    cat = callback.data.split(":")[1]
    lang = get_lang(user_id)
    user = db.get_user(user_id)
    uname = (user["username"] if user else None) or "—"
    db.add_purchase(user_id, cat)

    # Админге хабарлама
    cat_name = TEXTS["kk"][CATEGORIES[cat]]
    try:
        await bot.send_message(
            ADMIN_ID,
            f"🛒 <b>Сатып алу қызығушылығы</b>\n\n"
            f"ID: <code>{user_id}</code>\n"
            f"Username: @{uname}\n"
            f"Категория: {cat_name}\n"
            f"Тіл: {lang}\n\n"
            f"Қолданушыға @{ADMIN_USERNAME}-ге жазу ұсынылды.",
            parse_mode=ParseMode.HTML
        )
    except Exception as e:
        logger.error(f"Buy notify error: {e}")

    # Қолданушыға — тікелей админге жазу
    b = InlineKeyboardBuilder()
    b.button(
        text=f"💬 Админге жазу (@{ADMIN_USERNAME})" if lang == "kk" else f"💬 Написать админу (@{ADMIN_USERNAME})",
        url=f"https://t.me/{ADMIN_USERNAME}"
    )
    b.button(text=TEXTS[lang]["back"], callback_data=f"cat:{cat}")
    b.button(text=TEXTS[lang]["to_main"], callback_data="menu:main")
    b.adjust(1)

    sent = await callback.message.answer(
        TEXTS[lang]["buy_sent"],
        reply_markup=b.as_markup(),
        parse_mode=ParseMode.HTML
    )
    db.save_bot_message(user_id, sent.message_id)

@router.callback_query(F.data == "menu:free")
async def menu_free(callback: CallbackQuery):
    await callback.answer()
    user_id = callback.from_user.id
    if db.is_blocked(user_id):
        return
    lang = get_lang(user_id)
    user = db.get_user(user_id)
    needed = int(db.get_setting("ref_needed", "3"))
    count = user["referrals_count"] if user else 0

    text = TEXTS[lang]["free_channel"] + "\n\n" + TEXTS[lang]["ref_progress"].format(count=count, needed=needed)

    if user and user["got_free"]:
        link = db.get_setting("free_channel_link", "")
        text += "\n\n" + (TEXTS[lang]["ref_done"].format(link=link) if link else TEXTS[lang]["already_got"])
    elif count >= needed:
        link = db.get_setting("free_channel_link", "")
        if link:
            db.mark_got_free(user_id)
            text += "\n\n" + TEXTS[lang]["ref_done"].format(link=link)
        else:
            text += "\n\n⏳ Сілтеме әзірге орнатылмаған." if lang == "kk" else "\n\n⏳ Ссылка пока не установлена."

    await safe_edit(callback.message, text, free_kb(lang))

@router.callback_query(F.data == "ref:link")
async def ref_link(callback: CallbackQuery):
    await callback.answer()
    user_id = callback.from_user.id
    if db.is_blocked(user_id):
        return
    lang = get_lang(user_id)
    me = await bot.get_me()
    link = f"https://t.me/{me.username}?start=ref_{user_id}"
    sent = await callback.message.answer(
        TEXTS[lang]["ref_link"].format(link=link),
        parse_mode=ParseMode.HTML
    )
    db.save_bot_message(user_id, sent.message_id)

@router.callback_query(F.data == "ref:share")
async def ref_share(callback: CallbackQuery):
    await callback.answer()
    user_id = callback.from_user.id
    if db.is_blocked(user_id):
        return
    lang = get_lang(user_id)
    me = await bot.get_me()
    link = f"https://t.me/{me.username}?start=ref_{user_id}"
    share = "Қызықты бот! Қарап көр 👉 " if lang == "kk" else "Интересный бот! Заходи 👉 "
    sent = await callback.message.answer(f"{share}{link}")
    db.save_bot_message(user_id, sent.message_id)

@router.callback_query(F.data == "menu:help")
async def menu_help(callback: CallbackQuery):
    await callback.answer()
    user_id = callback.from_user.id
    if db.is_blocked(user_id):
        return
    lang = get_lang(user_id)
    await safe_edit(callback.message, TEXTS[lang]["help"], back_main_kb(lang))

@router.callback_query(F.data == "menu:admin_chat")
async def menu_admin_chat(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    user_id = callback.from_user.id
    if db.is_blocked(user_id):
        return
    lang = get_lang(user_id)
    await safe_edit(callback.message, TEXTS[lang]["write_admin"], back_main_kb(lang))
    await state.set_state(UserStates.waiting_admin_msg)

@router.message(UserStates.waiting_admin_msg)
async def user_to_admin(message: Message, state: FSMContext):
    user_id = message.from_user.id
    if db.is_blocked(user_id):
        await state.clear()
        return
    lang = get_lang(user_id)
    uname = message.from_user.username or "—"
    text = message.text or message.caption or ""
    file_id = file_type = None
    if message.photo:
        file_id = message.photo[-1].file_id
        file_type = "photo"
    elif message.video:
        file_id = message.video.file_id
        file_type = "video"
    elif message.voice:
        file_id = message.voice.file_id
        file_type = "voice"

    db.add_message(user_id, ADMIN_ID, text, file_id, file_type)
    notify = (
        f"📩 <b>Жаңа хабарлама</b>\n"
        f"ID: <code>{user_id}</code>\n"
        f"Username: @{uname}\n\n"
        f"{text or '[медиа]'}"
    )
    try:
        if file_type == "photo":
            await bot.send_photo(ADMIN_ID, file_id, caption=notify, parse_mode=ParseMode.HTML)
        elif file_type == "video":
            await bot.send_video(ADMIN_ID, file_id, caption=notify, parse_mode=ParseMode.HTML)
        elif file_type == "voice":
            await bot.send_voice(ADMIN_ID, file_id, caption=notify, parse_mode=ParseMode.HTML)
        else:
            await bot.send_message(ADMIN_ID, notify, parse_mode=ParseMode.HTML)
    except Exception as e:
        logger.error(f"Forward error: {e}")

    await message.answer(TEXTS[lang]["msg_sent"])
    await state.clear()
    text_main = TEXTS[lang]["welcome"] + "\n\n" + TEXTS[lang]["main_menu"]
    await message.answer(text_main, reply_markup=main_menu_kb(lang), parse_mode=ParseMode.HTML)

# ====================== ADMIN HANDLERS ======================
@router.message(Command("admin"))
async def admin_cmd(message: Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return
    await state.clear()
    await message.answer(TEXTS["kk"]["admin_panel"], reply_markup=admin_panel_kb(), parse_mode=ParseMode.HTML)

@router.callback_query(F.data == "admin:panel")
async def admin_panel(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("⛔", show_alert=True)
        return
    await callback.answer()
    await state.clear()
    await safe_edit(callback.message, TEXTS["kk"]["admin_panel"], admin_panel_kb())

@router.callback_query(F.data == "admin:stats")
async def admin_stats(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        return
    await callback.answer()
    s = db.get_stats()
    text = (
        f"📊 <b>Статистика</b>\n\n"
        f"👥 Жалпы: <b>{s['total_users']}</b>\n"
        f"✅ Белсенді: <b>{s['active']}</b>\n"
        f"🚫 Ботты бұғаттаған: <b>{s['bot_blocked']}</b>\n"
        f"🗑 Қара тізім: <b>{s['blacklist']}</b>\n"
        f"🇰🇿 Қазақша: <b>{s['kk']}</b>\n"
        f"🇷🇺 Орысша: <b>{s['ru']}</b>\n"
        f"🔗 Рефералдар: <b>{s['total_refs']}</b>\n"
        f"🎁 Тегін алғандар: <b>{s['got_free']}</b>\n"
        f"🛒 Сатып алу: <b>{s['purchases']}</b>"
    )
    b = InlineKeyboardBuilder()
    b.button(text="🔙 Админ панель", callback_data="admin:panel")
    await safe_edit(callback.message, text, b.as_markup())

@router.callback_query(F.data == "admin:content")
async def admin_content(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        return
    await callback.answer()
    await safe_edit(callback.message, "📂 Контент басқару\n\nКатегорияны таңдаңыз:", admin_content_kb())

@router.callback_query(F.data.startswith("admin_cat:"))
async def admin_cat(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        return
    await callback.answer()
    cat = callback.data.split(":")[1]
    await safe_edit(callback.message, f"📂 {TEXTS['kk'][CATEGORIES[cat]]}", admin_cat_actions_kb(cat))

@router.callback_query(F.data.startswith("admin_add:"))
async def admin_add_content(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id != ADMIN_ID:
        return
    await callback.answer()
    cat = callback.data.split(":")[1]
    await state.set_state(AdminStates.waiting_content)
    await state.update_data(category=cat)
    await callback.message.answer(
        f"Контент жіберіңіз (фото / видео / мәтін).\nКатегория: <b>{cat}</b>\n"
        f"Бірнеше рет жібере аласыз.\nАяқтау: /done",
        parse_mode=ParseMode.HTML
    )

@router.message(AdminStates.waiting_content)
async def admin_save_content(message: Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return
    if message.text and message.text.strip().lower() == "/done":
        await state.clear()
        await message.answer("✅ Контент сақтау аяқталды.", reply_markup=admin_panel_kb())
        return
    data = await state.get_data()
    cat = data.get("category", "kk")
    caption = message.caption or message.text or ""
    if message.photo:
        db.add_content(cat, message.photo[-1].file_id, "photo", caption)
        await message.answer("✅ Фото қосылды.")
    elif message.video:
        db.add_content(cat, message.video.file_id, "video", caption)
        await message.answer("✅ Видео қосылды.")
    elif message.text:
        db.add_content(cat, message.text, "text", message.text)
        await message.answer("✅ Мәтін қосылды.")
    else:
        await message.answer("Қолдау көрсетілмейтін формат.")

@router.callback_query(F.data.startswith("admin_view:"))
async def admin_view_content(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        return
    await callback.answer()
    cat = callback.data.split(":")[1]
    contents = db.get_content(cat)
    if not contents:
        await callback.message.answer("Контент жоқ.")
        return
    for c in contents[:10]:
        try:
            if c["file_type"] == "photo":
                await bot.send_photo(ADMIN_ID, c["file_id"], caption=c["caption"] or None)
            elif c["file_type"] == "video":
                await bot.send_video(ADMIN_ID, c["file_id"], caption=c["caption"] or None)
            else:
                await bot.send_message(ADMIN_ID, c["caption"] or c["file_id"])
            await asyncio.sleep(0.2)
        except Exception as e:
            logger.error(e)
    await callback.message.answer(f"Барлығы: {len(contents)}")

@router.callback_query(F.data.startswith("admin_clear:"))
async def admin_clear_content(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        return
    await callback.answer()
    cat = callback.data.split(":")[1]
    db.clear_content(cat)
    await callback.message.answer("✅ Контент тазаланды.")

@router.callback_query(F.data == "admin:ref")
async def admin_ref(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        return
    await callback.answer()
    needed = db.get_setting("ref_needed", "3")
    text = f"🎁 Реферал баптаулары\n\nҚазіргі қажетті саны: <b>{needed}</b>"
    await safe_edit(callback.message, text, admin_ref_kb())

@router.callback_query(F.data == "admin:set_ref")
async def admin_set_ref(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id != ADMIN_ID:
        return
    await callback.answer()
    await state.set_state(AdminStates.waiting_ref_count)
    await callback.message.answer("Жаңа реферал санын енгізіңіз (тек сан):")

@router.message(AdminStates.waiting_ref_count)
async def admin_save_ref(message: Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return
    try:
        n = int(message.text.strip())
        if n < 1:
            raise ValueError
        db.set_setting("ref_needed", str(n))
        await message.answer(f"✅ Қажетті реферал саны: {n}")
    except ValueError:
        await message.answer("Тек оң сан енгізіңіз.")
        return
    await state.clear()
    await message.answer(TEXTS["kk"]["admin_panel"], reply_markup=admin_panel_kb(), parse_mode=ParseMode.HTML)

@router.callback_query(F.data == "admin:free_link")
async def admin_free_link(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id != ADMIN_ID:
        return
    await callback.answer()
    link = db.get_setting("free_channel_link", "")
    await state.set_state(AdminStates.waiting_free_link)
    await callback.message.answer(
        f"🔗 Тегін канал сілтемесі\n\nҚазіргі:\n{link or 'орнатылмаған'}\n\nЖаңа сілтемені жіберіңіз:"
    )

@router.message(AdminStates.waiting_free_link)
async def admin_save_free_link(message: Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return
    db.set_setting("free_channel_link", message.text.strip())
    await message.answer("✅ Тегін канал сілтемесі сақталды.")
    await state.clear()
    await message.answer(TEXTS["kk"]["admin_panel"], reply_markup=admin_panel_kb(), parse_mode=ParseMode.HTML)

@router.callback_query(F.data == "admin:blacklist")
async def admin_blacklist(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        return
    await callback.answer()
    await safe_edit(callback.message, "🚫 Бұғаттау жүйесі", admin_blacklist_kb())

@router.callback_query(F.data == "admin:block")
async def admin_block_start(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id != ADMIN_ID:
        return
    await callback.answer()
    await state.set_state(AdminStates.waiting_block_id)
    await callback.message.answer("Бұғаттайтын Telegram ID енгізіңіз:")

@router.message(AdminStates.waiting_block_id)
async def admin_do_block(message: Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return
    try:
        uid = int(message.text.strip())
        db.block_user(uid, "admin")

        # Бұрынғы хабарламаларды өшіру
        deleted = 0
        msg_ids = db.get_bot_messages(uid)
        user = db.get_user(uid)
        if user and user.get("main_message_id"):
            msg_ids.append(user["main_message_id"])

        for mid in set(msg_ids):
            try:
                await bot.delete_message(uid, mid)
                deleted += 1
                await asyncio.sleep(0.04)
            except Exception:
                pass

        db.clear_bot_messages(uid)
        if user:
            db.update_user(uid, main_message_id=None)

        await message.answer(f"✅ {uid} бұғатталды.\n🗑 Өшірілген хабарламалар: {deleted}")
    except ValueError:
        await message.answer("Тек сан енгізіңіз.")
        return
    await state.clear()

@router.callback_query(F.data == "admin:unblock")
async def admin_unblock_start(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id != ADMIN_ID:
        return
    await callback.answer()
    await state.set_state(AdminStates.waiting_unblock_id)
    await callback.message.answer("Бұғаттан шығаратын Telegram ID енгізіңіз:")

@router.message(AdminStates.waiting_unblock_id)
async def admin_do_unblock(message: Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return
    try:
        uid = int(message.text.strip())
        db.unblock_user(uid)
        await message.answer(f"✅ {uid} бұғаттан шығарылды.")
    except ValueError:
        await message.answer("Тек сан енгізіңіз.")
        return
    await state.clear()

@router.callback_query(F.data == "admin:list_bl")
async def admin_list_bl(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        return
    await callback.answer()
    bl = db.get_blacklist()
    if not bl:
        text = "Қара тізім бос."
    else:
        lines = [f"• <code>{r['user_id']}</code> ({r['created_at'][:10]})" for r in bl[:50]]
        text = "📋 Қара тізім:\n\n" + "\n".join(lines)
    await callback.message.answer(text, parse_mode=ParseMode.HTML)

@router.callback_query(F.data == "admin:broadcast")
async def admin_broadcast_start(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id != ADMIN_ID:
        return
    await callback.answer()
    await state.set_state(AdminStates.waiting_broadcast)
    await callback.message.answer(
        "📢 Рассылка үшін мәтін немесе медиа жіберіңіз.\n"
        "Алдын ала қараудан кейін жібересіз.\n"
        "Бас тарту: /cancel"
    )

@router.message(AdminStates.waiting_broadcast)
async def admin_broadcast_receive(message: Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return
    if message.text and message.text.strip().lower() == "/cancel":
        await state.clear()
        await message.answer("Бас тартылды.", reply_markup=admin_panel_kb())
        return

    data = {"text": message.text or message.caption or "", "file_id": None, "file_type": None}
    if message.photo:
        data["file_id"] = message.photo[-1].file_id
        data["file_type"] = "photo"
    elif message.video:
        data["file_id"] = message.video.file_id
        data["file_type"] = "video"

    pending_broadcast[ADMIN_ID] = data
    preview = data["text"] or "[медиа]"
    await message.answer(
        f"Алдын ала қарау:\n\n{preview}\n\nЖіберуді растаңыз:",
        reply_markup=confirm_bc_kb()
    )

@router.callback_query(F.data == "bc:confirm")
async def bc_confirm(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id != ADMIN_ID:
        return
    await callback.answer()
    data = pending_broadcast.get(ADMIN_ID)
    if not data:
        await callback.message.answer("Деректер жоқ.")
        return
    await state.clear()
    await callback.message.edit_text("⏳ Рассылка басталды...", reply_markup=stop_bc_kb())
    asyncio.create_task(run_broadcast(data, callback.message))

@router.callback_query(F.data == "bc:cancel")
async def bc_cancel(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id != ADMIN_ID:
        return
    await callback.answer()
    pending_broadcast.pop(ADMIN_ID, None)
    await state.clear()
    await safe_edit(callback.message, "Бас тартылды.", admin_panel_kb())

@router.callback_query(F.data == "bc:stop")
async def bc_stop(callback: CallbackQuery):
    global broadcast_stop
    if callback.from_user.id != ADMIN_ID:
        return
    await callback.answer("Тоқтату сұранысы жіберілді")
    broadcast_stop = True

async def run_broadcast(data: dict, status_msg: Message):
    global broadcast_stop
    broadcast_stop = False
    users = db.get_all_user_ids(exclude_blocked=True)
    ok = err = 0

    for i, uid in enumerate(users):
        if broadcast_stop:
            break
        try:
            if data["file_type"] == "photo":
                await bot.send_photo(uid, data["file_id"], caption=data["text"] or None)
            elif data["file_type"] == "video":
                await bot.send_video(uid, data["file_id"], caption=data["text"] or None)
            else:
                await bot.send_message(uid, data["text"])
            ok += 1
        except TelegramRetryAfter as e:
            await asyncio.sleep(e.retry_after + 1)
            try:
                if data["file_type"] == "photo":
                    await bot.send_photo(uid, data["file_id"], caption=data["text"] or None)
                elif data["file_type"] == "video":
                    await bot.send_video(uid, data["file_id"], caption=data["text"] or None)
                else:
                    await bot.send_message(uid, data["text"])
                ok += 1
            except Exception:
                err += 1
                db.update_user(uid, is_bot_blocked=1)
        except (TelegramForbiddenError, TelegramBadRequest):
            err += 1
            db.update_user(uid, is_bot_blocked=1)
        except Exception as e:
            logger.error(f"BC {uid}: {e}")
            err += 1

        if i % 20 == 0:
            await asyncio.sleep(1.0)
        else:
            await asyncio.sleep(0.05)

    text = f"✅ Рассылка аяқталды.\nЖіберілді: {ok}\nҚате: {err}"
    if broadcast_stop:
        text = f"⏹ Рассылка тоқтатылды.\nЖіберілді: {ok}\nҚате: {err}"

    try:
        await status_msg.edit_text(text, reply_markup=admin_panel_kb())
    except Exception:
        await bot.send_message(ADMIN_ID, text, reply_markup=admin_panel_kb())

    conn = db._conn()
    conn.execute(
        "INSERT INTO broadcast_log (total, success, failed, created_at) VALUES (?, ?, ?, ?)",
        (ok + err, ok, err, datetime.now().isoformat())
    )
    conn.commit()
    conn.close()

@router.callback_query(F.data == "admin:users")
async def admin_users(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        return
    await callback.answer()
    s = db.get_stats()
    text = (
        f"👥 Қолданушылар: <b>{s['total_users']}</b>\n\n"
        f"Хабарлама жіберу: /reply <id> <мәтін>"
    )
    b = InlineKeyboardBuilder()
    b.button(text="🔙 Админ панель", callback_data="admin:panel")
    await safe_edit(callback.message, text, b.as_markup())

@router.callback_query(F.data == "admin:chat")
async def admin_chat(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        return
    await callback.answer()
    text = (
        "💬 Хат алмасу\n\n"
        "Қолданушыдан келген хабарламалар осында көрінеді.\n"
        "Жауап беру: /reply <user_id> <мәтін>"
    )
    b = InlineKeyboardBuilder()
    b.button(text="🔙 Админ панель", callback_data="admin:panel")
    await safe_edit(callback.message, text, b.as_markup())

@router.callback_query(F.data == "admin:settings")
async def admin_settings(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        return
    await callback.answer()
    text = (
        "⚙️ Бот баптаулары\n\n"
        f"Реферал қажетті саны: {db.get_setting('ref_needed')}\n"
        f"Тегін сілтеме: {db.get_setting('free_channel_link') or 'жоқ'}\n"
        f"DB: {DB_PATH}"
    )
    b = InlineKeyboardBuilder()
    b.button(text="🔙 Админ панель", callback_data="admin:panel")
    await safe_edit(callback.message, text, b.as_markup())

@router.message(Command("reply"))
async def admin_reply_cmd(message: Message):
    if message.from_user.id != ADMIN_ID:
        return
    parts = message.text.split(maxsplit=2)
    if len(parts) < 3:
        await message.answer("Формат: /reply <user_id> <мәтін>")
        return
    try:
        uid = int(parts[1])
        text = parts[2]
        await bot.send_message(uid, f"💬 Админ:\n\n{text}")
        db.add_message(ADMIN_ID, uid, text, is_admin=1)
        await message.answer("✅ Жіберілді.")
    except Exception as e:
        await message.answer(f"Қате: {e}")

@router.message()
async def fallback(message: Message, state: FSMContext):
    user_id = message.from_user.id
    if user_id == ADMIN_ID:
        return
    if db.is_blocked(user_id):
        await message.answer(TEXTS["kk"]["blocked"])
        return
    current = await state.get_state()
    if current:
        return
    user = db.get_user(user_id)
    if not user:
        await message.answer(TEXTS["kk"]["choose_lang"], reply_markup=lang_kb())
        return
    lang = user["language"] or "kk"
    await message.answer(
        "Менюді пайдаланыңыз 👇" if lang == "kk" else "Используйте меню 👇",
        reply_markup=main_menu_kb(lang)
    )

# ====================== MAIN ======================
async def main():
    logger.info("Бот іске қосылуда...")
    db._init_db()
    await dp.start_polling(bot, allowed_updates=["message", "callback_query"])

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Бот тоқтатылды.")
