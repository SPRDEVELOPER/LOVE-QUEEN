"""All user-facing text (plain HTML). `sc()` is applied centrally by the UI layer."""
from __future__ import annotations

from html import escape as e

from src.games.flames import LABELS

LINE = "━━━━━━━━━━━━━━"
EMOJI = {"F": "🤝", "L": "❤️", "A": "💕", "M": "💍", "E": "⚔️", "S": "👨‍👩‍👧"}

STYLE = {
    "F": dict(deco="🤝", line="━━━━━━━━━━━━━━", mid="🤝", quote="a bond that never breaks — best buddies forever! 🥳"),
    "L": dict(deco="❤️", line="❤️━━━━━━━━━━━━❤️", mid="❤️", quote="looks like there's some chemistry! 😍"),
    "A": dict(deco="💕", line="💕─────────────💕", mid="💞", quote="so much care and warmth between you two! 🥰"),
    "M": dict(deco="💍", line="💍✦━━━━━━━━━✦💍", mid="💍", quote="wedding bells are ringing! 🔔💒"),
    "E": dict(deco="⚔️", line="⚔️▬▬▬▬▬▬▬▬▬▬⚔️", mid="⚔️", quote="sparks fly — but not the good kind! 😤🔥"),
    "S": dict(deco="👨‍👩‍👧", line="🌸┈┈┈┈┈┈┈┈┈┈🌸", mid="👨‍👩‍👧", quote="family vibes — protective and annoying in equal measure! 😂"),
}

ERRORS = {
    "empty": "⚠️ name can't be empty. please type a name.",
    "too_long": "⚠️ that name is too long. please keep it shorter.",
    "no_letters": "⚠️ names need at least one letter — numbers or symbols alone don't work.",
    "same": "⚠️ please enter two different names.",
    "busy": "⏳ hold on, your result is being calculated!",
    "expired": "⌛ this game expired. tap play to start again.",
    "generic": "⚠️ something went wrong. please try again.",
    "db": "🛠 the database is busy right now. please try again soon.",
    "unexpected": "💬 i didn't get that. use the menu below 👇",
    "non_text": "📝 please send the name as plain text.",
    "unknown_cmd": "❓ unknown command. try /help",
    "unauthorized": "⛔ not authorized.",
    "banned": "🚫 you are banned from using this bot.",
    "slow": "⏳ slow down a little!",
}


def cooldown(n: int) -> str:
    return f"⏳ cooling down… try again in {n}s."


def bar(pct: int, width: int = 10) -> str:
    filled = round(pct / 100 * width)
    return "▰" * filled + "▱" * (width - filled)


def welcome() -> str:
    return (
        "🔥 <b>welcome to flames bot</b> 🔥\n"
        f"{LINE}\n"
        "want to know your relationship result? 😏❤️\n\n"
        "enter two names and let flames decide!\n\n"
        "🤝 friends\n❤️ lovers\n💕 affection\n💍 marriage\n⚔️ enemies\n👨‍👩‍👧 siblings\n\n"
        "👇 tap below to start!"
    )


def help_text() -> str:
    return (
        "ℹ️ <b>how to play</b>\n"
        f"{LINE}\n"
        "1️⃣ press play flames.\n"
        "2️⃣ enter the first name.\n"
        "3️⃣ enter the second name.\n"
        "4️⃣ the bot calculates the common letters.\n"
        "5️⃣ flames elimination is performed.\n"
        "6️⃣ your final relationship result is displayed.\n\n"
        "📜 <b>commands</b>\n"
        "/start • /flames • /result\n/stats • /leaderboard • /cancel • /help\n\n"
        "⚠️ <i>this is only a fun entertainment game, not a real relationship prediction.</i>"
    )


def prompt_first() -> str:
    return (
        "🔥 <b>new flames game</b>\n"
        f"{LINE}\n"
        "👤 <b>type the first name</b> in the chat 👇\n\n"
        "<i>/cancel to stop</i>"
    )


