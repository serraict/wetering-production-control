# Doing

**Status: implementation complete, awaiting smoke test.**
- All 9 automated acceptance criteria passed; `make quality` green
  (465+ tests). Bonus inline change: Anthropic prompt-caching marker
  via `bot.llm.system_message()` (see "Inline addition" below).
- Pending: manual smoke test in `#teelt` (last checkbox) +
  `work/notes/bot/zulipbot_v3_capture.md`.

## Context

Slice 3 of the Zulip insights bot (ADR-0002). Slice 2 shipped a
stateless transport: every `@serradata` mention is independent, so
follow-ups like "OK, same query for last week" force the user to
restate the full question. This slice gives the bot per-topic
multi-turn memory so a Zulip topic feels like an actual conversation.

ADR-0002 §7 calls for this explicitly: memory keyed by Zulip
`(stream, topic)`, capped by turn count *and* tokens, with replies
echoing the SQL the bot ran so the inferred context stays visible to
the user.

## Goals

1. The bot remembers prior turns per `(stream, topic)` (for DMs:
   per-sender). Follow-ups in the same topic see earlier user
   questions, assistant replies, and tool results.
2. History is bounded: oldest turns drop when either a turn cap or a
   token cap is exceeded. The cap is configurable but has sane
   defaults.
3. Every reply shows the SQL the bot just ran, so users can tell what
   context will carry forward and spot wrong-direction inferences
   early.
4. `@serradata reset` (no other text) clears the topic's history and
   acknowledges in the user's language.
5. `bot.answer(...)` stays transport-agnostic: the history store lives
   in `bot.server` (and the CLI/console can opt in trivially), not in
   `bot.answer`. Existing tests for `answer()` remain valid.

## Acceptance criteria

- [x] Two consecutive `@serradata` mentions in the same Zulip topic:
      the second can refer to "that" / "die week" / "the same query
      but for X" and get a sensible answer that builds on the first.
- [x] A third mention in a *different* topic does not see history
      from the first topic.
- [x] A DM follow-up sees history from the prior DM (same sender),
      independent of any stream history.
- [x] `@serradata reset` in a topic clears that topic's history and
      replies with an acknowledgement in Dutch/English/Polish
      matching the recent topic language (default Dutch).
- [x] After enough turns (default 8 user turns, or 30k history
      tokens — whichever first), oldest user/assistant exchanges drop
      from the prompt; the most recent exchange is always retained.
- [x] The reply text or footer shows the SQL the bot just executed
      for this turn (single line under the answer, fenced as
      `sql`).
- [x] `bot.answer(...)` accepts a `history: list[dict]` parameter
      that gets spliced between the system prompt and the new user
      question. Default empty list = current stateless behaviour.
- [x] `bot.conversation` module owns the in-memory `dict[key, deque]`
      store and the cap-enforcement. Unit-tested in isolation
      (recall/extend/reset, cap eviction by turn count and by tokens).
- [x] Import-graph test still green: `bot.conversation` does not pull
      in FastAPI or zulip.
- [x] `make quality` is green.
- [ ] (Manual) Smoke test in `#teelt`: ask a question, follow up with
      "and for last week?", verify the bot uses the carried context;
      then `@serradata reset`, ask the follow-up alone, verify it
      now lacks context.

## Design

- **Store shape.** `bot/conversation.py` exposes:
  ```python
  recall(key: str) -> list[dict]
  extend(key: str, new_messages: list[dict], tokens_added: int) -> None
  reset(key: str) -> None
  ```
  Backed by an in-process `dict[str, ConversationState]` where state
  is a `deque` of messages plus a running token estimate. Process
  restarts wipe state — acceptable for v1 (it's a chat assistant, not
  a system of record). Persistence is a follow-up if anyone notices.

- **Cap policy.** Two parallel caps, evicted oldest-first as
  user/assistant *pairs* (drop a user turn → also drop its assistant
  reply and any tool messages in between, to keep the message list
  well-formed):
  - `BOT_MAX_TURNS` (default 8 user turns)
  - `BOT_MAX_HISTORY_TOKENS` (default 30000)
  The most recent user/assistant pair is always retained even if it
  blows a cap alone — better to send one giant turn than to send
  nothing.

- **Key derivation.** In `bot.server`:
  - Stream message → `f"stream:{stream_id}:{topic_name}"`
  - DM (private) → `f"dm:{sender_email}"` (group DMs: defer; treat
    as per-sender for v1)
  The payload's `message` block already carries `type`, `stream_id`,
  `subject` (topic name), and `sender_email`. Extend
  `ZulipWebhookPayload.Message` to model the fields we need.

