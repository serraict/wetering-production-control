"""Command line interface for Production Control."""

import logging
from pathlib import Path
import typer
from rich.console import Console
from rich.logging import RichHandler
from rich.table import Table
from typing import Optional
from . import __version__
from .products.models import ProductRepository
from .data import backup

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(message)s", handlers=[RichHandler(rich_tracebacks=True)]
)
logger = logging.getLogger("production_control")

app = typer.Typer()
console = Console()

# Add sub-commands
app.add_typer(backup.app, name="backup", help="Dremio backup commands")








@app.callback()
def callback():
    """Application to help track production information at Wetering Potlilium."""


@app.command()
def version():
    """Show the application version."""
    logger.info("Checking Production Control version")
    typer.echo(f"Production Control version: {__version__}")


@app.command()
def products():
    """Display a table of all products with their groups."""
    logger.info("Retrieving product list")
    repository = ProductRepository()
    products_list = repository.get_all()

    table = Table(title="Products")
    table.add_column("ID", justify="right", style="cyan")
    table.add_column("Name", style="green")
    table.add_column("Product Group", style="blue")

    for product in products_list:
        table.add_row(
            str(product.id),
            product.name,
            product.product_group_name,
        )

    console.print(table)
    logger.info(f"Found {len(products_list)} products")








def cli():
    """Entry point for the CLI."""
    app()


if __name__ == "__main__":
    cli()
