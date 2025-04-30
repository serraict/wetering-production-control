# Dremio CLI Access

This directory contains tools and documentation for accessing Dremio via the command line.

## Overview

The Dremio CLI access allows AI agents and developers to:

- Inspect schema information
- Validate data
- Test SQL queries
- Support development with data exploration
- Troubleshoot issues

## Important Note for Apple Silicon Users

We've discovered that the Arrow Flight SQL ODBC driver is not supported on Apple Silicon (M1/M2/M3) architecture, as stated in the [Dremio documentation](https://docs.dremio.com/software/drivers/odbc-driver/).

For this reason, we've provided a Python-based solution that uses the Flight SQL connection directly, which works on all platforms including Apple Silicon.

## Components

1. **Python Script** - A Python script for executing SQL queries against Dremio
2. **ODBC Documentation** - Documentation about ODBC setup (for non-Apple Silicon machines)
3. **Example Queries** - SQL queries for various use cases

## Quick Start

### Using the Python Script (Recommended)

The Python script uses the Flight SQL connection directly and works on all platforms, including Apple Silicon.

```bash
# Execute a simple query
./scripts/dremio_cli/dremio_query.py "SELECT * FROM table"

# Execute a query from a file
./scripts/dremio_cli/dremio_query.py --file path/to/query.sql
```

### Using the Alias (Easier)

For convenience, you can create an alias to the script:

```bash
# Add the alias to your current shell session
source scripts/dremio_cli/dremio_alias.sh

# Now you can use the alias
dremio-query "SELECT * FROM table"
```

To make the alias permanent, add the following line to your shell profile file (e.g., ~/.bashrc, ~/.zshrc):

```bash
source /path/to/production_control/scripts/dremio_cli/dremio_alias.sh
```

### Using ISQL with ODBC (Non-Apple Silicon Only)

If you're not using Apple Silicon, you can try the ISQL approach:

1. Install the Dremio ODBC driver (see [ODBC Setup](./odbc_setup/install.md))
2. Configure your ODBC connection (see [ODBC Configuration](./odbc_setup/configuration.md))
3. Use the connect.sh script:

```bash
# Connect to Dremio and run a query
./scripts/dremio_cli/connect.sh
```

## Use Cases

### Schema Inspection
View available tables and views, examine column definitions, understand relationships between tables.

```bash
# List all schemas
./scripts/dremio_cli/dremio_query.py "SHOW SCHEMAS"

# List all tables in a specific schema (note: schema name is required)
./scripts/dremio_cli/dremio_query.py "SHOW TABLES IN Productie"

# Show table details
./scripts/dremio_cli/dremio_query.py "DESCRIBE TABLE Productie.producten"
```

### Data Validation
Verify data quality, check for null values, validate data transformations.

```bash
# Check for null values in a specific column
./scripts/dremio_cli/dremio_query.py "SELECT COUNT(*) FROM table WHERE column IS NULL"
```

### Query Testing
Test SQL queries before implementing them in code, debug complex queries.

```bash
# Test a complex query
./scripts/dremio_cli/dremio_query.py "SELECT * FROM table WHERE complex_condition"
```

### Development Support
Generate test data, create fixtures, verify changes haven't broken existing queries.

```bash
# Execute a complex query
./scripts/dremio_cli/dremio_query.py "SELECT * FROM table WHERE condition"
```

### Troubleshooting
Investigate production issues, compare expected vs actual data.

```bash
# Check for data inconsistencies
./scripts/dremio_cli/dremio_query.py "SELECT * FROM table1 t1 LEFT JOIN table2 t2 ON t1.id = t2.id WHERE t2.id IS NULL"
```
