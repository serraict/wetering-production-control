"""Dremio backup command implementation.

This module provides commands for backing up Dremio query results to CSV files.
The backup command supports:
- Custom naming of backup files with --name
- Output directory configuration via DREMIO_BACKUP_DIR environment variable
- Automatic chunking of large result sets
"""

import csv
from pathlib import Path
from typing import Annotated

import sqlalchemy as sa
import typer
from sqlalchemy.engine import Engine
from sqlmodel import Session

from production_control.data.repository import DremioRepository

app = typer.Typer()


def get_engine() -> Engine:
    """Get SQLAlchemy engine from repository configuration."""
    # Create a dummy repository to get the engine
    repo = DremioRepository(None)
    return repo.engine


@app.command(name="query")
def backup_query(
    query: Annotated[
        str, typer.Argument(help="SQL query to execute (e.g. 'SELECT * FROM bestelling')")
    ],
    name: Annotated[
        str, typer.Option(help="Name prefix for the backup files (e.g. 'afroep_opdrachten')")
    ] = None,
    output_dir: Annotated[
        Path,
        typer.Option(
            file_okay=False,
            dir_okay=True,
            envvar="DREMIO_BACKUP_DIR",
            help="Output directory (default: $DREMIO_BACKUP_DIR or ./backups)",
        ),
    ] = Path.cwd()
    / "backups",
    chunk_size: Annotated[
        int, typer.Option(help="Rows per CSV file chunk (default: 100,000)")
    ] = 100_000,
):
    """Execute a Dremio query and save results as CSV files.

    The command executes the provided SQL query against Dremio and saves the results
    in one or more CSV files. Large result sets are automatically split into multiple
    files based on the chunk_size parameter.

    Each output file follows the naming pattern: {name}_{number}.csv
    where {name} is either the provided name or 'backup' by default,
    and {number} is a 3-digit sequence starting at 001.

    Examples:
        pc backup query "SELECT * FROM bestelling WHERE ar > 0" --name afroep_opdrachten
        pc backup query "SELECT * FROM bestelling" --output-dir /path/to/dir
        DREMIO_BACKUP_DIR=/backup/path pc backup query "SELECT * FROM bestelling"
    """
    try:
        output_dir.mkdir(parents=True, exist_ok=True)

        with Session(get_engine()) as session:
            result = session.exec(sa.text(query))

            file_counter = 1
            while True:
                chunk = result.fetchmany(chunk_size)
                if not chunk:
                    break

                filename = output_dir / f"{name or 'backup'}_{file_counter:03d}.csv"
                with open(filename, "w", newline="") as f:
                    writer = csv.writer(f)
                    writer.writerow(result.keys())  # Write header
                    writer.writerows(chunk)

                file_counter += 1

        typer.echo(f"Success: Saved {file_counter - 1} file(s) to {output_dir}")

    except sa.exc.SQLAlchemyError as e:
        typer.echo(f"Database error: {str(e)}", err=True)
        raise typer.Abort()
    except OSError as e:
        typer.echo(f"File system error: {str(e)}", err=True)
        raise typer.Exit(code=1)
