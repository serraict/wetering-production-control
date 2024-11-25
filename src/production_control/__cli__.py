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
from .spacing.repositories import SpacingRepository
from .spacing.commands import CorrectSpacingRecord, FixMissingWdz2DateCommand
from .spacing.optech import OpTechClient, OpTechError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    handlers=[RichHandler(rich_tracebacks=True)]
)
logger = logging.getLogger("production_control")

app = typer.Typer()
console = Console()


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


@app.command(name="spacing-errors")
def spacing_errors(
    error: Optional[str] = typer.Option(None, "--error", "-e", help="Filter by error message")
):
    """Display a table of spacing records with errors."""
    logger.info("Retrieving spacing records with errors")
    repository = SpacingRepository()
    error_records = repository.get_error_records()

    # Filter records if error pattern provided
    if error:
        logger.info(f"Filtering records with error pattern: {error}")
        error_records = [
            r for r in error_records if error.lower() in r.wijderzet_registratie_fout.lower()
        ]
        if not error_records:
            msg = f"No records found with error matching: {error}"
            logger.info(msg)
            typer.echo(msg)
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
    logger.info(f"Found {len(error_records)} records with errors")


@app.command(name="correct-spacing")
def correct_spacing(
    partij_code: str,
    wdz1: Optional[int] = typer.Option(None, "--wdz1", help="Number of tables after first spacing"),
    wdz2: Optional[int] = typer.Option(None, "--wdz2", help="Number of tables after second spacing"),
    dry_run: bool = typer.Option(True, "--dry-run/--no-dry-run", help="Preview changes without applying them"),
):
    """Correct spacing data for a batch."""
    logger.info(f"Looking up spacing record for partij {partij_code}")
    repository = SpacingRepository()
    record = repository.get_by_partij_code(partij_code)

    if not record:
        msg = f"Partij {partij_code} not found"
        logger.error(msg)
        typer.echo(msg, err=True)
        raise typer.Exit(code=1)

    # Validate inputs
    if wdz1 is not None and wdz1 <= 0:
        msg = "Number of tables must be positive"
        logger.error(msg)
        typer.echo(msg, err=True)
        raise typer.Exit(code=1)

    if wdz2 is not None and wdz1 is None:
        msg = "WDZ1 must be set when setting WDZ2"
        logger.error(msg)
        typer.echo(msg, err=True)
        raise typer.Exit(code=1)

    if wdz2 is not None and wdz2 <= 0:
        msg = "Number of tables must be positive"
        logger.error(msg)
        typer.echo(msg, err=True)
        raise typer.Exit(code=1)

    # Preview changes
    changes = []
    if wdz1 is not None and wdz1 != record.aantal_tafels_na_wdz1:
        changes.append(f"wdz1: {record.aantal_tafels_na_wdz1} -> {wdz1}")
    if wdz2 is not None and wdz2 != record.aantal_tafels_na_wdz2:
        changes.append(f"wdz2: {record.aantal_tafels_na_wdz2} -> {wdz2}")

    if not changes:
        msg = "No changes specified"
        logger.info(msg)
        typer.echo(msg)
        return

    # Format preview message
    preview = (
        f"{'[DRY RUN] ' if dry_run else ''}"
        f"Would update partij {partij_code} ({record.product_naam}): {', '.join(changes)}"
    )
    logger.info(preview)
    typer.echo(preview)

    # Apply changes if not dry run
    if not dry_run:
        try:
            # Create correction command
            command = CorrectSpacingRecord.from_record(record)
            if wdz1 is not None:
                command.aantal_tafels_na_wdz1 = wdz1
            if wdz2 is not None:
                command.aantal_tafels_na_wdz2 = wdz2

            # Send correction
            logger.info("Sending correction to OpTech API")
            client = OpTechClient()
            result = client.send_correction(command)

            typer.echo(result.message)
            logger.info("Correction applied successfully")

        except OpTechError as e:
            msg = f"Failed to update spacing data: {str(e)}"
            logger.error(msg)
            typer.echo(msg, err=True)
            raise typer.Exit(code=1)


