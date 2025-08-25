.PHONY: all opc-server opc-monitor

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

opc-server:
	@echo "Starting programmatic OPC/UA server for potting lines..."
	uv run python scripts/opc_test_server.py

opc-monitor:
	@echo "Starting OPC/UA server monitor..."
	uv run python scripts/opc_monitor.py

# OPC UA development tools using asyncua built-ins
opc-discover:
	@echo "Discovering OPC/UA servers and endpoints..."
	uv run uadiscover

opc-browse:
	@echo "Browsing OPC/UA server nodes..."
	uv run uabrowse -u opc.tcp://127.0.0.1:4840

opc-browse-potting:
	@echo "Browsing potting lines structure..."
	uv run uabrowse -u opc.tcp://127.0.0.1:4840 -n "ns=2;s=PottingLines"

opc-read-line1-pc:
	@echo "Reading Line 1 PC active lot..."
	uv run uaread -u opc.tcp://127.0.0.1:4840 -n "ns=2;s=Lijn1_PC_nr_actieve_partij"

opc-read-line1-os:
	@echo "Reading Line 1 OS active pallet..."
	uv run uaread -u opc.tcp://127.0.0.1:4840 -n "ns=2;s=Lijn1_OS_partij_nr_actieve_pallet"

opc-read-line2-pc:
	@echo "Reading Line 2 PC active lot..."
	uv run uaread -u opc.tcp://127.0.0.1:4840 -n "ns=2;s=Lijn2_PC_nr_actieve_partij"

opc-read-line2-os:
	@echo "Reading Line 2 OS active pallet..."
	uv run uaread -u opc.tcp://127.0.0.1:4840 -n "ns=2;s=Lijn2_OS_partij_nr_actieve_pallet"

opc-write-line1-pc:
	@echo "Writing test value to Line 1 PC..."
	uv run uawrite -u opc.tcp://127.0.0.1:4840 -n "ns=2;s=Lijn1_PC_nr_actieve_partij" -t int32 12345

opc-write-line1-os:
	@echo "Writing test value to Line 1 OS..."
	uv run uawrite -u opc.tcp://127.0.0.1:4840 -n "ns=2;s=Lijn1_OS_partij_nr_actieve_pallet" -t int32 11111

opc-write-line2-pc:
	@echo "Writing test value to Line 2 PC..."
	uv run uawrite -u opc.tcp://127.0.0.1:4840 -n "ns=2;s=Lijn2_PC_nr_actieve_partij" -t int32 67890

opc-write-line2-os:
	@echo "Writing test value to Line 2 OS..."
	uv run uawrite -u opc.tcp://127.0.0.1:4840 -n "ns=2;s=Lijn2_OS_partij_nr_actieve_pallet" -t int32 22222

opc-subscribe-line1-pc:
	@echo "Subscribing to Line 1 PC changes..."
	uv run uasubscribe -u opc.tcp://127.0.0.1:4840 -n "ns=2;s=Lijn1_PC_nr_actieve_partij"

opc-subscribe-line2-pc:
	@echo "Subscribing to Line 2 PC changes..."
	uv run uasubscribe -u opc.tcp://127.0.0.1:4840 -n "ns=2;s=Lijn2_PC_nr_actieve_partij"

opc-client:
	@echo "Starting interactive OPC/UA client shell..."
	uv run uaclient -u opc.tcp://127.0.0.1:4840
