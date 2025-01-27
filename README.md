# Production Control

Application to help track production information at Wetering Potlilium.

## Development

See [CONTRIBUTING.md](CONTRIBUTING.md) for development setup and guidelines.

## Installation

### From Repository Checkout using venv

1. Create and activate a virtual environment:

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Unix
   # or
   .\venv\Scripts\activate  # On Windows
   ```

1. Install the package in editable mode:

   ```bash
   pip install -e .
   ```

1. Copy and configure environment variables:

   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

### Production Deployment using Docker Compose

1. Create a `docker-compose.yml` file:

   ```yaml
   services:
     production_control:
       image: ghcr.io/serraict/wetering-production-control:latest
       ports:
         - "7903:8080"
       env_file:
         - .env
       networks:
         - serra-vine
       restart: unless-stopped

   networks:
     serra-vine:
       external: true
   ```

1. Create `.env` file with your configuration:

   ```bash
   # Copy from .env.example and adjust settings
   cp .env.example .env
   ```

1. Start the service:

   ```bash
   docker compose up -d
   ```

## Features

### Dremio Backup Command

The `backup` command allows you to export Dremio query results to CSV files:

```bash
# Basic usage - saves to ./backups by default
production-control backup backup-table "SELECT * FROM Verkoop.afroepbestellingen"

# Specify output directory
production-control backup backup-table "SELECT * FROM table" --output-dir /path/to/backups

# Control chunk size for large results (default: 100,000 rows per file)
production-control backup backup-table "SELECT * FROM table" --chunk-size 50000
```

The command will:
- Execute the provided SQL query against Dremio
- Save results as CSV files with headers
- Split large results into multiple files based on chunk size
- Create output directory if it doesn't exist