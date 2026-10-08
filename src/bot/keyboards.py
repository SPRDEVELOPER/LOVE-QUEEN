from __future__ import annotations

from urllib.parse import quote

from telegram import InlineKeyboardButton as B, InlineKeyboardMarkup as M

from src.bot import texts
from src.utils.smallcaps import sc


def main_menu() -> M:
    return M(
        [
            [B(sc("🔥 PLAY FLAMES"), callback_data="menu:play")],
            [B(sc("📊 MY STATS"), callback_data="menu:stats"), B(sc("🏆 LEADERBOARD"), callback_data="lb:0")],
            [B(sc("ℹ️ HOW TO PLAY"), callback_data="menu:help")],
        ]
    )


def prompt(step: int) -> M:
    label = "👤 ENTER FIRST NAME" if step == 1 else "💑 ENTER SECOND NAME"
    return M([[B(sc(label), callback_data="noop")], [B(sc("❌ CANCEL"), callback_data="game:cancel")]])


def result(letter: str, p1: str, p2: str, bot_username: str) -> M:
    share = texts.share_text(letter, p1, p2, bot_username)
    url = f"https://t.me/share/url?url={quote('https://t.me/' + bot_username)}&text={quote(sc(share))}"
    return M(
        [
            [B(sc("🔄 PLAY AGAIN"), callback_data="menu:play"), B(sc("📤 SHARE RESULT"), url=url)],
            [B(sc("🏠 MAIN MENU"), callback_data="menu:home")],
        ]
    )


def home_only() -> M:
    return M([[B(sc("🏠 MAIN MENU"), callback_data="menu:home")]])


def play_and_home() -> M:
    return M(
        [[B(sc("🔥 PLAY FLAMES"), callback_data="menu:play")], [B(sc("🏠 MAIN MENU"), callback_data="menu:home")]]
    )


def leaderboard(page: int, pages: int) -> M:
    nav = []
    if page > 0:
        nav.append(B(sc("⬅️ PREV"), callback_data=f"lb:{page - 1}"))
    if page < pages - 1:
        nav.append(B(sc("NEXT ➡️"), callback_data=f"lb:{page + 1}"))
    rows = [nav] if nav else []
    rows.append([B(sc("🏠 MAIN MENU"), callback_data="menu:home")])
    return M(rows)


def admin() -> M:
    return M(
        [[B(sc("🔄 REFRESH"), callback_data="admin:refresh")], [B(sc("🏠 MAIN MENU"), callback_data="menu:home")]]
    )
