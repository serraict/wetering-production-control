# Deployment & Configuration

How to deploy Production Control and the auxiliary OPC/UA tooling, and
where the configuration knobs are.

## Topology

- Production Control runs in a Docker container on `serraserver`
  (`10.0.0.3`) inside the **Serra Vine** docker network.
- Image: `ghcr.io/serraict/wetering-production-control:latest`.
- Two compose services share that image:
  - `production_control` — the NiceGUI web app + OPC client (port `7901`).
  - `opcua_test` — sibling service for ad-hoc OPC/UA scripts and the
    monitor/TUI; same image, same env, same certs volume.
- External systems: Dremio (data), Firebird (subset of data), OpTech
  (spacing), Zulip (per-lot conversation), Omron PLC and Leuze scanner
  on the plant network.

## Container images

We split the image to keep deploys fast and to reuse the heavy base
image across app revisions.

- `Dockerfile.base` bakes Python dependencies via
  `uv pip install -r pyproject.toml`. GHA workflow
  `package_base.yml` rebuilds it automatically when `pyproject.toml`,
  `uv.lock`, or `Dockerfile.base` change on `main`.
- `Dockerfile` (app) does `uv pip install . --no-deps` on top of the
  base. GHA workflow `package.yml` builds and pushes the app image when
  a `v*` tag is pushed.

**Releasing a new version:**

```sh
make release          # bumps tag (setuptools_scm), pushes tag
                      # → package.yml rebuilds ghcr.io/.../wetering-production-control:latest
```

If you've added or upgraded a dependency, push the dependency change to
`main` first so the base image rebuild lands, then `make release` so the
app image picks up the new base layers.

## Environment variables

All env vars below live in `.env` on serraserver (mounted by the compose
services via `env_file`). `.env.example` in the repo is the canonical
list — copy it and fill in real values.

### Core app

| Var                        | Purpose                                       |
| -------------------------- | --------------------------------------------- |
| `VINEAPP_DB_CONNECTION`    | Dremio Flight SQL connection string.          |
| `VINEAPP_SQL_ECHO`         | `true` to log SQL queries.                    |
| `VINEAPP_FIBERY_URL`       | Fibery base URL for knowledge-base links.     |
| `VINEAPP_FIBERY_SPACE`     | Fibery space name.                            |
| `VINEAPP_OPTECH_API_URL`   | OpTech base URL.                              |
| `NICEGUI_PORT`             | Port the API uses to build base URLs.         |
| `NICEGUI_STORAGE_SECRET`   | Storage signing secret.                       |
| `QR_CODE_BASE_URL`         | Base URL embedded in QR codes.                |
| `LABEL_WIDTH`, `LABEL_HEIGHT` | Label dimensions.                          |

### Firebird

| Var                | Default                       |
| ------------------ | ----------------------------- |
| `FIREBIRD_HOST`    | `localhost`                   |
| `FIREBIRD_PORT`    | `3050`                        |
| `FIREBIRD_DATABASE`| `/firebird/data/production.fdb` |
| `FIREBIRD_USER`    | `SYSDBA`                      |
| `FIREBIRD_PASSWORD`| `masterkey`                   |

### OPC/UA (ontstapelaar)

| Var                            | Notes                                                          |
| ------------------------------ | -------------------------------------------------------------- |
| `VINEAPP_OPCUA_PLC_URL`        | e.g. `opc.tcp://10.0.0.190:4840`                                |
| `VINEAPP_OPCUA_PLC_USER`       | OPC UA user on the PLC (restricted to protocol nodes).         |
| `VINEAPP_OPCUA_PLC_PASSWORD`   |                                                                |
| `VINEAPP_OPCUA_LEUZE_URL`      | e.g. `opc.tcp://10.0.0.191:4840`; unset → Leuze source skipped. |
| `VINEAPP_OPCUA_LEUZE_USER`     |                                                                |
| `VINEAPP_OPCUA_LEUZE_PASSWORD` |                                                                |
| `VINEAPP_OPCUA_CLIENT_CERT`    | Path (in container) to client cert (DER).                       |
| `VINEAPP_OPCUA_CLIENT_KEY`     | Path (in container) to client private key (PEM).                |
| `VINEAPP_OPCUA_CLIENT_APP_URI` | Optional. Default `urn:serra:production-control-client`. Must ≤44 chars and match the SAN URI in the client cert (Omron limit). |
| `VINEAPP_OPCUA_SECURITY`       | `none` disables SignAndEncrypt (test only). Default: secure.    |
| `VINEAPP_OPCUA_MONITOR_LOG_DIR`| Reserved for monitor v4 (file logging); unused today.           |

### Zulip

