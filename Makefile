.PHONY: help qdrant-up backend-install backend-dev frontend-install frontend-dev up down test lint

help:  ## Show available commands
	@grep -E '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-16s\033[0m %s\n", $$1, $$2}'

qdrant-up:  ## Start local Qdrant (Docker)
	docker compose up -d qdrant

backend-install:  ## Install backend dependencies with uv
	cd backend && uv sync

backend-dev:  ## Run the FastAPI dev server on :8000
	cd backend && uv run uvicorn app.main:app --reload --port 8000

frontend-install:  ## Install frontend dependencies with npm
	cd frontend && npm install

frontend-dev:  ## Run the Next.js dev server on :3000
	cd frontend && npm run dev

up:  ## Run the full stack in containers (like Cloud Run) on :8080
	docker compose --profile app up -d --build

down:  ## Stop all containers
	docker compose --profile app down

test:  ## Run backend tests
	cd backend && uv run pytest

lint:  ## Lint and format-check backend
	cd backend && uv run ruff check . && uv run ruff format --check .
