# Parcel Locker Service

Python REST API for parcel locker registration and parcel-to-slot assignment.

## Stack

- **FastAPI** + **SQLAlchemy 2.0 (async)** + **Alembic**
- **PostgreSQL 16 + PostGIS**
- **PDM** (in-container dependency management)
- **Docker** + **docker compose**

## Run

Requires Docker. No local Python install needed.

```bash
make up        # build + start api & db
make migrate   # apply migrations
make logs      # follow api logs
make down      # stop
```

API: http://localhost:8000 — Docs: http://localhost:8000/docs

## Development

Source is mounted into the container; `uvicorn --reload` reflects changes instantly.

```bash
make sh                  # shell into api container
make test                # run pytest
make lint                # ruff + mypy
make pdm-add pkg=foo     # add dependency (lockfile written to host)
```

See `plan.md` for architecture and phased delivery.
