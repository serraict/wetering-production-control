"""Transport-agnostic core of the bot.

`answer(question)` builds a system prompt, runs the LLM tool-use loop
(cap 8 iterations), writes an audit record, and returns an
`AnswerResult` containing the final text + metadata.
"""

from __future__ import annotations

import json
import re
import time
from dataclasses import dataclass, field
from typing import Any, Callable, List, Optional

from sqlalchemy import Engine

from production_control.bot import audit, llm, schema, tools

MAX_TOOL_ITERATIONS = 8

SYSTEM_RULES = """You are an internal data assistant for the
Wetering production_control app. Answer the user's question about the
data shown in the overviews below by writing Dremio SQL and calling
the `run_dremio_sql` tool.

Rules:
- Use only the overviews listed below. Do not invent table or column
  names. If the data is not in any overview, say so plainly.
- Dremio identifiers are case-sensitive and view names need
  double-quoted schema + table, e.g. "Productie.Oppotten"."oppotlijst".
- Prefer concrete queries (with WHERE / ORDER BY / GROUP BY) over
  SELECT *.
- Reply in the user's language; default to Dutch.
- After you have the data, give a short answer (1-3 sentences) above
  the data table.
"""

_ROWS_RE = re.compile(r"_\((\d+) rows\)_")
_TRUNC_RE = re.compile(r"showing \d+ of (\d+) rows")


@dataclass
class AnswerResult:
    text: str
    sql: List[str] = field(default_factory=list)
    rows: int = 0
    latency_ms: int = 0
    tokens: int = 0
    iterations: int = 0
    model: str = ""
    error: Optional[str] = None


def _system_prompt() -> str:
    return SYSTEM_RULES + "\n" + schema.render()


def _count_rows(markdown: str) -> int:
    m = _ROWS_RE.search(markdown)
    if m:
        return int(m.group(1))
    m = _TRUNC_RE.search(markdown)
    if m:
        return int(m.group(1))
    return 0


def _call_tool(name: str, arguments: str, engine: Optional[Engine]) -> str:
    if name not in tools.BY_NAME:
        return f"ERROR: unknown tool {name!r}"
    try:
        args = json.loads(arguments) if arguments else {}
    except json.JSONDecodeError as e:
        return f"ERROR: invalid tool arguments JSON: {e}"
    tool = tools.BY_NAME[name]
    if name == "run_dremio_sql":
        return tool.call(engine=engine, **args)
    return tool.call(**args)


def answer(
    question: str,
    *,
    engine: Optional[Engine] = None,
    llm_chat: Callable[..., Any] = llm.chat,
    audit_path: Optional[str] = None,
) -> AnswerResult:
    """Answer a user question via the configured LLM and bot tools."""
    started = time.monotonic()
    model = llm.model_name()

    messages: List[dict] = [
        {"role": "system", "content": _system_prompt()},
        {"role": "user", "content": question},
    ]

    sql_seen: List[str] = []
    rows_seen = 0
    tokens = 0
    text_out = ""
    error: Optional[str] = None
    iters = 0

    try:
        for iters in range(1, MAX_TOOL_ITERATIONS + 1):
            response = llm_chat(messages=messages, tools=tools.SPECS)
            choice = response.choices[0]
            msg = choice.message
            usage = getattr(response, "usage", None)
            if usage is not None:
                tokens += getattr(usage, "total_tokens", 0) or 0

            tool_calls = getattr(msg, "tool_calls", None) or []

            assistant_dict: dict = {"role": "assistant"}
            if msg.content:
                assistant_dict["content"] = msg.content
            if tool_calls:
                assistant_dict["tool_calls"] = [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments,
                        },
                    }
                    for tc in tool_calls
                ]
            messages.append(assistant_dict)

            if not tool_calls:
                text_out = msg.content or ""
                break

            for tc in tool_calls:
                name = tc.function.name
                args = tc.function.arguments
                if name == "run_dremio_sql":
                    try:
                        parsed = json.loads(args) if args else {}
                    except json.JSONDecodeError:
                        parsed = {}
                    q = parsed.get("query", "") if isinstance(parsed, dict) else ""
                    if q:
                        sql_seen.append(q)
                result = _call_tool(name, args, engine)
                rows_seen += _count_rows(result)
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tc.id,
                        "content": result,
                    }
                )
        else:
            error = f"tool-use loop hit the {MAX_TOOL_ITERATIONS}-iteration cap"
            text_out = text_out or (
                "Sorry, ik liep tegen mijn iteratielimiet aan voordat ik een " "antwoord kon geven."
            )
    except Exception as e:  # surface but still record audit
        error = f"{type(e).__name__}: {e}"
        text_out = text_out or f"Sorry, er ging iets mis: {error}"

    latency_ms = int((time.monotonic() - started) * 1000)

    result = AnswerResult(
        text=text_out,
        sql=sql_seen,
        rows=rows_seen,
        latency_ms=latency_ms,
        tokens=tokens,
        iterations=iters,
        model=model,
        error=error,
    )

    audit.append(
        {
            "question": question,
            "model": model,
            "sql": sql_seen,
            "rows": rows_seen,
            "latency_ms": latency_ms,
            "tokens": tokens,
            "iterations": iters,
            "error": error,
        },
        path=audit_path,
    )

    return result


def footer(result: AnswerResult) -> str:
    return (
        f"_via {result.model} · {result.latency_ms} ms · "
        f"{result.tokens} tokens · {result.iterations} step(s)_"
    )
