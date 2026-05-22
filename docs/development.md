# Development

How to set up a local environment, run the test suites, and run the app
in "test mode" against the bundled OPC test server. For prod / serraserver
deployment see [`deployment.md`](deployment.md).

## First-time setup

```sh
make bootstrap          # uv venv
source .venv/bin/activate
make update             # uv sync --frozen --extra dev
cp .env.example .env    # fill in real values for Dremio / Firebird etc.
```

Use **uv** for everything Python (`uv sync`, `uv add`, `uv run`). Do not
use pip.

## Running tests

The CI gate is `make quality` — it runs flake8, black `--check`, the
full unit suite (with coverage), and the behave OS↔PC protocol suite.
**Run it before every commit.** If it's red, fix it; don't commit.

```sh
make quality            # the CI gate — what you commit against
```

For tighter loops while developing a slice:

```sh
# targeted unit tests
uv run pytest tests/opcua/test_scan_parser.py -v

# single behave feature or scenario
uv run behave features/protocol/scan_cycle.feature
uv run behave -n "PC publishes a parsed partij when the guard allows"

# full unit suite without lint/format/behave
make dev-test
```

### Integration tests

`make dev-test-integration` exercises the real OPC client wiring against
a live test server. Boot the server in another terminal first:

```sh
# terminal 1
make opc-server                 # uv run python scripts/opc_test_server.py

# terminal 2
make dev-test-integration
```

The integration tests set `VINEAPP_OPCUA_SECURITY=none` and
`VINEAPP_OPCUA_PLC_URL=opc.tcp://127.0.0.1:4840` themselves (via
`monkeypatch`), so no extra env is needed.

## Test mode for the OPC clients

"Test mode" means talking to the local `scripts/opc_test_server.py`
(anonymous, NoSecurity) instead of the real Omron PLC and Leuze scanner.
The toggle is one env var:

```sh
# in .env, or your shell, while developing
VINEAPP_OPCUA_SECURITY=none
VINEAPP_OPCUA_PLC_URL=opc.tcp://127.0.0.1:4840
VINEAPP_OPCUA_LEUZE_URL=opc.tcp://127.0.0.1:4840
```

`VINEAPP_OPCUA_SECURITY=none` skips the user/password and the
client cert/key entirely — only the `*_URL` vars are required. The
contract is enforced in
[`src/production_control/opcua/config.py`](../src/production_control/opcua/config.py);
every OPC caller in this repo goes through `build_client(role)` there,
so the toggle covers the web app, the headless monitor, the TUI, the
behave suite, and `scripts/write_plc.py` uniformly.

`.env.example` ships with the line commented out — prod is
secure-by-default; uncomment for local dev.

### Run the web app in test mode

```sh
# terminal 1 — fake PLC + Leuze on :4840
make opc-server

# terminal 2 — the NiceGUI app (uses the dev .env above)
make dev-server                 # python -m production_control.__web__
```

Open <http://localhost:7901>.

### Run the OPC monitor / TUI in test mode

```sh
# terminal 1 — fake PLC + Leuze
make opc-server

# terminal 2
make opc-monitor                # textual TUI

# or the headless JSONL monitor
uv run python -m production_control.opcua.monitor
```

The TUI preflights the required env vars before taking over the
terminal — if a var is missing it prints to stderr and exits with code
2 (no flashed-then-wiped error message). With `SECURITY=none` only the
two `*_URL` vars are required.

### Drive the protocol from the outside

`scripts/write_plc.py` writes to any of the protocol nodes; useful for
faking PLC state during commissioning or while iterating on the UI.

```sh
uv run python scripts/write_plc.py --scanresultaat 27246
uv run python scripts/write_plc.py --partij1 12345 --partij2 67890
uv run python scripts/write_plc.py --clear
```

In test mode (`SECURITY=none`) no creds or cert are needed.

## Related

- Project conventions and stop-conditions: [`../CLAUDE.md`](../CLAUDE.md).
- Architecture overview: [`architecture.md`](architecture.md).
- OS↔PC protocol contract: [`protocol.md`](protocol.md).
- Production deployment: [`deployment.md`](deployment.md).
