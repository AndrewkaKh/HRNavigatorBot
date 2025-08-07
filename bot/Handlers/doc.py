from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes, ConversationHandler
from docxtpl import DocxTemplate
import io
from datetime import date, datetime
import asyncio

from bot.Handlers.scalars import build_fix_keyboard
from database.crud_sync import upsert_student_sync
from bot.config import ARCHIVE_CHANNEL_ID, CONFIRM_DOC, CHOOSE_TBL_FIELD, CHOOSE_EDIT_MENU, CHOOSE_TABLE, TABLE_SPECS


def build_tables_keyboard(ctx: ContextTypes.DEFAULT_TYPE) -> InlineKeyboardMarkup:
    """
    Формирует клавиатуру с перечнем всех табличных разделов,
    показывая у каждого, сколько строк уже добавлено.
    Используется в меню редактирования таблиц (handlers/doc.py).
    """
    rows = []
    for key, spec in TABLE_SPECS.items():
        count = len(ctx.user_data.get(key, []))
        rows.append([
            InlineKeyboardButton(
                text=f"{spec['caption']} ({count})",
                callback_data=f"edittbl:{key}"
            )
        ])
    # Кнопка возврата к меню редактирования (📋 Поля/📋 Таблицы)
    rows.append([
        InlineKeyboardButton("⬅️ Назад", callback_data="back_to_edit_menu")
    ])
    return InlineKeyboardMarkup(rows)

async def doc_edit_menu_callback(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    """
        Обработка меню после нажатия «✏️ Изменить»:
        - edit_scalars → правка скалярных полей
        - edit_tables  → правка табличных разделов
        - back_to_confirm → возврат к предпросмотру
        """
    q = update.callback_query
    await q.answer()
    choice = q.data

    if choice == "edit_scalars":
        # Переходим к правке скалярных полей
        await q.message.reply_text(
            "Какое поле хотите изменить?",
            reply_markup=build_fix_keyboard(page=0)
        )
        return CHOOSE_TBL_FIELD

    if choice == "edit_tables":
        # Переходим к выбору таблицы
        await q.message.reply_text(
            "Выберите таблицу для правки:",
            reply_markup=build_tables_keyboard(ctx)
        )
        return CHOOSE_TABLE

    if choice == "back_to_confirm":
        # Возвращаем предпросмотр анкеты
        await q.message.delete()
        return CONFIRM_DOC

    return CHOOSE_EDIT_MENU

async def finish_and_send(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    """
        Генерирует DOCX в памяти и сразу шлёт пользователю,
        без сохранения на диск.
    """
    # Рендерим документ в BytesIO
    doc_stream = render_doc_in_memory(ctx.user_data)
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("👍 Одобрить", callback_data="doc_ok")],
        [InlineKeyboardButton("✏️ Изменить", callback_data="doc_edit")],
    ])
    # Отправляем поток как файл
    await update.message.reply_document(
        document=doc_stream,
        filename="anketa.docx",
        caption="Проверьте анкету:",
        reply_markup=kb
    )
    return CONFIRM_DOC

async def doc_callback(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Обрабатывает нажатия кнопок 👍 Одобрить / ✏️ Изменить.
    При одобрении отправляет в архив и сохраняет в БД без файлов на диск.
    """
    q = update.callback_query
    await q.answer()

    if q.data == "doc_ok":
        # Создаем документ в памяти
        doc_stream = render_doc_in_memory(ctx.user_data)
        fio = f"{ctx.user_data.get('last_name','')} {ctx.user_data.get('first_name','')}".strip() or "—"
        phone = (ctx.user_data.get('phone_mobile') or "—").strip()
        social = ctx.user_data.get('social_links') or None
        ts = datetime.now().strftime("%Y-%m-%d %H:%M")

        # Отправляем в приватный архивный канал
        msg = await ctx.bot.send_document(
            chat_id=ARCHIVE_CHANNEL_ID,
            document=doc_stream,
            filename="anketa.docx",
            caption=f"Анкета: {fio}\nСоздано: {ts}",
            protect_content=True,
            disable_notification=True
        )
        link = make_private_post_link(msg.chat_id, msg.message_id)

        # Сохраняем запись в БД в фоновом потоке
        await asyncio.to_thread(
            upsert_student_sync,
            full_name=fio,
            phone=phone,
            social_url=social,
            doc_url=link,
            file_id=msg.document.file_id,
            message_id=msg.message_id,
            channel_id=msg.chat_id,
        )

        # Уведомляем пользователя
        await q.message.reply_text(
            f"Анкета одобрена и сохранена ✅\nСсылка: {link}\nfile_id: {msg.document.file_id}"
        )
        return ConversationHandler.END

    #✏️ doc_edit
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("✏️ Поля", callback_data="edit_scalars")],
        [InlineKeyboardButton("📋 Таблицы", callback_data="edit_tables")],
        [InlineKeyboardButton("⬅️ Отмена", callback_data="back_to_confirm")],
    ])
    await q.message.reply_text("Что хотите изменить?", reply_markup=kb)
    return CHOOSE_EDIT_MENU


# Утилиты для doc
def render_doc_in_memory(ctx_data: dict) -> io.BytesIO:
    """
    Рендерит шаблон в памя́ти и возвращает BytesIO,
    готовый к отправке как файл.
    """
    tpl = DocxTemplate("anketa_template.docx")
    # добавляем дату
    ctx = {**ctx_data, "form_date": date.today().strftime("%d.%m.%Y")}
    tpl.render(ctx)

    bio = io.BytesIO()
    bio.name = "anketa.docx"
    tpl.save(bio)
    bio.seek(0)
    return bio


def make_private_post_link(chat_id: int, message_id: int) -> str:
    s = str(chat_id)
    internal = s[4:] if s.startswith("-100") else s.lstrip("-")
    return f"https://t.me/c/{internal}/{message_id}"