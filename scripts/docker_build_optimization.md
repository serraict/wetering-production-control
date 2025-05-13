# Docker Build Optimization Guide

This guide explains how to leverage the multi-stage Dockerfile for faster builds and deployments.

## Understanding the Multi-stage Dockerfile

The Dockerfile has been restructured with three stages:

1. **Base**: Contains system dependencies
2. **Dependencies**: Installs Python packages
3. **Final**: Combines base, dependencies, and application code

This structure allows for better layer caching and faster builds when only Python code changes.

## Development Workflow

For local development, you can continue using the existing docker-compose.yml:

```bash
# Build with the optimized Dockerfile
docker compose build

# Run the application
docker compose up
```

## Production Deployment Optimization

To optimize production deployments with `docker compose pull`, follow these steps:

### 1. Build and Push the Dependencies Image

Build and tag just the dependencies stage:

```bash
# Build dependencies image
docker build --target dependencies -t your-registry/production-control:deps .

# Push dependencies image
docker push your-registry/production-control:deps
```

This image only needs to be rebuilt when dependencies change (pyproject.toml or requirements-dev.txt).

### 2. Build and Push the Final Image

Build the final image that includes your application code:

```bash
# Build final image
docker build -t your-registry/production-control:latest .

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

## CI/CD Integration

For optimal CI/CD integration:

1. Only rebuild and push the dependencies image when requirements files change
2. Always rebuild and push the final image for code changes
3. Use appropriate tags to maintain this separation (e.g., `:deps` and `:latest`)
