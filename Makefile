SHELL := /usr/bin/env bash
COMPOSE := docker compose
SERVICE := api

.DEFAULT_GOAL := help

.PHONY: help up down build rebuild logs ps sh psql \
        migrate migration downgrade \
        test lint format typecheck \
        pdm-add pdm-add-dev pdm-remove pdm-lock pdm-install \
        bootstrap-files clean

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# ---------- lifecycle ----------

up: .env bootstrap-files ## Build (if needed) and start stack
	$(COMPOSE) up -d --build

bootstrap-files: ## Ensure files mounted into containers exist on host
	@touch pdm.lock alembic.ini
	@mkdir -p src tests migrations

down: ## Stop stack
	$(COMPOSE) down

build: ## Build images
	$(COMPOSE) build

rebuild: ## Rebuild images from scratch
	$(COMPOSE) build --no-cache

logs: ## Tail api logs
	$(COMPOSE) logs -f $(SERVICE)

ps: ## List running services
	$(COMPOSE) ps

# ---------- shells ----------

sh: ## Shell into api container
	$(COMPOSE) exec $(SERVICE) bash

psql: ## psql into db
	$(COMPOSE) exec db psql -U $${POSTGRES_USER:-parcel} -d $${POSTGRES_DB:-parcel}

# ---------- alembic ----------

migrate: ## Apply migrations
	$(COMPOSE) exec $(SERVICE) alembic upgrade head

migration: ## Generate migration: make migration m="msg"
	$(COMPOSE) exec $(SERVICE) alembic revision --autogenerate -m "$(m)"

downgrade: ## Roll back one migration
	$(COMPOSE) exec $(SERVICE) alembic downgrade -1

# ---------- quality ----------

test: ## Run pytest
	$(COMPOSE) exec $(SERVICE) pytest

lint: ## Lint (ruff + mypy)
	$(COMPOSE) exec $(SERVICE) ruff check src tests
	$(COMPOSE) exec $(SERVICE) mypy src

format: ## Format code
	$(COMPOSE) exec $(SERVICE) ruff format src tests
	$(COMPOSE) exec $(SERVICE) ruff check --fix src tests

typecheck: ## mypy only
	$(COMPOSE) exec $(SERVICE) mypy src

# ---------- pdm (deps inside container; lockfile written to host via mount) ----------

pdm-add: ## Add runtime dep: make pdm-add pkg=foo
	$(COMPOSE) exec $(SERVICE) pdm add $(pkg)

pdm-add-dev: ## Add dev dep: make pdm-add-dev pkg=foo
	$(COMPOSE) exec $(SERVICE) pdm add -dG dev $(pkg)

pdm-remove: ## Remove dep: make pdm-remove pkg=foo
	$(COMPOSE) exec $(SERVICE) pdm remove $(pkg)

pdm-lock: ## Refresh pdm.lock
	$(COMPOSE) exec $(SERVICE) pdm lock

pdm-install: ## pdm install inside container
	$(COMPOSE) exec $(SERVICE) pdm install

# ---------- helpers ----------

.env: ## Bootstrap .env from .env.example
	@if [ ! -f .env ]; then cp .env.example .env && echo "Created .env from .env.example"; fi

clean: ## Stop and remove volumes
	$(COMPOSE) down -v
