# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

IdentityCrisis is a Discord bot + FastAPI web dashboard. It assigns random nicknames to users when they join voice channels. `main.py` runs both services concurrently via `asyncio.gather`.

## Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Run the application (bot + web together)
python main.py
```

There is no test suite or linter configured in this repo.

## Architecture

### Startup Flow
`main.py` → calls `load_config()` and `init_database()` from `shared/`, then spawns both the Discord bot and uvicorn web server as concurrent async tasks.

### Three packages
- **`shared/`** — `config.py` (dataclass loaded once from env, accessed via `get_config()`) and `database.py` (SQLAlchemy async models + `Database` manager, accessed via `get_db()`). Both use a module-level singleton initialized at startup.
- **`bot/`** — `bot.py` creates the `IdentityCrisisBot` and loads cogs from `bot/cogs/`. The single cog `voice_handler.py` handles all voice state events. Default and custom nicknames come from `bot/data/`. Custom channel transformations (reverse, upside-down, leetspeak, etc.) are defined in `bot/data/transformers.py`.
- **`web/`** — FastAPI app created by `web/app.py`. Routes split into `auth.py` (Discord OAuth2 login/callback), `pages.py` (Jinja2 page renders), `api.py` (REST endpoints for guild management), and `dependencies.py` (`get_current_user` dependency that reads/refreshes the session cookie).

### Database Models (`shared/database.py`)
- `Guild` — per-server settings (enabled, restore_on_leave, immunity_role_id)
- `Nickname` — custom nickname pool per guild
- `IncludedChannel` — whitelist of voice channels where the bot operates
- `CustomChannel` — voice channels with per-channel transformation rules (stored as JSON array)
- `MemberNickname` — per-user reset nickname (populated on voice join; `reset_nickname_manual=True` when set from dashboard)
- `UserSession` — web dashboard OAuth sessions

Tables are auto-created on startup via `Base.metadata.create_all`.

### Channel Whitelist Logic
If no `IncludedChannel` or `CustomChannel` records exist for a guild, the bot operates in all channels. Once any included or custom channel is configured, only those channels are active. Custom channels are always implicitly included.

### Authentication
Web dashboard uses Discord OAuth2. The `session_id` cookie stores the Discord user ID. `get_current_user` in `dependencies.py` looks up the `UserSession` and auto-refreshes expired tokens. The `LOG_VIEWER_ID` env var grants a single Discord user access to the `/dashboard/logs` page and the full guild list in the API.

## Key Conventions

- DB sessions: `async with db.async_session() as session:` — always `await session.commit()` after mutations
- Discord IDs are `BigInteger` in the DB and cast to `str` in API JSON responses
- `Config` is accessed via `get_config()` after `load_config()` is called in `main.py`
- `get_db()` raises `RuntimeError` if called before `init_database()`; same pattern for `get_config()`
- Nickname length is capped at 32 characters (Discord limit); enforced in the API and in `apply_rules()`
- Member nickname entries older than 30 days are pruned on each `GET /api/guilds/{id}/member-nicknames` call

## Environment Variables

Required: `DISCORD_TOKEN`, `DATABASE_URL`

Optional: `DISCORD_CLIENT_ID`, `DISCORD_CLIENT_SECRET`, `DISCORD_REDIRECT_URI`, `SECRET_KEY`, `WEB_HOST`, `WEB_PORT`, `BASE_URL`, `LOG_FILE_PATH`, `LOG_LEVEL`, `LOG_VIEWER_ID`

The `DATABASE_URL` driver prefix is normalized automatically (`postgres://` → `postgresql+asyncpg://`).
