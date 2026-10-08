"""The signature FLAMES animation: loading bar -> letters cancelling -> FLAMES letters being struck out."""
from __future__ import annotations

import asyncio
from html import escape

from src.bot import texts
from src.bot.ui import render, safe_edit_caption
from src.games.flames import FLAMES, FlamesResult
from src.utils.smallcaps import sc

HEAD = "🔥 <b>flames bot</b> 🔥\n━━━━━━━━━━━━━━\n"


def _name_row(name: str, mask=None) -> str:
    out = []
    for i, ch in enumerate(name):
        c = escape(ch)
        out.append(f"<s>{c}</s>" if mask and mask[i] else c)
    return " ".join(out)


def _flames_row(removed: set, current: str = "") -> str:
    out = []
    for ch in FLAMES:
        if ch in removed:
            out.append(f"<s>{ch}</s>")
        else:
            out.append(ch)
    return "  ".join(out)


async def play(bot, images, chat_id, mid, res: FlamesResult, delay: float = 0.85):
    """Runs the animation and returns the (possibly new) message id."""
    bar = texts.bar

    mid = await render(
        bot, images, chat_id, mid, "loading",
        HEAD + "⏳ calculating your flames result...\n" + f"{bar(0)} 0%",
    )
    if mid is None:
        return None

    async def frame(body: str):
        await asyncio.sleep(delay)
        await safe_edit_caption(bot, chat_id, mid, sc(HEAD + body))

    await frame(f"🔥 calculating...\n{bar(20)} 20%")
    await frame(f"❤️ matching names...\n\n👤 {_name_row(res.name1)}\n💑 {_name_row(res.name2)}\n\n{bar(40)} 40%")
    await frame(
        "❤️ matching names...\n\n"
        f"👤 {_name_row(res.name1, res.mask1)}\n💑 {_name_row(res.name2, res.mask2)}\n\n"
        f"💥 common letters cancelled!\n🔢 remaining letters: <b>{res.remaining}</b>\n\n{bar(60)} 60%"
    )

    if not res.steps:
        await frame(f"💫 running flames...\n\n🌟 perfect match — every letter cancelled!\n\n{bar(90)} 90%")
    else:
        removed: set = set()
        total = len(res.steps)
        for i, step in enumerate(res.steps, start=1):
            removed.add(step.removed)
            pct = 60 + int(30 * i / total)
            await frame(
                f"💫 running flames...\n🔢 counting by <b>{res.remaining}</b>\n\n"
                f"{_flames_row(removed)}\n\n"
                f"💥 <b>{step.removed}</b> eliminated — {len(step.remaining)} left\n\n{bar(pct)} {pct}%"
            )

    await frame(f"✨ result ready!\n\n🎯 final letter: <b>{res.letter}</b>\n\n{bar(100)} 100%")
    await asyncio.sleep(0.6)
    return mid
