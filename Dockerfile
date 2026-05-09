ARG PYTHON_VERSION=3.12
ARG PDM_VERSION=2.22.4

# ---------- base ----------
FROM python:${PYTHON_VERSION}-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PDM_CHECK_UPDATE=0

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        curl \
        libpq-dev \
    && rm -rf /var/lib/apt/lists/*

ARG PDM_VERSION
RUN pip install --no-cache-dir "pdm==${PDM_VERSION}" "hishel<0.1.0"

WORKDIR /app

RUN pdm config python.use_venv true \
    && pdm config venv.in_project true \
    && pdm config venv.with_pip true \
    && pdm config check_update false

# ---------- deps ----------
FROM base AS deps

# Copy only dependency manifests for cacheable install layer.
COPY pyproject.toml ./
COPY pdm.lock* ./

# If lock missing/empty, generate; then install dev deps into .venv.
RUN if [ ! -s pdm.lock ]; then pdm lock; fi \
    && pdm install --dev --no-self

# ---------- dev ----------
FROM base AS dev

COPY --from=deps /app/.venv /app/.venv
ENV PATH="/app/.venv/bin:${PATH}" \
    VIRTUAL_ENV=/app/.venv \
    PYTHONPATH=/app/src

EXPOSE 8000

CMD ["uvicorn", "parcel_locker.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload", "--reload-dir", "/app/src"]
