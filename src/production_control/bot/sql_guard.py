"""Read-only SQL guard for the Zulip insights bot.

Defence-in-depth on top of the read-only Dremio account: parses the
SQL the model generated, enforces a single read-only statement, and
injects a row LIMIT if absent. See ADR-0002.
"""

from __future__ import annotations

import sqlglot
from sqlglot import exp

DEFAULT_LIMIT = 500


class BadSqlError(ValueError):
    """The generated SQL was rejected by the guard."""


_FORBIDDEN_NODES = (
    exp.Create,
    exp.Drop,
    exp.Alter,
    exp.Insert,
    exp.Update,
    exp.Delete,
    exp.Merge,
    exp.TruncateTable,
    exp.Command,
    exp.Set,
    exp.SetItem,
    exp.Use,
    exp.Show,
)

_QUERY_ROOTS = (exp.Select, exp.Union, exp.Intersect, exp.Except)


def normalize(sql: str, default_limit: int = DEFAULT_LIMIT) -> str:
    """Return a guarded, normalized SQL string or raise BadSqlError."""
    if sql is None or not sql.strip():
        raise BadSqlError("empty SQL")

    try:
        statements = sqlglot.parse(sql)
    except sqlglot.errors.ParseError as e:
        raise BadSqlError(f"could not parse SQL: {e}") from e

    statements = [s for s in statements if s is not None]
    if not statements:
        raise BadSqlError("no statement parsed")
    if len(statements) > 1:
        raise BadSqlError(f"expected a single statement, got {len(statements)}")

    stmt = statements[0]
    if not isinstance(stmt, _QUERY_ROOTS):
        raise BadSqlError(f"only SELECT queries are allowed (got {type(stmt).__name__})")

    for node in stmt.find_all(*_FORBIDDEN_NODES):
        raise BadSqlError(f"forbidden construct in SQL: {type(node).__name__}")

    if stmt.args.get("limit") is None:
        stmt = stmt.limit(default_limit)

    return stmt.sql()
