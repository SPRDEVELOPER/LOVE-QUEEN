"""Global error handler - logs the traceback, shows users only a friendly message."""
from __future__ import annotations

import logging

from pymongo.errors import PyMongoError
from telegram import Update
from telegram.error import NetworkError, TimedOut
from telegram.ext import ContextTypes

from src.bot import texts
from src.utils.smallcaps import sc

log = logging.getLogger(__name__)


async def on_error(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    err = context.error
    log.error("update caused error", exc_info=err)
    if isinstance(err, (NetworkError, TimedOut)) or not isinstance(update, Update):
        return
    key = "db" if isinstance(err, PyMongoError) else "generic"
    try:
        if update.callback_query:
            await update.callback_query.answer(sc(texts.ERRORS[key]), show_alert=True)
        elif update.effective_message:
            await update.effective_message.reply_text(sc(texts.ERRORS[key]))
        if context.user_data is not None:
            context.user_data["busy"] = False
    except Exception:  # last line of defence - never raise from here
        pass
