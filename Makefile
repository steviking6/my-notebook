.PHONY: help qdrant-up qdrant-down backend-install backend-dev test lint

help:  ## Show available commands
	@grep -E '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-16s\033[0m %s\n", $$1, $$2}'

qdrant-up:  ## Start local Qdrant (Docker)
	docker compose up -d qdrant

qdrant-down:  ## Stop local Qdrant
	docker compose down

backend-install:  ## Install backend dependencies with uv
	cd backend && uv sync

backend-dev:  ## Run the FastAPI dev server on :8000
	cd backend && uv run uvicorn app.main:app --reload --port 8000

test:  ## Run backend tests
	cd backend && uv run pytest

lint:  ## Lint and format-check backend
	cd backend && uv run ruff check . && uv run ruff format --check .
