# Production Control

Application to help track production information at Wetering Potlilium.

## Development

See [CONTRIBUTING.md](CONTRIBUTING.md) for development setup and guidelines.

## Features

- List potting jobs and print potting labels
- List spacing job results
- List bulb picking jobs and print labels
- backup information from Dremio to csv

### Configurable Label Sizes

The application supports configurable label sizes for bulb picklist labels. You can set the dimensions in your `.env` file:

```
# Label dimensions
LABEL_WIDTH="151mm"
LABEL_HEIGHT="101mm"
```

The label layout will automatically scale to fit the specified dimensions while maintaining proper proportions.

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
