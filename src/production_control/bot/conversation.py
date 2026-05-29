"""In-process per-key conversation memory for the bot.

Owns a dict from conversation key (e.g. `"stream:42:teelt"`,
`"dm:foo@bar"`) to a sequence of past turns. Each turn is one
user/assistant exchange — possibly multi-step due to tool calls —
captured as the list of messages `bot.answer` appended for that call,
plus the LLM-reported token total.

Caps are enforced at `extend()`: the oldest turns drop FIFO when
either the turn count or the cumulative token estimate exceeds the
limit. The most recent turn is always retained.

The store is in-process; a restart wipes it. Persistence (Redis,
SQLite) is out of scope for slice 3.
"""

from __future__ import annotations

import os
from collections import deque
from dataclasses import dataclass, field
from typing import Deque, Dict, List


DEFAULT_MAX_TURNS = 8
DEFAULT_MAX_TOKENS = 30_000


@dataclass
class _Turn:
    messages: List[dict] = field(default_factory=list)
    tokens: int = 0


_STORE: Dict[str, Deque[_Turn]] = {}


def _max_turns() -> int:
    raw = os.environ.get("BOT_MAX_TURNS")
    if not raw:
        return DEFAULT_MAX_TURNS
    try:
        return max(1, int(raw))
    except ValueError:
        return DEFAULT_MAX_TURNS


def _max_tokens() -> int:
    raw = os.environ.get("BOT_MAX_HISTORY_TOKENS")
    if not raw:
        return DEFAULT_MAX_TOKENS
    try:
        return max(1, int(raw))
    except ValueError:
        return DEFAULT_MAX_TOKENS


def recall(key: str) -> List[dict]:
    """Flat message list for `key`, oldest first. Empty if unknown."""
    turns = _STORE.get(key)
    if not turns:
        return []
    out: List[dict] = []
    for t in turns:
        out.extend(t.messages)
    return out


def extend(key: str, new_messages: List[dict], tokens_added: int) -> None:
    """Record one new turn and enforce caps oldest-first."""
    if not new_messages:
        return
    turns = _STORE.setdefault(key, deque())
    turns.append(_Turn(messages=list(new_messages), tokens=max(0, tokens_added)))
    _enforce_caps(turns)


def reset(key: str) -> None:
    _STORE.pop(key, None)


def clear_all() -> None:
    """Test helper — wipe every key in the store."""
    _STORE.clear()


def _enforce_caps(turns: Deque[_Turn]) -> None:
    max_turns = _max_turns()
    max_tokens = _max_tokens()
    # Drop oldest while over either cap, but always keep ≥1 turn.
    while len(turns) > 1 and (len(turns) > max_turns or sum(t.tokens for t in turns) > max_tokens):
        turns.popleft()
