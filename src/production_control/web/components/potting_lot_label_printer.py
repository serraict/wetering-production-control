"""Label printing functionality for potting lots."""

import logging
from typing import Dict, Any
from datetime import date

from nicegui import ui, run

from ...potting_lots.models import PottingLot
from ...potting_lots.label_generation import LabelGenerator
from .table_state import ClientStorageTableState

logger = logging.getLogger(__name__)


def _generate_labels_in_background(records) -> str:
    """Generate PDF labels for records in a background process.

    This function creates a new LabelGenerator instance to avoid pickling issues.

    Args:
        records: List of PottingLot records or single PottingLot record

    Returns:
        Path to the generated PDF file
    """
    label_generator = LabelGenerator()
    return label_generator.generate_pdf(records)


def create_label_action(table_state_key: str) -> Dict[str, Any]:
    """Create a label action for individual potting lots."""

    async def handle_label(e: Dict[str, Any]) -> None:
        id_value = e.args.get("key")
        table_state = ClientStorageTableState.initialize(table_state_key)
        record = next(
            (PottingLot(**row) for row in table_state.rows if row["id"] == id_value), None
        )

        if record:
            # Create a descriptive filename, this is used for the downloaded file for the user
            filename = f"oppotpartij_{record.id}_{record.naam.replace(' ', '_')}.pdf"
            ui.notify("Generating label...")

            try:
                pdf_path = await run.cpu_bound(_generate_labels_in_background, record)
                ui.download(pdf_path, filename=filename)
                # Clean up the PDF file after download
                label_generator = LabelGenerator()
                label_generator.cleanup_pdf(pdf_path)
            except Exception as e:
                msg = f"Error generating label: {str(e)}"
                logger.error(msg)
                ui.notify(msg)

    return {
        "icon": "print",
        "tooltip": "Druk 2 labels af voor deze partij",
        "handler": handle_label,
    }


async def print_all_labels(table_state_key: str) -> None:
    """Print labels for all visible potting lots."""
    table_state = ClientStorageTableState.initialize(table_state_key)

    records = [PottingLot(**visible_row) for visible_row in table_state.rows]

    if not records:
        return

    ui.notify("Generating labels...")

    try:
        # Generate labels in background process
        pdf_path = await run.cpu_bound(_generate_labels_in_background, records)

        # Download and cleanup
        filename = f"oppotpartijen_{date.today():%gW%V-%u}.pdf"
        ui.download(pdf_path, filename=filename)
        # Clean up the PDF file after download
        label_generator = LabelGenerator()
        label_generator.cleanup_pdf(pdf_path)

    except Exception as e:
        msg = f"Error generating labels: {str(e)}"
        logger.error(msg)
        ui.notify(msg)
