# Parcel Locker Service

Python REST API for parcel locker registration and parcel-to-slot assignment.

## Stack

- **FastAPI** + **SQLAlchemy 2.0 (async)** + **Alembic**
- **PostgreSQL 16 + PostGIS** (geographic queries)
- **PDM** (in-container dependency management)
- **Docker** + **docker compose** — no host Python install required
- **pytest** + **ruff** + **mypy**

## Run

Requirements: Docker (with `docker compose`).

```bash
cp .env.example .env       # adjust the bearer token + Nominatim UA contact
make up                    # build and start api + db
make migrate               # apply database migrations
```

API: <http://localhost:8000> — interactive docs: <http://localhost:8000/docs>

```bash
make logs                  # follow api logs
make down                  # stop
make clean                 # stop + remove db volume
```

## Development

The `src/` and `tests/` directories are bind-mounted into the api container; Uvicorn `--reload` reflects edits instantly.

```bash
make sh                    # shell into the api container
make test                  # run pytest
make lint                  # ruff + mypy
make format                # ruff format + autofix
make migration m="message" # autogenerate alembic revision
make pdm-add pkg=foo       # add runtime dep (lockfile written to host)
```

## API

| Method | Path                                | Auth | Description                              |
|--------|-------------------------------------|------|------------------------------------------|
| GET    | `/health`                           | —    | Liveness                                 |
| GET    | `/health/ready`                     | —    | Readiness (DB)                           |
| POST   | `/api/v1/lockers`                   | bearer | Create locker (geocoded via Nominatim) |
| GET    | `/api/v1/lockers`                   | —    | List lockers (paginated)                 |
| GET    | `/api/v1/lockers/{id}`              | —    | Fetch locker                             |
| GET    | `/api/v1/lockers/nearest?address=…` | —    | Nearest-N lockers by address             |
| PUT    | `/api/v1/lockers/{id}`              | bearer | Update locker                          |
| DELETE | `/api/v1/lockers/{id}`              | bearer | Delete locker                          |
| POST   | `/api/v1/parcels`                   | bearer | Create parcel and auto-assign slot     |
| GET    | `/api/v1/parcels`                   | —    | List parcels                             |
| GET    | `/api/v1/parcels/{id}`              | —    | Fetch parcel                             |
| POST   | `/api/v1/parcels/{id}/transition`   | bearer | Move parcel to a new state             |

Authentication: `Authorization: Bearer <API_BEARER_TOKEN>`.

### Parcel state machine

```
CREATED → ASSIGNED → IN_LOCKER → PICKED_UP
                  ↘ EXPIRED
        ↘ CANCELLED
```

Parcels are created in `ASSIGNED` after a fitting slot is acquired (`SELECT … FOR UPDATE SKIP LOCKED` to be concurrency-safe). Slot is released on `PICKED_UP`, `EXPIRED`, or `CANCELLED`.

### Timezones

API accepts ISO 8601 timestamps with offset (e.g., `2026-05-08T10:00:00+02:00`); naive timestamps are rejected with 422. Stored as `TIMESTAMPTZ` (UTC); responses are normalized to UTC (`Z` suffix).

## Architecture

```
src/parcel_locker/
├── api/            # routers (thin HTTP layer)
├── core/           # config, logging, security
├── domain/         # enums, exceptions (no I/O)
├── db/             # SQLAlchemy base, session, ORM models
├── repositories/   # data access
├── services/       # business logic, geocoding
└── schemas/        # pydantic request/response
```

Layering: `api → services → repositories → db`. Domain has no infrastructure deps. Schemas decouple ORM from public API.

## Notes

- **Geocoding**: Nominatim public endpoint requires a non-generic User-Agent with a real contact (the service rejects defaults). Configure via `NOMINATIM_USER_AGENT` in `.env`.
- **Submission window**: parcels expire `PARCEL_SUBMISSION_TTL_HOURS` after submission (default 48h).
- **Auth**: a single static bearer token is sufficient per the task spec ("minimal effort"). For production, swap to OAuth/JWT and per-user tokens.
- **PostGIS**: required for the `nearest` endpoint and the geography column on `lockers`.
