.PHONY: install dev run run-ui clean build test lint

PYTHON := .venv/Scripts/python
PIP := .venv/Scripts/pip
UVICORN := .venv/Scripts/uvicorn
STREAMLIT := .venv/Scripts/streamlit

install:
	@echo "==> Setting up Python virtual environment..."
	python -m venv .venv
	$(PIP) install --upgrade pip
	$(PIP) install -e ".[dev]"

dev:
	$(UVICORN) src.api.main:app --reload --host 0.0.0.0 --port 8000

run:
	$(UVICORN) src.api.main:app --host 0.0.0.0 --port 8000 --workers 2

run-ui:
	$(STREAMLIT) run src/ui/streamlit_app.py --server.port 8501

build:
	docker-compose build

clean:
	@echo "==> Cleaning build artifacts..."
	rm -rf build dist *.egg-info .pytest_cache .mypy_cache htmlcov .coverage
	rm -rf data/uploads/* data/logs/*
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true

test:
	$(PYTHON) -m pytest tests/ -v

lint:
	$(PYTHON) -m ruff check src/

security:
	$(PYTHON) -m bandit -r src/ -ll
	$(PYTHON) -m safety check

all: clean install lint test
