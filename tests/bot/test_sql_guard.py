"""Tests for the SQL guard."""

from __future__ import annotations

import pytest

from production_control.bot.sql_guard import BadSqlError, DEFAULT_LIMIT, normalize


class TestAccepts:
    def test_plain_select_gets_limit_injected(self):
        out = normalize("SELECT id FROM t")
        assert "LIMIT" in out.upper()
        assert str(DEFAULT_LIMIT) in out

    def test_existing_limit_is_preserved(self):
        out = normalize("SELECT id FROM t LIMIT 10")
        # Round-trip should keep the original limit, not double it.
        assert "10" in out
        assert str(DEFAULT_LIMIT) not in out

    def test_with_cte(self):
        out = normalize("WITH c AS (SELECT id FROM t) SELECT * FROM c")
        assert "LIMIT" in out.upper()

    def test_union(self):
        out = normalize("SELECT 1 UNION ALL SELECT 2")
        assert out  # parses and returns something

    def test_quoted_identifiers_preserved(self):
        out = normalize('SELECT "id" FROM "Productie.Oppotten"."oppotlijst"')
        assert "oppotlijst" in out


class TestRejects:
    def test_empty(self):
        with pytest.raises(BadSqlError):
            normalize("")

    def test_whitespace_only(self):
        with pytest.raises(BadSqlError):
            normalize("   \n  ")

    def test_none(self):
        with pytest.raises(BadSqlError):
            normalize(None)  # type: ignore[arg-type]

    def test_unparseable(self):
        with pytest.raises(BadSqlError):
            normalize("not actually sql !!")

    def test_multiple_statements(self):
        with pytest.raises(BadSqlError):
            normalize("SELECT 1; SELECT 2")

    def test_insert(self):
        with pytest.raises(BadSqlError):
            normalize("INSERT INTO t VALUES (1)")

    def test_update(self):
        with pytest.raises(BadSqlError):
            normalize("UPDATE t SET x = 1")

    def test_delete(self):
        with pytest.raises(BadSqlError):
            normalize("DELETE FROM t")

    def test_create_table(self):
        with pytest.raises(BadSqlError):
            normalize("CREATE TABLE t (x INT)")

    def test_drop_table(self):
        with pytest.raises(BadSqlError):
            normalize("DROP TABLE t")

    def test_alter_table(self):
        with pytest.raises(BadSqlError):
            normalize("ALTER TABLE t ADD COLUMN x INT")

    def test_set(self):
        with pytest.raises(BadSqlError):
            normalize("SET foo = 1")

    def test_use_schema(self):
        with pytest.raises(BadSqlError):
            normalize("USE my_schema")
