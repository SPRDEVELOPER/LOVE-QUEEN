from __future__ import annotations

from telegram import Update
from telegram.ext import ContextTypes

from src.bot import keyboards as kb, texts
from src.bot.screens import S, is_admin, show_help, show_home, show_leaderboard, show_stats
from src.bot.ui import render
from src.handlers import game
from src.utils.smallcaps import sc


def _ids(update):
    m = update.callback_query.message
    return m.chat_id, m.message_id


async def noop(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.callback_query.answer(sc("✍️ type the name in the chat 👇"), show_alert=False)


async def home(update, context):
    await update.callback_query.answer()
    chat_id, mid = _ids(update)
    await show_home(context, chat_id, mid, "menu")


async def play(update, context):
    q = update.callback_query
    problem = game.precheck(context)
    if problem:
        await q.answer(sc(problem), show_alert=True)
        return
    await q.answer()
    chat_id, mid = _ids(update)
    await game.begin_game(context, chat_id, mid)


async def cancel(update, context):
    q = update.callback_query
    if context.user_data.get("busy"):
        await q.answer(sc(texts.ERRORS["busy"]), show_alert=True)
        return
    await q.answer(sc("❌ cancelled"))
    chat_id, mid = _ids(update)
    await game.cancel_game(context, chat_id, mid)


async def stats(update, context):
    await update.callback_query.answer()
    chat_id, mid = _ids(update)
    await show_stats(context, chat_id, mid, update.effective_user)


async def help_(update, context):
    await update.callback_query.answer()
    chat_id, mid = _ids(update)
    await show_help(context, chat_id, mid)


async def leaderboard(update, context):
    await update.callback_query.answer()
    chat_id, mid = _ids(update)
    try:
        page = int(update.callback_query.data.split(":")[1])
    except (IndexError, ValueError):
        page = 0
    await show_leaderboard(context, chat_id, mid, page)


async def admin_refresh(update, context):
    q = update.callback_query
    if not is_admin(context, update.effective_user.id):
        await q.answer(sc(texts.ERRORS["unauthorized"]), show_alert=True)
        return
    await q.answer(sc("🔄 refreshed"))
    st = S(context)
    chat_id, mid = _ids(update)
    text = texts.dashboard(await st.db.global_stats()) + texts.ADMIN_HELP
    await render(context.bot, st.images, chat_id, mid, "admin", text, kb.admin())


async def stale(update, context):
    """Any callback we do not know (old buttons) - just stop the spinner."""
    await update.callback_query.answer()
