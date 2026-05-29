# Doing

**Status: shipped 2026-05-29 (commit `c6257b4`).** Capture in
`work/notes/bot/zulipbot_v2_capture.md`. Smoke-tested in #teelt — bot
answers in Dutch with markdown table and footer.

## Context

Slice 2 of the Zulip insights bot (ADR-0002). The CLI/console
prototype works end-to-end against real Dremio and OpenRouter; this
slice gives the bot a Zulip-facing surface so the rest of the team
can actually talk to it.

Picking the outgoing-webhook style (as flagged in ADR-0002): Zulip
POSTs a JSON payload to our endpoint when the bot is @-mentioned in a
stream or DM'd; our endpoint replies synchronously with the answer
content. No long-poll, no Zulip Python SDK on our side — we just
speak the HTTP webhook protocol. This keeps `bot.answer(...)`
transport-agnostic and `bot.server` thin.

## Goals

1. A `bot.server` FastAPI app exposes `POST /zulip` and `GET /health`.
2. `POST /zulip` validates a shared outgoing-webhook token, extracts
   the user's question (mention prefix stripped), calls
   `bot.answer(...)`, and responds with
   `{"content": "<answer text + footer>"}`.
3. The bot runs as its own compose service alongside the web app and
   the protocol daemon, sharing the image but with a different
   entrypoint.
4. v1 stays stateless: each @-mention or DM is an independent call.
   Per-topic memory is slice 3.

## Acceptance criteria

- [ ] `POST /zulip` with a valid Zulip outgoing-webhook payload and
      the correct token returns 200 with JSON
      `{"content": "<text>\n\n<footer>"}` where the text comes from
      `bot.answer(question).text` and the footer from
      `answer.footer(result)`.
- [ ] `POST /zulip` with a wrong/missing token returns 401.
- [ ] `POST /zulip` with a malformed payload returns 422 (FastAPI
      default; document this — Zulip will retry).
- [ ] The mention prefix (`@**Bot Name**`, including silent-mention
      form `@_**Bot Name**`) is stripped from the message content
      before it reaches `bot.answer`.
- [ ] `GET /health` returns 200 with a small JSON body
      (`{"status": "ok"}`).
- [ ] `bot.server` does not import the `zulip` package (we speak the
      HTTP protocol directly). Extended import-graph test verifies.
- [ ] `docker-compose.yml` has a new `bot` service: same image,
      entrypoint runs `uvicorn production_control.bot.server:app`,
      env_file: `.env`, restart policy + healthcheck.
- [ ] `.env.example` documents `ZULIP_OUTGOING_WEBHOOK_TOKEN`.
- [ ] `make quality` is green.
- [ ] (Manual) Smoke test in a Zulip dev org: register an outgoing
      webhook bot, @-mention it in a stream → response posts under
      the same topic; DM it → response posts in the DM.

## Design

- **Module shape.**
  - `bot/server.py` — FastAPI app with two routes.
  - `bot/zulip_payload.py` — Pydantic models for the outgoing
    webhook payload + mention-stripping helper. Pure functions,
    unit-tested in isolation.
  - `tests/bot/test_zulip_payload.py` — payload parsing + mention
    stripping.
  - `tests/bot/test_server.py` — FastAPI `TestClient`, mocked
    `answer.answer` (avoid hitting OpenRouter / Dremio in unit tests).
- **Payload model (lean).** Zulip's outgoing-webhook POST is a fat
  JSON; we only need:
  - `token: str`
  - `bot_full_name: str` (used to strip the mention)
  - `data: str` (the raw message content, including the mention)
  - `message.type: "stream" | "private"` (informational; v1 doesn't
    branch on it)
  Other fields accepted-and-ignored via `model_config = {"extra":
  "ignore"}`.
- **Token verification.** Compare `payload.token` to
  `os.environ["ZULIP_OUTGOING_WEBHOOK_TOKEN"]` with `secrets.compare_digest`.
  If the env var is unset, refuse all requests (return 503 or 401 +
  log a clear error — pick 401 for simplicity).
- **Mention stripping.** Strip leading
  `@**<bot_full_name>** ` and `@_**<bot_full_name>** ` (both forms;
  silent-mention variant has an underscore). Trim whitespace. If
  nothing remains after stripping, return 200 with an empty body so
  Zulip doesn't loop.
- **Response shape.** `{"content": text + "\n\n" + footer}`. Zulip
  posts that under the same stream/topic for stream mentions, as a
  DM reply for DMs — Zulip handles the routing based on the original
  message.
- **Compose service.**
  ```yaml
  bot:
    image: ghcr.io/serraict/wetering-production-control:latest
    entrypoint: ["uvicorn", "production_control.bot.server:app",
                 "--host", "0.0.0.0", "--port", "7902"]
    ports:
      - "7902:7902"
    env_file:
      - .env
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "python", "-c",
             "import urllib.request,sys; urllib.request.urlopen('http://localhost:7902/health', timeout=2)"]
      interval: 30s
      timeout: 5s
      retries: 2
      start_period: 10s
    networks:
      - serra-vine
  ```
  Port `7902` chosen to sit next to `7901` (web). Adjust if it's
  taken.
- **Out of scope for this slice.** Per-topic conversation memory
  (slice 3). Auth scoping (slice 4). Rate limiting. Async/background
  response — Zulip's outgoing webhook is synchronous, the answer must
  fit within the webhook timeout (typically ~30s).

## Implementation steps

- [ ] Add `bot/zulip_payload.py`: Pydantic models + `strip_mention(...)`
      helper. Unit tests for both mention forms, with and without
      surrounding whitespace, and the "nothing left" edge case.
- [ ] Add `bot/server.py`: FastAPI `app`, `POST /zulip`, `GET /health`,
      token verification via `secrets.compare_digest`. The route calls
      `answer.answer(question)` and assembles `text + "\n\n" + footer`.
- [ ] Tests with FastAPI `TestClient`: happy path (mocked answer),
      wrong token → 401, missing token env → 401, malformed payload
      → 422, `/health` → 200, mention stripping behavior end-to-end.
- [ ] Extend `tests/bot/test_import_graph.py` so `bot.server` is also
      asserted not to import `zulip` (FastAPI is allowed for the
      server module specifically — the strict no-FastAPI rule only
      applies to `bot.answer`).
- [ ] Add the `bot` service to `docker-compose.yml`.
- [ ] Add `ZULIP_OUTGOING_WEBHOOK_TOKEN=` to `.env.example` (with a
      brief note on where to get the value in the Zulip admin UI).
- [ ] `make quality` green.
- [ ] (Manual, on user) Register an outgoing-webhook bot in the
      Zulip dev org, set the URL to the bot service, smoke-test
      stream-mention and DM.
