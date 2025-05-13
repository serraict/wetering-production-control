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
