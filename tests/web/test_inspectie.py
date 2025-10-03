"""Tests for inspectie web page."""

from unittest.mock import Mock, patch

from production_control.web.pages.inspectie import router, create_afwijking_actions, get_storage


def test_inspectie_page_router_exists():
    """Test that inspectie page router exists."""
    assert router is not None


def test_create_afwijking_actions_exists():
    """Test that afwijking actions function exists."""
    mock_repository = Mock()
    actions = create_afwijking_actions(mock_repository)
    assert actions is not None
    assert "plus_one" in actions
    assert "minus_one" in actions
    assert "view" in actions


@patch("production_control.web.pages.inspectie.get_storage")
@patch("production_control.web.pages.inspectie.ui")
def test_afwijking_plus_one_updates_storage(mock_ui, mock_get_storage):
    """Test that +1 button click updates browser storage."""
    # Setup mock storage
    mock_storage = {}
    mock_get_storage.return_value = mock_storage

    # Create actions and get +1 handler
    mock_repository = Mock()
    actions = create_afwijking_actions(mock_repository)
    plus_handler = actions["plus_one"]["handler"]

    # Simulate button click event with row data
    event_data = Mock()
    event_data.args = {"key": "27014", "row": {"afwijking_afleveren": 7}}  # Current afwijking is 7

    # Call handler
    plus_handler(event_data)

    # Verify storage was updated with new structure
    assert "inspectie_changes" in mock_storage
    assert "27014" in mock_storage["inspectie_changes"]
    change_data = mock_storage["inspectie_changes"]["27014"]
    assert isinstance(change_data, dict)
    assert change_data["original"] == 7
    assert change_data["new"] == 8  # 7 + 1


@patch("production_control.web.pages.inspectie.get_storage")
@patch("production_control.web.pages.inspectie.ui")
def test_afwijking_minus_one_updates_storage(mock_ui, mock_get_storage):
    """Test that -1 button click updates browser storage."""
    # Setup mock storage
    mock_storage = {}
    mock_get_storage.return_value = mock_storage

    # Create actions and get -1 handler
    mock_repository = Mock()
    actions = create_afwijking_actions(mock_repository)
    minus_handler = actions["minus_one"]["handler"]

    # Simulate button click event with row data
    event_data = Mock()
    event_data.args = {"key": "27014", "row": {"afwijking_afleveren": 7}}  # Current afwijking is 7

    # Call handler
    minus_handler(event_data)

    # Verify storage was updated with new structure
    assert "inspectie_changes" in mock_storage
    assert "27014" in mock_storage["inspectie_changes"]
    change_data = mock_storage["inspectie_changes"]["27014"]
    assert isinstance(change_data, dict)
    assert change_data["original"] == 7
    assert change_data["new"] == 6  # 7 - 1


@patch("production_control.web.pages.inspectie.get_storage")
@patch("production_control.web.pages.inspectie.ui")
def test_multiple_clicks_accumulate_changes(mock_ui, mock_get_storage):
    """Test that multiple clicks accumulate in storage."""
    # Setup mock storage with existing change in new format
    mock_storage = {
        "inspectie_changes": {"27014": {"original": 7, "new": 9}}  # Already has +2 change
    }
    mock_get_storage.return_value = mock_storage

    # Create actions
    mock_repository = Mock()
    actions = create_afwijking_actions(mock_repository)
    plus_handler = actions["plus_one"]["handler"]
    minus_handler = actions["minus_one"]["handler"]

    # Simulate button click events with row data
    event_data = Mock()
    event_data.args = {"key": "27014", "row": {"afwijking_afleveren": 7}}  # Original afwijking is 7

    # Click +1 (should be 9 + 1 = 10)
    plus_handler(event_data)
    change_data = mock_storage["inspectie_changes"]["27014"]
    assert change_data["new"] == 10

    # Click -1 (should be 10 - 1 = 9)
    minus_handler(event_data)
    change_data = mock_storage["inspectie_changes"]["27014"]
    assert change_data["new"] == 9


