# Full page-module template

Annotated version of what to write into `src/production_control/web/pages/<x>.py`. Based on `web/pages/spacing.py` (without the edit form) and `web/pages/products.py`. Copy and adapt.

## Minimal list + detail page

```python
"""<X> page implementation."""

from nicegui import APIRouter

from ...<x>.repositories import <ModelName>Repository
from ...<x>.models import <ModelName>
from ..components import frame
from ..components.model_detail_page import display_model_detail_page, create_model_view_action
from ..components.model_list_page import display_model_list_page


router = APIRouter(prefix="/<route>")


def get_repository() -> <ModelName>Repository:
    """Per-request repository instance — avoids session caching issues."""
    return <ModelName>Repository()


@router.page("/")
def <x>_page() -> None:
    """Overview page — sortable, filterable, paginated table."""
    row_actions = {
        "view": create_model_view_action(
            repository=get_repository(),
            id_field="<pk>",      # only override when PK isn't called "id"
            dialog=True,          # eye icon opens a record in a dialog
        ),
    }

    with frame("<Dutch page title>"):
        display_model_list_page(
            repository=get_repository(),
            model_cls=<ModelName>,
            table_state_key="<x>_table",
            title="<Dutch page title>",  # currently still required (see helpers cheatsheet)
            row_actions=row_actions,
        )


@router.page("/{<pk>}")
def <x>_detail(<pk>: <pk_type>) -> None:
    """Detail page — bookmarkable URL with the back link."""
    record = get_repository().get_by_id(<pk>)

    with frame("<Dutch detail title>"):
        display_model_detail_page(
            model=record,
            title="<Dutch detail title>",
            back_link_text="← Terug naar <Dutch page title>",
            back_link_url="/<route>",
        )
```

## Variants

### Navigate instead of dialog for the row action

When the record is big enough that a dialog feels cramped, drop the dialog and link to the detail URL:

```python
"view": create_model_view_action(
    repository=get_repository(),
    dialog=False,
    detail_url="/<route>/{id}",
),
```

The `{id}` placeholder is literal — `create_model_view_action` does the substitution with the row's `key`.

### Custom display function

When the standard model card isn't enough — extra buttons, conditional warnings, related records — pass a `custom_display_function`:

```python
def show_<x>(record: <ModelName>) -> None:
    from ..components.model_card import display_model_card

    if record.<some_field> == "warning":
        with ui.card().classes("mb-4 bg-warning bg-opacity-10"):
            ui.label("Let op").classes("text-lg font-bold")
            ui.label("...")

    display_model_card(record, title=str(record))


@router.page("/")
def <x>_page() -> None:
    repo = get_repository()
    row_actions = {
        "view": create_model_view_action(
            repository=repo,
            custom_display_function=show_<x>,
        ),
    }
    with frame("<Dutch page title>"):
        display_model_list_page(
            repository=repo,
            model_cls=<ModelName>,
            table_state_key="<x>_table",
            title="<Dutch page title>",
            row_actions=row_actions,
        )


@router.page("/{<pk>}")
def <x>_detail(<pk>: <pk_type>) -> None:
    record = get_repository().get_by_id(<pk>)
    with frame("<Dutch detail title>"):
        display_model_detail_page(
            model=record,
            title="<Dutch detail title>",
            back_link_text="← Terug naar <Dutch page title>",
            back_link_url="/<route>",
            custom_display_function=show_<x>,  # reuse the same renderer
        )
```

### Multiple row actions

`row_actions` is a dict — keys become CSS-ish marker names, values are `{"icon": ..., "handler": ...}` dicts. Each row gets the icons in the order listed.

```python
row_actions = {
    "view": create_model_view_action(repository=repo, ...),
    "edit": create_edit_action(repo),                          # custom — see spacing.py
    "label": potting_lot_label_printer.create_label_action(),  # domain-specific
}
```

For "view" and "edit" the helpers exist; for one-off actions, build the dict by hand:

```python
def my_action() -> Dict[str, Any]:
    def handle(e: Dict[str, Any]) -> None:
        id_value = e.args.get("key")  # the row's PK
        # do something...
    return {"icon": "rocket_launch", "handler": handle}
```

## Less-used parameters

`display_model_list_page` accepts a few extras that are worth knowing about but rarely needed on a first pass:

- **`card_width="max-w-5xl"`** — narrows the card. Use only if the model has few columns and a full-width table looks empty.
- **`enable_fullscreen=True`** — adds an expand-to-fullscreen button on the table. Useful for dense data the user wants to read without distractions.
- **`columns=["id", "naam", "datum"]`** — show only these columns in the list, regardless of `ui_hidden`. Lets you keep one model that drives multiple views with different column sets.
- **`custom_filters=lambda row: ...`** — extra filter UI rendered to the left of the search box. The `inspectie.py` page is the reference for adding date-range pickers, presets, etc.
- **`custom_load_data=...`** — replace the default load function entirely. Needed when paging requires kwargs the standard signature doesn't support (e.g. date filters in `inspectie.py`).

If the user asks for "filter by date" or "show only the last N", reach for `custom_filters` + `custom_load_data` together. Read `web/pages/inspectie.py` for the working pattern.
