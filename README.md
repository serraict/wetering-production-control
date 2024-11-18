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

2. Install the package in editable mode:

   ```bash
   pip install -e .
   ```

3. Copy and configure environment variables:

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

2. Create `.env` file with your configuration:

   ```bash
   # Copy from .env.example and adjust settings
   cp .env.example .env
   ```

3. Start the service:

   ```bash
   docker compose up -d
   ```
