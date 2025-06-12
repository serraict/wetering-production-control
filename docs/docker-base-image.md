# Docker Base Image Strategy

This document explains the Docker base image strategy implemented to reduce download times and improve build efficiency.

## Problem

The original Dockerfile required downloading and installing system dependencies (apt packages, WeasyPrint dependencies, etc.) every time a new application image was built. This resulted in:

- Large download times for each build
- Repeated `apt-get update` operations creating unnecessary layers
- Inefficient Docker layer caching

## Solution

We've implemented a base image strategy that separates common system dependencies from application-specific code:

### Base Image (`Dockerfile.base`)

Contains all common dependencies:

- Python 3.12 slim runtime
- System packages (WeasyPrint dependencies, build tools, runtime tools)
- Common Python tools (uv, setuptools_scm)
- Optimized with proper cleanup to minimize size

### Application Image (`Dockerfile`)

Now only contains:

- Application-specific Python dependencies
- Application source code
- Application configuration

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

1. **Reduced Download Time**: System dependencies downloaded once and reused
2. **Faster Builds**: Only application layers rebuild when code changes
3. **Better Caching**: More effective Docker layer caching
4. **Consistent Environment**: All applications use same base dependencies

## Maintenance

### When to Rebuild Base Image

Rebuild when:
- System dependencies change
- Python version updates
- Security updates needed
- WeasyPrint or other system library updates

### Workflow

1. Update `Dockerfile.base` with new dependencies
2. Run `make docker_base` to build locally
3. Test with `make docker_image` 
4. Push with `make docker_push_base` when ready

The base image should be rebuilt infrequently (monthly or when dependencies change), while application images can be built frequently as code changes.
