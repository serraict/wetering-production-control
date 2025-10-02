"""Tests for data table components."""

from unittest.mock import Mock
from nicegui import ui
from nicegui.testing import User

from production_control.web.components.data_table import server_side_paginated_table
from production_control.web.components.table_state import ClientStorageTableState
from production_control.inspectie.models import InspectieRonde


async def test_server_side_paginated_table_without_fullscreen(user: User) -> None:
    """Test that table renders without fullscreen button by default."""

    # Given
    mock_state = Mock(spec=ClientStorageTableState)
    mock_state.rows = []
    mock_state.pagination = Mock()
    mock_state.pagination.to_dict.return_value = {"rowsPerPage": 10}

    # When
    @ui.page("/test")
    def test_page():
        server_side_paginated_table(
            cls=InspectieRonde,
            state=mock_state,
            on_request=lambda e: None,
            row_actions={},
            enable_fullscreen=False,
        )

    await user.open("/test")

    # Then - Table should be present but no fullscreen button
    table = user.find(ui.table)
    assert table.elements  # Table exists
    # Should not have fullscreen button - no buttons should be present
    try:
        user.find(ui.button)
        assert False, "Expected no buttons but found some"
    except AssertionError as e:
        if "expected to find at least one" in str(e):
            pass  # This is expected - no buttons should be found
        else:
            raise


async def test_server_side_paginated_table_with_fullscreen(user: User) -> None:
    """Test that table renders with fullscreen button when enabled."""

    # Given
    mock_state = Mock(spec=ClientStorageTableState)
    mock_state.rows = []
    mock_state.pagination = Mock()
    mock_state.pagination.to_dict.return_value = {"rowsPerPage": 10}

    # When
    @ui.page("/test")
    def test_page():
        server_side_paginated_table(
            cls=InspectieRonde,
            state=mock_state,
            on_request=lambda e: None,
            row_actions={},
            enable_fullscreen=True,
        )

    await user.open("/test")

    # Then - Table should be present with fullscreen button
    table = user.find(ui.table)
    assert table.elements  # Table exists
    # Should have fullscreen button
    await user.should_see("Volledig scherm")
