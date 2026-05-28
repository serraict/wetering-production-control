"""The bot's single v1 tool: run a read-only SELECT against Dremio."""

from __future__ import annotations

from typing import Optional

from sqlalchemy import Engine

from production_control.bot import dremio_tool, sql_guard


SPEC = {
    "type": "function",
    "function": {
        "name": "run_dremio_sql",
        "description": (
            "Execute a single read-only SELECT against Dremio and return the "
            "result as a markdown table. Only SELECT/WITH/UNION/INTERSECT/"
            "EXCEPT are allowed; DDL, DML, SET and USE are rejected. If you "
            "omit a LIMIT, one is injected (default 500). Use the "
            "fully-qualified view names from the 'Available overviews' "
            "section in the system prompt; column names are case-sensitive."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": (
                        "A single SQL SELECT statement against Dremio. Use "
                        "double-quoted identifiers for schemas and tables, "
                        'e.g. "Productie.Oppotten"."oppotlijst".'
                    ),
                },
            },
            "required": ["query"],
        },
    },
}


def call(query: str, *, engine: Optional[Engine] = None) -> str:
    """Guard → execute → format. Returns model-visible text (never raises)."""
    try:
        sql = sql_guard.normalize(query)
    except sql_guard.BadSqlError as e:
        return f"ERROR: SQL rejected by guard: {e}"

    try:
        cols, rows = dremio_tool.execute(sql, engine=engine)
    except Exception as e:  # surfaced back to the model for self-correction
        return f"ERROR: query failed: {type(e).__name__}: {e}"

    body = dremio_tool.format_result(cols, rows)
    return f"Executed:\n```sql\n{sql}\n```\n\n{body}"
