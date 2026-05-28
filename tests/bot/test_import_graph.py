"""Guard: the bot core must not pull in transport-layer libraries.

`bot.answer` is the transport-agnostic entrypoint; slice 2 will wrap
it from a FastAPI endpoint. If `answer` itself starts importing
fastapi or zulip, the slice boundary has been crossed by accident.
"""

from __future__ import annotations

import subprocess
import sys


PROBE = """
import sys
import production_control.bot.answer  # noqa: F401
leaked = sorted(
    m for m in sys.modules
    if m == "fastapi" or m.startswith("fastapi.")
    or m == "zulip" or m.startswith("zulip.")
)
if leaked:
    raise SystemExit("LEAKED: " + ",".join(leaked))
"""


def test_answer_does_not_import_fastapi_or_zulip():
    proc = subprocess.run(
        [sys.executable, "-c", PROBE],
        check=False,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, (
        f"bot.answer pulled in transport libs.\n" f"stdout: {proc.stdout}\nstderr: {proc.stderr}"
    )
