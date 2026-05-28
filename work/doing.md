# Doing

## Context

Follow-up to the slice 1 smoke-run (see
`work/notes/bot/zulipbot_v1_capture.md`): when asked about "this year"
the bot used 2025 instead of 2026 because the system prompt has no
temporal anchor — the model fell back on its training data. Operators
ask time-relative questions ("deze week", "vorig jaar", "afgelopen
maand") all the time, so the bot needs to know what "now" is.

Two other things to settle in the same prompt-shaping pass while
we're here:

- **Languages.** The bot needs to understand and reply in Dutch,
  English, and Polish — Wetering's workforce mixes the three. The
  current `SYSTEM_RULES` defaults to Dutch and is silent on the
  others.
- **Date display.** Use ISO 8601 week date notation (`YYYY-Www-D`,
  Monday = day 1) as the bot's default way to talk about dates. This
  keeps temporal answers unambiguous across the three languages and
  matches how the team reasons about production weeks.

Tiny fix per concern; all three land in one slice because they share
the same `_system_prompt()` change and the same smoke-run.

## Goals

1. The bot's system prompt contains today as an ISO 8601 week date
   (`YYYY-Www-D`) plus enough surrounding info (weekday name, year,
   week bounds) for the model to resolve Dutch, English, and Polish
   temporal phrases against the operator's calendar.
2. Time-relative questions ("deze week", "this year", "w zeszłym
   tygodniu") resolve against the operator's calendar — not the
   model's training cutoff — and the bot can reply in the language of
   the question.
3. The bot defaults to ISO 8601 week date notation when it talks
   about dates and periods in its answers, regardless of reply
   language.
4. `_system_prompt()` is deterministic when an explicit `now` is
   passed, so tests don't depend on the real clock.

## Acceptance criteria

- [ ] System prompt includes a "Current date" block with: today as
      ISO 8601 week date (`2026-W22-4`), today as ISO calendar date
      (`2026-05-28`) for cross-reference, English weekday name, year,
      and pre-resolved "this week" bounds (`2026-W22-1` through
      `2026-W22-7`).
- [ ] System prompt instructs the bot to reply in the user's language
      (Dutch / English / Polish), and to express dates and periods in
      ISO 8601 week date form by default.
- [ ] `answer.answer(...)` accepts an optional `now: date | datetime`
      argument so tests can inject a fixed "today"; default is
      `date.today()`.
- [ ] Unit test: with `now=date(2026, 5, 28)`, the rendered system
      prompt contains `2026-W22-4`, `2026-05-28`, `Thursday`, `2026`,
      `2026-W22-1`, and `2026-W22-7`.
- [ ] Unit test: the rendered system prompt explicitly names Dutch,
      English, and Polish as supported reply languages.
- [ ] Unit test: a question with `now=date(2026, 5, 28)` flowing
      through `answer.answer(...)` reaches the LLM with the date block
      in `messages[0].content` (verified via fake `llm_chat`).
- [ ] `make quality` is green.

## Design

- **Where the date lives.** New helper `bot/answer.py::_temporal_context(now)`
  returning a small markdown block. Concatenated into `_system_prompt()`
  alongside `SYSTEM_RULES` and `schema.render()`. Keeping it in
  `answer.py` (not `schema.py`) reflects the static/dynamic split:
  schema is content the model can cache; the date changes every day.
- **Format.** ISO 8601 week date as the primary form, with the ISO
  calendar date alongside so the model can join against Dremio columns
  that come back as `YYYY-MM-DD`:
  ```
  ## Current date
  Today: 2026-W22-4 (Thursday, 2026-05-28)
  Current year: 2026
  Current week: 2026-W22 — 2026-W22-1 (2026-05-25) through 2026-W22-7 (2026-05-31)
  ```
  Pre-resolving the week bounds is the highest-leverage line — the
  model doesn't have to know ISO week conventions, it just substitutes.
  `date.isocalendar()` gives `(year, week, weekday)` with `weekday`
  already Monday=1..Sunday=7, so no conversion math.
- **Language rules — replace the current Dutch-only default.**
  `SYSTEM_RULES` currently says "Reply in the user's language; default
  to Dutch." Change to: "Detect whether the user wrote in Dutch,
  English, or Polish, and reply in the same language. Default to
  Dutch if the language is unclear or mixed." Add: "When you talk
  about dates or periods in your reply, use ISO 8601 week date
  notation (`YYYY-Www-D`, where day 1 is Monday) regardless of
  language."
- **Injection seam.** `answer.answer(...)` gains a kwarg
  `now: date | datetime | None = None`. When `None`, `date.today()` is
  used. `_system_prompt()` takes the same `now` and forwards to
  `_temporal_context`.
- **No locale-specific weekday names.** English `%A` is fine — the
  model handles the translation. Avoids the `locale.setlocale` mess
  and keeps the prompt deterministic across environments.
- **Tests.** Add `tests/bot/test_temporal_context.py` for the helper
  directly; extend `tests/bot/test_answer.py` with one test asserting
  that an injected `now` and the multilingual rule reach the LLM via
  `messages[0].content`.

## Implementation steps

- [ ] Add `_temporal_context(now: date) -> str` in `bot/answer.py`
      returning the markdown block above (ISO week date + ISO calendar
      date + week bounds).
- [ ] Update `SYSTEM_RULES`: replace the Dutch-only line with the
      Dutch / English / Polish rule, and add the ISO 8601 week-date
      display rule.
- [ ] Thread an optional `now` kwarg through `_system_prompt()` and
      `answer()`; default to `date.today()` at the `answer()` call
      site so `_system_prompt` stays pure.
- [ ] Write `tests/bot/test_temporal_context.py` with the
      acceptance-criterion assertions (week date, calendar date,
      weekday, year, week bounds).
- [ ] Extend `tests/bot/test_answer.py` with: (a) the injected-`now`
      flow-through test, (b) an assertion that the language rule
      names all three languages.
- [ ] `make quality` green.
- [ ] Smoke-run the CLI on real Dremio: ask "wat speelt er deze week"
      (Dutch), "what's happening this week" (English), and one Polish
      question; confirm the SQL filters on the right week and that
      replies come back in the matching language with ISO week-date
      formatting.
