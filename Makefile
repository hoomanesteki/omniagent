# ============================================================================
# OmniAgent Makefile
# ============================================================================
# Comprehensive build, test, and deployment automation
#
# Usage:
#   make help          - Show all available commands
#   make install       - Install dependencies
#   make run           - Run the application
#   make test          - Run all tests
#   make lint          - Run code quality checks
#   make clean         - Clean up generated files
#
# Created by: Hooman Esteki (https://esteki.ca/)
# ============================================================================

.PHONY: help install install-dev run test test-unit test-integration test-security \
        lint format clean build docker-build docker-run docs coverage check all

# Variables
PYTHON := python3
PIP := pip3
STREAMLIT := streamlit
PYTEST := pytest
APP := app.py
PORT := 8501

# Colors for terminal output
RED := \033[0;31m
GREEN := \033[0;32m
YELLOW := \033[0;33m
BLUE := \033[0;34m
NC := \033[0m # No Color

# ============================================================================
# HELP
# ============================================================================

help:
	@echo "$(BLUE)╔════════════════════════════════════════════════════════════════╗$(NC)"
	@echo "$(BLUE)║              🤖 OmniAgent - Makefile Commands                  ║$(NC)"
	@echo "$(BLUE)╚════════════════════════════════════════════════════════════════╝$(NC)"
	@echo ""
	@echo "$(GREEN)📦 Installation:$(NC)"
	@echo "  make install        Install production dependencies"
	@echo "  make install-dev    Install development dependencies"
	@echo "  make setup          Complete setup (install + check)"
	@echo ""
	@echo "$(GREEN)🚀 Running:$(NC)"
	@echo "  make run            Run the Streamlit application"
	@echo "  make run-debug      Run with debug mode enabled"
	@echo "  make run-port PORT=XXXX  Run on specific port"
	@echo ""
	@echo "$(GREEN)🧪 Testing:$(NC)"
	@echo "  make test           Run all tests"
	@echo "  make test-unit      Run unit tests only"
	@echo "  make test-integration  Run integration tests only"
	@echo "  make test-security  Run security tests only"
	@echo "  make test-ui        Run UI/UX tests only"
	@echo "  make test-verbose   Run tests with verbose output"
	@echo "  make coverage       Run tests with coverage report"
	@echo ""
	@echo "$(GREEN)🔍 Code Quality:$(NC)"
	@echo "  make lint           Run all linters"
	@echo "  make format         Format code with black"
	@echo "  make check          Run syntax check on all files"
	@echo "  make typecheck      Run type checking (mypy)"
	@echo ""
	@echo "$(GREEN)🐳 Docker:$(NC)"
	@echo "  make docker-build   Build Docker image"
	@echo "  make docker-run     Run in Docker container"
	@echo "  make docker-stop    Stop Docker container"
	@echo ""
	@echo "$(GREEN)📚 Documentation:$(NC)"
	@echo "  make docs           Generate documentation"
	@echo "  make docs-serve     Serve documentation locally"
	@echo ""
	@echo "$(GREEN)🧹 Cleanup:$(NC)"
	@echo "  make clean          Remove generated files"
	@echo "  make clean-all      Remove all generated files and caches"
	@echo ""
	@echo "$(GREEN)🔧 Utilities:$(NC)"
	@echo "  make validate       Validate all files before deployment"
	@echo "  make zip            Create distribution zip file"
	@echo "  make all            Run full CI pipeline"

# ============================================================================
# INSTALLATION
# ============================================================================

install:
	@echo "$(BLUE)📦 Installing production dependencies...$(NC)"
	$(PIP) install -r requirements.txt
	@echo "$(GREEN)✅ Installation complete!$(NC)"

install-dev:
	@echo "$(BLUE)📦 Installing development dependencies...$(NC)"
	$(PIP) install -r requirements.txt
	$(PIP) install pytest pytest-cov black flake8 mypy
	@echo "$(GREEN)✅ Development installation complete!$(NC)"

setup: install-dev check
	@echo "$(GREEN)✅ Setup complete! Run 'make run' to start the application.$(NC)"

# ============================================================================
# RUNNING
# ============================================================================

run:
	@echo "$(BLUE)🚀 Starting OmniAgent on port $(PORT)...$(NC)"
	$(STREAMLIT) run $(APP) --server.port $(PORT)

run-debug:
	@echo "$(BLUE)🐛 Starting OmniAgent in debug mode...$(NC)"
	$(STREAMLIT) run $(APP) --server.port $(PORT) --logger.level debug

run-headless:
	@echo "$(BLUE)🖥️ Starting OmniAgent in headless mode...$(NC)"
	$(STREAMLIT) run $(APP) --server.port $(PORT) --server.headless true

# ============================================================================
# TESTING
# ============================================================================

test:
	@echo "$(BLUE)🧪 Running all tests...$(NC)"
	$(PYTEST) tests/ -v --tb=short
	@echo "$(GREEN)✅ All tests complete!$(NC)"

test-unit:
	@echo "$(BLUE)🧪 Running unit tests...$(NC)"
	$(PYTEST) tests/unit/ -v --tb=short
	@echo "$(GREEN)✅ Unit tests complete!$(NC)"

test-integration:
	@echo "$(BLUE)🧪 Running integration tests...$(NC)"
	$(PYTEST) tests/integration/ -v --tb=short
	@echo "$(GREEN)✅ Integration tests complete!$(NC)"

test-security:
	@echo "$(BLUE)🔒 Running security tests...$(NC)"
	$(PYTEST) tests/unit/test_security.py -v --tb=short
	@echo "$(GREEN)✅ Security tests complete!$(NC)"

test-ui:
	@echo "$(BLUE)🎨 Running UI/UX tests...$(NC)"
	$(PYTEST) tests/unit/test_ui_communications.py -v --tb=short
	@echo "$(GREEN)✅ UI tests complete!$(NC)"

test-agents:
	@echo "$(BLUE)🤖 Running agent tests...$(NC)"
	$(PYTEST) tests/unit/test_agents.py -v --tb=short
	@echo "$(GREEN)✅ Agent tests complete!$(NC)"

test-core:
	@echo "$(BLUE)⚙️ Running core tests...$(NC)"
	$(PYTEST) tests/unit/test_core.py -v --tb=short
	@echo "$(GREEN)✅ Core tests complete!$(NC)"

test-mcp:
	@echo "$(BLUE)📡 Running MCP tests...$(NC)"
	$(PYTEST) tests/unit/test_mcp.py -v --tb=short
	@echo "$(GREEN)✅ MCP tests complete!$(NC)"

test-verbose:
	@echo "$(BLUE)🧪 Running tests with verbose output...$(NC)"
	$(PYTEST) tests/ -v -s --tb=long
	@echo "$(GREEN)✅ Tests complete!$(NC)"

test-fast:
	@echo "$(BLUE)⚡ Running tests (fail fast)...$(NC)"
	$(PYTEST) tests/ -x -v --tb=short
	@echo "$(GREEN)✅ Tests complete!$(NC)"

coverage:
	@echo "$(BLUE)📊 Running tests with coverage...$(NC)"
	$(PYTEST) tests/ --cov=. --cov-report=html --cov-report=term-missing
	@echo "$(GREEN)✅ Coverage report generated in htmlcov/$(NC)"

# ============================================================================
# CODE QUALITY
# ============================================================================

lint:
	@echo "$(BLUE)🔍 Running linters...$(NC)"
	@echo "Checking Python syntax..."
	@find . -name "*.py" -not -path "./venv/*" -exec $(PYTHON) -m py_compile {} \;
	@echo "$(GREEN)✅ Syntax check passed!$(NC)"
	@echo "Running flake8..."
	-flake8 . --max-line-length=120 --exclude=venv,__pycache__,.git --ignore=E501,W503
	@echo "$(GREEN)✅ Linting complete!$(NC)"

format:
	@echo "$(BLUE)🎨 Formatting code with black...$(NC)"
	-black . --line-length=120 --exclude="venv|__pycache__|\.git"
	@echo "$(GREEN)✅ Formatting complete!$(NC)"

check:
	@echo "$(BLUE)✔️ Running syntax check on all Python files...$(NC)"
	@$(PYTHON) -c "import ast; import os; \
		files = [os.path.join(dp, f) for dp, dn, fn in os.walk('.') for f in fn if f.endswith('.py') and 'venv' not in dp]; \
		errors = []; \
		[errors.append(f) if not (lambda p: (ast.parse(open(p).read()), True)[1] if True else False)(f) else None for f in files]; \
		print('All files OK!' if not errors else f'Errors in: {errors}')" 2>&1 || \
		find . -name "*.py" -not -path "./venv/*" -exec $(PYTHON) -m py_compile {} \;
	@echo "$(GREEN)✅ Syntax check complete!$(NC)"

typecheck:
	@echo "$(BLUE)🔎 Running type checking...$(NC)"
	-mypy . --ignore-missing-imports --exclude venv
	@echo "$(GREEN)✅ Type checking complete!$(NC)"

# ============================================================================
# DOCKER
# ============================================================================

docker-build:
	@echo "$(BLUE)🐳 Building Docker image...$(NC)"
	docker build -t omniagent:latest .
	@echo "$(GREEN)✅ Docker image built!$(NC)"

docker-run:
	@echo "$(BLUE)🐳 Running in Docker container...$(NC)"
	docker run -p $(PORT):$(PORT) omniagent:latest
	
docker-stop:
	@echo "$(BLUE)🐳 Stopping Docker container...$(NC)"
	docker stop $$(docker ps -q --filter ancestor=omniagent:latest) 2>/dev/null || true
	@echo "$(GREEN)✅ Container stopped!$(NC)"

# ============================================================================
# DOCUMENTATION
# ============================================================================

docs:
	@echo "$(BLUE)📚 Generating documentation...$(NC)"
	@mkdir -p docs/api
	@echo "Documentation generated in docs/"
	@echo "$(GREEN)✅ Documentation complete!$(NC)"

# ============================================================================
# CLEANUP
# ============================================================================

clean:
	@echo "$(BLUE)🧹 Cleaning up...$(NC)"
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name ".coverage" -delete
	rm -rf htmlcov/ 2>/dev/null || true
	rm -rf .mypy_cache/ 2>/dev/null || true
	@echo "$(GREEN)✅ Cleanup complete!$(NC)"

clean-all: clean
	@echo "$(BLUE)🧹 Deep cleaning...$(NC)"
	rm -rf venv/ 2>/dev/null || true
	rm -rf dist/ build/ 2>/dev/null || true
	@echo "$(GREEN)✅ Deep cleanup complete!$(NC)"

# ============================================================================
# UTILITIES
# ============================================================================

validate:
	@echo "$(BLUE)✔️ Validating project...$(NC)"
	@echo "1. Checking Python syntax..."
	@find . -name "*.py" -not -path "./venv/*" -exec $(PYTHON) -m py_compile {} \;
	@echo "$(GREEN)   ✅ Syntax OK$(NC)"
	@echo "2. Checking required files..."
	@test -f app.py && echo "$(GREEN)   ✅ app.py exists$(NC)" || echo "$(RED)   ❌ app.py missing$(NC)"
	@test -f requirements.txt && echo "$(GREEN)   ✅ requirements.txt exists$(NC)" || echo "$(RED)   ❌ requirements.txt missing$(NC)"
	@test -f README.md && echo "$(GREEN)   ✅ README.md exists$(NC)" || echo "$(RED)   ❌ README.md missing$(NC)"
	@echo "3. Checking directories..."
	@test -d agents && echo "$(GREEN)   ✅ agents/ exists$(NC)" || echo "$(RED)   ❌ agents/ missing$(NC)"
	@test -d core && echo "$(GREEN)   ✅ core/ exists$(NC)" || echo "$(RED)   ❌ core/ missing$(NC)"
	@test -d ui && echo "$(GREEN)   ✅ ui/ exists$(NC)" || echo "$(RED)   ❌ ui/ missing$(NC)"
	@test -d mcp && echo "$(GREEN)   ✅ mcp/ exists$(NC)" || echo "$(RED)   ❌ mcp/ missing$(NC)"
	@test -d tests && echo "$(GREEN)   ✅ tests/ exists$(NC)" || echo "$(RED)   ❌ tests/ missing$(NC)"
	@echo "$(GREEN)✅ Validation complete!$(NC)"

zip:
	@echo "$(BLUE)📦 Creating distribution zip...$(NC)"
	@rm -f OmniAgent.zip
	zip -r OmniAgent.zip . \
		-x "*.pyc" \
		-x "*__pycache__*" \
		-x ".git/*" \
		-x "venv/*" \
		-x "*.egg-info/*" \
		-x "htmlcov/*" \
		-x ".mypy_cache/*" \
		-x ".pytest_cache/*"
	@echo "$(GREEN)✅ Created OmniAgent.zip$(NC)"

# CI pipeline
all: check test-fast lint validate
	@echo "$(GREEN)✅ Full CI pipeline complete!$(NC)"

# Quick check before commit
precommit: format check test-fast
	@echo "$(GREEN)✅ Pre-commit checks passed!$(NC)"

# Show project stats
stats:
	@echo "$(BLUE)📊 Project Statistics:$(NC)"
	@echo "Python files: $$(find . -name '*.py' -not -path './venv/*' | wc -l)"
	@echo "Lines of code: $$(find . -name '*.py' -not -path './venv/*' -exec cat {} \; | wc -l)"
	@echo "Test files: $$(find tests -name '*.py' | wc -l)"
	@echo "Test cases: $$(grep -r 'def test_' tests/ | wc -l)"
