"""Command line interface for Production Control."""

import typer
from rich.console import Console
from rich.table import Table
from typing import Optional
from . import __version__
from .products.models import ProductRepository
from .spacing.repository import SpacingRepository

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


@app.command(name="spacing-errors")
def spacing_errors(
    error: Optional[str] = typer.Option(None, "--error", "-e", help="Filter by error message")
):
    """Display a table of spacing records with errors."""
    repository = SpacingRepository()
    error_records = repository.get_error_records()

    # Filter records if error pattern provided
    if error:
        error_records = [
            r for r in error_records if error.lower() in r.wijderzet_registratie_fout.lower()
        ]
        if not error_records:
            console.print(f"No records found with error matching: {error}")
            return

    table = Table(title="Spacing Records with Errors")
    table.add_column("Partij", style="cyan")
    table.add_column("Product", style="green")
    table.add_column("Productgroep", style="blue")
    table.add_column("Oppotdatum", style="magenta")
    table.add_column("Fout", style="red")

    for record in error_records:
        oppotdatum = (
            record.datum_oppotten_real.strftime("%Y-%m-%d") if record.datum_oppotten_real else ""
        )
        table.add_row(
            record.partij_code,
            record.product_naam,
            record.productgroep_naam,
            oppotdatum,
            record.wijderzet_registratie_fout or "",
        )

    console.print(table)


def cli():
    """Entry point for the CLI."""
    app()


if __name__ == "__main__":
    cli()
