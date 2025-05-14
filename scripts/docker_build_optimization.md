# Docker Build Optimization Guide

This guide explains how to leverage the multi-stage Dockerfile with uv for faster builds and deployments.

## Understanding the Three-stage Dockerfile

The Dockerfile has been restructured with three stages:

1. **Base**: Contains system dependencies and uv installation
2. **Builder**: Installs Python dependencies and builds the application wheel
3. **Final**: Creates the production runtime environment

This structure allows for better layer caching and faster builds when only Python code changes.

## Using UV for Dependency Management

The Dockerfile uses [uv](https://github.com/astral-sh/uv), a fast Python package installer and resolver. This provides several benefits:

1. Faster dependency installation (up to 10-100x faster than pip)
2. Better caching of dependencies
3. Cleaner virtual environment management
4. Improved dependency resolution

## Version Handling

The Dockerfile accepts a `VERSION` build argument that is passed to setuptools_scm via the `SETUPTOOLS_SCM_PRETEND_VERSION` environment variable. This ensures proper versioning even without the .git directory in the Docker build context.

The GitHub Actions workflow should be configured to:
1. Extract the version from the git tag
2. Pass it as a build argument to Docker

## Development Workflow

For local development, you can use the existing docker-compose.yml:

```bash
# Build with the optimized Dockerfile (specify version for local development)
docker compose build --build-arg VERSION=0.1.0-dev

# Run the application
docker compose up
```

## Production Deployment Optimization

To optimize production deployments with `docker compose pull`, follow these steps:

### 1. Build and Push the Base Image

Build and tag just the base stage:

```bash
# Build base image
docker build --target base -t your-registry/production-control:base .

# Push base image
docker push your-registry/production-control:base
```

This image only needs to be rebuilt when system dependencies change.

### 2. Build and Push the Builder Image

Build and tag the builder stage:

```bash
# Build builder image (specify version)
docker build --target builder --build-arg VERSION=0.1.14 -t your-registry/production-control:builder .

# Push builder image
docker push your-registry/production-control:builder
```

This image only needs to be rebuilt when dependencies change (pyproject.toml or requirements-dev.txt).

### 3. Build and Push the Final Image

Build the final image that includes your application code:

```bash
# Build final image (specify version)
docker build --build-arg VERSION=0.1.14 -t your-registry/production-control:latest .

# Push final image
docker push your-registry/production-control:latest
```

### 4. Pull and Deploy

On your production server:

```bash
# Pull the latest images
docker compose pull

# Deploy
docker compose up -d
```

## Benefits

- **Faster Deployments**: When only Python code changes, only the final stage needs to be rebuilt
- **Efficient Caching**: Dependencies are cached in separate images
- **Reduced Download Size**: When pulling updates with only code changes, less data needs to be downloaded
- **Proper Versioning**: Version is passed as a build argument, ensuring correct versioning without git metadata
- **Faster Dependency Installation**: Using `uv` significantly speeds up the dependency installation process
- **Smaller Final Image**: The final image only contains what's needed for runtime
- **Better Build Performance**: The three-stage approach optimizes the build process for different types of changes

## CI/CD Integration

The GitHub Actions workflow should be updated to:
1. Extract the version from the git tag
2. Pass it as a build argument to Docker
3. Build and push the image with proper versioning
4. Optionally, build and push the base and builder images separately for better caching

### Example GitHub Actions Workflow

```yaml
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
        with:
          fetch-depth: 0  # Fetch all history for setuptools_scm

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v2

      - name: Get version
        id: get_version
        run: echo "VERSION=$(python -c 'from setuptools_scm import get_version; print(get_version())')" >> $GITHUB_OUTPUT

      - name: Login to Docker Registry
        uses: docker/login-action@v2
        with:
          registry: your-registry
          username: ${{ secrets.REGISTRY_USERNAME }}
          password: ${{ secrets.REGISTRY_PASSWORD }}

      - name: Build and push base image
        uses: docker/build-push-action@v4
        with:
          context: .
          target: base
          push: true
          tags: your-registry/production-control:base
          cache-from: type=registry,ref=your-registry/production-control:base
          cache-to: type=inline

      - name: Build and push builder image
        uses: docker/build-push-action@v4
        with:
          context: .
          target: builder
          push: true
          tags: your-registry/production-control:builder
          build-args: |
            VERSION=${{ steps.get_version.outputs.VERSION }}
          cache-from: |
            type=registry,ref=your-registry/production-control:base
            type=registry,ref=your-registry/production-control:builder
          cache-to: type=inline

      - name: Build and push final image
        uses: docker/build-push-action@v4
        with:
          context: .
          push: true
          tags: |
            your-registry/production-control:latest
            your-registry/production-control:${{ steps.get_version.outputs.VERSION }}
          build-args: |
            VERSION=${{ steps.get_version.outputs.VERSION }}
          cache-from: |
            type=registry,ref=your-registry/production-control:base
            type=registry,ref=your-registry/production-control:builder
          cache-to: type=inline
```

This workflow ensures that the version is correctly set in the Docker image and leverages the multi-stage build for optimal caching.
