import math
from docxtpl import DocxTemplate
from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup,
)
from telegram.ext import (
    ConversationHandler, ContextTypes, CallbackContext
)

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
    """
    Команда /help. Вывод списка доступных команд.
    """
    commands = [
        ("/start", "Приветствие и запуск бота"),
        ("/help", "Список доступных команд"),
        ("/apply", "Начать заполнение анкеты"),
        ("/cancel", "Отмена текущей операции"),
    ]
    help_text = "Доступные команды:\n" + "\n".join(f"{cmd} — {desc}" for cmd, desc in commands)
    await update.message.reply_text(help_text)

async def cancel(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Заполнение прервано.")
    return ConversationHandler.END