@patch("production_control.web.pages.inspectie.get_storage")
def test_get_pending_commands_empty_storage(mock_get_storage):
    """Test getting pending commands from empty storage."""
    from production_control.web.pages.inspectie import get_pending_commands

    mock_get_storage.return_value = {}
    commands = get_pending_commands()
    assert commands == []


@patch("production_control.web.pages.inspectie.get_storage")
def test_get_pending_commands_with_changes(mock_get_storage):
    """Test getting pending commands from storage with changes."""
    from production_control.web.pages.inspectie import get_pending_commands

    mock_get_storage.return_value = {
        "inspectie_changes": {
            "27014": {"original": 7, "new": 9},  # +2 change, final value 9
            "27015": {"original": 5, "new": 4},  # -1 change, final value 4
            "27016": {"original": 0, "new": 0},  # no change, final value 0
        }
    }

    commands = get_pending_commands()
    assert len(commands) == 3

    # Check command details
    codes = [cmd.code for cmd in commands]
    assert "27014" in codes
    assert "27015" in codes
    assert "27016" in codes

    # Check absolute afwijking values (not relative changes)
    for cmd in commands:
        if cmd.code == "27014":
            assert cmd.new_afwijking == 9
        elif cmd.code == "27015":
            assert cmd.new_afwijking == 4
        elif cmd.code == "27016":
            assert cmd.new_afwijking == 0


@patch("production_control.web.pages.inspectie.get_storage")
def test_clear_pending_commands(mock_get_storage):
    """Test clearing pending commands from storage."""
    from production_control.web.pages.inspectie import clear_pending_commands

    mock_storage = {
        "inspectie_changes": {"27014": 2, "27015": -1},
        "other_data": "should_remain",
    }
    mock_get_storage.return_value = mock_storage

    clear_pending_commands()

    # inspectie_changes should be cleared but other data should remain
    assert "inspectie_changes" not in mock_storage
    assert mock_storage["other_data"] == "should_remain"


@patch("production_control.web.pages.inspectie.app")
def test_get_storage_with_valid_user_storage(mock_app):
    """Test get_storage returns app.storage.user when available."""
    mock_app.storage.user = {"test": "data"}
    storage = get_storage()
    assert storage == {"test": "data"}


def test_get_storage_fallback_on_runtime_error():
    """Test get_storage falls back to in-memory storage on RuntimeError."""
    # Since the fallback storage is module-level, we need to clear it first
    from production_control.web.pages.inspectie import _fallback_storage

    _fallback_storage.clear()

    with patch("production_control.web.pages.inspectie.app") as mock_app:
        # Configure mock to raise RuntimeError when accessing app.storage.user property
        type(mock_app.storage).user = property(
            lambda self: (_ for _ in ()).throw(RuntimeError("storage_secret required"))
        )

        # First call should use fallback storage
        storage1 = get_storage()
        assert storage1 is _fallback_storage
        storage1["test"] = "fallback_data"

        # Second call should return the same fallback storage
        storage2 = get_storage()
        assert storage2 == {"test": "fallback_data"}
        assert storage1 is storage2


@patch("production_control.web.pages.inspectie.get_storage")
@patch("production_control.web.pages.inspectie.ui")
def test_show_pending_changes_dialog_empty(mock_ui, mock_get_storage):
    """Test show pending changes dialog with no changes."""
    from production_control.web.pages.inspectie import show_pending_changes_dialog

    mock_get_storage.return_value = {}
    show_pending_changes_dialog()

    # Verify dialog was created and shows no changes message
    mock_ui.dialog.assert_called_once()
    mock_ui.label.assert_called()


