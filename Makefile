# Git-AI Development Makefile

.PHONY: help install test lint format clean build

help: ## Show this help message
	@echo "Git-AI Development Commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-15s %s\n", $$1, $$2}'

install: ## Install the package in development mode
	pip install -e ".[dev]"

test: ## Run the test suite
	pytest tests/ -v

test-cov: ## Run tests with coverage
	pytest tests/ --cov=gitai --cov-report=html

lint: ## Run linting
	ruff check gitai tests
	mypy gitai

format: ## Format code
	ruff format gitai tests
	ruff check gitai tests --fix

check: lint test ## Run linting and tests

clean: ## Clean up build artifacts
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf .coverage
	rm -rf htmlcov/
	rm -rf .pytest_cache/
	rm -rf gitai/__pycache__/
	rm -rf tests/__pycache__/

build: ## Build the package
	python -m build

install-build: build ## Build and install the package
	pip install dist/*.whl

run: ## Run the CLI
	python -m gitai.cli

help-dev: ## Show development help
	@echo "Development Workflow:"
	@echo "1. make install    # Install in development mode"
	@echo "2. make test       # Run tests"
	@echo "3. make lint       # Check code quality"
	@echo "4. make format     # Format code"
	@echo "5. make build      # Build package"
	@echo "6. make clean      # Clean build artifacts"
