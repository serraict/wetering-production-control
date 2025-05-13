# Doing

## Optimize Dockerfile for Faster Deployments with Multi-stage Builds

Restructure the Dockerfile to use multi-stage builds for better optimization when pulling updates. This approach is specifically designed for workflows using `docker compose pull`, separating dependencies from code to speed up deployments when only Python code changes.

### Implementation Plan

1. Multi-stage Dockerfile to separate dependencies from code:
```dockerfile
# Stage 1: Dependencies
FROM python:3.12 as deps
WORKDIR /deps
COPY pyproject.toml requirements-dev.txt ./
RUN pip install --upgrade pip setuptools wheel
RUN pip install --no-cache-dir -r requirements-dev.txt

# Stage 2: Runtime
FROM python:3.12
WORKDIR /production_control

# Copy system dependencies setup
RUN apt-get update && \
    apt-get install -y curl gnupg2 apt-transport-https cron && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Copy dependencies from deps stage
COPY --from=deps /usr/local/lib/python3.12/site-packages/ /usr/local/lib/python3.12/site-packages/

# Copy application code
COPY . .
RUN pip install --no-cache-dir --upgrade .

# Setup logs and entrypoint
RUN touch /var/log/cron.log /var/log/webapp.log
RUN chmod +x /production_control/docker-entrypoint.sh

EXPOSE 8000
ENTRYPOINT ["/production_control/docker-entrypoint.sh"]
```

### Benefits
- Dependencies layer is built and cached separately
- Only code changes trigger rebuilds of the final stage
- Faster pulls when only Python code has changed
- Full rebuilds only happen when dependencies change

### Verification Steps
```bash
# Test 1: Time a pull after requirements change
# This will be slower as it needs to rebuild and pull all layers
time docker compose pull

# Test 2: Time a pull after only Python code change
# This should be significantly faster as it only pulls the final layer
time docker compose pull
```

### CI/CD Considerations
- Build and push base image (with dependencies) when requirements change
- Build and push final image (with code) for code changes
- Use appropriate tags to maintain this separation
- Consider using semantic versioning for dependency changes vs. code changes
