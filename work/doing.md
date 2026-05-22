# Doing

## Context

Five modules independently wire OPC UA clients from `VINEAPP_OPCUA_*`
env vars (`monitor.py`, `leuze.py`, `protocol/scan_cycle.py`,
`potting_lots/line_controller.py`, `scripts/write_plc.py`). Each has its
own `_env()` helper and its own copy of "set user, set password, set
security". Only two of them (`monitor.py`, `line_controller.py`) honor
`VINEAPP_OPCUA_SECURITY=none`; the other three demand user/pwd even when
the dev fallback is requested.

Symptoms surfaced today:

- `make opc-monitor` flashes a SystemExit(2) and clears the screen
  because `_env()` fails inside an asyncio task after Textual has taken
  over. The preflight check landed in `tui.py` is a workaround; the
  underlying inconsistency stays.
- `features/protocol/environment.py` already proves the env-based
  `SECURITY=none` shape works — but only against modules that honor it.

Goal of this slice: collapse to one config helper so dev runs with no
certs/creds and prod runs unchanged, decided by env vars only.

## Goals

- Single source of truth for "build a configured asyncua client".
- `VINEAPP_OPCUA_SECURITY=none` works for **every** OPC UA caller, not
  just two of them. Anonymous + NoSecurity, no creds, no cert.
- Default (env unset or any other value) stays exactly as today:
  user/pwd + Basic256Sha256_SignAndEncrypt, cert/key from env.
- No new abstractions in callers — each callsite collapses to "build
  client, use client".
- Preflight error messages name the missing vars for the *selected*
  mode (so `SECURITY=none` mode only complains about URLs, not certs).

## Acceptance criteria

- [ ] `src/production_control/opcua/config.py` exports
      `require_env(name)` and `build_client(role)` with the behavior
      table below. Unit tests cover both modes for both roles.
- [ ] `monitor.py`, `leuze.py`, `protocol/scan_cycle.py`,
      `potting_lots/line_controller.py`, and `scripts/write_plc.py` all
      use `build_client` exclusively. Their private `_env()` helpers
      are gone.
- [ ] `PottingLineController.__init__` no longer takes `secure=`;
      `tests/test_opc_integration.py` drops the override and relies on
      `VINEAPP_OPCUA_SECURITY=none` in the test env (parity with the
      behave suite).
- [ ] `tui.py` preflight asks `config.required_env_for(mode)` instead
      of holding its own static list, so `SECURITY=none` only requires
      `VINEAPP_OPCUA_PLC_URL` and `VINEAPP_OPCUA_LEUZE_URL`.
- [ ] `make quality` green. `make behave` green. `make
      dev-test-integration` green when run against `make opc-server`.
- [ ] `docs/deployment.md` env table reflects the two modes (already
      documents `SECURITY=none`; just verify it matches the new code).

## Design

### Behavior matrix

| `VINEAPP_OPCUA_SECURITY` | Auth      | Transport                  | Required env (per role)              |
| ------------------------ | --------- | -------------------------- | ------------------------------------ |
| unset / any other value  | user+pwd  | Basic256Sha256_SignAndEncrypt | URL, USER, PASSWORD, CLIENT_CERT, CLIENT_KEY |
| `none`                   | anonymous | NoSecurity                 | URL only                             |

`VINEAPP_OPCUA_CLIENT_APP_URI` stays optional in both modes.

### Public API

```python
# src/production_control/opcua/config.py
SecurityMode = Literal["secure", "none"]

def current_mode() -> SecurityMode: ...
def required_env_for(mode: SecurityMode, role: Role) -> list[str]: ...
def require_env(name: str) -> str: ...
def build_client(role: Literal["plc", "leuze"]) -> Client: ...
```

Why a function returning a `Client` and not a class: callers want an
already-wired client and nothing else. A class adds a seam without a
payoff.

Why role-based: PLC and Leuze read different URL/user/password vars but
share the secure/insecure shape. Two roles isolate "which credentials"
from "how we secure them" without making every callsite pass six args.

### What stays put

- The Leuze malformed-cert monkey-patch (`LenientCertificate` in
  `leuze.py`). It's a device-firmware workaround, not a security-config
  concern. Keep it as a side effect at module import.
- The hardcoded `Basic256Sha256` policy. Only one policy is in use; an
  env var for policy choice is YAGNI until a second deployment needs
  something else.
- `scripts/show_opcua_config.py` — read-only, doesn't open a client,
  leave it.

### Risk

Behavior-preserving for prod (same env vars, same defaults). Dev gets a
real fix: `leuze.py`, `scan_cycle.py`, and `write_plc.py` will now
honor `SECURITY=none` (they refused to before). That's the bug we're
fixing, not a regression.

## Implementation steps

Each step ends with a commit and `make quality` green. Stop after each
and wait for go-ahead.

- [ ] **`opcua/config.py` + unit tests.** No callers migrated yet.
  - `current_mode`, `required_env_for`, `require_env`, `build_client`.
  - `tests/opcua/test_config.py`: secure mode wires user/pwd + cert,
    none-mode is anonymous, missing env raises with a clear message,
    `required_env_for("none", "plc") == ["VINEAPP_OPCUA_PLC_URL"]`.

- [ ] **Migrate `monitor.py` and `tui.py` preflight.** Smallest
      change; monitor already honors `SECURITY=none` so behavior is
      preserved. TUI preflight switches to `required_env_for`.

- [ ] **Migrate `leuze.py`.** Drops its private `_env`; gains
      `SECURITY=none` support for the first time. Verify the behave
      suite still passes (it uses `SECURITY=none` via
      `features/protocol/environment.py`).

- [ ] **Migrate `protocol/scan_cycle.py`.** Drops `_env`, `_secure`,
      `_build_client`, `_leuze_client`. Behave suite is the regression
      gate.

- [ ] **Migrate `potting_lots/line_controller.py`.** Drop the
      `secure=` constructor arg and the `_secure_default()` helper;
      env decides. Update `tests/test_opc_integration.py` to rely on
      `VINEAPP_OPCUA_SECURITY=none` (already true in the behave env).

- [ ] **Migrate `scripts/write_plc.py`.** Last caller. After this,
      grep for `_env(` and `set_user(` outside `config.py` should turn
      up nothing in `src/` or `scripts/`.

- [ ] **Capture + doc sweep.**
  - `docs/deployment.md`: confirm env table matches `config.py`.
  - `work/notes/opcua_security_refactor_capture.md` for anything
    surprising (Leuze patch side effects, behave-env gotchas).
  - Roll this `doing.md` back into a backlog one-liner once shipped.
