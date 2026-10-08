"""Runs before every handler: ban check, rate-limit (anti-spam), user bookkeeping."""
from __future__ import annotations

import logging
import time

from telegram import Update
from telegram.ext import ApplicationHandlerStop, ContextTypes

from src.bot import texts
from src.bot.ui import reply_small
from src.utils.smallcaps import sc

log = logging.getLogger(__name__)


async def guard(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    if user is None or user.is_bot:
        raise ApplicationHandlerStop
    st = context.bot_data["state"]
    admin = user.id in st.settings.admin_ids
    query, message = update.callback_query, update.effective_message
    now = time.time()

    if user.id in st.banned and not admin:
        if query:
            await query.answer(sc(texts.ERRORS["banned"]), show_alert=True)
        elif message and now - st.warned.get(("ban", user.id), 0) > 60:
            st.warned[("ban", user.id)] = now
            await reply_small(message, texts.ERRORS["banned"])
        raise ApplicationHandlerStop

    if not admin and not st.limiter.allow(user.id):
        if query:
            await query.answer(sc(texts.ERRORS["slow"]))
        elif message and now - st.warned.get(("slow", user.id), 0) > 10:
            st.warned[("slow", user.id)] = now
            await reply_small(message, texts.ERRORS["slow"])
        raise ApplicationHandlerStop

    if now - st.synced.get(user.id, 0) > 300:
        try:
            await st.db.upsert_user(user)
            st.synced[user.id] = now
        except Exception as exc:  # DB hiccup must never block the bot
            log.warning("user sync failed: %s", exc)
    if len(st.warned) > 5000:
        st.warned.clear()
