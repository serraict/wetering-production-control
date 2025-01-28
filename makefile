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
	python -m venv venv
	@echo "Run 'source venv/bin/activate' to activate the virtual environment followed by 'make update' to install dependencies."

update:
	python -m pip install --upgrade pip build
	python -m pip install -r requirements-dev.txt
	pip install -e .

console:

format-python:
	black src tests scripts

format-markdown:
	mdformat .

format: format-python format-markdown

test:
	pytest --cov=src/production_control --cov-report=term -m "not integration"

test-integration:
	pytest --cov=src/production_control --cov-report=term -m "integration"

coverage:
	pytest --cov=src/production_control --cov-report=term --cov-report=html

build:
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

docker_image:
	docker build -t ghcr.io/serraict/production_control:$(VERSION) .

docker_push: docker_image
	docker push ghcr.io/serraict/production_control:$(VERSION)

docker_compose_debug:
	docker compose up --build

quality:
	@echo "Running code quality checks..."
	flake8 src tests
	black --check src tests
	@echo "Running tests with coverage..."
	pytest --cov=src/production_control --cov-report=term --cov-report=xml  -m "not integration"
	@echo "Code quality checks completed."

server:
	@echo "Starting web server..."
	python -m production_control.__web__

check-ci:
	@echo "Checking CI workflow..."
	./scripts/check_workflow.py ci.yml --watch

check-package:
	@echo "Checking package workflow..."
	./scripts/check_workflow.py package.yml --watch

check-workflows: check-ci check-package
