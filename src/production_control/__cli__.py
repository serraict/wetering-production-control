"""Command line interface for Production Control."""

import logging
from pathlib import Path
import typer
from rich.console import Console
from rich.logging import RichHandler
from rich.table import Table
from typing import Optional, Union
from . import __version__
from .products.models import ProductRepository
from .spacing.repositories import SpacingRepository
from .spacing.commands import CorrectSpacingRecord, FixMissingWdz2DateCommand
from .spacing.optech import OpTechClient, OpTechError
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


def send_spacing_correction(
    correction: CorrectSpacingRecord,
    dry_run: bool = True,
    manual_review_logger: Optional[logging.Logger] = None,
) -> bool:
    """Send a spacing correction to the OpTech API.

    Args:
        correction: The correction to send
        dry_run: If True, only preview the changes
        manual_review_logger: Optional logger for manual review cases

    Returns:
        True if correction was successful or dry run, False if it failed
    """
    if dry_run:
        return True

    try:
        client = OpTechClient()
        result = client.send_correction(correction)
        typer.echo(result.message)
        logger.info("Correction applied successfully")
        return True

    except OpTechError as e:
        msg = f"Failed to update partij {correction.partij_code}: {str(e)}"
        logger.error(msg)
        typer.echo(msg, err=True)
        if manual_review_logger:
            manual_review_logger.error(msg)
        return False


def format_preview(
    record_id: str,
    record_name: str,
    changes: Union[str, list[str]],
    dry_run: bool = True,
) -> str:
    """Format a preview message for spacing changes.

    Args:
        record_id: The record identifier (e.g. partij_code)
        record_name: The record name (e.g. product_naam)
        changes: Description of changes, either a string or list of strings
        dry_run: If True, add [DRY RUN] prefix

    Returns:
        Formatted preview message
    """
    if isinstance(changes, list):
        changes_str = ", ".join(changes)
    else:
        changes_str = changes

    return (
        f"{'[DRY RUN] ' if dry_run else ''}"
        f"{'Would update' if dry_run else 'Updating'} partij {record_id} "
        f"({record_name}): {changes_str}"
    )


def setup_manual_review_logger(log_file: Path) -> logging.Logger:
    """Set up a logger for manual review cases.

    Args:
        log_file: Path to the log file

    Returns:
        Configured logger
    """
    manual_review_logger = logging.getLogger("manual_review")
    handler = logging.FileHandler(log_file)
    handler.setFormatter(logging.Formatter("%(asctime)s - %(message)s"))
    manual_review_logger.addHandler(handler)
    manual_review_logger.setLevel(logging.INFO)
    return manual_review_logger


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
    table.add_column("Productgroep", style="cyan")
    table.add_column("Oppotdatum", style="cyan")
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
    wdz2: Optional[int] = typer.Option(
        None, "--wdz2", help="Number of tables after second spacing"
    ),
    dry_run: bool = typer.Option(
        True, "--dry-run/--no-dry-run", help="Preview changes without applying them"
    ),
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
    preview = format_preview(record.partij_code, record.product_naam, changes, dry_run)
    logger.info(preview)
    typer.echo(preview)

    # Apply changes if not dry run
    if not dry_run:
        # Create correction command
        command = CorrectSpacingRecord.from_record(record)
        if wdz1 is not None:
            command.aantal_tafels_na_wdz1 = wdz1
        if wdz2 is not None:
            command.aantal_tafels_na_wdz2 = wdz2

        if not send_spacing_correction(command, dry_run):
            raise typer.Exit(code=1)


@app.command(name="fix-spacing-errors")
def fix_spacing_errors(
    error_type: str = typer.Option(..., "--error", "-e", help="Error type to fix"),
    log_file: Optional[Path] = typer.Option(
        None, "--log", "-l", help="Path to log file for manual review cases"
    ),
    dry_run: bool = typer.Option(
        True, "--dry-run/--no-dry-run", help="Preview changes without applying them"
    ),
):
    """Fix spacing errors of a specific type."""
    logger.info(f"Retrieving spacing records with error type: {error_type}")
    repository = SpacingRepository()
    error_records = [
        r
        for r in repository.get_error_records()
        if error_type.lower() in r.wijderzet_registratie_fout.lower()
    ]

    if not error_records:
        msg = f"No records found with error matching: {error_type}"
        logger.info(msg)
        typer.echo(msg)
        return

    logger.info(f"Found {len(error_records)} records to process")

    # Set up manual review logging if needed
    manual_review_logger = setup_manual_review_logger(log_file) if log_file else None

    # Process records
    fixed = 0
    manual_review = 0

    for record in error_records:
        # Handle missing WDZ2 date errors
        if "Geen wdz2 datum, maar wel tafel aantal na wdz 2" in record.wijderzet_registratie_fout:
            fix_command = FixMissingWdz2DateCommand.from_record(record)
            if fix_command.can_fix_automatically():
                correction = fix_command.get_correction()
                if correction:
                    preview = format_preview(
                        record.partij_code,
                        record.product_naam,
                        f"Move WDZ2 count ({record.aantal_tafels_na_wdz2}) to WDZ1, clear WDZ2",
                        dry_run,
                    )
                    logger.info(preview)
                    typer.echo(preview)

                    if send_spacing_correction(correction, dry_run, manual_review_logger):
                        fixed += 1
                    else:
                        manual_review += 1
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
