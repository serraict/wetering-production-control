# Docker Build Optimization Guide

This guide explains how to leverage the multi-stage Dockerfile for faster builds and deployments.

## Understanding the Multi-stage Dockerfile

The Dockerfile has been restructured with three stages:

1. **Base**: Contains system dependencies
2. **Dependencies**: Installs Python packages
3. **Final**: Combines base, dependencies, and application code

This structure allows for better layer caching and faster builds when only Python code changes.

## Version Handling

The Dockerfile now accepts a `VERSION` build argument that is passed to setuptools_scm via the `SETUPTOOLS_SCM_PRETEND_VERSION` environment variable. This ensures proper versioning even without the .git directory in the Docker build context.

The GitHub Actions workflow has been updated to:
1. Extract the version from the git tag
2. Pass it as a build argument to Docker

## Development Workflow

For local development, you can continue using the existing docker-compose.yml:

```bash
# Build with the optimized Dockerfile (specify version for local development)
docker compose build --build-arg VERSION=0.1.0-dev

# Run the application
docker compose up
```

## Production Deployment Optimization

To optimize production deployments with `docker compose pull`, follow these steps:

### 1. Build and Push the Dependencies Image

Build and tag just the dependencies stage:

```bash
# Build dependencies image (specify version)
docker build --target dependencies --build-arg VERSION=0.1.14 -t your-registry/production-control:deps .

# Push dependencies image
docker push your-registry/production-control:deps
```

This image only needs to be rebuilt when dependencies change (pyproject.toml or requirements-dev.txt).

### 2. Build and Push the Final Image

Build the final image that includes your application code:

```bash
# Build final image (specify version)
docker build --build-arg VERSION=0.1.14 -t your-registry/production-control:latest .

# Push final image
docker push your-registry/production-control:latest
```

### 3. Pull and Deploy

On your production server:

```bash
# Pull the latest images
docker compose pull

# Deploy
docker compose up -d
```

## Benefits

- **Faster Deployments**: When only Python code changes, only the final stage needs to be rebuilt
- **Efficient Caching**: Dependencies are cached in a separate image
- **Reduced Download Size**: When pulling updates with only code changes, less data needs to be downloaded
- **Proper Versioning**: Version is passed as a build argument, ensuring correct versioning without git metadata

## CI/CD Integration

The GitHub Actions workflow has been updated to:
1. Extract the version from the git tag
2. Pass it as a build argument to Docker
3. Build and push the image with proper versioning

This ensures that the version is correctly set in the Docker image, even without the .git directory in the build context.
