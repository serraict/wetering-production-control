## ------------------------------- Build Stage ------------------------------ ##
FROM python:3.12-slim-bookworm AS builder

# Install build dependencies including git for version detection
RUN apt-get update && apt-get install --no-install-recommends -y \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install uv
RUN pip install uv

WORKDIR /app

# Copy everything including .git for setuptools_scm version detection
COPY . .

# Install dependencies and package in production mode (setuptools_scm can now read git history for proper versioning)
RUN uv sync --no-dev && uv pip install .

## ------------------------------- App Stage ------------------------------ ##
FROM python:3.12-slim-bookworm AS app

# Install runtime dependencies including WeasyPrint requirements and runtime tools
RUN apt-get update && apt-get install --no-install-recommends -y \
    curl \
    ca-certificates \
    # Runtime tools
    gnupg2 \
    apt-transport-https \
    cron \
    # WeasyPrint dependencies
    libcairo2 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf2.0-0 \
    libffi-dev \
    shared-mime-info \
    libgirepository1.0-dev \
    libglib2.0-0 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

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
