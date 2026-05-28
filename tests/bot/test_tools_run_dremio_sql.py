"""Tests for the run_dremio_sql tool wiring (guard + execute + format)."""

from __future__ import annotations

import pytest
from sqlalchemy import create_engine

from production_control.bot import tools
from production_control.bot.tools import run_dremio_sql


@pytest.fixture()
def sqlite_engine():
    eng = create_engine("sqlite:///:memory:")
    with eng.connect() as c:
        c.exec_driver_sql("CREATE TABLE t (id INTEGER, naam TEXT)")
        c.exec_driver_sql("INSERT INTO t VALUES (1, 'aap'), (2, 'noot')")
        c.commit()
    return eng


def test_registry_exposes_run_dremio_sql():
    assert "run_dremio_sql" in tools.BY_NAME
    assert tools.BY_NAME["run_dremio_sql"] is run_dremio_sql


def test_spec_is_well_formed():
    spec = run_dremio_sql.SPEC
    assert spec["type"] == "function"
    fn = spec["function"]
    assert fn["name"] == "run_dremio_sql"
    assert fn["description"]  # non-empty
    assert fn["parameters"]["properties"]["query"]["type"] == "string"
    assert fn["parameters"]["required"] == ["query"]


def test_happy_path_returns_executed_sql_and_table(sqlite_engine):
    out = run_dremio_sql.call("SELECT id, naam FROM t ORDER BY id", engine=sqlite_engine)
    assert "Executed:" in out
    assert "```sql" in out
    assert "| id | naam |" in out
    assert "| 1 | aap |" in out
    # LIMIT injection should be visible in the executed SQL block.
    assert "LIMIT 500" in out.upper()


def test_existing_limit_preserved(sqlite_engine):
    out = run_dremio_sql.call("SELECT id FROM t ORDER BY id LIMIT 1", engine=sqlite_engine)
    assert "| 1 |" in out
    assert "LIMIT 500" not in out.upper()


def test_guard_rejection_is_model_visible(sqlite_engine):
    out = run_dremio_sql.call("DELETE FROM t", engine=sqlite_engine)
    assert out.startswith("ERROR: SQL rejected by guard:")


def test_execution_error_is_model_visible(sqlite_engine):
    out = run_dremio_sql.call("SELECT does_not_exist FROM t", engine=sqlite_engine)
    assert out.startswith("ERROR: query failed:")
