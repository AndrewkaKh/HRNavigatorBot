import math
from docxtpl import DocxTemplate
from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup,
)
from telegram.ext import (
    ConversationHandler, ContextTypes, CallbackContext
)

from bot.config import ADMIN_IDS
from database.db import SessionLocal


async def start(update: Update, context: CallbackContext):
    """
    Приветственная команда /start.
    """
    db = SessionLocal()
    greeting = f"Привет, {update.effective_user.first_name}! 👋\n"
    greeting += "Добро пожаловать в систему подбора вакансий.\n"
    greeting += "Узнайте о всех командах, с помощью команды /help.\n"
    await update.message.reply_text(greeting)

async def help(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    if is_admin(update):
        cmds = [
            ("/help",             "Список админ-команд"),
            ("/vacancies",        "Посмотреть список вакансий"),
            ("/vacancy_add",      "Добавить вакансию"),
            ("/vacancy_del",      "Удалить вакансию"),
            ("/comment <id>",     "Добавить пометку студенту"),
            ("/export_students",  "Экспорт студентов в XLSX"),
            ("/cancel",           "Отмена текущей операции"),
        ]
    else:
        cmds = [
            ("/start",       "Приветствие"),
            ("/help",        "Список команд"),
            ("/vacancies",   "Список доступных вакансий"),
            ("/apply",       "Заполнить анкету"),
            ("/cancel",      "Отмена текущей операции"),
        ]
    text = "Доступные команды:\n" + "\n".join(f"{c} — {d}" for c, d in cmds)
    await update.message.reply_text(text)

async def cancel(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Заполнение прервано.")
    return ConversationHandler.END

def is_admin(update) -> bool:
    user = update.effective_user
    return bool(user and user.id in ADMIN_IDS)