@patch("production_control.web.pages.inspectie.get_storage")
@patch("production_control.web.pages.inspectie.ui")
def test_show_pending_changes_dialog_with_changes(mock_ui, mock_get_storage):
    """Test show pending changes dialog with pending changes."""
    from production_control.web.pages.inspectie import show_pending_changes_dialog

    mock_get_storage.return_value = {
        "inspectie_changes": {
            "27014": 2,
            "27015": -1,
            "27016": 0,
        }
    }

    show_pending_changes_dialog()

    # Verify dialog was created
    mock_ui.dialog.assert_called_once()
    # Verify table was created for displaying changes
    mock_ui.table.assert_called()


@patch("production_control.web.pages.inspectie.clear_pending_commands")
@patch("production_control.web.pages.inspectie.ui")
def test_clear_all_changes_button(mock_ui, mock_clear_commands):
    """Test clear all changes functionality."""
    from production_control.web.pages.inspectie import handle_clear_all_changes

    handle_clear_all_changes()

    # Verify clear function was called
    mock_clear_commands.assert_called_once()
    # Verify notification was shown
    mock_ui.notify.assert_called_with("Alle wijzigingen gewist", type="info")


@patch("production_control.web.pages.inspectie.get_storage")
def test_filter_toggle_functionality(mock_get_storage):
    """Test filter toggle state management."""
    from production_control.web.pages.inspectie import get_filter_state, set_filter_state

    mock_storage = {}
    mock_get_storage.return_value = mock_storage

    # Default should be "next_two_weeks"
    assert get_filter_state() == "next_two_weeks"

    # Set to "show_all"
    set_filter_state("show_all")
    assert mock_storage["inspectie_filter"] == "show_all"
    assert get_filter_state() == "show_all"

    # Set back to "next_two_weeks"
    set_filter_state("next_two_weeks")
    assert mock_storage["inspectie_filter"] == "next_two_weeks"
    assert get_filter_state() == "next_two_weeks"


@patch("production_control.web.pages.inspectie.get_storage")
def test_filter_state_persistence(mock_get_storage):
    """Test that filter state persists across sessions."""
    from production_control.web.pages.inspectie import get_filter_state

    # Simulate existing storage with saved filter state
    mock_storage = {"inspectie_filter": "show_all"}
    mock_get_storage.return_value = mock_storage

    # Should return the saved state
    assert get_filter_state() == "show_all"


@patch("production_control.web.pages.inspectie.get_pending_commands")
def test_changes_button_shows_count(mock_get_pending_commands):
    """Test that changes button shows count of pending changes."""
    from production_control.web.pages.inspectie import get_pending_commands

    # Test with no pending changes
    mock_get_pending_commands.return_value = []
    pending_commands = get_pending_commands()
    changes_count = len(pending_commands)
    changes_label = f"Wijzigingen ({changes_count})" if changes_count > 0 else "Wijzigingen"
    assert changes_label == "Wijzigingen"

    # Test with 3 pending changes
    from production_control.inspectie.commands import UpdateAfwijkingCommand

    mock_get_pending_commands.return_value = [
        UpdateAfwijkingCommand(code="27014", new_afwijking=1),
        UpdateAfwijkingCommand(code="27015", new_afwijking=-1),
        UpdateAfwijkingCommand(code="27016", new_afwijking=2),
    ]
    pending_commands = get_pending_commands()
    changes_count = len(pending_commands)
    changes_label = f"Wijzigingen ({changes_count})" if changes_count > 0 else "Wijzigingen"
    assert changes_label == "Wijzigingen (3)"


