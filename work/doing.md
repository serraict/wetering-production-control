# Doing

## Context

Growers, planners, and operators currently have no in-app place to discuss a
specific production lot. Questions, photos, and decisions land in WhatsApp,
e-mail or hallway conversations and are then lost from the lot's history.

Wetering already uses Zulip as its team chat. Zulip's stream/topic model maps
cleanly onto our domain: one topic per lot inside a dedicated stream. A bot
account in the Zulip org can act on our behalf to read and post messages, so
the production_control app does not need per-user OAuth.

Entry point for this feature is the existing scan landing page
`src/production_control/web/pages/scan.py:180` (`/scan/view/{id}`), which
already renders the lot's high-level details on a mobile-friendly layout.

## Goals

- Make the conversation about a lot visible **from** the lot, not next to it.
- One Zulip topic per `PottingLot.id`, in the `teelt` stream.
- Single shared bot identity for read + post; no per-user auth in v1.
- Don't ship a generic chat UI — ship the minimum that closes the
  "where's the conversation about lot N?" loop.

## Acceptance criteria

- [x] On `/scan/view/{id}`, below the existing lot detail cards, a
      "Communicatie" card lists recent messages from the lot's Zulip topic
      (sender + relative timestamp + content), newest at the bottom.
- [x] The card has a text input + send button that posts a message to that
      topic via the bot. After posting, the new message appears in the list
      without a full-page reload.
