# Doing

## Docker Image Size Optimization Plan

### Problem

- App layer is 404MB, causing slow deployments over slow connections
- Goal: Deploy code changes in <1 minute
- Current: Every deployment downloads 404MB of Python dependencies

### Analysis Results

- **Base image**: 661MB (system deps + Python runtime)
- **Full image**: 1.07GB 
- **App layer**: 404MB (entirely from `.venv` directory with Python packages)
- **Root cause**: Python dependencies installed in app layer, not base layer

### Solution: Move Python Dependencies to Base Image

#### ✅ Phase 1: Modify Base Image (`Dockerfile.base`)

- Install all production dependencies from `pyproject.toml`
- Let uv manage the virtual environment at `/app/.venv`
- Keep it simple - no directory juggling

```dockerfile
# After existing RUN commands, add:

# Copy dependency files
COPY pyproject.toml README.md ./

# Install all production dependencies
RUN uv sync --no-dev --no-install-project

# The .venv is now at /app/.venv with all dependencies installed
```

> Lock file support will be added in a later phase for automated base image rebuilds

#### ✅ Phase 2: Dockerfile with Build Stage

- Keep build stage for git metadata (setuptools_scm requirement)
- Use pre-built venv from base image
- Copy only essential runtime files to app layer

```dockerfile
## Build Stage - needed for git metadata
FROM ghcr.io/serraict/wetering-production-control-base:latest AS builder

WORKDIR /app

# Copy everything including .git for setuptools_scm
COPY . .

# Install only the package (dependencies already in base)
RUN uv pip install . --no-deps

## App Stage
FROM ghcr.io/serraict/wetering-production-control-base:latest AS app

WORKDIR /app

# Copy the installed package from builder
COPY --from=builder /app/.venv /app/.venv

# Copy only runtime necessities
COPY docker-entrypoint.sh ./
COPY src/production_control/assets ./src/production_control/assets
# Add any other runtime-only files as needed

# Set up environment
ENV PATH="/app/.venv/bin:$PATH"

RUN touch /var/log/cron.log /var/log/webapp.log && \
    chmod +x /app/docker-entrypoint.sh

EXPOSE 8000
ENTRYPOINT ["/app/docker-entrypoint.sh"]
```

#### ❌ Phase 3: Create `.dockerignore`

NOT NEEDED (YET)

#### Phase 4: Update Build Process

- Add makefile target for dependency changes
- Update GitHub Actions for base image builds

#### Phase 5: Update Documentation

- Document new workflow in `docs/docker-base-image.md`
- Explain when to rebuild base vs app

#### Phase 6: Future Enhancement - Lock File Support

- Add uv lock file generation and usage
- Automate base image rebuilds when dependencies change
- This will be implemented after the core optimization is working

### Expected Results

- **Base image**: ~1GB (from 661MB) - downloaded once
- **App layer**: ~5-10MB (from 404MB) - fast deployments
- **Code changes**: <1 minute deployment time
- **Dependency changes**: Require base image rebuild (infrequent)

### Implementation Steps

1. Create `.dockerignore` file
2. Test locally with modified Dockerfiles
3. Validate functionality
4. Update CI/CD pipeline
5. Update documentation

### Rollback Plan

- Use previous base image tag if issues arise
- Revert Dockerfile changes
- No infrastructure changes required

---

**Status**: Plan documented, ready for review and implementation
