# Doing

**Status: slice shipped in `286d30f`. Smoke-run on real Dremio
user-confirmed.** Only bookkeeping left: write the v1 capture note
under `work/notes/bot/zulipbot_v1_capture.md` once we have something
worth recording, then clear this file.

## Context

First slice of the Zulip insights bot (ADR-0002). The bot answers
ad-hoc questions about the app's overviews by writing read-only SQL
against Dremio. This slice ships the **transport-agnostic core plus a
CLI** — no Zulip wiring yet, so we can iterate on prompt, schemas, and
the SQL guard against the real Dremio without the chat moving piece in
the loop.

See [`docs/adr/0002-zulip-insights-bot.md`](../docs/adr/0002-zulip-insights-bot.md)
for the architecture rationale (process shape, OpenRouter, tool
organisation, audit log).

## Goals

1. `python -m production_control.bot.cli "<question>"` returns a useful
   answer for at least one realistic question against real Dremio,
   using the SQLModel-derived schema context and the `run_dremio_sql`
   tool.
2. The bot is wired through the configured model on OpenRouter
   (`BOT_MODEL`, default `anthropic/claude-sonnet-4.6`).
3. `bot.answer(question) -> str` is transport-agnostic — no Zulip or
   FastAPI imports — so slice 2 only adds the webhook.
4. Every CLI invocation appends a structured record to the audit JSONL
   from the first commit.

## Acceptance criteria

- [x] `uv run python -m production_control.bot.cli "..."` prints a
      coherent answer against real Dremio (user-confirmed: bot answers
      basic questions correctly).
- [x] SQL guard rejects: non-`SELECT` statements, multiple statements,
      `PRAGMA`/`SET`, and unparseable input. Unit-tested for each
      rejection path. (`tests/bot/test_sql_guard.py`, 18 cases.)
- [x] SQL guard injects `LIMIT 500` when absent and leaves an existing
      `LIMIT` alone. Unit-tested.
- [x] Schema renderer walks the current SQLModel classes (potting_lots,
      bulb_picklist, inspectie, spacing, vloerplan, products) and
      produces a stable system-prompt section. Unit-tested against
      the live model classes (`tests/bot/test_schema.py`).
- [x] `bot.answer(...)` is callable without importing FastAPI or any
      Zulip SDK (`tests/bot/test_import_graph.py`, subprocess probe).
      Required pruning `production_control/potting_lots/__init__.py`
      re-exports to keep nicegui out of the import chain.
- [x] Audit JSONL contains one record per CLI invocation with
      `{ts, question, model, sql, rows, latency_ms, tokens,
      iterations, error}` — verified by `tests/bot/test_answer.py`.
- [x] `make quality` is green (391 unit tests, behave protocol suite
      still green).

## Design

- **Engine.** Reuse `create_engine(os.getenv("VINEAPP_DB_CONNECTION"))`
  exactly as `DremioRepository` does (`src/production_control/data/repository.py:79`).
  No new connection plumbing.
- **LLM.** `bot/llm.py` wraps the OpenAI-compatible client pointed at
  OpenRouter. One function: `chat(messages, tools) -> response`.
  Reads `OPENROUTER_API_KEY` and `BOT_MODEL` from env. No
  provider abstraction.
- **Tools.** One tool — `bot/tools/run_dremio_sql.py` — exporting
  `SPEC` (hand-written JSON schema) and `call(query: str) -> str`.
  Collected in `bot/tools/__init__.py` (`TOOLS`, `SPECS`, `BY_NAME`).
  Hand-written SPEC, not type-hint reflection.
- **SQL guard.** `bot/sql_guard.py` uses sqlglot to parse the
  generated SQL. Reject if not single `SELECT`/`WITH`; reject
  DDL/DML/`PRAGMA`/`SET`; if no top-level `LIMIT`, inject `LIMIT 500`.
  Raises `BadSqlError` (caught by the tool call site, which returns
  the message to the model so it can retry).
- **Schema renderer.** `bot/schema.py` introspects each SQLModel via
  `model.__table__` / `model.__fields__` and renders one markdown
  block per overview with view name, columns + types, and one or two
  example queries pulled from the repository code where available.
  Output is deterministic so the system prompt is stable across runs.
- **Answer loop.** `bot/answer.py` builds the system prompt
  (`schema` + rules), appends the user question, calls `llm.chat`,
  and processes `tool_calls` via `tools.BY_NAME`. Caps at 8
  iterations. Returns the final assistant text, including a
  generated footer with model/latency/tokens.
- **Audit.** `bot/audit.py` appends one JSON object per invocation to
  `BOT_AUDIT_PATH` (env, default `var/bot-audit.jsonl`).
- **CLI.** `bot/cli.py` parses `sys.argv[1]`, calls
  `answer(question)`, prints the result + footer + SQL on stdout.
  Non-zero exit on uncaught exception.
- **Tests.** Under `tests/bot/`:
  - `test_sql_guard.py` — each rejection path + LIMIT injection.
  - `test_schema.py` — renders against the real SQLModel classes,
    snapshot or structural assertions (no live Dremio call).
  - `test_tools_run_dremio_sql.py` — happy path with an in-memory or
    fake engine; guard rejection produces a model-visible error
    string.
  - `test_answer.py` — drives `answer(...)` with a fake LLM that
    returns a scripted tool call, asserts loop termination, footer
    content, and audit record shape.
  - `test_import_graph.py` — `bot.answer` import must not pull in
    `fastapi` or `zulip`.

## Implementation steps

- [x] Add OpenRouter / sqlglot dependencies via `uv add`
      (`openai`, `sqlglot`).
- [x] Scaffold `src/production_control/bot/{__init__,llm,sql_guard,
      schema,dremio_tool,answer,audit,cli}.py` and
      `src/production_control/bot/tools/{__init__,run_dremio_sql}.py`.
- [x] Implement `sql_guard.normalize` + unit tests.
- [x] Implement `schema.render` walking the existing SQLModel classes;
      unit tests against the live classes.
- [x] Implement `dremio_tool.execute` + `dremio_tool.format` (markdown
      table, row cap). Tests use an in-memory SQLite engine.
- [x] Implement `bot/tools/run_dremio_sql.py` (SPEC + call wiring
      guard → execute → format).
- [x] Implement `llm.chat` against the OpenAI-compatible client.
- [x] Implement `answer.answer(question)`: build prompt, loop tool
      calls (cap 8), assemble footer. Audit wired from `answer` so
      every call is recorded (including LLM exceptions).
- [x] Implement `audit.append(record)` writing JSONL with ISO ts.
- [x] Implement `bot/cli.py` (stdin question → stdout answer).
- [x] Add `tests/bot/` covering the acceptance criteria (48 tests
      across guard/schema/dremio_tool/tools/answer/cli/console/
      import-graph).
- [x] Bonus: `bot/console.py` REPL + `make bot` / `make bot-console`
      Makefile targets, mirroring web's `make console`.
- [x] Smoke-run the CLI against real Dremio with one realistic
      question (user-confirmed). Capture note pending — see open
      questions below.
- [x] `make quality` green.