- [x] A link "Open in Zulip" jumps to the topic in the Zulip web client (uses
      Zulip's narrow URL with the stream + topic name).
- [x] If the bot can't reach Zulip, the card degrades to a non-blocking error
      state ("Zulip onbereikbaar") and the rest of the page still renders.
- [x] Topic naming is deterministic: the topic name is exactly the lot id as
      a string (e.g. `"12345"`). No mapping table.
- [x] Posts are attributed to the logged-in user: the message body is
      prefixed with `**{user_name}**: ` where `user_name` comes from
      `web/auth.py:get_current_user()`. The Zulip account is still the bot.
- [x] Archived / completed lots behave the same as active lots — the card is
      always shown and writable.
- [x] Zulip credentials live in env vars (`ZULIP_*`), loaded via a
      `ZulipConfig` dataclass following the pattern of
      `src/production_control/config/opc_config.py`.
- [x] Integration tests against a real Zulip env, marked
      `@pytest.mark.integration`, mirroring `tests/test_opc_integration.py`.
- [x] Unit tests for topic-name derivation and the rendering helper, with the
      Zulip client stubbed.

## Design

### Stream & topic mapping

- Stream: `teelt` (existing).
- Topic name: the lot id rendered as a string, nothing else (e.g. `"12345"`).
  Deterministic, never changes, no mapping table.

### Reusable module, not page-specific

The Zulip integration lives in its own module behind a service interface, so
the same `get_messages(lot)` / `post(lot, content)` calls can later back other
entry points (inspectie, other detail pages) without rewiring. The scan page
is just the first caller. Same pattern as the OPC/UA client today.

### Module layout

```
src/production_control/
  zulip/
    __init__.py
    client.py         # thin wrapper over zulip-python or httpx
    topics.py         # topic_name_for(lot), parse_lot_id_from_topic(name)
    service.py        # high-level: get_messages(lot), post(lot, content)
  config/
    zulip_config.py   # ZulipConfig dataclass + manager (OPC pattern)
  web/pages/
    scan.py           # extended: render_communication_card(lot)
```

`service.py` is the only thing the web layer talks to. It returns plain
dataclasses (`ZulipMessage(sender, timestamp, content_html)`), so the UI never
imports the Zulip SDK.

### Library choice

Use the official [`zulip`](https://pypi.org/project/zulip/) Python client
(Zulip's own SDK). It's synchronous and fits NiceGUI's event handlers via
`run.io_bound`.

### Configuration

```python
@dataclass
class ZulipConfig:
    site: str                # e.g. "https://wetering.zulipchat.com"
    bot_email: str           # e.g. "production-bot@wetering.zulipchat.com"
    bot_api_key: str         # secret
    stream: str = "teelt"
    request_timeout: int = 5
    message_history_limit: int = 50
```

Env vars: `ZULIP_SITE`, `ZULIP_BOT_EMAIL`, `ZULIP_BOT_API_KEY`,
`ZULIP_STREAM`, `ZULIP_TIMEOUT`, `ZULIP_HISTORY_LIMIT`. Loaded via the same
manager-singleton pattern as `OPCConfigManager`.

### UI behaviour

- On render, fire `service.get_messages(lot)` in a background task; show a
  small spinner inside the card while loading. Don't block the page.
- Messages render as: bold sender (the bot, always), muted relative
  timestamp, then the message body. Body is Zulip's `rendered_content`
  (server-sanitized HTML) injected via `ui.html` — supports @mentions,
  emoji, code blocks, links.
- Input is a plain `ui.textarea` + send button. The submitted text is
  prefixed with `**{current_user.name}**: ` (from
  `web/auth.py:get_current_user()`) before being sent via the bot, so the
  human author is visible in every message. Guest users post as "Guest".
- On send, re-fetch the topic and re-render the message list. No optimistic
  append.
- No realtime/long-poll in v1. Add a small "Vernieuwen" button. Realtime via
  Zulip's event queue is a follow-up.
- The card is always rendered, regardless of lot status.

### Failure modes

- Network error or 401/403 from Zulip → log + render a single-line error in
  the card. No exception bubbles to the page.
- Topic does not exist yet → posting creates it (Zulip auto-creates topics on
  first message). Reading a non-existent topic returns zero messages — that's
  fine.

## Decisions (resolved)

- Topic name = lot id as string, nothing else.
- No `lot_id ↔ topic` mapping table; topic name is deterministic.
- Use the official `zulip` Python SDK.
- Render Zulip's `rendered_content` (server-sanitized HTML) via `ui.html`.
- After posting, re-fetch the topic — no optimistic append.
- Posts are prefixed with `**{user_name}**: ` from `get_current_user()`; the
  Zulip account is always the bot. Guest fallback when unauthenticated.
- Archived / completed lots behave like any other lot — card always shown.

## Implementation steps

- [x] Add `zulip` to `pyproject.toml` dependencies; `uv sync`.
- [x] Create `src/production_control/config/zulip_config.py` with
      `ZulipConfig` + `ZulipConfigManager` + `get_zulip_config()`, copying the
      OPC config pattern.
- [x] Create `src/production_control/zulip_chat/topics.py` with
      `topic_name_for(lot) -> str` and unit tests in
      `tests/zulip_chat/test_topics.py`. (Module is `zulip_chat`, not
      `zulip`, to avoid shadowing the upstream SDK.)
- [x] Create `src/production_control/zulip_chat/client.py` — a thin
      `ZulipClient` wrapping the SDK, with `get_messages_in_topic(stream,
      topic, limit)` and `send_message(stream, topic, content)`. Connection
      lazy + reused.
- [x] Create `src/production_control/zulip_chat/service.py` exposing
      `get_messages(lot) -> list[ZulipMessage]`, `post(lot, content) -> int`,
      `narrow_url(lot) -> str`. Returns dataclasses, hides the SDK.
- [x] Extend `src/production_control/web/pages/scan.py:view_batch` with a
      `render_communication_card(lot)` block (lives in
      `web/components/communication_card.py`).
- [x] Wire the send button → `service.post(lot, content)` →  re-fetch →
      update the message list.
- [x] Add a refresh button + "Open in Zulip" link.
- [x] Failure-mode handling: catch in `service`, return an error dataclass,
      render a one-line state in the card.
- [x] Integration test `tests/test_zulip_integration.py`
      (`@pytest.mark.integration`) that, against a real Zulip env, posts a
      message to a throw-away topic and reads it back.
- [x] Unit tests for `service` with the client mocked: empty topic, populated
      topic, post path, error path, prefix parse + fallback.
- [x] Docs: messaging decisions captured as an ADR
      (`docs/adr/0001-zulip-messaging-backend.md`) instead of a `work/notes`
      page. ADR README sits at `docs/adr/README.md`.

## Deltas from the original plan

- Backend module is named `zulip_chat` (not `zulip`) so it doesn't shadow
  the upstream `zulip` SDK package.
- The UI uses `ui.chat_message` bubbles rather than a stack of `ui.html`
  blocks — gives a chat-like look, with `sent=True` aligning the current
  user's bubbles to the right and `name` suppressed on own messages.
- The service parses the leading `**name**: ` prefix on read and exposes
  `author_name` / `body_html`, so the bubble shows the human author rather
  than the bot's account name.
- The standalone "Opmerkingen" card was removed; `lot.opmerking` now
  renders as a pinned bubble at the top of the Communicatie card with
  author "Teeltopmerking" and no stamp.
- Documentation took the form of an ADR rather than a `work/notes/`
  scratchpad — better fit for the decisions that need to outlive this work
  item.

## Out of scope (v1)

- Realtime updates (Zulip event queue / long poll).
- Per-user identity in posts.
- File / image upload from the lot view.
- Notifications/mentions routed back into production_control.
- Other entry points beyond `/scan/view/{id}` — same backend will support
  them, but UI work is separate.
