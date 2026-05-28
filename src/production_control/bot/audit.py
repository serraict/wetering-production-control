"""Append-only JSONL audit log for bot invocations."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

DEFAULT_AUDIT_PATH = "var/bot-audit.jsonl"


def _resolve_path(path: Optional[str]) -> Path:
    return Path(path or os.environ.get("BOT_AUDIT_PATH", DEFAULT_AUDIT_PATH))


def append(record: Dict[str, Any], path: Optional[str] = None) -> Path:
    """Append a single JSON record to the audit log (one line, UTC ISO ts)."""
    out = _resolve_path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    full = {"ts": datetime.now(timezone.utc).isoformat(), **record}
    with out.open("a", encoding="utf-8") as f:
        f.write(json.dumps(full, default=str) + "\n")
    return out
