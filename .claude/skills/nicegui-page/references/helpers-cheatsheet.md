# Helpers cheatsheet

Quick reference for the components under `src/production_control/web/components/`. The list and detail helpers do a lot — knowing what they handle vs. what you have to handle yourself saves rework.

## `display_model_list_page(...)`

Renders: a card with a title row + filter input + standard sortable/paginated table + row-action icon column.

| Parameter | Type | Notes |
|---|---|---|
| `repository` | any | Must have `get_paginated(pagination=..., filter_text=...)` returning `(items, total)`. Provided by `DremioRepository[T]`. |
| `model_cls` | `Type[SQLModel]` | Field metadata (`sa_column_kwargs["info"]`) drives column headers, sortability, and visibility (`ui_hidden`). |
| `table_state_key` | `str` | Unique per page. Stores sort, filter, current page in client storage so the user keeps their place. |
| `title` | `str` | Currently still required despite the code comment saying "to do: remove". |
| `row_actions` | `dict` | `{name: {"icon": ..., "handler": ...}}`. See "Row actions" below. |
| `card_width` | `str` | Tailwind max-width, e.g. `"max-w-5xl"`. Leave default unless the table is sparse. |
| `filter_placeholder` | `str` | Search box placeholder. Default "Zoek …". |
| `custom_filters` | `Callable[[ui.row], None]` | Extra UI rendered next to the filter input. |
| `custom_load_data` | `Callable[[repo, state], Callable]` | Replaces the default load function — needed for pages with extra filter kwargs (see `inspectie.py`). |
| `enable_fullscreen` | `bool` | Adds an expand-to-fullscreen toggle on the table. |
| `columns` | `List[str] \| None` | Restrict to these columns. Default: every non-hidden field from the model. |

## `display_model_detail_page(...)`

Renders: a back link, then either the model card or a custom display, with a "Record niet gevonden" branch when `model is None`.

| Parameter | Notes |
|---|---|
| `model` | The record, or `None`. |
| `title` | Frame title (the page-frame caller is separate; this is shown inside the card). |
| `back_link_text` | The "← Terug naar …" link. |
| `back_link_url` | Where the back link goes. |
| `model_title_field` | Optional attribute name used as the card title. Default: `str(model)`. |
| `custom_display_function` | Renders the record yourself instead of using `display_model_card`. |

## `create_model_view_action(...)`

Builds the dict for the row's eye-icon action. Two modes:

```python
# Opens a dialog with the record (lightweight)
create_model_view_action(repository=repo, dialog=True)

# Navigates to a detail URL (bookmarkable)
create_model_view_action(repository=repo, dialog=False, detail_url="/<route>/{id}")
```

Both accept `id_field` (default `"id"`) and `custom_display_function`. The handler reads the row's PK from `e.args["key"]`.

## `display_model_card(model, title=...)`

Lays out the model's fields in a card using each field's `title` and `description` from `sa_column_kwargs["info"]`. Used inside both the detail page and the dialog opened by the view action.

## `frame("<title>")`

Context manager that wraps the page in the standard header (menu, scan button, account icon) and main column. Every page body goes inside one. The title shows in the top bar.

## Things the helpers do NOT handle

- **Mutations.** No create/update/delete UI. For edits, build a Pydantic command + `create_command_form(...)` and a custom row action (see `spacing.py`).
- **Real-time updates.** Tables are loaded on request, not pushed. If the user wants live data, you'll need a manual refresh button or `ui.timer`.
- **File uploads / downloads.** The label-printing action in `potting_lots.py` is a working pattern for "row action that produces a file."
- **Auth / role gating.** The frame shows the current user but doesn't restrict pages. If a page should be admin-only, add the check yourself at the top of the page function.

## Common props on the underlying components

When you do reach past the helpers (e.g. building a custom display), these props/classes show up everywhere:

- Cards: `ui.card().classes("w-full p-4")` or `CARD_CLASSES` from `styles.py`.
- Header text: `ui.label(...).classes(HEADER_CLASSES)` ("text-2xl font-bold text-primary").
- Links: `ui.link(...).classes(LINK_CLASSES)` ("text-accent hover:text-secondary").
- Dialog: `with ui.dialog() as dialog, ui.card(): ...; dialog.open()`.
- Notifications: `ui.notify("...", type="positive" | "negative" | "warning")`.
- Navigation: `ui.navigate.to("/path")` — prefer `router.url_path_for("view_name", id=...)` when crossing routes within the same module (see `feedback_url_construction` memory).
