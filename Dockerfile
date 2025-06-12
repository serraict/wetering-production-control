## ------------------------------- Build Stage ------------------------------ ##
FROM ghcr.io/serraict/wetering-production-control-base:latest AS builder

WORKDIR /app

# Copy everything including .git for setuptools_scm version detection
COPY . .

# Install dependencies and package in production mode (setuptools_scm can now read git history for proper versioning)
RUN uv sync --no-dev && uv pip install .

## ------------------------------- App Stage ------------------------------ ##
FROM ghcr.io/serraict/wetering-production-control-base:latest AS app

WORKDIR /app

# Copy the built virtual environment from builder stage (package is now installed in site-packages)
COPY --from=builder /app/.venv /app/.venv

# Copy only runtime files needed
COPY docker-entrypoint.sh /app/

# Set up environment variables for production
ENV PATH="/app/.venv/bin:$PATH"

# Create log files as requested
RUN touch /var/log/cron.log /var/log/webapp.log

# Make entrypoint script executable
RUN chmod +x /app/docker-entrypoint.sh

EXPOSE 8000
ENTRYPOINT ["/app/docker-entrypoint.sh"]
