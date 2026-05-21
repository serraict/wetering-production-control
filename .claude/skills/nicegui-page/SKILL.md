---
name: nicegui-page
description: Build a NiceGUI list+detail page in src/production_control/web/pages/ on top of an existing SQLModel + DremioRepository (usually one produced by the dremio-sqlmodel skill). Wires the router into web/startup.py, adds a menu entry in web/components/menu.py, and writes a smoke test under tests/web/. Use this skill whenever the user wants to surface a model in the web UI — "make a page for X", "add a screen for the Y data", "I want to browse the Z table in the app", "expose this repository as a list", "wire up a NiceGUI page for the new model" — even if they don't explicitly say "list page" or "NiceGUI". If a Dremio source is mentioned but no model/repo exists yet, run the dremio-sqlmodel skill first, then come back to this one.
---

# NiceGUI page from a SQLModel + Repository

This skill turns an existing `SQLModel` + `DremioRepository[T]` pair into a working list page (sortable table + search + paging) and a detail page (dialog from the list row + dedicated URL). It also handles the three pieces of plumbing that are easy to forget: registering the router, adding a menu item, and writing a smoke test.

It is the natural follow-up to `dremio-sqlmodel`. If the user is starting from a Dremio source and there's no model yet, do that skill first.

## When to apply

- "Add a page for the new spacing view."
- "I want a screen where I can browse the inspectie records."
- "Wire up the X repository in the web UI."
- "Make this model visible in the app."
- The user has just finished modeling a Dremio source and asks "what's next?" — building the page is almost always next.

If the user wants something fundamentally different (a dashboard with charts, a form-only page with no list, a mobile-optimized scan flow), the helpers here aren't a great fit — fall back to building the page from scratch, but still register the router and add the menu item the same way.

## Files you'll touch

For a domain `<x>` (snake_case, matches the folder under `src/production_control/<x>/`):

1. **`src/production_control/web/pages/<x>.py`** — new file. The list and detail page bodies.
2. **`src/production_control/web/pages/__init__.py`** — add `<x>` to the imports and `__all__`.
3. **`src/production_control/web/startup.py`** — `app.include_router(<x>.router)`.
4. **`src/production_control/web/components/menu.py`** — `ui.menu_item("<Dutch label>", lambda: ui.navigate.to("/<route>"))`.
5. **`tests/web/test_<x>.py`** — new file. One list-page test, one detail-page test.

## Workflow

### 1. Confirm the model and repo exist

Open `src/production_control/<x>/models.py` and `src/production_control/<x>/repositories.py`. You need:

- A `SQLModel` class with `table=True` and `sa_column_kwargs={"info": {...}}` field metadata (the list-page helper reads this to render the table).
- A repository class extending `DremioRepository[T]` with `get_paginated(...)` and `get_by_id(...)`.

If either is missing, stop and run `dremio-sqlmodel` (or write them by hand following its patterns). The page helpers depend on the contract those classes provide.

While you're here, note:
- The primary key field name and type (`id: int`, `code: str`, `partij_code: str`, etc.). The detail route's path parameter must match.
- Whether the model defines `__str__` — `display_model_detail_page` uses it for the title when no `model_title_field` is given.

### 2. Write the page module

Start from the leanest template — `web/pages/spacing.py` minus the edit/correction code, or `web/pages/products.py`. The full annotated example is in `references/page-template.md`; the short version:

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
    # Fresh per-request instance — repositories aren't thread-safe to share.
    return <ModelName>Repository()


@router.page("/")
def <x>_page() -> None:
    row_actions = {
        "view": create_model_view_action(
            repository=get_repository(),
            id_field="<pk>",          # default "id" — only set if PK is something else
            dialog=True,              # eye icon opens a dialog with the record
            # dialog=False, detail_url="/<route>/{id}"  # navigate instead of dialog
        ),
    }

    with frame("<Dutch page title>"):
        display_model_list_page(
            repository=get_repository(),
            model_cls=<ModelName>,
            table_state_key="<x>_table",     # unique key; persists sort/filter/page
            title="<Dutch page title>",      # legacy parameter, still required
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
        )
```

A few small but important conventions:

- **Route prefix mirrors the URL the user types**, kebab-case where the domain is multi-word: `/potting-lots`, `/bulb-picking`, `/inspectie`. Pick the most natural Dutch noun.
- **`table_state_key` must be unique across pages** — it's the key for client-side pagination/filter state. `"<x>_table"` is the convention.
- **The legacy `title=` parameter on `display_model_list_page` is required** even though the file annotates it as "to do: remove". Don't skip it.
- **Dialog vs. dedicated detail URL.** Most pages use both: `dialog=True` for the row eye-icon (quick peek), plus a `/{id}` route for bookmarkable/linkable detail. The dialog uses `display_model_card`; the dedicated route uses `display_model_detail_page`. Wire both unless the user says otherwise.
- **`get_by_id` parameter type** — int IDs come through the path as int because of the type hint (`def <x>_detail(id: int)`). String PKs come through as str. Match what the model says.

### 3. Register the router

Edit `src/production_control/web/pages/__init__.py` — add `<x>` to the import list and `__all__`:

```python
from . import home, products, spacing, bulb_picklist, potting_lots, scan, <x>

