"""Game flow: play -> first name -> second name -> animation -> result."""
from __future__ import annotations

import logging
import time

from telegram.error import TelegramError

from src.bot import animations, keyboards as kb, texts
from src.bot.screens import S, show_home
from src.bot.ui import reply_small, render
from src.games.flames import calculate, normalize
from src.utils.validators import validate_name

log = logging.getLogger(__name__)
STATE_TTL = 300  # seconds a game may wait for a name


def precheck(context):
    """Return an error text if a new game cannot start right now, else None."""
    ud, cfg = context.user_data, context.bot_data["settings"]
    if ud.get("busy"):
        return texts.ERRORS["busy"]
    left = int(cfg.cooldown - (time.time() - ud.get("last_game", 0)) + 0.999)
    if left > 0:
        return texts.cooldown(left)
    return None


def _state(ud):
    st = ud.get("state")
    if st and time.time() - ud.get("state_ts", 0) > STATE_TTL:
        ud.pop("state", None)
        return "expired"
    return st


async def begin_game(context, chat_id, mid) -> None:
    ud = context.user_data
    ud.update(state="first", state_ts=time.time())
    ud.pop("p1", None)
    new_mid = await render(context.bot, S(context).images, chat_id, mid, "prompt1", texts.prompt_first(), kb.prompt(1))
    ud["msg"] = (chat_id, new_mid)


async def cancel_game(context, chat_id, mid) -> bool:
    """Cancel the running game. Returns False when there was nothing to cancel (command use)."""
    ud = context.user_data
    if ud.get("busy"):
        return False
    had = bool(ud.pop("state", None))
    ud.pop("p1", None)
    prompt = ud.pop("msg", None)
    if mid is None:
        if not had:
            return False
        mid = prompt[1] if prompt else None
    await show_home(context, chat_id, mid, "menu")
    return True


async def _try_delete(message) -> None:
    try:
        await message.delete()
    except TelegramError:
        pass


async def handle_text(update, context) -> None:
    """Called for plain text while a game is waiting for a name."""
    msg, ud = update.effective_message, context.user_data
    st, cfg, user = S(context), context.bot_data["settings"], update.effective_user
    state = _state(ud)

    if ud.get("busy"):
        return
    if state == "expired":
        await reply_small(msg, texts.ERRORS["expired"], kb.play_and_home())
        return

    ok, name, err = validate_name(msg.text, cfg.max_name_len)
    if not ok:
        await reply_small(msg, texts.ERRORS[err])
        return

    chat_id = msg.chat_id
    prompt_mid = ud.get("msg", (chat_id, None))[1]

    if state == "first":
        await _try_delete(msg)
        ud.update(p1=name, state="second", state_ts=time.time())
        mid = await render(context.bot, st.images, chat_id, prompt_mid, "prompt2", texts.prompt_second(name), kb.prompt(2))
        ud["msg"] = (chat_id, mid)
        return

    # state == "second"
    p1 = ud.get("p1", "")
    if normalize(p1) == normalize(name):
        await reply_small(msg, texts.ERRORS["same"])
        return
    await _try_delete(msg)
    ud.update(busy=True, state=None)
    try:
        res = calculate(p1, name)
        mid = await animations.play(context.bot, st.images, chat_id, prompt_mid, res)
        username = cfg.bot_username or context.bot.username
        await render(
            context.bot, st.images, chat_id, mid, f"res_{res.letter}",
            texts.result_text(res.letter, res.percent, p1, name),
            kb.result(res.letter, p1, name, username),
        )
        try:
            await st.db.record_game(user, p1, name, res.letter, res.percent)
        except Exception as exc:  # the user still gets the result if the DB is down
            log.error("could not save game: %s", exc)
    finally:
        ud.update(busy=False, last_game=time.time())
        ud.pop("p1", None)
        ud.pop("msg", None)
