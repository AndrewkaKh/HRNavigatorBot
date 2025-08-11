import math
from docxtpl import DocxTemplate
from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup,
)
from telegram.ext import (
    ConversationHandler, ContextTypes, CallbackContext
)

from bot.config import ADMIN_IDS


async def start(update: Update, context: CallbackContext):
    """
    Приветственная команда /start.
    """
    if is_admin(update):
        txt = (
            f"🔹 <b>Добро пожаловать, {update.effective_user.first_name}!</b> 👋\n\n"
            "Вы вошли в <b>HR-панель МРСК ЧелябЭнерго</b>\n\n"
            "⚡ <b>Ваши административные возможности:</b>\n"
            "• Управление вакансиями компании\n"
            "• Просмотр и обработка анкет соискателей\n"
            "• Добавление комментариев к кандидатам\n"
            "• Экспорт данных для анализа\n\n"
            "Полный список команд: /help\n\n"
            "<i>Используйте /vacancies для просмотра текущего списка вакансий</i>"
        )
    else:
        txt = (
            f"🔹 <b>Добро пожаловать, {update.effective_user.first_name}!</b> 👋\n\n"
            "Я — HR-ассистент <b>МРСК ЧелябЭнерго</b>, ваш проводник в мире карьерных возможностей!\n\n"
            "⚡ <i>Энергия вашей карьеры начинается здесь!</i>\n\n"
            "✨ <b>Что я могу для вас сделать:</b>\n"
            "• Показать актуальные вакансии компании\n"
            "• Помочь подать заявку на интересующую должность\n"
            "• Рассказать о требованиях и условиях работы\n"
            "• Ответить на ваши вопросы\n\n"
            "Чтобы увидеть все возможности, используйте команду /help\n\n"
            "<i>Давайте вместе создадим энергию будущего!</i> ⚡"
        )
    greeting = txt
    await update.message.reply_text(
        text=greeting,
        parse_mode='HTML'
    )


async def help(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    if is_admin(update):
        header = "🛠 <b>Панель администратора</b> (HR-специалист)\n\n"
        cmds = [
            ("/vacancies", "📋 Просмотр всех вакансий"),
            ("/vacancy_add", "➕ Добавить новую вакансию"),
            ("/vacancy_del", "🗑 Удалить вакансию"),
            ("/comment id", "📝 Добавить заметку к анкете"),
            ("/export_students", "📊 Экспорт анкет в Excel"),
            ("/help", "ℹ️ Это меню помощи"),
            ("/cancel", "❌ Отмена текущего действия"),
        ]
    else:
        header = "🔹 <b>Меню помощника по карьере в МРСК ЧелябЭнерго</b>\n\n"
        cmds = [
            ("/start", "🏠 Главное меню"),
            ("/vacancies", "🔎 Актуальные вакансии"),
            ("/apply", "📝 Подать заявку на вакансию"),
            ("/help", "ℹ️ Это меню помощи"),
            ("/cancel", "❌ Отмена текущего действия"),
        ]

    text = (
            header +
            "⚡ <b>Доступные команды:</b>\n\n" +
            "\n".join(f"• <code>{c}</code> — {d}" for c, d in cmds) +
            "\n\n<i>Для связи с HR-отделом используйте контакты из описания вакансий</i>"
    )

    await update.message.reply_text(
        text=text,
        parse_mode='HTML'
    )

async def cancel(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Заполнение прервано.")
    return ConversationHandler.END

def is_admin(update) -> bool:
    user = update.effective_user
    return bool(user and user.id in ADMIN_IDS)