__all__ = [..., "<x>"]
```

Edit `src/production_control/web/startup.py` — add `app.include_router(<x>.router)` in the same block as the others. Order doesn't matter functionally; keep it grouped with the data-page routers.

### 4. Add a menu item

Edit `src/production_control/web/components/menu.py`. Add a line in the main `ui.menu()` block:

```python
ui.menu_item("<Dutch label>", lambda: ui.navigate.to("/<route>"))
```

Dutch label, sentence case. Match the page title for consistency unless the user specifies otherwise. Less-frequent or admin-y pages can nest under the "Info" submenu — follow the existing structure.

### 5. Write a smoke test

`tests/web/conftest.py` already provides the `user` fixture (a NiceGUI `User` that auto-starts the app). Use it to assert the page renders and the table is populated. Pattern in `references/test-template.md`; minimal shape:

```python
"""Tests for the <x> web page."""

from unittest.mock import Mock, patch
from nicegui.testing import User

from production_control.<x>.models import <ModelName>


async def test_<x>_page_shows_table(user: User) -> None:
    """List page renders the table with rows from the repository."""
    with patch("production_control.web.pages.<x>.<ModelName>Repository") as mock_repo_class:
        mock_repo = Mock()
        mock_repo_class.return_value = mock_repo
        mock_repo.get_paginated.return_value = (
            [<ModelName>(<pk>=<sample_pk>, ...)],
            1,
        )

        await user.open("/<route>")

        await user.should_see("<a value from the sample row>")


async def test_<x>_detail_page_shows_record(user: User) -> None:
    """Detail page renders fields of the fetched record."""
    with patch("production_control.web.pages.<x>.<ModelName>Repository") as mock_repo_class:
        mock_repo = Mock()
        mock_repo_class.return_value = mock_repo
        mock_repo.get_by_id.return_value = <ModelName>(<pk>=<sample_pk>, ...)

        await user.open("/<route>/<sample_pk>")

        await user.should_see("<a value from the record>")
        await user.should_see("← Terug naar <Dutch page title>")
```

Why these two:

- **List test** proves the page mounts, the helper reads the model's field metadata, and the table renders. If the model is wrong (missing fields, bad annotations), this test catches it.
- **Detail test** proves the route accepts the right PK type and the model card renders fields. Together, list + detail covers ~90% of breakage from the page wiring.

Patch the repository at the page-module path (`production_control.web.pages.<x>.<ModelName>Repository`), not at its origin. That's the binding the page module looks up.

Use `should_see` for value text and link text rather than asserting on `ui.table.rows`/`columns` directly — it's less brittle when columns get added or renamed. The `test_products.py` file has the column-level pattern if you need it for a richer test later, but for a smoke test keep it loose.

### 6. Run the test and exercise the page

```bash
uv run pytest tests/web/test_<x>.py -v
```

If the dev server is running on port 7901, hit the new route in the browser and click the eye icon to confirm the dialog works. If it isn't running, start it the way the project normally does (or just say so to the user and let them poke at it).

### 7. Tell the user what you did

Recap: the four files touched, the route, the menu label, and any small judgment calls (which fields default-visible vs hidden — though those live on the model, not the page; whether you used `dialog=True` or navigation for the row action; whether you nested the menu item under Info).

## What not to do

- **Don't reach past the helpers** for routine list/detail work. `display_model_list_page` already handles search, pagination, sorting, row actions, and storage of filter state. If you find yourself writing a `ui.table(...)` call from scratch, ask whether the helper would do — usually it would, and you're adding maintenance debt.
- **Don't share repository instances across requests.** Use `get_repository()` style and create per-request. NiceGUI page functions run per-connection; the engine is reused, the repository wrapper isn't.
- **Don't hardcode URL strings inside the page** when one route needs to link to another. Use `router.url_path_for("<view_name>", id=...)`. See the `feedback_url_construction` memory.
- **Don't write the page without the menu item.** Pages that aren't menu-linked get rediscovered awkwardly. If the user wants a hidden page, ask explicitly.
- **Don't introduce a Pydantic command form, dialog flow, or custom display function** unless the user asks. They're worthwhile patterns (see `spacing.py` for an edit form, `inspectie.py` for storage-backed dialogs) but they belong in a separate iteration — smoke first, polish second.
- **Don't skip the smoke test.** It's three minutes of typing and catches the dumb wiring breaks (wrong import path, missing router registration, PK type mismatch) before the user clicks the link.

## References

- `references/page-template.md` — full annotated example with the dialog-vs-navigation choice, custom display function, and notes on `card_width` / `enable_fullscreen` / `columns`.
- `references/test-template.md` — the smoke-test pattern, plus the richer column/row-assertion pattern from `test_products.py` for when you want stronger coverage.
- `references/helpers-cheatsheet.md` — what `display_model_list_page`, `display_model_detail_page`, `create_model_view_action`, `display_model_card` do at a glance, including the parameters that are noted "to do: remove" but are currently still required.
