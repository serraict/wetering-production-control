"""Tests for web authentication functionality."""

import os
from unittest.mock import Mock, patch
import pytest
from fastapi import Request

from production_control.web.auth import get_current_user


@pytest.fixture
def mock_request():
    """Create a mock FastAPI Request object."""
    return Mock(spec=Request)


@pytest.fixture
def mock_context():
    """Create a mock NiceGUI context."""
    with patch("production_control.web.auth.context") as mock_ctx:
        yield mock_ctx


def test_returns_guest_when_no_context_available(mock_context):
    """Should return default guest user when context is not available."""
    mock_context.client.request = None

    result = get_current_user()

    assert result == {"name": "Guest", "roles": [], "email": "", "profile_page": ""}


def test_returns_guest_when_headers_access_fails(mock_context):
    """Should return default guest user when header access raises exception."""
    mock_context.client.request.headers.get.side_effect = Exception("Test error")

    result = get_current_user()

    assert result["name"] == "Guest"


def test_all_headers_set(mock_context, mock_request):
    """Should return complete user info when all headers are provided."""
    mock_request.headers.get.side_effect = lambda key: {
        "remote-user": "john.doe",
        "remote-name": "John Doe",
        "remote-email": "john.doe@example.com",
        "remote-groups": "admin,user,production_employee",
    }.get(key)
    mock_context.client.request = mock_request

    result = get_current_user()
    print(result)
    assert result == {
        "name": "John Doe",  # remote-name takes precedence
        "roles": ["admin", "user", "production_employee"],
        "email": "john.doe@example.com",
        "profile_page": os.getenv("PROFILE_PAGE_URL", ""),
    }


def test_remote_user_without_remote_name(mock_context, mock_request):
    """Should use remote-user when remote-name is not available."""
    mock_request.headers.get.side_effect = lambda key: {
        "remote-user": "john.doe",
        "remote-name": None,
        "remote-email": "john.doe@example.com",
        "remote-groups": "user",
    }.get(key)
    mock_context.client.request = mock_request

    result = get_current_user()

    assert result["name"] == "john.doe"
    assert result["email"] == "john.doe@example.com"
    assert result["roles"] == ["user"]


def test_empty_groups_string(mock_context, mock_request):
    """Should return empty roles list when remote-groups is empty string."""
    mock_request.headers.get.side_effect = lambda key: {
        "remote-user": "john.doe",
        "remote-groups": "",
    }.get(key)
    mock_context.client.request = mock_request

    result = get_current_user()

    assert result["name"] == "john.doe"
    assert result["roles"] == []


def test_single_admin_group(mock_context, mock_request):
    """Should parse single admin group correctly."""
    mock_request.headers.get.side_effect = lambda key: {
        "remote-user": "admin.user",
        "remote-groups": "admin",
    }.get(key)
    mock_context.client.request = mock_request

    result = get_current_user()

    assert result["name"] == "admin.user"
    assert result["roles"] == ["admin"]


def test_multiple_groups_with_spaces(mock_context, mock_request):
    """Should parse multiple groups correctly, trimming whitespace."""
    mock_request.headers.get.side_effect = lambda key: {
        "remote-user": "multi.user",
        "remote-groups": " admin , user , production_employee ",
    }.get(key)
    mock_context.client.request = mock_request

    result = get_current_user()

    assert result["name"] == "multi.user"
    assert result["roles"] == ["admin", "user", "production_employee"]


def test_profile_page_from_env_var(mock_context, mock_request):
    """Should set profile_page when PROFILE_PAGE_URL environment variable is set."""
    mock_request.headers.get.side_effect = lambda key: {"remote-user": "test.user"}.get(key)
    mock_context.client.request = mock_request

    with patch.dict(os.environ, {"PROFILE_PAGE_URL": "https://profile.example.com"}):
        result = get_current_user()

        assert result["name"] == "test.user"
        assert result["profile_page"] == "https://profile.example.com"


def test_no_profile_page_when_env_var_not_set(mock_context, mock_request):
    """Should leave profile_page empty when PROFILE_PAGE_URL is not set."""
    mock_request.headers.get.side_effect = lambda key: {"remote-user": "test.user"}.get(key)
    mock_context.client.request = mock_request

    with patch.dict(os.environ, {}, clear=True):
        result = get_current_user()

        assert result["name"] == "test.user"
        assert result["profile_page"] == ""
