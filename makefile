.PHONY: all

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
	uv sync --frozen
	uv pip install -r requirements-dev.txt

lock:
	uv lock

console:

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
	uv run pytest --cov=src/production_control --cov-report=term --cov-report=xml  -m "not integration"
	@echo "Code quality checks completed."

server:
	@echo "Starting web server..."
	uv run python -m production_control.__web__

check-ci:
	@echo "Checking CI workflow..."
	./scripts/check_workflow.py ci.yml --watch

check-package:
	@echo "Checking package workflow..."
	./scripts/check_workflow.py package.yml --watch

check-workflows: check-ci check-package
