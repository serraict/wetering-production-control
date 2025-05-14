## ------------------------------- Base Stage ------------------------------ ##
FROM python:3.12 AS base

# Install minimal system dependencies
RUN apt-get update && apt-get install --no-install-recommends -y \
    curl \
    ca-certificates \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

## ------------------------------- Builder Stage ------------------------------ ##
FROM base AS builder

# Accept build argument for version
ARG VERSION=0.1.0-dev
ENV SETUPTOOLS_SCM_PRETEND_VERSION=$VERSION
ENV SETUPTOOLS_SCM_PRETEND_VERSION_FOR_PRODUCTION_CONTROL=$VERSION

# Download the latest installer, install it and then remove it
ADD https://astral.sh/uv/install.sh /install.sh
RUN chmod -R 655 /install.sh && /install.sh && rm /install.sh

# Set up the UV environment path correctly
ENV PATH="/root/.local/bin:${PATH}"

WORKDIR /app

RUN mkdir -p /app/src
COPY ./pyproject.toml .

RUN uv sync

## ------------------------------- Production Stage ------------------------------ ##
FROM python:3.12-slim-bookworm AS production

RUN apt-get update && apt-get install --no-install-recommends -y \
    curl gnupg2 apt-transport-https cron \
    ca-certificates \
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


# Accept build argument for version
ARG VERSION=0.1.0-dev
ENV SETUPTOOLS_SCM_PRETEND_VERSION=$VERSION
ENV SETUPTOOLS_SCM_PRETEND_VERSION_FOR_PRODUCTION_CONTROL=$VERSION

# RUN useradd --create-home appuser
# USER appuser

WORKDIR /app

COPY . .
COPY --from=builder /app/.venv .venv

# Set up environment variables for production
ENV PATH="/app/.venv/bin:$PATH"

# Create log files
RUN touch /var/log/cron.log /var/log/webapp.log

# Make entrypoint script executable
RUN chmod +x /app/docker-entrypoint.sh

EXPOSE 8000
ENTRYPOINT ["/app/docker-entrypoint.sh"]
