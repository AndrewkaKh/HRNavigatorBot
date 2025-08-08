import asyncio

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from database.crud_sync import list_vacancies_sync

VAC_PAGE_SIZE = 5

def _short_line(text: str, maxlen: int = 60) -> str:
    if not text:
        return ""
    line = text.splitlines()[0].strip()
    if len(line) > maxlen:
        line = line[: maxlen - 1] + "…"
    return line

def _build_list_keyboard(vacs: list[dict], page: int) -> InlineKeyboardMarkup:
    total = len(vacs)
    total_pages = max(1, (total + VAC_PAGE_SIZE - 1) // VAC_PAGE_SIZE)
    page = max(0, min(page, total_pages - 1))
    start = page * VAC_PAGE_SIZE
    end = min(start + VAC_PAGE_SIZE, total)

    rows: list[list[InlineKeyboardButton]] = []
    for idx in range(start, end):
        v = vacs[idx]
        #who = _short_line(v["description"])
        text = f"{v['name']}"
        rows.append([InlineKeyboardButton(text=text, callback_data=f"vac:open:{idx}:{page}")])

    if total_pages > 1:
        prev_page = (page - 1) % total_pages
        next_page = (page + 1) % total_pages
        nav = [
            InlineKeyboardButton("«", callback_data="vac:page:0"),
            InlineKeyboardButton("‹", callback_data=f"vac:page:{prev_page}"),
            InlineKeyboardButton(f"{page+1}/{total_pages}", callback_data="vac:page:{page}"),  # индикатор
            InlineKeyboardButton("›", callback_data=f"vac:page:{next_page}"),
            InlineKeyboardButton("»", callback_data=f"vac:page:{total_pages-1}"),
        ]
        rows.append(nav)

    return InlineKeyboardMarkup(rows)

def _build_list_text(vacs: list[dict], page: int) -> str:
    total = len(vacs)
    total_pages = max(1, (total + VAC_PAGE_SIZE - 1) // VAC_PAGE_SIZE)
    page = max(0, min(page, total_pages - 1))
    start = page * VAC_PAGE_SIZE
    end = min(start + VAC_PAGE_SIZE, total)

    lines = [f"📋 Вакансии — страница {page+1}/{total_pages}"]
    """for idx in range(start, end):
        v = vacs[idx]
        who = _short_line(v["description"])
        lines.append(f"• {v['name']}" + (f" — {who}" if who else ""))"""
    return "\n".join(lines)

async def cmd_vacancies(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    vacs_db = await asyncio.to_thread(list_vacancies_sync)
    if not vacs_db:
        await (update.message or update.callback_query.message).reply_text("Пока нет активных вакансий.")
        return

    vacs = [{"name": v.name, "description": v.description or ""} for v in vacs_db]
    ctx.user_data["__vacs"] = vacs

    page = 0
    text = _build_list_text(vacs, page)
    kb = _build_list_keyboard(vacs, page)
    await (update.message or update.callback_query.message).reply_text(text, reply_markup=kb)

async def vacancies_callback(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    vacs: list[dict] = ctx.user_data.get("__vacs", [])

    if not vacs:
        await q.message.reply_text("Список вакансий устарел. Наберите /vacancies ещё раз.")
        return

    data = q.data

    if data.startswith("vac:page:"):
        page = int(data.split(":", 2)[2])
        text = _build_list_text(vacs, page)
        kb = _build_list_keyboard(vacs, page)
        await q.message.edit_text(text, reply_markup=kb)
        return

    if data.startswith("vac:open:"):
        _, _, idx_str, page_str = data.split(":", 3)
        idx = int(idx_str)
        page = int(page_str)
        if idx < 0 or idx >= len(vacs):
            await q.message.reply_text("Эта вакансия больше недоступна. Обновите список: /vacancies")
            return
        v = vacs[idx]
        text = f"**{v['name']}**\n\n{v['description']}".replace("*", "•")  # лёгкая защита от Markdown
        kb = InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Назад", callback_data=f"vac:back:{page}")]])
        await q.message.edit_text(text, reply_markup=kb)
        return

    if data.startswith("vac:back:"):
        page = int(data.split(":", 2)[2])
        text = _build_list_text(vacs, page)
        kb = _build_list_keyboard(vacs, page)
        await q.message.edit_text(text, reply_markup=kb)
        return
