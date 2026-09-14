# CLAUDE.md

Internal CRM for itela, built module by module with TDD. Read `CONTEXT.md` for the domain language before touching the model.

## Language

All code, identifiers, comments, commit messages, issues and documentation are written in English. Conversation with the owner happens in Spanish.

## Stack

Settled on the wayfinder map (issue #1) — do not change these without new evidence:

Python 3.13 · FastAPI · SQLAlchemy 2.0 async with psycopg3 (`postgresql+psycopg://`) · PostgreSQL 17 · Alembic · uv.

Runtime dependencies are pinned to exact versions and `uv.lock` is committed. Frontend is Jinja2 with Bootstrap 5, Chart.js and HTMX, all vendored under `static/` — the demo network may have no outbound access.

## Commands

```
uv sync
uv run pytest
uv run ruff check . && uv run ruff format --check .
uv run mypy
uv run alembic upgrade head
uv run uvicorn crm.main:app --reload
docker compose up -d db db-test
```

## Module layout

Each feature module lives under `src/crm/<module>/` and repeats the same five files: `models.py`, `schemas.py` (`XCreate`, `XUpdate`, `XRead`), `service.py`, `router.py` (JSON under `/api/...`), `views.py` (HTML), plus a `templates/` directory.

Service functions take `AsyncSession` as their first argument and use it directly. There is no repository layer.

## Testing

Test first. Tests cover services, API endpoints and report calculations; every view gets one thin test asserting 200 and the expected content in the HTML. Chart rendering is checked by eye.

Tests run against a real PostgreSQL (the `db-test` service on port 55432), never SQLite — each test inside a transaction that rolls back.

## Workflow

Branch and PR per module, CI green before merge. Commits show the red→green cycle rather than collapsing a module into one commit.

Specs and decisions live in GitHub issues, not in files.
