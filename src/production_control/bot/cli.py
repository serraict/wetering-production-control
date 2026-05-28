"""CLI entrypoint: ``python -m production_control.bot.cli "<question>"``."""

from __future__ import annotations

import sys
from typing import List, Optional

from production_control.bot import answer as answer_mod


def main(argv: Optional[List[str]] = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if not args:
        print(
            'usage: python -m production_control.bot.cli "<question>"',
            file=sys.stderr,
        )
        return 2

    question = " ".join(args)
    result = answer_mod.answer(question)

    print(result.text)
    if result.sql:
        print()
        print("SQL:")
        for sql in result.sql:
            print(f"  {sql}")
    print()
    print(answer_mod.footer(result))

    return 0 if not result.error else 1


if __name__ == "__main__":
    sys.exit(main())