@app.command(name="fix-spacing-errors")
def fix_spacing_errors(
    error_type: str = typer.Option(..., "--error", "-e", help="Error type to fix"),
    log_file: Optional[Path] = typer.Option(None, "--log", "-l", help="Path to log file for manual review cases"),
    dry_run: bool = typer.Option(True, "--dry-run/--no-dry-run", help="Preview changes without applying them"),
):
    """Fix spacing errors of a specific type."""
    logger.info(f"Retrieving spacing records with error type: {error_type}")
    repository = SpacingRepository()
    error_records = [
        r for r in repository.get_error_records()
        if error_type.lower() in r.wijderzet_registratie_fout.lower()
    ]

    if not error_records:
        msg = f"No records found with error matching: {error_type}"
        logger.info(msg)
        typer.echo(msg)
        return

    logger.info(f"Found {len(error_records)} records to process")

    # Set up manual review logging if needed
    manual_review_logger = None
    if log_file:
        manual_review_logger = logging.getLogger("manual_review")
        handler = logging.FileHandler(log_file)
        handler.setFormatter(logging.Formatter("%(asctime)s - %(message)s"))
        manual_review_logger.addHandler(handler)
        manual_review_logger.setLevel(logging.INFO)

    # Process records
    fixed = 0
    manual_review = 0
    client = OpTechClient()

    for record in error_records:
        # Handle missing WDZ2 date errors
        if "Geen wdz2 datum maar wel tafel aantal na wdz 2" in record.wijderzet_registratie_fout:
            fix_command = FixMissingWdz2DateCommand.from_record(record)
            if fix_command.can_fix_automatically():
                correction = fix_command.get_correction()
                if correction:
                    preview = (
                        f"{'[DRY RUN] ' if dry_run else ''}"
                        f"Fixing partij {record.partij_code} ({record.product_naam}): "
                        f"Move WDZ2 count ({record.aantal_tafels_na_wdz2}) to WDZ1, clear WDZ2"
                    )
                    logger.info(preview)
                    typer.echo(preview)

                    if not dry_run:
                        try:
                            result = client.send_correction(correction)
                            typer.echo(result.message)
                            fixed += 1
                        except OpTechError as e:
                            msg = f"Failed to update partij {record.partij_code}: {str(e)}"
                            logger.error(msg)
                            typer.echo(msg, err=True)
                            if manual_review_logger:
                                manual_review_logger.error(msg)
                            manual_review += 1
                    else:
                        fixed += 1
            else:
                msg = (
                    f"Partij {record.partij_code} ({record.product_naam}) needs manual review: "
                    f"WDZ1 count ({record.aantal_tafels_na_wdz1}) doesn't match "
                    f"rounded plan ({record.rounded_aantal_tafels_oppotten_plan})"
                )
                logger.info(msg)
                if manual_review_logger:
                    manual_review_logger.info(msg)
                manual_review += 1
        else:
            # Log other error types for manual review
            msg = (
                f"Partij {record.partij_code} ({record.product_naam}) needs manual review: "
                f"{record.wijderzet_registratie_fout}"
            )
            logger.info(msg)
            if manual_review_logger:
                manual_review_logger.info(msg)
            manual_review += 1

    # Summary
    summary = (
        f"\nProcessed {len(error_records)} records:\n"
        f"- {'Would fix' if dry_run else 'Fixed'}: {fixed}\n"
        f"- Manual review needed: {manual_review}"
    )
    if log_file and manual_review > 0:
        summary += f"\nRecords needing manual review have been logged to: {log_file}"

    logger.info(summary)
    typer.echo(summary)


def cli():
    """Entry point for the CLI."""
    app()


if __name__ == "__main__":
    cli()
