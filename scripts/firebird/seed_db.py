#!/usr/bin/env python3
"""
Seed Firebird database with data from Dremio using remote connection.

This script extracts data from Dremio and loads it into the Firebird database via TCP connection.
"""

import os
import sys
from pathlib import Path

# Add parent directory to path to import dremio_query module
sys.path.insert(0, str(Path(__file__).parent.parent / "dremio_cli"))

import pandas as pd
from dremio_simple_query.connect import DremioConnection, get_token
from urllib.parse import urlparse


def get_dremio_connection():
    """Get a connection to Dremio using the environment variable."""
    connection_string = os.getenv("SIMPLE_QUERY_CONNECTION")
    if not connection_string:
        raise ValueError("SIMPLE_QUERY_CONNECTION environment variable not set")

    parsed_url = urlparse(connection_string)
    username = parsed_url.username
    password = parsed_url.password
    host = parsed_url.hostname
    port = parsed_url.port
    protocol = parsed_url.scheme

    arrow_endpoint = f"{protocol}://{host}:{port}"

    # Get token from API
    login_endpoint = f"http://{host}:9047/apiv2/login"
    payload = {"userName": username, "password": password}
    token = get_token(uri=login_endpoint, payload=payload)

    return DremioConnection(token, arrow_endpoint)


def seed_database():
    """Extract data from Dremio and create SQL insert statements."""
    print("Connecting to Dremio...")
    dremio = get_dremio_connection()

    print("Fetching data from Dremio...")
    query = "SELECT * FROM Productie.Planning.teeltpl"
    df = dremio.toPandas(query)
    print(f"Fetched {len(df)} rows from Dremio")

    # Generate SQL insert file
    sql_file = Path(__file__).parent / "02_seed_data.sql"

    print(f"Generating SQL insert statements to {sql_file}...")

    with open(sql_file, "w") as f:
        # Delete existing data
        f.write("DELETE FROM TEELTPL;\n\n")

        # Prepare column names
        columns = df.columns.tolist()

        # Write insert statements in batches
        for idx, row in df.iterrows():
            values = []
            for val in row:
                if pd.isna(val):
                    values.append("NULL")
                elif isinstance(val, str):
                    # Escape single quotes
                    escaped = val.replace("'", "''")
                    values.append(f"'{escaped}'")
                elif isinstance(val, (int, float)):
                    values.append(str(val))
                elif hasattr(val, 'strftime'):  # Date/datetime
                    values.append(f"'{val.strftime('%Y-%m-%d')}'")
                else:
                    values.append(f"'{val}'")

            insert_sql = f"INSERT INTO TEELTPL ({', '.join(columns)}) VALUES ({', '.join(values)});\n"
            f.write(insert_sql)

            if (idx + 1) % 100 == 0:
                print(f"  Generated {idx + 1} insert statements...")

        f.write("\nCOMMIT;\n")

    print(f"Successfully generated {len(df)} insert statements")
    print("\nNow importing data into Firebird...")

    # Execute the SQL file via docker
    import subprocess
    result = subprocess.run(
        ["docker", "compose", "exec", "-T", "firebird",
         "/opt/firebird/bin/isql", "-user", "SYSDBA", "-password", "masterkey",
         "localhost:/firebird/data/production.fdb"],
        stdin=open(sql_file),
        capture_output=True,
        text=True
    )

    if result.returncode == 0:
        print("Data imported successfully!")
    else:
        print(f"Error importing data: {result.stderr}")
        sys.exit(1)


if __name__ == "__main__":
    seed_database()
