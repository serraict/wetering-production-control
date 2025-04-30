# Dremio CLI Access

This directory contains tools and documentation for accessing Dremio via the command line using ISQL with ODBC.

## Overview

The Dremio CLI access allows AI agents and developers to:
- Inspect schema information
- Validate data
- Test SQL queries
- Support development with data exploration
- Troubleshoot issues

## Components

1. **ODBC Setup** - Configuration files and installation instructions for Dremio ODBC drivers
2. **ISQL Integration** - Tools for connecting to Dremio using the ISQL command-line utility
3. **Helper Scripts** - Convenience scripts for common operations
4. **Example Queries** - SQL queries for various use cases

## Quick Start

1. Install the Dremio ODBC driver (see [ODBC Setup](./odbc_setup/install.md))
2. Configure your ODBC connection (see [ODBC Configuration](./odbc_setup/configuration.md))
3. Use the helper scripts to connect to Dremio:

```bash
# Connect to Dremio and run a query
./scripts/dremio_cli/connect.sh

# Run a specific example query
./scripts/dremio_cli/run_query.sh example_queries/schema_inspection.sql
```

## Use Cases

### Schema Inspection
View available tables and views, examine column definitions, understand relationships between tables.

```bash
# List all tables in Dremio
./scripts/dremio_cli/run_query.sh example_queries/list_tables.sql
```

### Data Validation
Verify data quality, check for null values, validate data transformations.

```bash
# Check for null values in a specific column
./scripts/dremio_cli/run_query.sh example_queries/check_nulls.sql
```

### Query Testing
Test SQL queries before implementing them in code, debug complex queries.

```bash
# Interactive SQL session
./scripts/dremio_cli/connect.sh
```

### Development Support
Generate test data, create fixtures, verify changes haven't broken existing queries.

```bash
# Generate test data
./scripts/dremio_cli/run_query.sh example_queries/generate_test_data.sql
```

### Troubleshooting
Investigate production issues, compare expected vs actual data.

```bash
# Check for data inconsistencies
./scripts/dremio_cli/run_query.sh example_queries/data_consistency.sql
```
