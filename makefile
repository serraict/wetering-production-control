.PHONY: all opc-server opc-monitor next-work-item

VERSION := $(shell git describe --tags 2>/dev/null || echo "")
ifeq ($(strip $(VERSION)),)
VERSION := v0.0.1
endif

NEW_VERSION := $(shell python -m setuptools_scm --strip-dev 2>/dev/null || echo "")
ifeq ($(strip $(NEW_VERSION)),)
NEW_VERSION := 0.0.1
endif

bootstrap:
	uv venv
	@echo "Run 'source .venv/bin/activate' to activate the virtual environment followed by 'make update' to install dependencies."

update:
	uv sync --frozen --extra dev

lock:
	uv lock

console: server

format-python:
	uv run black src tests scripts

format-markdown:
	mdformat .

format: format-python format-markdown

test:
	uv run pytest --cov=src/production_control --cov-report=term -m "not integration"

test-integration:
	uv run pytest --cov=src/production_control --cov-report=term

coverage:
	uv run pytest --cov=src/production_control --cov-report=term --cov-report=html

build:
	# NOTE: Use system python, not 'uv run python'
	# python -m build creates its own isolated environment and manages dependencies
	python -m build

printversion:
	@python -m setuptools_scm

releasable:
	@if [ -n "$$(git status --porcelain)" ]; then \
		echo "There are uncommitted changes or untracked files"; \
		exit 1; \
	fi
	@if [ "$$(git rev-parse --abbrev-ref HEAD)" != "main" ]; then \
		echo "Not on main branch"; \
		exit 1; \
	fi
	@if [ "$$(git rev-parse HEAD)" != "$$(git rev-parse origin/main)" ]; then \
		echo "Local branch is ahead of origin"; \
		exit 1; \
	fi

release: releasable
	sed -i '' "s/\[Unreleased\]/[$(NEW_VERSION)] - $$(date +%Y-%m-%d)/" CHANGELOG.md
	if [ -n "$$(git status --porcelain CHANGELOG.md)" ]; then \
		git add CHANGELOG.md && \
		git commit -m "Update CHANGELOG.md for version $(NEW_VERSION)"; \
	fi
	git tag v$(NEW_VERSION) && \
	git push origin main --tags

docker_base:
	docker build -f Dockerfile.base -t ghcr.io/serraict/wetering-production-control-base:latest .

docker_image:
	docker build --target app \
		--build-arg VERSION=$(subst v,,$(VERSION)) \
		-t ghcr.io/serraict/wetering-production-control:$(VERSION) \
		-t ghcr.io/serraict/wetering-production-control:latest \
		.

docker_push_base: docker_base
	docker push ghcr.io/serraict/wetering-production-control-base:latest

docker_push: docker_image
	docker push ghcr.io/serraict/wetering-production-control:$(VERSION)
	docker push ghcr.io/serraict/wetering-production-control:latest

docker_push_all: docker_push_base docker_push

docker_compose_debug:
	docker compose up --build

quality:
	@echo "Running code quality checks..."
	uv run flake8 src tests
	uv run black --check src tests
	@echo "Running tests with coverage..."
	uv run pytest -q --cov=src/production_control --cov-report=xml -m "not integration"
	@echo "Running OS↔PC protocol behave suite..."
	uv run behave --format progress --logging-level WARNING features/protocol
	@echo "Code quality checks completed."

quality-verbose:
	@echo "Running code quality checks (verbose)..."
	uv run flake8 src tests
	uv run black --check src tests
	@echo "Running tests with coverage..."
	uv run pytest --cov=src/production_control --cov-report=term --cov-report=xml -m "not integration"
	@echo "Running OS↔PC protocol behave suite..."
	uv run behave features/protocol
	@echo "Code quality checks completed."

server:
	@echo "Starting web server..."
	uv run python -m production_control.__web__

bot:
	@echo "Starting bot console..."
	uv run python -m production_control.bot.console

bot-console: bot

bot-server:
	uv run uvicorn production_control.bot.server:app --host 0.0.0.0 --port 7902 --reload

bot-prompt:
	uv run python -m production_control.bot.print_prompt

check-ci:
	@echo "Checking CI workflow..."
	uv run python scripts/check_workflow.py CI --watch

check-package:
	@echo "Checking package workflow..."
	uv run python scripts/check_workflow.py package.yml --watch

check-workflows: check-ci check-package

dev-server:
	@echo "Starting web server..."
	python -m production_control.__web__

dev-test:
	pytest --cov=src/production_control --cov-report=term -m "not integration"

dev-test-integration:
	pytest --cov=src/production_control --cov-report=term

behave:
	@echo "Running OS↔PC protocol behave suite (features/protocol)..."
	uv run behave features/protocol

opc-server:
	@echo "Starting programmatic OPC/UA server for potting lines..."
	uv run python scripts/opc/test_server.py

opc-monitor:
	@echo "Starting OPC/UA TUI monitor..."
	uv run python -m production_control.opcua.tui

opc-protocol:
	@echo "Starting OS↔PC protocol handler..."
	uv run python -m production_control.opcua.protocol

test-qr-codes:
	@echo "Generating test QR codes PDF..."
	uv run python scripts/generate_test_qr_codes.py ./test_qr_codes.pdf

next-work-item:
	cp work/templates/doing.md work/doing.md
