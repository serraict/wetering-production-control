"""Tests for the Dremio query executor + result formatter."""

from __future__ import annotations

import pytest
from sqlalchemy import create_engine

from production_control.bot import dremio_tool


@pytest.fixture()
def sqlite_engine():
    """In-memory SQLite engine standing in for Dremio in tests."""
    eng = create_engine("sqlite:///:memory:")
    with eng.connect() as c:
        c.exec_driver_sql("CREATE TABLE t (id INTEGER, naam TEXT)")
        c.exec_driver_sql("INSERT INTO t VALUES (1, 'aap'), (2, 'noot'), (3, 'mies')")
        c.commit()
    return eng


class TestExecute:
    def test_returns_columns_and_rows(self, sqlite_engine):
        cols, rows = dremio_tool.execute("SELECT id, naam FROM t ORDER BY id", sqlite_engine)
        assert cols == ["id", "naam"]
        assert rows == [[1, "aap"], [2, "noot"], [3, "mies"]]

    def test_empty_result(self, sqlite_engine):
        cols, rows = dremio_tool.execute("SELECT id FROM t WHERE id > 99", sqlite_engine)
        assert cols == ["id"]
        assert rows == []


class TestFormat:
    def test_basic_table(self):
        out = dremio_tool.format_result(["id", "naam"], [[1, "aap"], [2, "noot"]])
        assert "| id | naam |" in out
        assert "| --- | --- |" in out
        assert "| 1 | aap |" in out
        assert "_(2 rows)_" in out

    def test_empty_rows(self):
        out = dremio_tool.format_result(["id"], [])
        assert "| id |" in out
        assert "(0 rows)" in out

    def test_no_columns(self):
        assert dremio_tool.format_result([], []) == "(no result)"

    def test_truncates_with_note(self):
        rows = [[i] for i in range(100)]
        out = dremio_tool.format_result(["n"], rows, max_rows=10)
        assert "showing 10 of 100 rows" in out
        assert "| 9 |" in out
        assert "| 10 |" not in out

    def test_none_rendered_as_empty(self):
        out = dremio_tool.format_result(["a"], [[None]])
        assert "|  |" in out

    def test_escapes_pipes(self):
        out = dremio_tool.format_result(["s"], [["a|b"]])
        assert "a\\|b" in out

    def test_replaces_newlines_in_cells(self):
        out = dremio_tool.format_result(["s"], [["line1\nline2"]])
        assert "line1 line2" in out

    def test_truncates_long_cells(self):
        long = "x" * (dremio_tool.MAX_CELL_CHARS + 50)
        out = dremio_tool.format_result(["s"], [[long]])
        # Truncation marker '…' present, full string not present.
        assert "…" in out
        assert long not in out