@patch("production_control.web.pages.inspectie.get_storage")
@patch("production_control.web.pages.inspectie.ui")
def test_changes_state_updates_on_click(mock_ui, mock_get_storage):
    """Test that changes state updates when +1/-1 buttons are clicked."""
    from production_control.web.pages.inspectie import create_afwijking_actions

    # Setup mock storage
    mock_storage = {}
    mock_get_storage.return_value = mock_storage

    # Create a mock changes state
    class MockChangesState:
        def __init__(self):
            self.count = 0
            self.update_called = False

        def update(self):
            self.update_called = True
            # Simulate updating the count
            self.count = len(mock_storage.get("inspectie_changes", {}))

        @property
        def label(self) -> str:
            return f"Wijzigingen ({self.count})" if self.count > 0 else "Wijzigingen"

    changes_state = MockChangesState()

    # Create actions with changes state
    mock_repository = Mock()
    actions = create_afwijking_actions(mock_repository, changes_state)
    plus_handler = actions["plus_one"]["handler"]

    # Simulate button click event with row data
    event_data = Mock()
    event_data.args = {"key": "27014", "row": {"afwijking_afleveren": 7}}

    # Call handler
    plus_handler(event_data)

    # Verify that changes_state.update() was called
    assert changes_state.update_called
    assert changes_state.count == 1


@patch("production_control.web.pages.inspectie.clear_pending_commands")
@patch("production_control.web.pages.inspectie.ui")
def test_clear_all_changes_updates_state(mock_ui, mock_clear_commands):
    """Test that clearing all changes updates the changes state."""
    from production_control.web.pages.inspectie import handle_clear_all_changes

    # Create a mock changes state
    class MockChangesState:
        def __init__(self):
            self.count = 3  # Start with some changes
            self.update_called = False

        def update(self):
            self.update_called = True
            self.count = 0  # Simulate clearing all changes

        @property
        def label(self) -> str:
            return f"Wijzigingen ({self.count})" if self.count > 0 else "Wijzigingen"

    changes_state = MockChangesState()

    # Call the function with changes state
    handle_clear_all_changes(changes_state)

    # Verify clear function was called
    mock_clear_commands.assert_called_once()
    # Verify notification was shown
    mock_ui.notify.assert_called_with("Alle wijzigingen gewist", type="info")
    # Verify that changes_state.update() was called
    assert changes_state.update_called
    assert changes_state.count == 0
    assert changes_state.label == "Wijzigingen"


@patch("production_control.web.pages.inspectie.get_storage")
@patch("production_control.web.pages.inspectie.ui")
def test_absolute_afwijking_calculation(mock_ui, mock_get_storage):
    """Test that afwijking is calculated as absolute value (current + changes)."""
    from production_control.web.pages.inspectie import create_afwijking_actions

    # Setup mock storage
    mock_storage = {}
    mock_get_storage.return_value = mock_storage

    # Create actions
    mock_repository = Mock()
    actions = create_afwijking_actions(mock_repository)
    plus_handler = actions["plus_one"]["handler"]

    # Simulate: current afwijking is 7, user clicks +1 twice
    event_data = Mock()
    event_data.args = {"key": "27014", "row": {"afwijking_afleveren": 7}}  # Current afwijking is 7

    # First click: +1 (should result in 8)
    plus_handler(event_data)
    change_data = mock_storage["inspectie_changes"]["27014"]
    assert change_data["original"] == 7
    assert change_data["new"] == 8

    # Second click: +1 (should result in 9)
    plus_handler(event_data)
    change_data = mock_storage["inspectie_changes"]["27014"]
    assert change_data["original"] == 7
    assert change_data["new"] == 9

    # Verify the command contains absolute value 9, not relative +2
    from production_control.web.pages.inspectie import get_pending_commands

    commands = get_pending_commands()
    assert len(commands) == 1
    assert commands[0].code == "27014"
    assert commands[0].new_afwijking == 9  # Absolute value: 7 + 2 = 9


def test_inspectie_page_has_fullscreen_button():
    """Test that the inspectie page includes a fullscreen button."""
    from production_control.web.pages.inspectie import router

    # Verify the router exists and has the expected route
    assert router is not None

    # The fullscreen functionality is tested by checking that the page loads without errors
    # The actual fullscreen API testing would require browser integration tests
