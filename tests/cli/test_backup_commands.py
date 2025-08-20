"""Tests for Dremio backup commands."""

import csv
from unittest.mock import MagicMock, patch

import pytest
import sqlalchemy as sa
from typer.testing import CliRunner

from production_control.__cli__ import app


@pytest.fixture
def mock_engine():
    """Mock SQLAlchemy engine."""
    engine = MagicMock()
    engine.connect.return_value.__enter__.return_value = MagicMock()
    return engine


@pytest.fixture
def mock_session(mock_engine):
    """Mock SQLModel session."""
    with patch("production_control.data.backup.Session") as mock_session:
        mock_session.return_value.__enter__.return_value = MagicMock()
        yield mock_session


@pytest.fixture
def runner():
    """Typer CLI test runner."""
    return CliRunner()


def test_backup_query_success(tmp_path, mock_engine, mock_session, runner):
    """Test successful backup of table data with default name."""
    # Mock query result
    mock_result = MagicMock()
    mock_result.keys.return_value = ["id", "name", "value"]
    mock_result.fetchmany.side_effect = [
        [(1, "test1", 100), (2, "test2", 200)],  # First chunk
        [],  # End of results
    ]
    mock_session.return_value.__enter__.return_value.exec.return_value = mock_result

    # Run backup command
    with patch("production_control.data.backup.DremioRepository") as mock_repo:
        mock_repo.return_value.engine = mock_engine
        result = runner.invoke(
            app, ["backup", "query", "SELECT * FROM test", "--output-dir", str(tmp_path)]
        )

    # Verify command output
    assert result.exit_code == 0
    assert "Success: Saved 1 file(s)" in result.stdout

    # Verify file contents
    output_file = tmp_path / "backup_001.csv"
    assert output_file.exists()
    with open(output_file) as f:
        reader = csv.reader(f)
        rows = list(reader)
        assert rows[0] == ["id", "name", "value"]  # Header
        assert rows[1:] == [["1", "test1", "100"], ["2", "test2", "200"]]  # Data


def test_backup_query_with_name(tmp_path, mock_engine, mock_session, runner):
    """Test successful backup of table data with custom name."""
    # Mock query result
    mock_result = MagicMock()
    mock_result.keys.return_value = ["id", "name"]
    mock_result.fetchmany.side_effect = [
        [(1, "test1")],
        [],
    ]
    mock_session.return_value.__enter__.return_value.exec.return_value = mock_result

    # Run backup command
    with patch("production_control.data.backup.DremioRepository") as mock_repo:
        mock_repo.return_value.engine = mock_engine
        result = runner.invoke(
            app,
            [
                "backup",
                "query",
                "SELECT * FROM test",
                "--name",
                "custom",
                "--output-dir",
                str(tmp_path),
            ],
        )

    # Verify command output
    assert result.exit_code == 0
    assert "Success: Saved 1 file(s)" in result.stdout

    # Verify file contents
    output_file = tmp_path / "custom_001.csv"
    assert output_file.exists()
    with open(output_file) as f:
        reader = csv.reader(f)
        rows = list(reader)
        assert rows[0] == ["id", "name"]  # Header
        assert rows[1:] == [["1", "test1"]]  # Data


@pytest.mark.integration
def test_backup_query_db_error(tmp_path, mock_engine, mock_session, runner):
    """Test handling of database errors."""
    # Mock database error
    mock_session.return_value.__enter__.return_value.exec.side_effect = sa.exc.SQLAlchemyError(
        "Connection failed"
    )

    # Run backup command
    with patch("production_control.data.backup.DremioRepository") as mock_repo:
        mock_repo.return_value.engine = mock_engine
        result = runner.invoke(
            app, ["backup", "query", "SELECT * FROM test", "--output-dir", str(tmp_path)]
        )

    # Verify error handling
    assert result.exit_code == 1
    assert "Database error: Connection failed" in result.stderr


@pytest.mark.integration
def test_backup_query_filesystem_error(tmp_path, mock_engine, mock_session, runner):
    """Test handling of filesystem errors."""
    # Mock query result
    mock_result = MagicMock()
    mock_result.keys.return_value = ["id"]
    mock_result.fetchmany.return_value = [(1,)]
    mock_session.return_value.__enter__.return_value.exec.return_value = mock_result

    # Make output directory read-only
    readonly_dir = tmp_path / "readonly"
    readonly_dir.mkdir()
    readonly_dir.chmod(0o555)  # Read + execute only

    # Run backup command
    with patch("production_control.data.backup.DremioRepository") as mock_repo:
        mock_repo.return_value.engine = mock_engine
        result = runner.invoke(
            app, ["backup", "query", "SELECT * FROM test", "--output-dir", str(readonly_dir)]
        )

    # Verify error handling
    assert result.exit_code == 1
    assert "File system error" in result.stderr


def test_backup_query_env_var_precedence(tmp_path, mock_engine, mock_session, runner):
    """Test that DREMIO_BACKUP_DIR environment variable takes precedence."""
    # Create two directories
    default_dir = tmp_path / "default"
    default_dir.mkdir()
    env_dir = tmp_path / "env"
    env_dir.mkdir()

    # Mock query result
    mock_result = MagicMock()
    mock_result.keys.return_value = ["id"]
    mock_result.fetchmany.side_effect = [
        [(1,)],  # First chunk
        [],  # End of results
    ]
    mock_session.return_value.__enter__.return_value.exec.return_value = mock_result

    # Run backup command with environment variable set
    with patch("production_control.data.backup.DremioRepository") as mock_repo:
        mock_repo.return_value.engine = mock_engine
        result = runner.invoke(
            app,
            ["backup", "query", "SELECT * FROM test"],
            env={"DREMIO_BACKUP_DIR": str(env_dir)},
        )

    # Verify command output
    assert result.exit_code == 0
    assert "Success: Saved 1 file(s)" in result.stdout

    # Verify file was created in env directory, not default
    assert not (default_dir / "backup_001.csv").exists()
    assert (env_dir / "backup_001.csv").exists()


def test_backup_query_large_result(tmp_path, mock_engine, mock_session, runner):
    """Test handling of large result sets with chunking."""
    # Mock query result with multiple chunks
    mock_result = MagicMock()
    mock_result.keys.return_value = ["id"]
    mock_result.fetchmany.side_effect = [
        [(i,) for i in range(5)],  # First chunk
        [(i,) for i in range(5, 10)],  # Second chunk
        [],  # End of results
    ]
    mock_session.return_value.__enter__.return_value.exec.return_value = mock_result

    # Run backup command with small chunk size
    with patch("production_control.data.backup.DremioRepository") as mock_repo:
        mock_repo.return_value.engine = mock_engine
        result = runner.invoke(
            app,
            [
                "backup",
                "query",
                "SELECT * FROM test",
                "--output-dir",
                str(tmp_path),
                "--chunk-size",
                "5",
            ],
        )

    # Verify command output
    assert result.exit_code == 0
    assert "Success: Saved 2 file(s)" in result.stdout

    # Verify file contents
    for i in range(1, 3):
        output_file = tmp_path / f"backup_{i:03d}.csv"
        assert output_file.exists()
        with open(output_file) as f:
            reader = csv.reader(f)
            rows = list(reader)
            assert rows[0] == ["id"]  # Header
            assert len(rows) == 6  # Header + 5 rows
