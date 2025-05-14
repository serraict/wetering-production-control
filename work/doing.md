# Doing

## Optimize Dockerfile with uv Package Manager and Multi-stage Builds (COMPLETED)

### Current Issue
When pulling the Docker image after minor code changes, multiple layers need to be downloaded despite only application code changing. This is inefficient as theoretically only the final layers should need updating.

### Root Cause
The current setup doesn't properly leverage Docker's layer caching mechanism. While our Dockerfile has multiple stages (base, builder, production), we're not building and pushing these stages separately, causing unnecessary layer downloads.

### Implementation Summary

1. **Simplified Dockerfile Structure**
   - Reduced from three stages (base, builder, production) to two stages (base, app)
   - Moved dependencies to the base stage
   - Used fixed version for base stage to ensure caching works
   - Ensured version format is PEP 440 compliant (0.1.0.dev0)

2. **Updated Build Process**
   - Added docker_base target to build just the base image
   - Updated docker_image target to use base image for caching
   - Added docker_push_base and docker_push_all targets
   - Fixed version handling in build args

3. **Updated docker-compose.yml**
   - Added target specification for app stage
   - Added cache_from configuration to use base image
   - Added version argument handling

4. **Simplified GitHub Actions Workflow**
   - Removed separate base image build step
   - Focused on building and pushing only the app image
   - Fixed image naming and tagging

### Findings and Challenges

1. **Local Build Optimization**
   - The multi-stage build approach works well for local development
   - When using `make docker_base` followed by `make docker_image`, only the app-specific layers are rebuilt

2. **Docker Pull Behavior**
   - Direct `docker pull` commands correctly leverage layer caching
   - When pulling the base image first, then the latest image, only app-specific layers are downloaded
   - Docker Compose's pull mechanism doesn't leverage layer caching as effectively

3. **Base Image Determinism**
   - The base image layers change between builds even when dependencies don't change
   - This is due to non-deterministic elements in the build process (apt-get updates, timestamps, etc.)
   - For truly deterministic builds, additional optimizations would be needed

### Recommended Deployment Approach

For production deployments, use a script that pulls images directly:

```bash
#!/bin/bash
docker pull ghcr.io/serraict/wetering-production-control:base
docker pull ghcr.io/serraict/wetering-production-control:latest
docker compose -f production-control-docker-compose.yml up -d
```

This ensures that Docker properly leverages layer caching between the base and latest images.

### Next Steps
- Monitor build times and pull times in production
- Consider implementing deterministic base image builds if needed
- Update documentation with the new build and deployment process
