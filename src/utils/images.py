"""Anime-girl image provider (fast version).

Images come from free SFW anime APIs (waifu.pics, nekos.best).
* Replies are NEVER delayed for long: if no image is ready within ~2.5s the bot sends text only.
* A small pool per screen is filled in the background, so later replies are instant.
* Override any screen with your own direct image URLs:  IMG_<SECTION>=url1,url2
"""
from __future__ import annotations

import asyncio
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
POOL_TARGET = 6


class ImageService:
    def __init__(self) -> None:
        self.client = httpx.AsyncClient(timeout=3.0, follow_redirects=True)
        self._cache: dict = {}
        self._tasks: dict = {}

    async def close(self) -> None:
        for t in list(self._tasks.values()):
            t.cancel()
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

    async def _fetch_one(self, section: str):
        url = await self._fetch(random.choice(SECTIONS.get(section, ["waifu"])))
        if url and not url.lower().endswith(".gif"):  # photos only
            pool = self._cache.setdefault(section, [])
            if url not in pool:
                pool.append(url)
                del pool[:-20]
            return url
        return None

    async def _refill(self, section: str) -> None:
        try:
            for _ in range(POOL_TARGET):
                if len(self._cache.get(section, [])) >= POOL_TARGET:
                    break
                await self._fetch_one(section)
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            log.debug("refill failed: %s", exc)
        finally:
            self._tasks.pop(section, None)

    def _start_refill(self, section: str) -> None:
        if section not in self._tasks:
            self._tasks[section] = asyncio.create_task(self._refill(section))

    async def get(self, section: str):
        override = os.getenv(f"IMG_{section.upper()}", "")
        urls = [u.strip() for u in override.split(",") if u.strip()]
        if urls:
            return random.choice(urls)

        pool = self._cache.get(section)
        if pool:  # instant
            if len(pool) < POOL_TARGET:
                self._start_refill(section)
            return random.choice(pool)

        self._start_refill(section)
        try:  # first use: wait a little, then fall back to text
            return await asyncio.wait_for(self._fetch_one(section), timeout=2.5)
        except Exception:
            return None
