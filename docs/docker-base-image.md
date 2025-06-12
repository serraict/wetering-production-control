# Docker Base Image Strategy

This document explains the Docker base image strategy implemented to optimize deployment times by moving Python dependencies to the base image.

## Problem

The application layer was 404MB, causing slow deployments over slow connections:

- **Goal**: Deploy code changes in <1 minute
- **Current**: Every deployment downloads 404MB of Python dependencies
- **Root cause**: Python dependencies installed in app layer, not base layer

### Analysis Results

- **Base image**: 661MB (system deps + Python runtime)
- **Full image**: 1.07GB 
- **App layer**: 404MB (entirely from `.venv` directory with Python packages)

## Solution: Move Python Dependencies to Base Image

We've implemented an optimized base image strategy that separates Python dependencies from application code:

### Base Image (`Dockerfile.base`)

Contains all dependencies needed for the application:

- Python 3.12 slim runtime
- System packages (WeasyPrint dependencies, build tools, runtime tools)
- Common Python tools (uv, setuptools_scm)
- **All production Python dependencies** from `pyproject.toml`
- Pre-built virtual environment at `/app/.venv`
- Optimized with proper cleanup to minimize size

### Application Image (`Dockerfile`)

Uses a multi-stage build approach to minimize the final app layer:

#### Build Stage
- Starts from the base image (with all dependencies pre-installed)
- Copies the entire source including `.git` (needed for setuptools_scm)
- Installs only the application package using `uv pip install . --no-deps`
- Dependencies are already available from the base image

#### App Stage  
- Starts fresh from the base image
- Copies the installed package from the build stage
- Copies only essential runtime files:
  - `docker-entrypoint.sh`
  - `src/production_control/assets/`
  - Other runtime-only files as needed

**Final app layer contains only**:
- Application source code (installed package)
- Runtime configuration files  
- Essential assets

**Does NOT contain**: Python dependencies (these are in the base image)

This approach ensures that build artifacts and unnecessary files don't bloat the final image.

## Usage

### Building the Base Image

#### Local Development

```bash
# Build the base image
make docker_base

# Build and push the base image
make docker_push_base
```

#### Production (GitHub Actions)

The base image can be built and pushed using GitHub Actions:

1. Go to the repository's Actions tab
2. Select "Package Base Image" workflow
3. Click "Run workflow"
4. Specify the tag (default: "latest")
5. Click "Run workflow"

This will build and push the base image to `ghcr.io/serraict/wetering-production-control-base:TAG`

### Building Applications

The existing workflow remains the same:

```bash
# Build application image (now uses base image)
make docker_image

# Push application image
make docker_push

# Build and push both base and application
make docker_push_all
```

## Benefits

1. **Dramatically Reduced App Layer**: From 404MB to ~5-10MB
2. **Fast Code Deployments**: <1 minute deployment time for code changes
3. **Better Caching**: Python dependencies downloaded once and reused
4. **Faster Builds**: Only small application layer rebuilds when code changes
5. **Consistent Environment**: All applications use same base dependencies

### Expected Results

- **Base image**: ~1GB (from 661MB) - downloaded once
- **App layer**: ~5-10MB (from 404MB) - fast deployments
- **Code changes**: <1 minute deployment time
- **Dependency changes**: Require base image rebuild (infrequent)

## Maintenance

### When to Rebuild Base Image vs App Image

#### Rebuild Base Image When:
- **Python dependencies change** (pyproject.toml modifications)
- System dependencies change
- Python version updates
- Security updates needed
- WeasyPrint or other system library updates

#### Rebuild App Image When:
- **Source code changes** (most common)
- Configuration file changes
- Asset updates
- Runtime script modifications

### Workflow for Different Change Types

#### Code Changes (Most Common)
```bash
# Only rebuild app image - fast!
make docker_image
make docker_push
```

#### Dependency Changes (Less Common)
```bash
# First rebuild base image
make docker_base
make docker_push_base

# Then rebuild app image
make docker_image
make docker_push
```

#### Complete Rebuild
```bash
# Build and push everything
make docker_push_all
```

### Frequency Guidelines

- **Base image**: Rebuild infrequently (when dependencies change, monthly for security updates)
- **App image**: Rebuild frequently (every code change, multiple times per day)

This separation ensures that the heavy Python dependencies are downloaded once, while code changes deploy quickly with minimal data transfer.

## Lock File Support

The project now includes uv lock file support for deterministic dependency management:

### Lock File Generation

```bash
# Generate/update the lock file
make lock
```

### Automated Base Image Rebuilds

The base image will automatically rebuild when:
- `uv.lock` file changes (dependency updates)
- `pyproject.toml` changes (new dependencies)
- `Dockerfile.base` changes (base image modifications)

This automation is handled by the GitHub Actions workflow, which monitors these files and triggers base image rebuilds automatically when changes are pushed to the main branch.

### Benefits of Lock File Support

1. **Deterministic Builds**: Exact dependency versions locked across environments
2. **Automated Rebuilds**: Base image automatically updates when dependencies change
3. **Version Control**: Lock file changes are tracked in git
4. **Consistency**: Same dependency versions in development and production
