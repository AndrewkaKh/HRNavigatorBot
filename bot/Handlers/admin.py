import asyncio
from io import BytesIO
import openpyxl
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler, MessageHandler, CommandHandler, CallbackQueryHandler, filters

from bot.Handlers.report import is_admin
from bot.config import ADMIN_IDS, V_ADD_TITLE, V_ADD_DESC
from database.crud_sync import add_vacancy_sync, list_vacancies_sync, delete_vacancy_sync, get_all_students_sync, \
    add_comment_sync


async def _guard(update: Update) -> bool:
    if not is_admin(update):
        target = update.message or update.callback_query.message
        await target.reply_text("❌ Команда доступна только администраторам.")
        return False
    return True

# -------- /vacancy_add --------

async def cmd_vacancy_add(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    if not await _guard(update):
        return ConversationHandler.END
    await update.message.reply_text("Введите *название* вакансии:", parse_mode="Markdown")
    return V_ADD_TITLE

async def vacancy_add_title(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    ctx.user_data["__vac_name"] = update.message.text.strip()
    await update.message.reply_text("Теперь введите *описание* вакансии (первая строка будет кратким превью):", parse_mode="Markdown")
    return V_ADD_DESC

async def vacancy_add_desc(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    name = ctx.user_data.pop("__vac_name", "").strip()
    desc = update.message.text.strip()
    if not name:
        await update.message.reply_text("Название не распознано. Запустите /vacancy_add ещё раз.")
        return ConversationHandler.END

    # апсерт синхронной функцией в пуле
    await asyncio.to_thread(add_vacancy_sync, name, desc)
    await update.message.reply_text(f"✅ Вакансия «{name}» сохранена.")
    return ConversationHandler.END

# -------- /vacancy_del --------

def _build_del_keyboard(names: list[str]) -> InlineKeyboardMarkup:
    """
    Клавиатура со списком вакансий на удаление.
    В callback передаём индекс, а сами имена держим в user_data.
    """
    rows = [[InlineKeyboardButton(text=n, callback_data=f"vacdel_idx:{i}")]
            for i, n in enumerate(names)]
    if not rows:
        rows = [[InlineKeyboardButton(text="—", callback_data="vacdel_none")]]
    return InlineKeyboardMarkup(rows)

async def cmd_vacancy_del(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    if not await _guard(update):
        return
    vacs = await asyncio.to_thread(list_vacancies_sync)
    names = [v.name for v in vacs]
    ctx.user_data["__vacs_del_names"] = names
    if not names:
        await update.message.reply_text("Удалять нечего — вакансий пока нет.")
        return
    await update.message.reply_text(
        "Выберите вакансию для удаления:",
        reply_markup=_build_del_keyboard(names)
    )

async def vacancy_del_callback(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    q = update.callback_query
    await q.answer()

    if not is_admin(update):
        await q.answer("Нет прав", show_alert=True)
        return

    data = q.data
    if data == "vacdel_none":
        return

    if not data.startswith("vacdel_idx:"):
        return

    try:
        idx = int(data.split(":", 1)[1])
    except ValueError:
        await q.message.reply_text("Некорректный выбор.")
        return

    names = ctx.user_data.get("__vacs_del_names", [])
    if idx < 0 or idx >= len(names):
        await q.message.reply_text("Эта вакансия уже исчезла из списка. Обновите /vacancy_del.")
        return

    name = names[idx]
    ok = await asyncio.to_thread(delete_vacancy_sync, name)

    # обновим список на кнопках
    vacs = await asyncio.to_thread(list_vacancies_sync)
    names = [v.name for v in vacs]
    ctx.user_data["__vacs_del_names"] = names

    if ok:
        text = f"🗑️ Удалено: «{name}»"
    else:
        text = f"Не удалось удалить: «{name}»"

    if names:
        # редактируем сообщение, чтобы сразу показать актуальный список
        await q.message.edit_text(text + "\n\nВыберите вакансию для удаления:",
                                  reply_markup=_build_del_keyboard(names))
    else:
        await q.message.edit_text(text + "\n\nБольше вакансий нет.")


async def cmd_comment(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды /comment <id> <текст комментария>"""
    if not is_admin(update):
        await update.message.reply_text("❌ Команда доступна только администраторам.")
        return

    if not update.message or not context.args or len(context.args) < 2:
        await update.message.reply_text("Использование: /comment <ID студента> <текст комментария>")
        return

    try:
        student_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text("ID студента должен быть числом")
        return

    comment_text = " ".join(context.args[1:])
    success = await asyncio.to_thread(add_comment_sync, student_id, comment_text)

    if success:
        await update.message.reply_text(f"✅ Комментарий добавлен к студенту с ID {student_id}")
    else:
        await update.message.reply_text(f"❌ Студент с ID {student_id} не найден")


async def cmd_export_students(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды /export_students - экспорт в XLSX"""
    if not is_admin(update):
        await update.message.reply_text("❌ Команда доступна только администраторам.")
        return

    students = await asyncio.to_thread(get_all_students_sync)

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Студенты"

    headers = [
        "ID",
        "ФИО",
        "Телефон",
        "Контакты",
        "Комментарии",
        "Документ",
        "Дата подачи"
    ]
    ws.append(headers)

    for student in students:
        comments = student.comments.replace("\n", "\r\n") if student.comments else ""

        ws.append([
            student.id,
            student.full_name,
            student.phone,
            student.social_url or "",
            comments,
            student.doc_url or "",
            student.created_at.strftime("%Y-%m-%d %H:%M")
        ])

    for col in ws.columns:
        column = col[0].column_letter
        ws.column_dimensions[column].width = 20

    ws.column_dimensions["E"].width = 50
    for row in ws.iter_rows(min_row=2, max_col=7, max_row=len(students) + 1):
        row[4].alignment = openpyxl.styles.Alignment(wrapText=True)

    excel_file = BytesIO()
    wb.save(excel_file)
    excel_file.seek(0)

    await update.message.reply_document(
        document=excel_file,
        filename=f"students_export_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
        caption="Экспорт данных о студентах"
    )
