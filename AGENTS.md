# IdentityCrisis Agent Guide
# For agentic coding assistants working in this repo.

## Repository overview
- Python 3.11+ Discord bot plus FastAPI web dashboard.
- Entry point: `main.py` runs bot + web concurrently.
- Async SQLAlchemy models live in `shared/database.py`.
- Web routes in `web/routes/` and templates/static assets in `web/`.

## Commands (build, lint, test)
This repo does not define linting or test scripts. Use the commands below for
running the app and note the gaps for tests/linting.

### Setup
- Create and activate venv:
  - `python -m venv venv`
  - `venv\Scripts\activate` (Windows) or `source venv/bin/activate`
- Install dependencies:
  - `pip install -r requirements.txt`
- Configure env:
  - `cp .env.example .env` and fill in `DISCORD_TOKEN` and `DATABASE_URL`.

### Run (dev)
- Run bot + web together:
  - `python main.py`

### Lint
- No linter configured in repo.
- If adding one, keep formatting compatible with existing style (4-space indent,
  type hints, docstrings, no enforced line length observed).

### Tests
- No automated test suite found.
- Single-test command: N/A (no test runner configured).

### Deployment notes
- No container or deployment scripts are provided.
- Production requires configuring `DATABASE_URL`, OAuth credentials, and a
  `SECRET_KEY` for the web dashboard.

## Code style and conventions
Follow the patterns in the existing codebase. The guidelines below are based on
current usage.

### Formatting
- Use 4-space indentation, no tabs.
- Keep lines readable; there is no strict line-length policy enforced.
- Use blank lines to separate logical blocks and import groups.
- Docstrings are common for modules, classes, and async handlers.
- Keep trailing whitespace out of files.

### Imports
- Group imports in this order:
  1. Standard library
  2. Third-party packages
  3. Local application imports
- Keep one blank line between each group.
- Prefer explicit imports over `import *`.

### Typing
- Use type hints on public functions and class methods.
- Prefer modern syntax like `list[str]`, `dict[str, int]`, and `Optional[T]`.
- Use `Optional[T]` or `T | None` consistently within a file.
- Pydantic models are used for API request/response schemas.
- Route handlers usually return plain dicts with JSON-friendly values.

### Naming
- Modules and functions: `snake_case`.
- Classes: `PascalCase`.
- Constants: `UPPER_SNAKE_CASE`.
- Private helpers: prefix with `_`.
- Discord- and DB-specific IDs are generally `int` in code and stringified in
  JSON responses.

### Data and JSON
- JSON payloads should be simple dicts/lists with serializable primitives.
- When returning Discord IDs, cast them to strings in API responses.
- Validate user-provided strings for length limits (nicknames cap at 32).

### Async patterns
- Prefer async SQLAlchemy sessions from the shared DB manager.
- Use `async with db.async_session() as session:` for DB operations.
- `await session.commit()` after mutations; `await session.refresh()` when
  you need updated ORM objects.
- Avoid blocking calls in async handlers.
- Use `httpx.AsyncClient` for Discord HTTP calls.

### Error handling and logging
- Use `logger = logging.getLogger(__name__)` per module.
- Log important lifecycle events (startup/shutdown, data sync, mutations).
- For FastAPI routes, raise `HTTPException` with clear `status_code` and
  `detail` strings.
- For Discord bot operations, catch `discord.Forbidden` and
  `discord.HTTPException`, log the error, and return a safe default.
- When catching generic `Exception`, log with context and re-raise if the
  failure should surface (example in `main.py` and bot setup).
- Prefer structured log messages with placeholders instead of string concat.

### FastAPI conventions
- Routes are grouped by router in `web/routes/` with tags and prefixes.
- Request/response bodies are defined with Pydantic models in the route module.
- Use dependency injection via `Depends(...)` (see `get_current_user`).
- Return JSON-friendly primitives (strings/ints/lists/dicts).
- Use cookies for session tracking (`session_id`) and keep session logic in
  `web/routes/auth.py` and `web/routes/dependencies.py`.

### Discord bot conventions
- Cogs live in `bot/cogs/` and are loaded in `IdentityCrisisBot.setup_hook`.
- Avoid direct `print` except in top-level CLI/entry points.
- Use `discord.Intents.default()` and enable only required intents.
- Keep Discord API errors handled in the cog where possible.

### Database modeling
- SQLAlchemy models inherit from `Base` in `shared/database.py`.
- Use `Mapped[...]` and `mapped_column` for typed columns.
- Keep relationships explicitly defined with `back_populates`.
- Defaults use SQL functions (`func.now`) for timestamps.
- IDs are stored as `BigInteger` for Discord snowflakes.

### Web templates and static assets
- Templates live under `web/templates/` and are rendered by routes in
  `web/routes/pages.py`.
- Static assets are served from `web/static/` and mounted in `web/app.py`.
- Keep template logic light; prefer passing computed values from routes.
- Tailwind classes and Alpine.js are used in templates (see README).

### Configuration
- Environment configuration lives in `shared/config.py` and loads from `.env`.
- `load_config()` should be called once at startup; use `get_config()` later.
- Use `Config` fields rather than raw `os.getenv` in most modules.

## Security and secrets
- Never commit `.env` values or tokens.
- Use `.env.example` as the reference for required variables.
- Avoid logging tokens or OAuth secrets.

## Repo-specific notes for agents
- There are no Cursor or Copilot instruction files in this repo.
- Keep changes focused; avoid reformatting unrelated code.
- Use existing logging patterns and error messages as references.
- Preserve the bot's playful messaging style where applicable.

## Recommended workflow for changes
1. Read relevant modules before edits (`main.py`, `bot/`, `web/`, `shared/`).
2. Apply minimal edits with the same style and typing patterns.
3. Run `python main.py` only if you can supply real env values.
4. Document any missing tests or linting in PR/notes when applicable.
