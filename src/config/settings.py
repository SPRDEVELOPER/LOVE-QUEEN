"""Environment based configuration. Nothing secret is ever hard-coded."""
from __future__ import annotations

import hashlib
import os
import re
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    bot_token: str
    mongodb_uri: str
    db_name: str
    admin_ids: frozenset
    bot_username: str
    mode: str
    webhook_base: str
    webhook_path: str
    webhook_secret: str
    port: int
    cooldown: int
    rate_max: int
    rate_window: int
    max_name_len: int
    lb_page_size: int


def _int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, "").strip() or default)
    except ValueError:
        return default


def load_settings() -> Settings:
    token = os.getenv("BOT_TOKEN", "").strip()
    uri = os.getenv("MONGODB_URI", "").strip()
    missing = [n for n, v in (("BOT_TOKEN", token), ("MONGODB_URI", uri)) if not v]
    if missing:
        raise RuntimeError(f"Missing required environment variable(s): {', '.join(missing)}")

    admin_ids = frozenset(int(x) for x in re.findall(r"-?\d+", os.getenv("ADMIN_ID", "")))

    base = os.getenv("WEBHOOK_URL", "").strip() or os.getenv("RENDER_EXTERNAL_URL", "").strip()
    if not base and os.getenv("RAILWAY_PUBLIC_DOMAIN"):
        base = "https://" + os.environ["RAILWAY_PUBLIC_DOMAIN"].strip()
    base = base.rstrip("/")

    mode = os.getenv("MODE", "").strip().lower()
    if mode not in ("polling", "webhook"):
        mode = "webhook" if base else "polling"
    if mode == "webhook" and not base:
        raise RuntimeError("MODE=webhook needs WEBHOOK_URL (or a Render/Railway public URL)")

    secret = os.getenv("WEBHOOK_SECRET", "").strip() or hashlib.sha256(token.encode()).hexdigest()[:48]
    path = hashlib.sha256(("path:" + token).encode()).hexdigest()[:40]

    return Settings(
        bot_token=token,
        mongodb_uri=uri,
        db_name=os.getenv("DB_NAME", "flames_bot").strip() or "flames_bot",
        admin_ids=admin_ids,
        bot_username=os.getenv("BOT_USERNAME", "").strip().lstrip("@"),
        mode=mode,
        webhook_base=base,
        webhook_path=path,
        webhook_secret=re.sub(r"[^A-Za-z0-9_-]", "", secret) or "flamesbot",
        port=_int("PORT", 8080),
        cooldown=max(0, _int("COOLDOWN_SECONDS", 8)),
        rate_max=max(1, _int("RATE_LIMIT_MAX", 8)),
        rate_window=max(1, _int("RATE_LIMIT_WINDOW", 10)),
        max_name_len=max(3, _int("MAX_NAME_LENGTH", 30)),
        lb_page_size=max(3, _int("LEADERBOARD_PAGE_SIZE", 10)),
    )