def prompt_second(p1: str) -> str:
    return (
        "🔥 <b>new flames game</b>\n"
        f"{LINE}\n"
        f"👤 first name: <b>{e(p1)}</b> ✅\n\n"
        "💑 <b>now type the second name</b> 👇\n\n"
        "<i>/cancel to stop</i>"
    )


def result_text(letter: str, percent: int, p1: str, p2: str) -> str:
    st = STYLE[letter]
    return (
        f"{st['deco']} <b>flames result</b> {st['deco']}\n"
        f"{st['line']}\n\n"
        f"👤 person 1: <b>{e(p1)}</b>\n"
        f"👤 person 2: <b>{e(p2)}</b>\n\n"
        f"💖 result: {EMOJI[letter]} <b>{LABELS[letter].upper()}</b>\n"
        f"🔥 compatibility: {bar(percent)} <b>{percent}%</b>\n\n"
        f"<i>“{st['quote']}”</i>\n\n"
        f"{st['line']}\n"
        "🔥 play again and test another pair!"
    )


def share_text(letter: str, p1: str, p2: str, bot_username: str) -> str:
    st = STYLE[letter]
    return (
        "🔥 FLAMES RESULT 🔥\n\n"
        f"{st['mid']} {p1} + {p2} {st['mid']}\n\n"
        f"Result: {LABELS[letter].upper()} {EMOJI[letter]}\n\n"
        f"Try your FLAMES result with:\n@{bot_username}"
    )


def stats(doc) -> str:
    if not doc or not doc.get("total_games"):
        return (
            "📊 <b>my stats</b>\n"
            f"{LINE}\n"
            "🎮 games played: <b>0</b>\n\n"
            "no games yet — tap play and try your first pair! 🔥"
        )
    res = doc.get("results", {})
    lines = [f"{EMOJI[k]} {LABELS[k].lower()}: <b>{res.get(k, 0)}</b>" for k in "FLAMES"]
    top = max("FLAMES", key=lambda k: (res.get(k, 0), -"FLAMES".index(k)))
    return (
        "📊 <b>my stats</b>\n"
        f"{LINE}\n"
        f"🎮 games played: <b>{doc['total_games']}</b>\n\n"
        + "\n".join(lines)
        + f"\n\n🏆 most common result: <b>{LABELS[top].upper()}</b> {EMOJI[top]}"
    )


def display_name(doc) -> str:
    name = doc.get("username") and "@" + doc["username"] or doc.get("first_name") or "player"
    return e(name[:22])


def leaderboard(rows, page: int, size: int, total: int) -> str:
    pages = max(1, -(-total // size))
    head = f"🏆 <b>flames leaderboard</b>\n{LINE}\n"
    if not rows:
        return head + "nobody has played yet — be the first! 🔥"
    medals = {1: "🥇", 2: "🥈", 3: "🥉"}
    out = []
    for i, d in enumerate(rows, start=page * size + 1):
        out.append(f"{i}. {medals.get(i, '🔸')} {display_name(d)} — <b>{d['total_games']}</b> games")
    return head + "\n".join(out) + f"\n\n📄 page {page + 1}/{pages}"


def dashboard(g: dict) -> str:
    top = f"{LABELS[g['top'][0]].upper()} {EMOJI[g['top'][0]]} ({g['top'][1]})" if g["top"] else "—"
    return (
        "🛠 <b>admin dashboard</b>\n"
        f"{LINE}\n"
        f"👥 total users: <b>{g['users']}</b>\n"
        f"🎮 total games: <b>{g['games']}</b>\n"
        f"📈 games today (utc): <b>{g['today']}</b>\n"
        f"🔥 most popular result: <b>{top}</b>\n"
        f"🚫 banned users: <b>{g['banned']}</b>"
    )


ADMIN_HELP = (
    "\n\n📜 <b>admin commands</b>\n"
    "/admin • /stats • /users\n"
    "/broadcast text (or reply to a message)\n"
    "/ban id • /unban id"
)
