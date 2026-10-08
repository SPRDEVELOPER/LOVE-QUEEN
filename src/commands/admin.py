from __future__ import annotations

import asyncio
import logging
from functools import wraps
from html import escape

from telegram import Update
from telegram.constants import ParseMode
from telegram.error import BadRequest, Forbidden, RetryAfter, TelegramError
from telegram.ext import ContextTypes

from src.bot import keyboards as kb, texts
from src.bot.screens import S, is_admin
from src.bot.ui import reply_small, render
from src.utils.smallcaps import sc

log = logging.getLogger(__name__)


def admin_only(fn):
    @wraps(fn)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not is_admin(context, update.effective_user.id):
            await reply_small(update.effective_message, texts.ERRORS["unauthorized"])
            return
        return await fn(update, context)

    return wrapper


@admin_only
async def admin(update, context):
    st = S(context)
    text = texts.dashboard(await st.db.global_stats()) + texts.ADMIN_HELP
    await render(context.bot, st.images, update.effective_chat.id, None, "admin", text, kb.admin())


@admin_only
async def users(update, context):
    st = S(context)
    g = await st.db.global_stats()
    rows = await st.db.recent_users(20)
    lines = [f"👥 <b>users: {g['users']}</b> (latest {len(rows)})\n"]
    for d in rows:
        name = escape(d.get("first_name") or "-")[:20]
        uname = f" @{d['username']}" if d.get("username") else ""
        flag = " 🚫" if d.get("banned") else ""
        lines.append(f"• <code>{d['_id']}</code> {name}{uname} — {d.get('total_games', 0)}🎮{flag}")
    text = sc("\n".join(lines))
    for i in range(0, len(text), 3800):
        await update.effective_message.reply_text(text[i : i + 3800], parse_mode=ParseMode.HTML)


async def _set_ban(update, context, flag: bool):
    msg = update.effective_message
    try:
        uid = int(context.args[0])
    except (IndexError, ValueError):
        await reply_small(msg, f"usage: /{'ban' if flag else 'unban'} user_id")
        return
    if uid in context.bot_data["settings"].admin_ids:
        await reply_small(msg, "⚠️ you can't ban an admin.")
        return
    found = await S(context).db.set_banned(uid, flag)
    if not found:
        await reply_small(msg, "❓ user not found in the database.")
        return
    banned = S(context).banned
    banned.add(uid) if flag else banned.discard(uid)
    await reply_small(msg, f"{'🚫 banned' if flag else '✅ unbanned'} <code>{uid}</code>")


@admin_only
async def ban(update, context):
    await _set_ban(update, context, True)


@admin_only
async def unban(update, context):
    await _set_ban(update, context, False)


async def _send_one(bot, uid: int, text, src) -> bool:
    for _ in range(2):
        try:
            if src is not None:
                await bot.copy_message(uid, src.chat_id, src.message_id)
            else:
                await bot.send_message(uid, text, parse_mode=ParseMode.HTML)
            return True
        except RetryAfter as exc:
            await asyncio.sleep(exc.retry_after + 1)
        except (Forbidden, BadRequest):
            return False
        except TelegramError:
            return False
    return False


async def _run_broadcast(bot, admin_chat: int, ids, text, src):
    ok = failed = 0
    for uid in ids:
        if await _send_one(bot, uid, text, src):
            ok += 1
        else:
            failed += 1
        await asyncio.sleep(0.05)  # stay far below Telegram's 30 msg/s limit
    try:
        await bot.send_message(
            admin_chat, sc(f"📣 <b>broadcast finished</b>\n✅ delivered: {ok}\n❌ failed: {failed}"), parse_mode=ParseMode.HTML
        )
    except TelegramError:
        pass


@admin_only
async def broadcast(update, context):
    msg = update.effective_message
    src = msg.reply_to_message
    text = None
    if src is None:
        parts = (msg.text_html or "").split(maxsplit=1)
        if len(parts) < 2:
            await reply_small(msg, "usage: /broadcast your message\nor reply to any message with /broadcast")
            return
        text = sc(parts[1])
    ids = await S(context).db.active_user_ids()
    await reply_small(msg, f"📣 broadcasting to <b>{len(ids)}</b> users…")
    context.application.create_task(_run_broadcast(context.bot, msg.chat_id, ids, text, src))
