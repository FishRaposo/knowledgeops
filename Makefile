.PHONY: install dev test lint format typecheck docker-up docker-down demo worker clean help

SERVICES := api-gateway auth-service ingestion-service retrieval-service eval-service trace-service

install: ## Install shared-core, shared models, and all service dependencies
	pip install -e '../shared-core[docparse,embeddings]'
	pip install -e shared/python
	pip install -r requirements.txt

dev: ## Start the full stack via docker compose
	docker compose up -d

test: ## Run each Python service's unit tests
	@for svc in $(SERVICES); do \
		echo "== $$svc =="; \
		(cd services/$$svc && python -m pytest -q) || exit 1; \
	done

lint: ## Lint all Python services with ruff
	ruff check services shared/python

format: ## Format all Python code with ruff
	ruff format services shared/python

typecheck: ## Type-check each Python service with pyright
	@for svc in $(SERVICES); do \
		echo "== $$svc =="; \
		(cd services/$$svc && pyright app) || true; \
	done

docker-up: ## Start PostgreSQL + Redis + all services
	docker compose up -d

docker-down: ## Stop all containers
	docker compose down

demo: ## Run the platform demo (shared-core + pricing/tracing wiring)
	python examples/run_demo.py

worker: ## Start the ingestion arq worker
	cd services/ingestion-service && python arq_worker.py

clean: ## Remove caches and build artifacts
	python -c "import shutil, pathlib; [shutil.rmtree(p, ignore_errors=True) for p in pathlib.Path('.').rglob('__pycache__')]; [shutil.rmtree(p, ignore_errors=True) for p in pathlib.Path('.').rglob('.pytest_cache')]; shutil.rmtree('.ruff_cache', ignore_errors=True)"

help: ## Show this help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-15s\033[0m %s\n", $$1, $$2}'
