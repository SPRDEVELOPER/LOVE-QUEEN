"""MongoDB layer (motor). Collections: users, games."""
from __future__ import annotations

import logging
from datetime import datetime, timezone

from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import ASCENDING, DESCENDING

log = logging.getLogger(__name__)
LETTERS = "FLAMES"


def _now() -> datetime:
    return datetime.now(timezone.utc)


class Database:
    def __init__(self, uri: str, name: str):
        self.client = AsyncIOMotorClient(uri, serverSelectionTimeoutMS=8000, tz_aware=True)
        self.db = self.client[name]
        self.users = self.db["users"]
        self.games = self.db["games"]

    async def connect(self) -> None:
        await self.client.admin.command("ping")
        await self.users.create_index([("total_games", DESCENDING), ("joined_at", ASCENDING)])
        await self.users.create_index("banned")
        await self.games.create_index([("user_id", ASCENDING), ("created_at", DESCENDING)])
        await self.games.create_index("created_at")
        log.info("MongoDB connected")

    def close(self) -> None:
        self.client.close()

    # ── users ────────────────────────────────────────────────
    async def upsert_user(self, tg_user) -> None:
        await self.users.update_one(
            {"_id": tg_user.id},
            {
                "$set": {
                    "username": tg_user.username,
                    "first_name": tg_user.first_name,
                    "last_seen": _now(),
                },
                "$setOnInsert": {
                    "joined_at": _now(),
                    "total_games": 0,
                    "results": {k: 0 for k in LETTERS},
                    "banned": False,
                },
            },
            upsert=True,
        )

    async def get_user(self, user_id: int):
        return await self.users.find_one({"_id": user_id})

    async def set_banned(self, user_id: int, flag: bool) -> bool:
        res = await self.users.update_one({"_id": user_id}, {"$set": {"banned": flag}})
        return res.matched_count > 0

    async def banned_ids(self) -> set:
        return {d["_id"] async for d in self.users.find({"banned": True}, {"_id": 1})}

    async def active_user_ids(self) -> list:
        return [d["_id"] async for d in self.users.find({"banned": {"$ne": True}}, {"_id": 1})]

    async def recent_users(self, limit: int = 20) -> list:
        cur = self.users.find({}).sort("joined_at", DESCENDING).limit(limit)
        return [d async for d in cur]

    # ── games ────────────────────────────────────────────────
    async def record_game(self, tg_user, p1: str, p2: str, letter: str, percent: int) -> None:
        await self.upsert_user(tg_user)
        await self.games.insert_one(
            {
                "user_id": tg_user.id,
                "player1": p1,
                "player2": p2,
                "result": letter,
                "percent": percent,
                "created_at": _now(),
            }
        )
        await self.users.update_one(
            {"_id": tg_user.id},
            {"$inc": {"total_games": 1, f"results.{letter}": 1}, "$set": {"last_game_at": _now()}},
        )

    async def last_game(self, user_id: int):
        return await self.games.find_one({"user_id": user_id}, sort=[("created_at", DESCENDING)])

    # ── leaderboard / dashboard ──────────────────────────────
    async def leaderboard(self, page: int, size: int):
        flt = {"total_games": {"$gt": 0}, "banned": {"$ne": True}}
        total = await self.users.count_documents(flt)
        cur = (
            self.users.find(flt)
            .sort([("total_games", DESCENDING), ("joined_at", ASCENDING)])
            .skip(page * size)
            .limit(size)
        )
        return total, [d async for d in cur]

    async def global_stats(self) -> dict:
        today = _now().replace(hour=0, minute=0, second=0, microsecond=0)
        users = await self.users.count_documents({})
        banned = await self.users.count_documents({"banned": True})
        games = await self.games.count_documents({})
        today_games = await self.games.count_documents({"created_at": {"$gte": today}})
        top = await self.games.aggregate(
            [{"$group": {"_id": "$result", "n": {"$sum": 1}}}, {"$sort": {"n": -1}}, {"$limit": 1}]
        ).to_list(1)
        return {
            "users": users,
            "banned": banned,
            "games": games,
            "today": today_games,
            "top": (top[0]["_id"], top[0]["n"]) if top else None,
        }
