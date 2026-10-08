"""Reusable screens, shared by command handlers and callback handlers."""
from __future__ import annotations

from src.bot import keyboards as kb, texts
from src.bot.ui import render

FIRE_EFFECT = "5104841245755180586"  # Telegram message effect: 🔥 (private chats)


def S(context):
    return context.bot_data["state"]


def is_admin(context, user_id: int) -> bool:
    return user_id in context.bot_data["settings"].admin_ids


async def show_home(context, chat_id, mid, section="menu", effect=None):
    return await render(context.bot, S(context).images, chat_id, mid, section, texts.welcome(), kb.main_menu(), effect)


async def show_help(context, chat_id, mid):
    return await render(context.bot, S(context).images, chat_id, mid, "help", texts.help_text(), kb.home_only())


async def show_stats(context, chat_id, mid, user):
    st = S(context)
    doc = await st.db.get_user(user.id)
    text = texts.stats(doc)
    if is_admin(context, user.id):
        text += "\n\n" + texts.dashboard(await st.db.global_stats())
    return await render(context.bot, st.images, chat_id, mid, "stats", text, kb.play_and_home())


async def show_leaderboard(context, chat_id, mid, page: int):
    st = S(context)
    size = st.settings.lb_page_size
    total, rows = await st.db.leaderboard(max(0, page), size)
    pages = max(1, -(-total // size))
    page = min(max(0, page), pages - 1)
    if rows == [] and total:  # page out of range -> reload last page
        total, rows = await st.db.leaderboard(page, size)
    return await render(
        context.bot, st.images, chat_id, mid, "leaderboard",
        texts.leaderboard(rows, page, size, total), kb.leaderboard(page, pages),
    )


async def show_last_result(context, chat_id, mid, user):
    st = S(context)
    game = await st.db.last_game(user.id)
    if not game:
        return await render(
            context.bot, st.images, chat_id, mid, "menu",
            "🔎 <b>no result yet</b>\n" + texts.LINE + "\nplay a game first! 🔥", kb.play_and_home(),
        )
    username = st.settings.bot_username or context.bot.username
    return await render(
        context.bot, st.images, chat_id, mid, f"res_{game['result']}",
        texts.result_text(game["result"], game["percent"], game["player1"], game["player2"]),
        kb.result(game["result"], game["player1"], game["player2"], username),
    )
