"""Interactive REPL for the bot.

Run with ``make bot-console`` or ``python -m production_control.bot.console``.
Each prompt is a one-shot question — v1 is stateless (ADR-0002), so
typing follow-ups like "and for last week?" won't carry context yet.
"""

from __future__ import annotations

import sys
from typing import Optional

from production_control.bot import answer as answer_mod
from production_control.bot import llm


_PROMPT = "bot> "


def _print_banner() -> None:
    print(
        f"Wetering production_control bot — model: {llm.model_name()}\n"
        "Type a question and press Enter. Empty line or Ctrl-D to exit.\n"
        "(stateless v1 — each question is independent)\n"
        "Switch model with BOT_MODEL=...; see "
        "src/production_control/bot/llm.py::MODEL_EXAMPLES for suggestions.\n",
        flush=True,
    )


def _read_question() -> Optional[str]:
    try:
        line = input(_PROMPT)
    except EOFError:
        print()
        return None
    return line.strip()


def _print_result(result: answer_mod.AnswerResult) -> None:
    print()
    print(result.text)
    if result.sql:
        print()
        print("SQL:")
        for sql in result.sql:
            print(f"  {sql}")
    print()
    print(answer_mod.footer(result))
    print()


def main() -> int:
    _print_banner()
    while True:
        question = _read_question()
        if question is None or question == "":
            return 0
        try:
            result = answer_mod.answer(question)
        except KeyboardInterrupt:
            print()
            return 0
        _print_result(result)


if __name__ == "__main__":
    sys.exit(main())
