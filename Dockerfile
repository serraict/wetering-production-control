## ------------------------------- Build Stage ------------------------------ ##
FROM ghcr.io/serraict/wetering-production-control-base:latest AS builder

WORKDIR /app

# Copy everything including .git for setuptools_scm
COPY . .

# Install only the package (dependencies already in base)
RUN uv pip install . --no-deps

# Create dist directory with proper structure for easy copying
RUN mkdir -p /app/dist/.venv/bin && \
    mkdir -p /app/dist/.venv/lib/python3.12/site-packages && \
    cp /app/.venv/bin/production_control /app/dist/.venv/bin/ && \
    cp -r /app/.venv/lib/python3.12/site-packages/production_control /app/dist/.venv/lib/python3.12/site-packages/ && \
    cp -r /app/.venv/lib/python3.12/site-packages/production_control-*.dist-info /app/dist/.venv/lib/python3.12/site-packages/

## ------------------------------- App Stage ------------------------------ ##
FROM ghcr.io/serraict/wetering-production-control-base:latest AS app

WORKDIR /app

# Copy only the installed application package from builder
COPY --from=builder /app/dist/.venv /app/.venv

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
