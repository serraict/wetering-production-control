#!/usr/bin/env python3
"""
Dremio Query Tool

This script allows executing SQL queries against Dremio using the Flight SQL connection.
It uses the VINEAPP_DB_CONNECTION environment variable to connect to Dremio.

Usage:
    ./dremio_query.py "SELECT * FROM table"
    ./dremio_query.py --file query.sql
    ./dremio_query.py --interactive
"""

import argparse
import os
import sys

try:
    import pandas as pd
    from sqlalchemy import create_engine, text
except ImportError:
    print("Required packages not found. Please install them with:")
    print("pip install pandas sqlalchemy sqlalchemy-dremio pyarrow")
    sys.exit(1)


def execute_query(query: str) -> None:
    """Execute a SQL query against Dremio and display the results."""
    # Get the connection string from environment variable
    connection_string = os.getenv("VINEAPP_DB_CONNECTION")
    if not connection_string:
        print("Error: VINEAPP_DB_CONNECTION environment variable not set")
        sys.exit(1)

    try:
        # Create the engine
        engine = create_engine(connection_string)

        # Execute the query
        with engine.connect() as connection:
            result = pd.read_sql(text(query), connection)

        # Display the results
        pd.set_option("display.max_rows", None)
        pd.set_option("display.max_columns", None)
        pd.set_option("display.width", None)
        print(result)

    except Exception as e:
        print(f"Error executing query: {e}")
        sys.exit(1)


def interactive_mode() -> None:
    """Run in interactive mode, allowing multiple queries to be executed."""
    # Get the connection string from environment variable
    connection_string = os.getenv("VINEAPP_DB_CONNECTION")
    if not connection_string:
        print("Error: VINEAPP_DB_CONNECTION environment variable not set")
        sys.exit(1)

    try:
        # Create the engine
        engine = create_engine(connection_string)

        print("Connected to Dremio. Type 'exit' or 'quit' to exit.")
        print("Enter SQL query (end with semicolon):")

        query = ""
        while True:
            try:
                line = input("> " if not query else "... ")
                if line.lower() in ("exit", "quit"):
                    break

                query += line + " "

                if line.strip().endswith(";"):
                    # Execute the query
                    with engine.connect() as connection:
                        result = pd.read_sql(text(query.strip(";")), connection)

                    # Display the results
                    pd.set_option("display.max_rows", None)
                    pd.set_option("display.max_columns", None)
                    pd.set_option("display.width", None)
                    print(result)

                    query = ""
            except KeyboardInterrupt:
                print("\nKeyboard interrupt. Type 'exit' or 'quit' to exit.")
                query = ""
            except Exception as e:
                print(f"Error: {e}")
                query = ""

    except Exception as e:
        print(f"Error connecting to Dremio: {e}")
        sys.exit(1)


def main() -> None:
    """Parse command line arguments and execute the query."""
    parser = argparse.ArgumentParser(description="Execute SQL queries against Dremio")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("query", nargs="?", help="SQL query to execute")
    group.add_argument("--file", help="File containing SQL query to execute")
    group.add_argument("--interactive", action="store_true", help="Run in interactive mode")

    args = parser.parse_args()

    if args.interactive:
        interactive_mode()
    elif args.file:
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
