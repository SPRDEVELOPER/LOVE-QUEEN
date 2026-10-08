"""Anime-girl image provider.

Images come from free SFW anime APIs (waifu.pics, nekos.best) at runtime.
Every section can be overridden with your own direct image URLs:  IMG_<SECTION>=url1,url2
If every source fails the bot simply falls back to a text-only message.
"""
from __future__ import annotations

import logging
import os
import random

import httpx

log = logging.getLogger(__name__)

# "nb:" prefix = nekos.best, otherwise waifu.pics /sfw/<category>
SECTIONS = {
    "welcome": ["waifu", "nb:waifu"],
    "menu": ["neko", "nb:neko"],
    "help": ["shinobu", "nb:waifu"],
    "stats": ["megumin", "waifu"],
    "leaderboard": ["waifu", "nb:waifu"],
    "loading": ["neko", "shinobu"],
    "prompt1": ["waifu", "nb:waifu"],
    "prompt2": ["nb:waifu", "neko"],
    "admin": ["megumin", "nb:kitsune"],
    "error": ["shinobu", "neko"],
    "res_F": ["shinobu", "waifu"],
    "res_L": ["waifu", "nb:waifu"],
    "res_A": ["neko", "nb:neko"],
    "res_M": ["waifu", "nb:kitsune"],
    "res_E": ["megumin", "nb:waifu"],
    "res_S": ["neko", "shinobu"],
}


class ImageService:
    def __init__(self) -> None:
        self.client = httpx.AsyncClient(timeout=4.0, follow_redirects=True)
        self._cache: dict = {}

    async def close(self) -> None:
        await self.client.aclose()

    async def _fetch(self, cat: str):
        try:
            if cat.startswith("nb:"):
                r = await self.client.get(f"https://nekos.best/api/v2/{cat[3:]}")
                r.raise_for_status()
                return r.json()["results"][0]["url"]
            r = await self.client.get(f"https://api.waifu.pics/sfw/{cat}")
            r.raise_for_status()
            return r.json()["url"]
        except Exception as exc:  # network / json / http errors - never fatal
            log.debug("image fetch failed (%s): %s", cat, exc)
            return None

    async def get(self, section: str):
        override = os.getenv(f"IMG_{section.upper()}", "")
        urls = [u.strip() for u in override.split(",") if u.strip()]
        if urls:
            return random.choice(urls)
        cats = SECTIONS.get(section, ["waifu"])
        for _ in range(3):
            url = await self._fetch(random.choice(cats))
            if url and not url.lower().endswith(".gif"):  # photos only (gifs can't be edited into photos)
                pool = self._cache.setdefault(section, [])
                pool.append(url)
                del pool[:-20]
                return url
        pool = self._cache.get(section)
        return random.choice(pool) if pool else None
