"""Tool registry for the bot.

Each tool module exports a `SPEC` (the JSON schema sent to the LLM
API as a function definition) and a `call(...)` implementation.
This module collects them.
"""

from . import run_dremio_sql

TOOLS = [run_dremio_sql]
SPECS = [t.SPEC for t in TOOLS]
BY_NAME = {t.SPEC["function"]["name"]: t for t in TOOLS}
