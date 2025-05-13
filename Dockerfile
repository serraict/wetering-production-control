# Stage 1: Base image with system dependencies
FROM python:3.12-slim as base
WORKDIR /production_control

# Install system dependencies
RUN apt-get update && \
    apt-get install -y curl gnupg2 apt-transport-https cron && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Stage 2: Dependencies only - this can be built and tagged separately
FROM base as dependencies
WORKDIR /deps

# Copy only requirements files
COPY pyproject.toml requirements-dev.txt ./

# Install Python dependencies
RUN pip install --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements-dev.txt

# Stage 3: Final image with application code
FROM base
WORKDIR /production_control

# Copy dependencies from the dependencies stage
COPY --from=dependencies /usr/local/lib/python3.12/site-packages/ /usr/local/lib/python3.12/site-packages/
COPY --from=dependencies /usr/local/bin/ /usr/local/bin/

# Copy application code
COPY . .
RUN pip install --no-cache-dir --upgrade .

# Create log files
RUN touch /var/log/cron.log /var/log/webapp.log

# Make entrypoint script executable
RUN chmod +x /production_control/docker-entrypoint.sh

EXPOSE 8000
ENTRYPOINT ["/production_control/docker-entrypoint.sh"]
