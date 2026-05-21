# Smoke-test template

Goes in `tests/web/test_<x>.py`. The `user` fixture in `tests/web/conftest.py` already starts the NiceGUI app — just import it.

## Minimal smoke test

```python
"""Tests for the <x> web page."""

from unittest.mock import Mock, patch

from nicegui.testing import User

from production_control.<x>.models import <ModelName>


async def test_<x>_page_shows_table(user: User) -> None:
    """List page renders with rows from the repository."""
    with patch(
        "production_control.web.pages.<x>.<ModelName>Repository"
    ) as mock_repo_class:
        mock_repo = Mock()
        mock_repo_class.return_value = mock_repo
        mock_repo.get_paginated.return_value = (
            [
                <ModelName>(
                    <pk>=<sample_pk>,
                    # ...fill in required (non-Optional) fields...
                ),
            ],
            1,  # total count
        )

        await user.open("/<route>")

        # Loose check — any value from the sample row.
        await user.should_see("<value_from_sample_row>")


async def test_<x>_detail_page_shows_record(user: User) -> None:
    """Detail page fetches by PK and renders the model."""
    with patch(
        "production_control.web.pages.<x>.<ModelName>Repository"
    ) as mock_repo_class:
        mock_repo = Mock()
        mock_repo_class.return_value = mock_repo
        mock_repo.get_by_id.return_value = <ModelName>(
            <pk>=<sample_pk>,
            # ...required fields...
        )

        await user.open("/<route>/<sample_pk>")

        await user.should_see("<value_from_record>")
        await user.should_see("← Terug naar <Dutch page title>")


async def test_<x>_detail_page_handles_missing_record(user: User) -> None:
    """Detail page shows error when the PK doesn't resolve."""
    with patch(
        "production_control.web.pages.<x>.<ModelName>Repository"
    ) as mock_repo_class:
        mock_repo = Mock()
        mock_repo_class.return_value = mock_repo
        mock_repo.get_by_id.return_value = None

        await user.open("/<route>/<nonexistent_pk>")

        await user.should_see("Record niet gevonden")
        await user.should_see("← Terug naar <Dutch page title>")
```

The third test is optional but recommended — it costs almost nothing and covers the only edge case the detail page actually handles (record not found).

## Where to patch

Always patch at the page-module path:

```python
patch("production_control.web.pages.<x>.<ModelName>Repository")
```

NOT at the origin (`production_control.<x>.repositories.<ModelName>Repository`). The page module imports the class by name, so the binding lives in the page module's namespace, and that's what `Mock` needs to intercept.

## Stronger column-level assertion (when you need it)

`test_products.py` is the reference if you want to assert the exact column set and row data. It's more precise but more brittle — adding a column to the model breaks it. Use this when the test's job is to lock down the contract, not just smoke the page.

```python
from nicegui import ui

table = user.find(ui.table).elements.pop()
assert table.columns == [
    {"name": "naam", "label": "Artikel", "field": "naam", "sortable": True},
    {"name": "actions", "label": "Acties", "field": "actions"},
]
assert table.rows == [
    {"id": <sample_pk>, "naam": "<sample_value>"},
]
```

## Testing filter flow

When the user wants to verify that typing in the search box reaches the repository, copy the pattern from `test_products.py::test_products_page_filtering_calls_repository`. It uses an `asyncio.Event` to wait for the debounced `get_paginated` call, then asserts on the kwargs. Don't write this for a first-pass smoke test — only when the filter behavior is something the page is specifically responsible for.

## Running the test

```bash
uv run pytest tests/web/test_<x>.py -v
```

If everything's wired correctly, the list test takes a second or two (NiceGUI spin-up) and asserts pass. Failures here are almost always one of:

- **`AttributeError` on a field** during `<ModelName>(...)` construction — the model has a non-Optional field you didn't supply in the test fixture.
- **`404` from `user.open(...)`** — the router wasn't registered in `web/startup.py`, or the prefix doesn't match what you typed in the test.
- **Mock not intercepted** — patched at the wrong path; check it's `production_control.web.pages.<x>.<ModelName>Repository`.
- **PK type mismatch in detail route** — `/{<pk>}` was typed as `int` but the model's PK is `str`, or vice versa. Match the model.
