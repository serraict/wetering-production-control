"""Guard: keep transport libs out of the bot's core.

- `bot.answer` is the transport-agnostic entrypoint; it must not
  import `fastapi` or `zulip`.
- `bot.server` is the Zulip-facing FastAPI app; FastAPI is allowed
  here (that's the whole point of the module) but the `zulip` Python
  library must not creep in — we speak the HTTP webhook protocol
  directly.
"""

from __future__ import annotations

import subprocess
import sys


_ANSWER_PROBE = """
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


_SERVER_PROBE = """
import sys
import production_control.bot.server  # noqa: F401
leaked = sorted(
    m for m in sys.modules
    if m == "zulip" or m.startswith("zulip.")
)
if leaked:
    raise SystemExit("LEAKED: " + ",".join(leaked))
"""


def _run(probe: str):
    return subprocess.run(
        [sys.executable, "-c", probe],
        check=False,
        capture_output=True,
        text=True,
    )


def test_answer_does_not_import_fastapi_or_zulip():
    proc = _run(_ANSWER_PROBE)
    assert proc.returncode == 0, (
        f"bot.answer pulled in transport libs.\n" f"stdout: {proc.stdout}\nstderr: {proc.stderr}"
    )


def test_server_does_not_import_zulip_library():
    proc = _run(_SERVER_PROBE)
    assert proc.returncode == 0, (
        f"bot.server pulled in the zulip library.\n" f"stdout: {proc.stdout}\nstderr: {proc.stderr}"
    )
