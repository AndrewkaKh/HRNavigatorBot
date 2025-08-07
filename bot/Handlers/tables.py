from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes
from telegram import Update, Message
from bot.Handlers.doc import finish_and_send
from bot.config import TABLE_SPECS, ASK_TBL_CELL, CONFIRM_TBL_ROW, CHOOSE_TABLE, CHOOSE_EDIT_MENU


async def start_table(update: ContextTypes.DEFAULT_TYPE, ctx: ContextTypes.DEFAULT_TYPE, key: str):
    spec = TABLE_SPECS[key]
    ctx.user_data["__table_key"] = key
    ctx.user_data["__tbl_cols"]  = spec["columns"]
    ctx.user_data["__tbl_row"]   = {}
    ctx.user_data.setdefault(key, [])
    caption = spec["columns"][0][1]
    await update.message.reply_text(f"{spec['caption']}\n{caption}:")
    return ASK_TBL_CELL

async def ask_next_tbl_cell(update: ContextTypes.DEFAULT_TYPE, ctx: ContextTypes.DEFAULT_TYPE):
    cols = ctx.user_data["__tbl_cols"]
    row  = ctx.user_data["__tbl_row"]
    idx  = len(row)
    if idx < len(cols):
        await update.message.reply_text(cols[idx][1] + ":")
        return ASK_TBL_CELL
    return None

async def tbl_cell_answer(update: ContextTypes.DEFAULT_TYPE, ctx: ContextTypes.DEFAULT_TYPE):
    cols = ctx.user_data["__tbl_cols"]
    row  = ctx.user_data["__tbl_row"]
    col_key = cols[len(row)][0]
    row[col_key] = update.message.text.strip()

    if len(row) < len(cols):
        return await ask_next_tbl_cell(update, ctx)

    tbl_key = ctx.user_data["__table_key"]
    ctx.user_data[tbl_key].append(row.copy())
    row.clear()

    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("➕ Добавить ещё", callback_data="tbl_add")],
        [InlineKeyboardButton("✅ Дальше", callback_data="tbl_next")],
    ])
    await update.message.reply_text("Строка добавлена.", reply_markup=kb)
    return CONFIRM_TBL_ROW

async def tbl_callback(update: ContextTypes.DEFAULT_TYPE, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    action = q.data

    if action == "tbl_add":
        return await ask_next_tbl_cell(q, ctx)

    next_key = next(ctx.user_data["__tables_iter"], None)
    if next_key:
        return await start_table(q, ctx, next_key)

    return await finish_and_send(q, ctx)

async def choose_edit_tables_callback(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Обработка меню редактирования таблиц:
     - edittbl:<key>   → показать список строк и операций
     - back_to_edit_menu → вернуться к меню «Изменить» (поля/таблицы)
    """
    q = update.callback_query
    await q.answer()
    data = q.data
    if data.startswith("edittbl:"):
        table_key = data.split(":", 1)[1]
        ctx.user_data[table_key] = []
        await start_table(q, ctx, table_key)
        return ASK_TBL_CELL

    if data == "back_to_edit_menu":
        await q.message.delete()
        return CHOOSE_EDIT_MENU

    # на всякий случай остаться в этом же состоянии
    return CHOOSE_TABLE

async def edit_rows_tables_callback(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Обработка меню редактирования таблиц:
     - При выборе edittbl:<key> очищаем старую таблицу и начинаем полный опрос заново.
     - back_to_edit_menu → вернуться к меню «Изменить» (поля/таблицы)
    """
    q = update.callback_query
    await q.answer()
    table_key = q.data.split(":", 1)[1]

    # 1) Сбрасываем уже введённые строки
    ctx.user_data[table_key] = []

    # 2) Запускаем dokładно ту же логику, что при первом вводе:
    #    спрашиваем первую ячейку первой строки
    await start_table(update, ctx, table_key)
    return ASK_TBL_CELL

