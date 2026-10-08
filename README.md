# 🔥 ꜰʟᴀᴍᴇꜱ ʙᴏᴛ

A modern Telegram **FLAMES** relationship game bot written in Python
(`python-telegram-bot` 21 + MongoDB).

* Deterministic FLAMES algorithm (same two names -> always the same result)
* Animated result: loading bar -> matching letters get struck out -> the FLAMES letters are eliminated one by one -> reveal
* Anime-girl image on every screen (welcome, menu, help, prompts, loading, all six results, stats, leaderboard, admin)
* **All bot text and button labels are rendered in small caps** (`ꜱᴍᴀʟʟ ᴄᴀᴘꜱ`)
* Stats, paginated leaderboard, share button, anti-spam, cooldown, ban system, admin dashboard, broadcast
* Polling **and** webhook mode, Docker ready

> ⚠️ FLAMES is only a fun entertainment game, not a real relationship prediction.

## Project layout

```
flames-bot/
├── src/
│   ├── main.py            entry point (polling / webhook)
│   ├── bot/               app wiring, UI renderer, animations, keyboards, texts
│   ├── commands/          /start /help /flames /result /stats /leaderboard /cancel + admin commands
│   ├── handlers/          game flow, callbacks, anti-spam guard, error handler
│   ├── games/flames.py    pure FLAMES algorithm (no Telegram, fully testable)
│   ├── database/          MongoDB layer (users + games)
│   ├── utils/             small-caps, validators, rate limiter, image provider
│   └── config/            environment settings
├── tests/                 pytest suite
├── .env.example  requirements.txt  Dockerfile  docker-compose.yml  render.yaml  railway.json
```

## Configuration (`.env`)

Copy `.env.example` to `.env` and fill in:

| variable | meaning |
|---|---|
| `BOT_TOKEN` | token from [@BotFather](https://t.me/BotFather) |
| `MONGODB_URI` | MongoDB connection string (local, or free [MongoDB Atlas](https://www.mongodb.com/atlas)) |
| `ADMIN_ID` | your numeric Telegram id (several: `111,222`) |
| `BOT_USERNAME` | bot username without `@` (optional, auto-detected) |

Optional: `DB_NAME`, `MODE` (`polling`/`webhook`), `WEBHOOK_URL`, `PORT`, `COOLDOWN_SECONDS`,
`MAX_NAME_LENGTH`, `RATE_LIMIT_MAX`, `RATE_LIMIT_WINDOW`, `LEADERBOARD_PAGE_SIZE`, `IMG_<SECTION>`.

Mode is chosen automatically: a public URL (`WEBHOOK_URL`, Render's `RENDER_EXTERNAL_URL`,
Railway's `RAILWAY_PUBLIC_DOMAIN`) -> webhook, otherwise polling.

## Anime images

Images are fetched live from the free SFW anime APIs **waifu.pics** and **nekos.best**,
so nothing is stored in the repo and every screen shows a fresh image.
To use your own pictures, set direct image URLs per section in `.env`:

```
IMG_WELCOME=https://example.com/a.jpg,https://example.com/b.jpg
IMG_RES_L=https://example.com/lovers.jpg
```
Sections: `WELCOME MENU HELP STATS LEADERBOARD LOADING PROMPT1 PROMPT2 ADMIN ERROR RES_F RES_L RES_A RES_M RES_E RES_S`.
If an image source is unreachable the bot falls back to a text-only message, it never crashes.

## 1. Local development

```bash
python -m venv .venv && source .venv/bin/activate     # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env                                  # fill BOT_TOKEN, MONGODB_URI, ADMIN_ID
python -m src.main
pytest                                                # run the tests
```

## 2. GitHub

```bash
git init && git add . && git commit -m "FLAMES BOT"
git branch -M main
git remote add origin https://github.com/<you>/flames-bot.git
git push -u origin main
```
`.env` is git-ignored - never commit your token.

## 3. Render (webhook mode, Docker)

1. Push to GitHub -> Render -> **New + -> Blueprint** (uses `render.yaml`) or **New Web Service -> Docker**.
2. Add env vars `BOT_TOKEN`, `MONGODB_URI`, `ADMIN_ID`, `BOT_USERNAME`.
3. Deploy. `RENDER_EXTERNAL_URL` is detected automatically and the webhook is registered on boot.
4. Free instances sleep when idle - use a paid instance (or an uptime pinger) for a bot that must always answer.

## 4. Railway

1. **New Project -> Deploy from GitHub repo** (the Dockerfile is used).
2. Add the same env vars. Under *Settings -> Networking* click **Generate Domain** -> webhook mode is enabled automatically.
   (Without a domain the bot runs in polling mode, which also works on Railway.)

## 5. Docker

```bash
docker compose up -d --build        # bot + local MongoDB, reads .env
# or just the bot with an external MongoDB:
docker build -t flames-bot .
docker run -d --env-file .env --name flames-bot flames-bot
```

## Commands

| user | admin only |
|---|---|
| `/start` `/help` `/flames` `/result` `/stats` `/leaderboard` `/cancel` | `/admin` `/users` `/broadcast` `/ban <id>` `/unban <id>` |

* `/stats` shows personal stats; admins additionally see the global dashboard
  (total users, total games, games today (UTC), most popular result).
* `/broadcast your text` or reply to any message with `/broadcast` (media is copied as-is).

## Privacy

User ids and names are stored only in your own database. The leaderboard shows just a public
`@username` (or first name) and a game count - never ids.

## Notes

* Identical names are a "perfect match" (all letters cancel) and give **Marriage**.
* Compatibility % is derived from a stable hash of the two names inside the range of the result, so it is consistent too.
* Anti-spam: sliding-window rate limit, game cooldown, name validation, per-user busy lock, global error handler (no stack traces for users).
