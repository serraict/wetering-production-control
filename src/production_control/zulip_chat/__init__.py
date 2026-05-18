"""Zulip chat integration: per-lot topic conversations.

The module is named `zulip_chat` to avoid shadowing the upstream `zulip` SDK.
"""

from .service import (
    ZulipMessage,
    ZulipServiceError,
    get_messages,
    narrow_url,
    post,
)
from .topics import topic_name_for

__all__ = [
    "ZulipMessage",
    "ZulipServiceError",
    "get_messages",
    "narrow_url",
    "post",
    "topic_name_for",
]
