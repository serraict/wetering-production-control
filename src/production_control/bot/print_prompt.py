"""Print the composed bot system prompt to stdout.

Useful for inspecting how the rules, today's temporal context, and
the rendered schema combine before they hit the LLM. Run via
`make bot-prompt`.
"""

from __future__ import annotations

from datetime import date

from production_control.bot.answer import _system_prompt


def main() -> None:
    print(_system_prompt(date.today()))


if __name__ == "__main__":
    main()
