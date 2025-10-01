"""Common style classes for the application."""

from nicegui import ui

# Common style classes
CARD_CLASSES = "w-full mx-auto p-4 shadow-lg"
HEADER_CLASSES = "text-2xl font-bold text-primary"
SUBHEADER_CLASSES = "text-lg text-gray-600"
LABEL_CLASSES = "font-bold text-secondary"
VALUE_CLASSES = ""
LINK_CLASSES = "text-accent hover:text-secondary"
NAV_CARD_CLASSES = "w-64 p-4 hover:shadow-lg transition-shadow"
MENU_LINK_CLASSES = "text-white hover:text-secondary transition-colors"


def add_print_styles(
    font_size: str = "7px",
    orientation: str = "portrait",
    margin: str = "0.3in",
    remove_borders: bool = True,
) -> None:
    """Add print-friendly CSS styles to the current page.

    Args:
        font_size: Font size for printed tables (default: "7px")
        orientation: Page orientation "portrait" or "landscape" (default: "portrait")
        margin: Page margins (default: "0.3in")
        remove_borders: Whether to remove borders from cards and items (default: True)
    """
    border_styles = ""
    if remove_borders:
        border_styles = """
        /* Remove borders from cards and items when printing */
        .q-card {
            border: none !important;
            box-shadow: none !important;
        }

        .q-item {
            border: none !important;
        }

        /* Remove any additional borders that might appear */
        .q-table__container,
        .q-table__middle,
        .q-page,
        .q-page-container {
            border: none !important;
            box-shadow: none !important;
        }
"""

    css = f"""
    <style>
    @media print {{
        /* Hide navigation and non-essential elements */
        .q-layout__section--marginal,
        .q-header,
        .q-footer,
        .q-page-sticky,
        .print-hide {{
            display: none !important;
        }}
{border_styles}

        /* Ensure table uses full width and wraps properly */
        .q-table {{
            width: 100% !important;
            max-width: none !important;
            overflow: visible !important;
            font-size: {font_size} !important;
        }}

        .q-table__container {{
            overflow: visible !important;
            max-height: none !important;
        }}

        .q-table__middle {{
            overflow: visible !important;
        }}

        /* Force table to break across pages if needed */
        .q-table thead {{
            display: table-header-group !important;
        }}

        .q-table tbody {{
            display: table-row-group !important;
        }}

        /* Ensure columns don't shrink too much */
        .q-table th,
        .q-table td {{
            white-space: nowrap !important;
            padding: 1px 2px !important;
            min-width: auto !important;
        }}

        /* Hide actions column when printing */
        .q-table th:last-child,
        .q-table td:last-child {{
            display: none !important;
        }}

        /* Alternative: Target specifically by header text */
        .q-table th:contains("Acties"),
        .q-table th:contains("Actions") {{
            display: none !important;
        }}

        /* Hide the corresponding table cells in the actions column */
        .q-table tr td:nth-last-child(1) {{
            display: none !important;
        }}

        /* Page setup */
        @page {{
            size: A4 {orientation};
            margin: {margin};
        }}

        body {{
            print-color-adjust: exact !important;
        }}
    }}
    </style>
    """

    ui.add_head_html(css)