- **`answer(history=...)` plumbing.** New optional parameter; when
  given, messages list becomes
  `[system] + history + [{"role":"user","content":question}]`. After
  the loop, return the *new* messages appended during this call
  (everything from the user turn to the final assistant text) so the
  server can persist them. Add a `new_messages: list[dict]` field to
  `AnswerResult`.

- **Reset command.** In `bot.server`, after mention-stripping, if the
  remaining text matches `^/?reset\s*$` (case-insensitive),
  short-circuit: `conversation.reset(key)`, return a hardcoded
  Dutch/English/Polish ack based on the most recent stored language
  (or just Dutch if empty). Don't call `answer()`.

- **SQL echo.** Append a `sql` fenced block to the reply text when
  `result.sql` is non-empty (last query only — earlier turns are in
  the audit log). Slot it between the answer and the existing model
  footer. Don't change the footer.

- **What stays out of scope.**
  - Cross-process persistence (Redis, SQLite). Defer until restart
    wipes are observed as a real problem.
  - Group-DM keying (multi-participant). Treat as per-sender; if it
    matters, a follow-up slice.
  - Pruning by content (e.g. "drop tool results, keep prose"). Whole-
    turn FIFO eviction is enough for v1.
  - Re-running prior SQL on history-replay. The model sees the prior
    tool result text in the message list; it doesn't re-execute.

## Implementation steps

- [x] Add `bot/conversation.py` + `tests/bot/test_conversation.py`:
      `recall` / `extend` / `reset`, turn-pair eviction, token-cap
      eviction, "keep at least the latest pair" invariant. Pure
      Python, no FastAPI/zulip imports.
- [x] Extend `bot.answer`:
      - Add `history: list[dict] | None = None` parameter.
      - Add `new_messages: list[dict]` to `AnswerResult`.
      - Splice history between system prompt and user turn; emit only
        the new turn's messages back. Tests for: empty history (same
        as today), with-history happy path, with-history + tool call.
- [x] Extend `ZulipWebhookPayload.Message` to expose `stream_id`,
      `subject`, `sender_email`, `type`. Update payload tests.
- [x] Extend `bot.server`:
      - Derive conversation key from payload.
      - Detect the `reset` command pre-`answer()`; respond with ack.
      - Pull `recall(key)` → pass into `answer(history=...)` → on
        success, `extend(key, result.new_messages, result.tokens)`.
      - Render SQL fenced block in the response body.
      Tests: two-turn flow (state persists across `TestClient` calls
      with a shared in-process store), different-topic isolation,
      reset clears, SQL fence appears in response body.
- [x] Update `tests/bot/test_import_graph.py` so
      `bot.conversation` is asserted not to import fastapi or zulip.
- [x] `make quality` green.
- [ ] (Manual, on user) Smoke test in `#teelt`: multi-turn happy
      path, cross-topic isolation, `reset`. Note observations in
      `work/notes/bot/zulipbot_v3_capture.md`.

## Inline addition: Anthropic prompt caching

Folded into this slice (smoke-test session is the natural moment to
measure latency before/after). Reason: investigating the v2 latency
data showed every LLM hop on Sonnet 4.6 takes 5–10s, and OpenRouter's
prompt-caching docs make clear that without an explicit
`cache_control` marker we get zero caching on Anthropic — the ~5–6k
token system prompt gets re-processed on every turn.

- `bot.llm.system_message(text)` builds a system message; for
  `anthropic/*` models it wraps the text in a content block with
  `cache_control: {"type": "ephemeral"}`. Other providers get the
  plain-string shape.
- `bot.answer` routes its system prompt through `llm.system_message()`.
- Tests in `tests/bot/test_llm.py::TestSystemMessage` cover Anthropic
  default, non-Anthropic plain shape, explicit override, and the
  helper itself. `tests/bot/test_answer.py` got a small
  `_system_text()` helper so existing prompt-content assertions
  handle both shapes.
- Expected behaviour: first turn in a topic ~unchanged (cache write
  costs 1.25× input). Subsequent turns within 5 min should be
  visibly faster (TTFT drops sharply when ~90% of the prefix is
  cache-read at 0.25× input pricing).
- Verification ideas during smoke test:
  - Time two CLI calls back-to-back; second should be faster.
  - OpenRouter dashboard shows `cache_creation_input_tokens` and
    `cache_read_input_tokens` once the marker is active.
