"""Tests for inspectie web page."""

from unittest.mock import Mock, patch

from production_control.web.pages.inspectie import router, create_afwijking_actions, get_storage


def test_inspectie_page_router_exists():
    """Test that inspectie page router exists."""
    assert router is not None


def test_create_afwijking_actions_exists():
    """Test that afwijking actions function exists."""
    actions = create_afwijking_actions()
    assert actions is not None
    assert "plus_one" in actions
    assert "minus_one" in actions


@patch("production_control.web.pages.inspectie.get_storage")
@patch("production_control.web.pages.inspectie.ui")
def test_afwijking_plus_one_updates_storage(mock_ui, mock_get_storage):
    """Test that +1 button click updates browser storage."""
    # Setup mock storage
    mock_storage = {}
    mock_get_storage.return_value = mock_storage

    # Create actions and get +1 handler
    actions = create_afwijking_actions()
    plus_handler = actions["plus_one"]["handler"]

    # Simulate button click event
    event_data = Mock()
    event_data.args = {"key": "27014"}

    # Call handler
    plus_handler(event_data)

    # Verify storage was updated
    assert "inspectie_changes" in mock_storage
    assert "27014" in mock_storage["inspectie_changes"]
    assert mock_storage["inspectie_changes"]["27014"] == 1


@patch("production_control.web.pages.inspectie.get_storage")
@patch("production_control.web.pages.inspectie.ui")
def test_afwijking_minus_one_updates_storage(mock_ui, mock_get_storage):
    """Test that -1 button click updates browser storage."""
    # Setup mock storage
    mock_storage = {}
    mock_get_storage.return_value = mock_storage

    # Create actions and get -1 handler
    actions = create_afwijking_actions()
    minus_handler = actions["minus_one"]["handler"]

    # Simulate button click event
    event_data = Mock()
    event_data.args = {"key": "27014"}

    # Call handler
    minus_handler(event_data)

    # Verify storage was updated
    assert "inspectie_changes" in mock_storage
    assert "27014" in mock_storage["inspectie_changes"]
    assert mock_storage["inspectie_changes"]["27014"] == -1


@patch("production_control.web.pages.inspectie.get_storage")
@patch("production_control.web.pages.inspectie.ui")
def test_multiple_clicks_accumulate_changes(mock_ui, mock_get_storage):
    """Test that multiple clicks accumulate in storage."""
    # Setup mock storage with existing change
    mock_storage = {"inspectie_changes": {"27014": 2}}
    mock_get_storage.return_value = mock_storage

    # Create actions
    actions = create_afwijking_actions()
    plus_handler = actions["plus_one"]["handler"]
    minus_handler = actions["minus_one"]["handler"]

    # Simulate button click events
    event_data = Mock()
    event_data.args = {"key": "27014"}

    # Click +1 (should be 2 + 1 = 3)
    plus_handler(event_data)
    assert mock_storage["inspectie_changes"]["27014"] == 3

    # Click -1 (should be 3 - 1 = 2)
    minus_handler(event_data)
    assert mock_storage["inspectie_changes"]["27014"] == 2


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
            "27014": 2,
            "27015": -1,
            "27016": 0,  # Should be included as well
        }
    }

    commands = get_pending_commands()
    assert len(commands) == 3

    # Check command details
    codes = [cmd.code for cmd in commands]
    assert "27014" in codes
    assert "27015" in codes
    assert "27016" in codes

    # Check afwijking values
    for cmd in commands:
        if cmd.code == "27014":
            assert cmd.new_afwijking == 2
        elif cmd.code == "27015":
            assert cmd.new_afwijking == -1
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
