"""Execute guarded SQL against Dremio and format the result.

The SQL must already have been passed through `sql_guard.normalize`;
this module trusts what it receives.
"""

from __future__ import annotations

import os
from typing import Any, List, Optional, Tuple

from sqlalchemy import Engine, create_engine, text


MAX_ROWS_IN_REPLY = 50
MAX_CELL_CHARS = 120


def _engine() -> Engine:
    conn = os.getenv("VINEAPP_DB_CONNECTION", "")
    if not conn:
        raise RuntimeError("VINEAPP_DB_CONNECTION is not set")
    return create_engine(conn)


def execute(sql: str, engine: Optional[Engine] = None) -> Tuple[List[str], List[List[Any]]]:
    """Execute SQL and return (columns, rows). `engine` is injectable for tests."""
    eng = engine or _engine()
    with eng.connect() as conn:
        result = conn.execute(text(sql))
        cols = list(result.keys())
        rows = [list(r) for r in result.fetchall()]
    return cols, rows


def _cell(v: Any) -> str:
    s = "" if v is None else str(v)
    if len(s) > MAX_CELL_CHARS:
        s = s[: MAX_CELL_CHARS - 1] + "…"
    return s.replace("|", "\\|").replace("\n", " ")


def format_result(
    columns: List[str],
    rows: List[List[Any]],
    max_rows: int = MAX_ROWS_IN_REPLY,
) -> str:
    """Format a query result as a compact markdown table, truncated."""
    if not columns:
        return "(no result)"

    header = "| " + " | ".join(columns) + " |"
    sep = "| " + " | ".join(["---"] * len(columns)) + " |"

    if not rows:
        return f"{header}\n{sep}\n\n_(0 rows)_"

    shown = rows[:max_rows]
    body = ["| " + " | ".join(_cell(v) for v in r) + " |" for r in shown]

    out = [header, sep, *body, ""]
    if len(rows) > max_rows:
        out.append(f"_… showing {max_rows} of {len(rows)} rows._")
    else:
        out.append(f"_({len(rows)} rows)_")
    return "\n".join(out)
