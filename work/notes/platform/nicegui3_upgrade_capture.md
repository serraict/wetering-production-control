# NiceGUI 3 upgrade — capture (2026-11-18)

## Why

Photo upload on the scan page failed in production with
`'UploadEventArguments' object has no attribute 'name'`. Production ran
NiceGUI **3.14.0** while `uv.lock` pinned **2.19.0**: `Dockerfile.base` did
`uv pip install -r pyproject.toml`, which ignores the lock and resolves the
newest releases each time the base image is rebuilt. Tests and production
had silently drifted apart (also FastAPI 0.115 → 0.16x, Starlette 0.46 → 1.x).

## What changed

- `pyproject.toml`: `nicegui>=3.14,<4`; `uv.lock` pinned to exactly 3.14.0
  (what production runs), so no behaviour change for production.
- `Dockerfile.base`: `uv sync --frozen --no-dev --no-install-project` —
  the base image now installs exactly the lock.
- Upload handler uses the 3.x API (`e.file.name`, `await e.file.read()`).

## Surprises in the NiceGUI 3 test plugin

- Needs `main_file = ""` in pytest ini options, else it looks for `main.py`.
- After each test the `user` fixture pops every module that defined a page,
  *and all parent packages* (incl. `production_control`), from
  `sys.modules`. With our `startup()`-based registration that left routes
  calling old page modules while `patch()` hit fresh copies, and broke
  SQLAlchemy's lookup of our Dremio dialect by module path.
  `tests/web/conftest.py` restores the popped modules after teardown.
- Module-level `@ui.refreshable`s keep targets from discarded test clients
  → "The client this element belongs to has been deleted" in the next test.
  The conftest clears those targets after each test.

## Deferred

- Module-level `server_side_paginated_table` / `_messages_block`
  refreshables are shared by all browser sessions: one user's `.refresh()`
  re-renders every connected user's table/thread (each with its own args, so
  mostly just wasted work). Worth making per-client at some point.
- NiceGUI 4.0 is out; upgrade deliberately later.
