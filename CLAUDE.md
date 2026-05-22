# CLAUDE.md — working conventions for this project

Short, hard rules. For background on what's in this repo see
[`docs/architecture.md`](docs/architecture.md),
[`docs/protocol.md`](docs/protocol.md), and
[`docs/deployment.md`](docs/deployment.md).

## Git commit style

When committing, use simple commands that match my pre-approved permissions:

- Run `git add` and `git commit` as **separate** commands, not chained with
  `&&`.
- Use `git commit -m "message"` with a single-line message. Do **not** use
  heredocs or command substitution (e.g. `"$(cat <<'EOF' ...)"`) to build the
  message.
- For multi-line messages, use repeated `-m` flags:
  `git commit -m "summary" -m "more detail"`.
- Don't use `git -C <path>`; just run git from the project root (the current
  working directory).

## Test discipline

Tests must always be green. Don't justify a failing test as pre-existing — fix
it before moving on.

**While developing a slice** (fast feedback, narrow scope):

- Run the targeted unit tests for the file/module you're changing, e.g.
  `uv run pytest tests/opcua/test_scan_parser.py -v`.
- Run a single behave feature or scenario when iterating:
  `uv run behave features/protocol/scan_cycle.feature` or
  `uv run behave -n "PC publishes a parsed partij when the guard allows"`.

**When finishing a slice** (before committing):

- `make dev-test` — full unit suite.
- `make behave` — full executable spec.
- Both must end green. If either is red, fix it (don't commit).

Integration tests (`make dev-test-integration`) need the OPC test server running
— `make opc-server` in another terminal first.

## Python tooling

- Use **uv**, never pip. Install deps with `uv sync`; add with `uv add` (or
  `uv add --dev`); run commands with `uv run`.
- Run scripts inside the production container via the `opcua_test` compose
  service pattern:
  `docker compose run --rm opcua_test python scripts/<name>.py`. No wrapper
  scripts.

## Shell habits

- Prefer the simplest bash idiom that gets the job done. Skip `2>&1`,
  `echo "exit=$?"`, multi-command chains, etc. unless they're actually needed —
  extra idioms trigger permission prompts.
- When a long-running process is needed (test server, dev server), tell me to
  run it in a separate terminal rather than backgrounding from the agent.

## Web app conventions

- Construct URLs with `router.url_path_for(...)`, not hardcoded strings, when
  the route is defined in this app.

## Don't pad

If you don't know how long something will take, say "I don't know" — don't
invent timelines to make tradeoffs sound weightier.
