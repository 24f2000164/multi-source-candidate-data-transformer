.PHONY: install install-dev lint format typecheck test test-unit test-integration \
        coverage clean help

PYTHON  := python
PYTEST  := pytest
SRC_DIR := src
TEST_DIR := tests

# ---------------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------------

install:          ## Install production dependencies
	pip install -e .

install-dev:      ## Install all dependencies including dev tools
	pip install -e ".[dev]"
	pre-commit install

# ---------------------------------------------------------------------------
# Code Quality
# ---------------------------------------------------------------------------

lint:             ## Run Ruff linter
	ruff check $(SRC_DIR) $(TEST_DIR)

lint-fix:         ## Run Ruff linter with auto-fix
	ruff check --fix $(SRC_DIR) $(TEST_DIR)

format:           ## Format code with Black
	black $(SRC_DIR) $(TEST_DIR)

format-check:     ## Check formatting without making changes
	black --check $(SRC_DIR) $(TEST_DIR)

typecheck:        ## Run MyPy static type checking
	mypy $(SRC_DIR)

check: lint format-check typecheck  ## Run all checks (lint + format + typecheck)

# ---------------------------------------------------------------------------
# Testing
# ---------------------------------------------------------------------------

test:             ## Run all tests
	$(PYTEST)

test-unit:        ## Run unit tests only
	$(PYTEST) $(TEST_DIR)/unit -m unit

test-integration: ## Run integration tests only
	$(PYTEST) $(TEST_DIR)/integration -m integration

coverage:         ## Run tests with coverage report
	$(PYTEST) --cov=$(SRC_DIR)/transformer --cov-report=term-missing --cov-report=html

# ---------------------------------------------------------------------------
# Maintenance
# ---------------------------------------------------------------------------

clean:            ## Remove build artifacts and cache files
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .mypy_cache  -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .ruff_cache  -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name htmlcov     -exec rm -rf {} + 2>/dev/null || true
	find . -name ".coverage" -delete 2>/dev/null || true

help:             ## Show this help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'
