from __future__ import annotations

from telegram import Update
from telegram.ext import ContextTypes

from src.bot import keyboards as kb, texts
from src.bot.ui import reply_small
from src.handlers import game


async def on_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    msg = update.effective_message
    if msg is None:
        return
    ud = context.user_data
    state = ud.get("state")
    if ud.get("busy"):
        return
    if state in ("first", "second"):
        if msg.text:
            await game.handle_text(update, context)
        else:
            await reply_small(msg, texts.ERRORS["non_text"])
        return
    await reply_small(msg, texts.ERRORS["unexpected"], kb.main_menu())


async def unknown_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await reply_small(update.effective_message, texts.ERRORS["unknown_cmd"], kb.main_menu())
