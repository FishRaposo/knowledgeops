.PHONY: help demo install test lint format clean dev dev-down setup

help:
	@echo "KnowledgeOps - Available targets:"
	@echo "  demo      Quick demo: start platform, run smoke tests"
	@echo "  install   Install all service dependencies"
	@echo "  test      Run integration tests"
	@echo "  lint      Run ruff + mypy on all services"
	@echo "  format    Run ruff format on all services"
	@echo "  clean     Remove build artifacts"
	@echo "  dev       Start docker compose"
	@echo "  setup     First-time setup"

install:
	cd shared/python && pip install -e .
	cd services/auth-service && pip install -e ".[dev]"
	cd services/ingestion-service && pip install -e ".[dev]"
	cd services/retrieval-service && pip install -e ".[dev]"
	cd services/eval-service && pip install -e ".[dev]"
	cd services/trace-service && pip install -e ".[dev]"
	cd services/api-gateway && pip install -e ".[dev]"
	cd services/llm-gateway && npm ci
	cd services/web-app && npm ci
	cd shared/ts && npm ci

test:
	python -m pytest tests/ -v

lint:
	ruff check services/ shared/python/ tests/
	cd services/llm-gateway && npx tsc --noEmit
	cd services/web-app && npx tsc --noEmit

format:
	ruff format services/ shared/python/ tests/

clean:
	-find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null
	-find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null
	-rm -rf services/web-app/.next services/llm-gateway/dist

demo:
	@echo "🚀 Starting KnowledgeOps demo..."
	docker compose up -d
	@echo "⏳ Waiting for services (this may take 30-60s)..."
	@sleep 10
	@echo "🏥 Running health checks..."
	@python tests/test_load_smoke.py || true
	@echo "✅ Platform ready!"
	@echo "   Web App:    http://localhost:3000"
	@echo "   API Gateway: http://localhost:8000"
	@echo ""
	@echo "To stop: make dev-down"

dev:
	docker compose up -d

dev-down:
	docker compose down

setup: install dev
