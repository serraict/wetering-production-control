## ------------------------------- Base Stage ------------------------------ ##
FROM python:3.12-slim-bookworm AS base

# Set a fixed version for the base image to ensure caching works
ENV SETUPTOOLS_SCM_PRETEND_VERSION=0.1.0.dev0
ENV SETUPTOOLS_SCM_PRETEND_VERSION_FOR_PRODUCTION_CONTROL=0.1.0.dev0

# Install all system dependencies including WeasyPrint requirements and runtime tools
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

# Download and install uv
ADD https://astral.sh/uv/install.sh /install.sh
RUN chmod -R 655 /install.sh && /install.sh && rm /install.sh

# Set up the UV environment path correctly
ENV PATH="/root/.local/bin:${PATH}"

WORKDIR /app

# Copy only dependency-related files first
COPY ./pyproject.toml .
RUN mkdir -p /app/src

# Install dependencies
RUN uv sync

## ------------------------------- App Stage ------------------------------ ##
FROM base AS app

# Accept build argument for version
ARG VERSION=0.1.0.dev0
ENV SETUPTOOLS_SCM_PRETEND_VERSION=$VERSION
ENV SETUPTOOLS_SCM_PRETEND_VERSION_FOR_PRODUCTION_CONTROL=$VERSION

# Copy application code
COPY . .

# Set up environment variables for production
ENV PATH="/app/.venv/bin:$PATH"

# Create log files
RUN touch /var/log/cron.log /var/log/webapp.log

# Make entrypoint script executable
RUN chmod +x /app/docker-entrypoint.sh

EXPOSE 8000
ENTRYPOINT ["/app/docker-entrypoint.sh"]
