import math
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from bot.config import SCALAR_FIELDS, TABLE_SPECS, ASK_SCALAR, ASK_TBL_CELL, CHOOSE_TBL_FIELD, CONFIRM_DOC, \
    CHOOSE_EDIT_MENU

# Пагинация
PAGE_SIZE = 10

def next_scalar_index(user_data: dict) -> int | None:
    for i, (k, _) in enumerate(SCALAR_FIELDS):
        if k not in user_data:
            return i
    return None

async def cmd_apply(update: ContextTypes.DEFAULT_TYPE, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    ctx.user_data.clear()
    ctx.user_data["__scalar_i"] = 0
    await update.message.reply_text(SCALAR_FIELDS[0][1] + ":")
    return ASK_SCALAR

async def scalar_answer(update: ContextTypes.DEFAULT_TYPE, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Обработка ответа на скалярный вопрос или правки одного поля.
    """
    # 1) Обработка режима редактирования одного поля
    fix_key = ctx.user_data.pop("__fix_key", None)
    if fix_key:
        # Сохраняем новое значение и сразу возвращаем предпросмотр
        ctx.user_data[fix_key] = update.message.text.strip()
        from bot.Handlers.doc import finish_and_send
        return await finish_and_send(update, ctx)

    # 2) Обычное заполнение анкеты:
    i = ctx.user_data["__scalar_i"]
    key, _ = SCALAR_FIELDS[i]
    ctx.user_data[key] = update.message.text.strip()

    # Ищем следующий скаляр
    next_i = next_scalar_index(ctx.user_data)
    if next_i is not None:
        ctx.user_data["__scalar_i"] = next_i
        await update.message.reply_text(SCALAR_FIELDS[next_i][1] + ":")
        return ASK_SCALAR

    # 3) Все скаляры заполнены — переходим к таблицам:
    ctx.user_data["__tables_iter"] = iter(TABLE_SPECS.keys())
    next_key = next(ctx.user_data["__tables_iter"], None)
    if not next_key:
        from bot.Handlers.doc import finish_and_send
        return await finish_and_send(update, ctx)
    from bot.Handlers.tables import start_table
    await start_table(update, ctx, next_key)
    return ASK_TBL_CELL

async def choose_field(update: ContextTypes.DEFAULT_TYPE, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    q = update.callback_query
    await q.answer()
    data = q.data

    if data.startswith("fixpage:"):
        page = int(data.split(":", 1)[1])
        kb = build_fix_keyboard(page)
        await q.message.edit_reply_markup(reply_markup=kb)
        return CHOOSE_TBL_FIELD

    if data == "fixnoop":
        return CHOOSE_TBL_FIELD

    if data == "back_to_confirm":
        await q.message.delete()
        return CHOOSE_EDIT_MENU

    if data.startswith("fix:"):
        key = data.split(":", 1)[1]
        cap = dict(SCALAR_FIELDS)[key]
        ctx.user_data["__fix_key"] = key
        await q.message.reply_text(f"Введите новое значение для «{cap}»:")
        await q.answer()
        return ASK_SCALAR

    return CHOOSE_TBL_FIELD


def build_fix_keyboard(page: int = 0) -> InlineKeyboardMarkup:
    total = len(SCALAR_FIELDS)
    total_pages = max(1, math.ceil(total / PAGE_SIZE))
    page = max(0, min(page, total_pages - 1))

    start = page * PAGE_SIZE
    slice_fields = SCALAR_FIELDS[start:start + PAGE_SIZE]

    rows = [[InlineKeyboardButton(text=cap, callback_data=f"fix:{key}")]
            for key, cap in slice_fields]

    if total_pages > 1:
        nav = [
            InlineKeyboardButton("«", callback_data="fixpage:0"),
            InlineKeyboardButton("‹", callback_data=f"fixpage:{page-1 if page>0 else total_pages-1}"),
            InlineKeyboardButton(f"{page+1}/{total_pages}", callback_data="fixnoop"),
            InlineKeyboardButton("›", callback_data=f"fixpage:{(page+1) % total_pages}"),
            InlineKeyboardButton("»", callback_data=f"fixpage:{total_pages-1}"),
        ]
        rows.append(nav)

    rows.append([InlineKeyboardButton("⬅️ Назад", callback_data="back_to_confirm")])
    return InlineKeyboardMarkup(rows)