| Var                   | Notes                                                  |
| --------------------- | ------------------------------------------------------ |
| `ZULIP_SITE`          | Per-environment Zulip URL.                             |
| `ZULIP_BOT_EMAIL`     | Bot account email.                                     |
| `ZULIP_BOT_API_KEY`   | Bot API key. Unset → communication card renders a notice. |
| `ZULIP_STREAM`        | Stream messages post into.                             |
| `ZULIP_TIMEOUT`       | Optional (seconds).                                    |
| `ZULIP_HISTORY_LIMIT` | Optional.                                              |

## OPC/UA client certificate

PC authenticates to both the Omron PLC and the Leuze scanner with **our
own** Application Instance certificate. The same cert is presented to
both servers, so it must include the required EKUs for each.

Required cert properties (Omron in particular is strict):

- EKU: `clientAuth` **and** `serverAuth`.
- Subject Alternative Name URI: matches `VINEAPP_OPCUA_CLIENT_APP_URI`.
- SAN DNS entry: matches the container hostname presented at handshake
  time. The PLC logs a warning when these don't match (cosmetic only).
- Application URI string: ≤ 44 characters (Omron limit).

Generation uses
`asyncua.crypto.cert_gen.setup_self_signed_certificate`; the convenience
wrapper is at `scripts/generate_client_cert.py`.

### Initial setup

From the deployment directory on serraserver:

```sh
# 1. Pull the image
docker compose pull opcua_test

# 2. Sanity-check the configured env vars
docker compose run --rm opcua_test python scripts/show_opcua_config.py

# 3. Generate the client cert into the shared certs volume
docker compose run --rm opcua_test \
  python scripts/generate_client_cert.py --out-dir /app/certs --hostname "$(hostname)"

# 4. Trust the new client cert on the Omron PLC:
#    Sysmac Studio → Communications → Security → Client Authentication
#    → select cert → Move to Trusted.
#    Configure the OPC UA user account on the PLC; restrict to the protocol
#    nodes; store credentials in .env.

# 5. Probe both endpoints to confirm
docker compose run --rm opcua_test sh -c \
  'python scripts/probe_opcua_endpoint.py "$VINEAPP_OPCUA_PLC_URL"'
docker compose run --rm opcua_test sh -c \
  'python scripts/probe_opcua_endpoint.py "$VINEAPP_OPCUA_LEUZE_URL"'
```

### Renewal

The current cert has **365-day validity** (asyncua hardcodes `days=365`
in the convenience helper). Steps to renew:

1. Regenerate via step 3 above (overwrites cert in the certs volume).
2. Re-trust on the Omron PLC (Sysmac Studio → Client Authentication →
   Move to Trusted).
3. Restart the app:
   `docker compose restart production_control`.
4. Verify with the monitor:
   `docker compose run --rm opcua_test python -m production_control.opcua.monitor`.

A multi-year cert is on the follow-up list (call
`generate_self_signed_app_certificate(..., days=3650)` directly instead
of the asyncua helper); see
[`work/notes/ontstapelmachine/doing_ontstapelaar.md`](../work/notes/ontstapelmachine/doing_ontstapelaar.md).

### Test setup credentials

The test-bench PLC and scanner use different IPs/credentials; see the
`MEMORY.md` entry in `.claude/`. Production uses different addresses and
credentials, and the test cert is **not** reusable on production.

## Running on serraserver

### Web app

```sh
docker compose pull production_control
docker compose up -d production_control
```

### Monitor & TUI (operator / diagnostics)

The headless monitor streams JSONL on stdout; the TUI is for an
interactive view over ssh. Both run inside the `opcua_test` service so
they don't perturb the running web app.

```sh
# headless JSONL monitor (PLC + Leuze)
docker compose run --rm opcua_test python -m production_control.opcua.monitor

# interactive TUI
docker compose run --rm -it opcua_test python -m production_control.opcua.tui
```

The TUI quits with `q`. It skips the Leuze pane if
`VINEAPP_OPCUA_LEUZE_URL` is unset.

### Manual PLC writes (commissioning)

```sh
docker compose run --rm opcua_test python scripts/write_plc.py --scanresultaat 27246
docker compose run --rm opcua_test python scripts/write_plc.py --clear
```

## Local development

```sh
uv sync                                       # install deps
uv run production-control                     # run the web app
uv run python scripts/opc_test_server.py      # fake PLC/Leuze on :4840
uv run python -m production_control.opcua.monitor  # against the fake server
```

For the fake server set `VINEAPP_OPCUA_PLC_URL=opc.tcp://127.0.0.1:4840`
and `VINEAPP_OPCUA_SECURITY=none`; the test server accepts anonymous
connections.

## Related

- Protocol contract: [`protocol.md`](protocol.md).
- System architecture: [`architecture.md`](architecture.md).
- Field-test status and on-site notes:
  [`work/notes/ontstapelmachine/doing_ontstapelaar.md`](../work/notes/ontstapelmachine/doing_ontstapelaar.md).
