# DataAgent

Natural-language data analyst over Postgres (Neon) built with LangGraph + LangChain-OpenAI.

## Layout

- `feed_db.py` — creates `users, vehicles, rides, payments, ratings` tables and loads `data/*.csv` via `COPY`.
- `Models/schema.py` — `AgentSchema`, `JudgeSchema`, `ETLAgentSchema` pydantic state.
- `utils/llm_pick.py` — `pick_llm(low|medium|high)` router.
- `utils/database.py` — `DatabaseUtil` for schema introspection (`schema_details`) and `execute_sql`.
- `utils/etl_tools.py` — `ETLTools.extract_load` (API JSON → csv/json in `data/extract`).
- `agents/sql_analyst.py` — SQL analyst graph: `curate → context → generate → judge (safe?) → execute → answer`.

## Quickstart

```bash
uv sync
# set DATABASE_URL in .env (Neon Postgres)
uv run feed_db.py
uv run agents/sql_analyst.py
```

Requires Python >=3.14. `data/`, `.env`, `.venv/` are git-ignored.
