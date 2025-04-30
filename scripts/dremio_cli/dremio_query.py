#!/usr/bin/env python3
"""
Dremio Query Tool

This script allows executing SQL queries against Dremio using the Arrow Flight connection.
It uses the VINEAPP_DB_CONNECTION environment variable to connect to Dremio.

Usage:
    ./dremio_query.py "SELECT * FROM table"
    ./dremio_query.py --file query.sql
"""

import argparse
import os
import sys
import pandas as pd
from urllib.parse import urlparse, parse_qs
from dremio_simple_query.connect import DremioConnection, get_token


def parse_connection_string(connection_string):
    """Parse the Dremio connection string to extract credentials and endpoint."""
    # Example: dremio+flight://user:pass@localhost:32010/dremio?UseEncryption=false
    try:
        # Parse the URL
        parsed_url = urlparse(connection_string)

        # Extract username and password
        username = parsed_url.username
        password = parsed_url.password

        # Extract host and port
        host = parsed_url.hostname
        port = parsed_url.port

        # Determine if encryption is used
        query_params = parse_qs(parsed_url.query)
        use_encryption = not (query_params.get("UseEncryption", ["true"])[0].lower() == "false")

        # Construct the Arrow endpoint
        protocol = "grpc+tls://" if use_encryption else "grpc://"
        arrow_endpoint = f"{protocol}{host}:{port}"

        return {"username": username, "password": password, "arrow_endpoint": arrow_endpoint}
    except Exception as e:
        print(f"Error parsing connection string: {e}")
        sys.exit(1)


def get_connection():
    """Get a connection to Dremio using the environment variable."""
    # Get the connection string from environment variable
    connection_string = os.getenv("VINEAPP_DB_CONNECTION")
    if not connection_string:
        print("Error: VINEAPP_DB_CONNECTION environment variable not set")
        sys.exit(1)

    # Parse the connection string
    conn_info = parse_connection_string(connection_string)
    
    try:
        # For Dremio Software, we need to get a token from the REST API
        # Extract host from the arrow endpoint
        host = conn_info["arrow_endpoint"].split("://")[1].split(":")[0]
        port = 9047  # Default REST API port
        login_endpoint = f"http://{host}:{port}/apiv2/login"
        
        # Create payload for login
        payload = {
            "userName": conn_info["username"],
            "password": conn_info["password"]
        }
        
        # Get token from API
        token = get_token(uri=login_endpoint, payload=payload)
        
        # Create the connection
        return DremioConnection(token, conn_info["arrow_endpoint"])
    except Exception as e:
        print(f"Error connecting to Dremio: {e}")
        sys.exit(1)


def execute_query(query: str) -> None:
    """Execute a SQL query against Dremio and display the results."""
    try:
        # Get the connection
        dremio = get_connection()

        # Execute the query and get results as a pandas DataFrame
        result = dremio.toPandas(query)

        # Display the results
        pd.set_option("display.max_rows", None)
        pd.set_option("display.max_columns", None)
        pd.set_option("display.width", None)
        print(result)

    except Exception as e:
        print(f"Error executing query: {e}")
        sys.exit(1)


def main() -> None:
    """Parse command line arguments and execute the query."""
    parser = argparse.ArgumentParser(description="Execute SQL queries against Dremio")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("query", nargs="?", help="SQL query to execute")
    group.add_argument("--file", help="File containing SQL query to execute")

    args = parser.parse_args()

    if args.file:
        try:
            with open(args.file, "r") as f:
                query = f.read()
            execute_query(query)
        except FileNotFoundError:
            print(f"Error: File {args.file} not found")
            sys.exit(1)
    else:
        execute_query(args.query)


if __name__ == "__main__":
    main()
