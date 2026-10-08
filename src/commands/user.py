from __future__ import annotations

from telegram import Update
from telegram.ext import ContextTypes

from src.bot import keyboards as kb, texts
from src.bot.screens import (
    FIRE_EFFECT, show_help, show_home, show_last_result, show_leaderboard, show_stats,
)
from src.bot.ui import reply_small
from src.handlers import game


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    context.user_data.pop("state", None)
    await show_home(context, update.effective_chat.id, None, "welcome", effect=FIRE_EFFECT)


async def help_cmd(update, context):
    await show_help(context, update.effective_chat.id, None)


async def flames(update, context):
    problem = game.precheck(context)
    if problem:
        await reply_small(update.effective_message, problem)
        return
    await game.begin_game(context, update.effective_chat.id, None)


async def result(update, context):
    await show_last_result(context, update.effective_chat.id, None, update.effective_user)


async def stats(update, context):
    await show_stats(context, update.effective_chat.id, None, update.effective_user)


async def leaderboard(update, context):
    await show_leaderboard(context, update.effective_chat.id, None, 0)


async def cancel(update, context):
    ok = await game.cancel_game(context, update.effective_chat.id, None)
    if not ok:
        if context.user_data.get("busy"):
            await reply_small(update.effective_message, texts.ERRORS["busy"])
        else:
            await reply_small(update.effective_message, "🤷 there's no active game to cancel.", kb.main_menu())
