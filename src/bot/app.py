from __future__ import annotations

import asyncio
import logging

from telegram import BotCommand, BotCommandScopeChat, Update
from telegram.ext import (
    Application, CallbackQueryHandler, CommandHandler, MessageHandler, TypeHandler, filters,
)

from src.bot.state import AppState
from src.commands import admin as admin_cmds, user as user_cmds
from src.config.settings import Settings
from src.database.mongo import Database
from src.handlers import callbacks as cb
from src.handlers.errors import on_error
from src.handlers.guard import guard
from src.handlers.messages import on_message, unknown_command
from src.utils.images import ImageService
from src.utils.ratelimit import RateLimiter
from src.utils.smallcaps import sc

log = logging.getLogger(__name__)

PUBLIC_COMMANDS = [
    ("start", "start the bot"),
    ("flames", "play a new flames game"),
    ("result", "show my latest result"),
    ("stats", "my game statistics"),
    ("leaderboard", "top players"),
    ("help", "how to play"),
    ("cancel", "cancel the current game"),
]
ADMIN_COMMANDS = [
    ("admin", "admin dashboard"),
    ("users", "list users"),
    ("broadcast", "send a message to everyone"),
    ("ban", "ban a user id"),
    ("unban", "unban a user id"),
]


async def post_init(app: Application) -> None:
    s: Settings = app.bot_data["settings"]
    db = Database(s.mongodb_uri, s.db_name)
    for attempt in range(1, 4):
        try:
            await db.connect()
            break
        except Exception as exc:
            log.error("MongoDB connection failed (%s/3): %s", attempt, exc)
            if attempt == 3:
                raise RuntimeError("could not connect to MongoDB - check MONGODB_URI") from exc
            await asyncio.sleep(2 * attempt)

    state = AppState(settings=s, db=db, images=ImageService(), limiter=RateLimiter(s.rate_max, s.rate_window))
    state.banned = await db.banned_ids()
    app.bot_data["state"] = state

    pub = [BotCommand(c, sc(d)) for c, d in PUBLIC_COMMANDS]
    try:
        await app.bot.set_my_commands(pub)
        for aid in s.admin_ids:
            await app.bot.set_my_commands(
                pub + [BotCommand(c, sc(d)) for c, d in ADMIN_COMMANDS], scope=BotCommandScopeChat(aid)
            )
    except Exception as exc:  # admin may not have started the bot yet
        log.warning("could not set command menu: %s", exc)
    log.info("FLAMES BOT ready as @%s (%s mode)", app.bot.username, s.mode)


async def post_shutdown(app: Application) -> None:
    st = app.bot_data.get("state")
    if st:
        await st.images.close()
        st.db.close()


def build_application(settings: Settings) -> Application:
    app = (
        Application.builder()
        .token(settings.bot_token)
        .concurrent_updates(True)  # animations must never block other users
        .post_init(post_init)
        .post_shutdown(post_shutdown)
        .build()
    )
    app.bot_data["settings"] = settings
    private = filters.ChatType.PRIVATE

    app.add_handler(TypeHandler(Update, guard), group=-1)

    for name, fn in (
        ("start", user_cmds.start), ("help", user_cmds.help_cmd), ("flames", user_cmds.flames),
        ("result", user_cmds.result), ("stats", user_cmds.stats),
        ("leaderboard", user_cmds.leaderboard), ("cancel", user_cmds.cancel),
        ("admin", admin_cmds.admin), ("users", admin_cmds.users), ("broadcast", admin_cmds.broadcast),
        ("ban", admin_cmds.ban), ("unban", admin_cmds.unban),
    ):
        app.add_handler(CommandHandler(name, fn, filters=private))

    for pattern, fn in (
        (r"^noop$", cb.noop), (r"^menu:home$", cb.home), (r"^menu:play$", cb.play),
        (r"^game:cancel$", cb.cancel), (r"^menu:stats$", cb.stats), (r"^menu:help$", cb.help_),
        (r"^lb:\d+$", cb.leaderboard), (r"^admin:refresh$", cb.admin_refresh),
    ):
        app.add_handler(CallbackQueryHandler(fn, pattern=pattern))
    app.add_handler(CallbackQueryHandler(cb.stale))

    app.add_handler(MessageHandler(private & ~filters.COMMAND, on_message))
    app.add_handler(MessageHandler(private & filters.COMMAND, unknown_command))
    app.add_error_handler(on_error)
    return app
