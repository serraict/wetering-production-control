"""Test configuration and fixtures."""

import sys
from typing import Generator

import pytest
from nicegui.functions.refreshable import refreshable
from nicegui.testing import User


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_teardown(item: pytest.Item) -> Generator[None, None, None]:
    """Undo NiceGUI 3's module purge after each test.

    On teardown, the `user` fixture pops every module that defined a page
    (and all its parent packages, including `production_control`) from
    `sys.modules`, expecting a `main.py` to re-import them. We register pages
    via `startup()` instead, so a half-purged package leaves routes pointing
    at the old page modules while `patch("production_control.web.pages...")`
    targets fresh copies — and SQLAlchemy can no longer resolve our dialect
    by module path. Restoring the popped modules keeps one consistent copy.
    """
    before = dict(sys.modules)
    yield
    for name, module in before.items():
        sys.modules.setdefault(name, module)
    _forget_refreshable_targets()


def _forget_refreshable_targets() -> None:
    """Drop targets that module-level `@ui.refreshable`s kept from this test.

    The fixture discards clients without marking their elements deleted, so
    `refreshable.prune()` keeps them, and the next test's `.refresh()` fails
    with "The client this element belongs to has been deleted".
    """
    for name, module in list(sys.modules.items()):
        if not name.startswith("production_control.web"):
            continue
        for value in vars(module).values():
            if isinstance(value, refreshable):
                value.targets.clear()


@pytest.fixture
def user(user: User) -> Generator[User, None, None]:
    """Initialize NiceGUI for testing."""
    from production_control.web.startup import startup

    startup()
    yield user
