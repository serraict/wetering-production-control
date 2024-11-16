# Production Control

Application to help track prodcution information at Wetering Potlilium

## Features

- Web interface built with NiceGUI
- Command-line interface
- Dremio integration for data access

## Installation

1. Create and activate a virtual environment:

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Unix
   # or
   .\venv\Scripts\activate  # On Windows
   ```

1. Install the package:

   ```bash
   pip install -e .
   ```

1. Copy `.env.example` to `.env` and configure:

   ```bash
   cp .env.example .env
   ```

## Usage

### Web Interface

Start the web server:

```bash
python -m production_control.__web__
```

Visit http://localhost:8080 in your browser.

### Command Line

Show version:

```bash
production_control version
```

List products:

```bash
production_control products
```

## Development

1. Install development dependencies:

   ```bash
   pip install -r requirements-dev.txt
   ```

1. Run tests:

   ```bash
   pytest
   ```

1. Run quality checks:

   ```bash
   make quality
   ```

### Docker Development

1. Build and start services:

   ```bash
   docker-compose up --build
   ```

1. Access the application:

   - Web UI: http://localhost:8080
   - CLI: `docker-compose exec app production_control version`
