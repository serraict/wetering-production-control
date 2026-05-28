# Architecture Decision Records

Significant architecture decisions are recorded here as ADRs, following the
short [Michael Nygard format](https://cognitect.com/blog/2011/11/15/documenting-architecture-decisions):

- **Status** — proposed, accepted, deprecated, superseded by ADR-XXXX.
- **Context** — the forces at play; what made this decision necessary.
- **Decision** — what we are going to do.
- **Consequences** — the resulting trade-offs, good and bad.

## Numbering

Files are named `NNNN-kebab-case-title.md` with a zero-padded sequence
number. Allocate the next free number; never reuse a number, even if the ADR
is later deprecated.

## When to write one

Write an ADR when a decision is hard to reverse, crosses module boundaries,
or would surprise a future reader who's only looking at the code. Don't ADR
routine implementation choices.

## Index

- [0001 — Zulip-backed per-lot messaging](0001-zulip-messaging-backend.md)
- [0002 — Zulip insights bot](0002-zulip-insights-bot.md)
