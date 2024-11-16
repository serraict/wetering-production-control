"""Command line interface for Production Control."""

import typer
from rich.console import Console
from rich.table import Table
from . import __version__
from .products.models import ProductRepository

app = typer.Typer()
console = Console()


@app.callback()
def callback():
    """Application to help track prodcution information at Wetering Potlilium"""


@app.command()
def version():
    """Show the application version."""
    typer.echo(f"Production Control version: {__version__}")


@app.command()
def products():
    """Display a table of all products with their groups."""
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


def cli():
    """Entry point for the CLI."""
    app()


if __name__ == "__main__":
    cli()
