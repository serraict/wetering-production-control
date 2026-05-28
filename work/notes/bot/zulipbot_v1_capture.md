# Zulip insights bot — v1 capture

Shipped: `286d30f` (2026-05-28). Slice 1 of ADR-0002 — transport-agnostic
core + CLI + console REPL.

## What was confirmed on real data

- Model: `anthropic/claude-sonnet-4.6` (the default `BOT_MODEL`).
- Overview selection was correct on the basic questions tried — the
  schema-renderer system prompt grounds the model well enough that it
  picked the right Dremio view and reasonable columns.
- Generated SQL was acceptable.

## What surprised us

- **The model used 2025 instead of 2026** for "this year" / current-week
  style filters. The system prompt currently includes no temporal
  anchor, so the model fell back on its training data. This is the
  clearest behavioural bug from the smoke-run.
- **Felt slow / laggy.** Subjective only — no measurement yet. Probable
  contributors: OpenRouter hop, schema-in-system-prompt token cost on
  every call (no caching wins through OpenRouter for many models), and
  the two-round-trip pattern (tool call → result → final text).

## Follow-ups (now in backlog)

- Inject the current date into the system prompt so "this week",
  "this year" etc. resolve to the operator's calendar, not the
  model's training cutoff.
- Investigate bot latency: instrument per-step timings in the audit
  log, then decide whether to chase caching, schema-via-tools, or a
  smaller/faster model.

## What stayed in scope and worked as planned

- SQL guard never tripped on real-model output during the smoke-run.
- Audit JSONL writes one record per question with the executed SQL,
  row count, tokens, and latency — useful for the slow/lag triage
  above.
- `make bot-console` REPL is convenient for iteration.

## Deferred (still slice 2+)

- Zulip transport (outgoing webhook + FastAPI endpoint).
- Per-topic multi-turn memory.
- Polish: locale-aware result formatting, links back into the app,
  cost/latency dashboards from the audit JSONL.
