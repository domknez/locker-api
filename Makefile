SHELL := /usr/bin/env bash
COMPOSE := docker compose
SERVICE := api

.DEFAULT_GOAL := help

.PHONY: help up down build rebuild logs ps sh psql \
        migrate migration downgrade \
        test lint format typecheck \
        pdm-add pdm-add-dev pdm-remove pdm-lock pdm-install \
        bootstrap-files ensure-up wait-api clean

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# ---------- lifecycle ----------

up: .env bootstrap-files ## Build (if needed) and start stack
	$(COMPOSE) up -d --build

bootstrap-files: ## Ensure files mounted into containers exist on host
	@touch pdm.lock alembic.ini
	@mkdir -p src tests migrations

ensure-up: .env bootstrap-files ## Start stack (idempotent) + wait + migrate
	@if [ -z "$$($(COMPOSE) ps -q $(SERVICE) 2>/dev/null)" ] || \
	   [ -z "$$(docker ps -q --no-trunc | grep -F "$$($(COMPOSE) ps -q $(SERVICE) 2>/dev/null)")" ]; then \
		echo ">> stack not running; starting…"; \
		$(COMPOSE) up -d --build; \
		$(MAKE) --no-print-directory wait-api; \
		$(COMPOSE) exec -T $(SERVICE) alembic upgrade head; \
	fi

wait-api: ## Block until api container accepts exec
	@printf ">> waiting for api"; \
	for i in $$(seq 1 60); do \
		if $(COMPOSE) exec -T $(SERVICE) true >/dev/null 2>&1; then echo " up."; exit 0; fi; \
		printf "."; sleep 1; \
	done; \
	echo " timeout."; exit 1

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

migrate: ensure-up ## Apply migrations
	$(COMPOSE) exec $(SERVICE) alembic upgrade head

migration: ensure-up ## Generate migration: make migration m="msg"
	$(COMPOSE) exec $(SERVICE) alembic revision --autogenerate -m "$(m)"

downgrade: ensure-up ## Roll back one migration
	$(COMPOSE) exec $(SERVICE) alembic downgrade -1

# ---------- quality ----------

test: ensure-up ## Run pytest (auto-starts stack + migrates if needed)
	$(COMPOSE) exec $(SERVICE) pytest

lint: ensure-up ## Lint (ruff + mypy)
	$(COMPOSE) exec $(SERVICE) ruff check src tests
	$(COMPOSE) exec $(SERVICE) mypy src

format: ensure-up ## Format code
	$(COMPOSE) exec $(SERVICE) ruff format src tests
	$(COMPOSE) exec $(SERVICE) ruff check --fix src tests

typecheck: ensure-up ## mypy only
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
