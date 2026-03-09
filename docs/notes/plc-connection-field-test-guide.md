# PLC Connection Field Test Guide

## Introduction

This guide helps you set up and verify the OPC/UA connection between the Production Control application and the actual PLC that controls the potting lines at Wetering Potlilium.

The Production Control application communicates with the potting line machines via OPC/UA to track which lot is actively being potted on each line. The application writes a lot number to the PLC when a lot is activated, and resets it to 0 when deactivated. The PLC exposes this data so that the machine operator (and the OS/operating system on the line) can see which lot is active.

### Relevant project documentation and code

Before starting the field test, review these to make sure we agree on the expected setup:

| What                    | Location                                                 | Description                                                         |
| ----------------------- | -------------------------------------------------------- | ------------------------------------------------------------------- |
| Architecture overview   | `docs/architecture.md`                                   | System components and data flow                                     |
| Namespace mismatch bug  | `docs/notes/nodesets-namespace-index-mismatch-bug.md`    | Why we use string-based NodeIds and namespace URI resolution        |
| asyncua library docs    | `docs/notes/asyncua/`                                    | Reference docs for the Python OPC/UA library we use                 |
| OPC config              | `src/production_control/config/opc_config.py`            | `OPCConfig` dataclass with all connection settings                  |
| Line controller         | `src/production_control/potting_lots/line_controller.py` | `PottingLineController` - the production code that talks to the PLC |
| Test server (simulated) | `scripts/opc_test_server.py`                             | A local OPC/UA server that mimics the PLC node structure            |
| OPC monitor             | `scripts/opc_monitor.py`                                 | Reads and displays current node values                              |
| Connection test script  | `scripts/plc_connection_test.py`                         | The comprehensive test script described in this guide               |

## What the application expects from the PLC

The PLC's OPC/UA server must expose the following:

### Namespace

- **URI**: `http://wetering.potlilium.nl/potting-lines`
- The namespace index is resolved at runtime (see the [namespace mismatch note](nodesets-namespace-index-mismatch-bug.md) for why we do this instead of hardcoding an index).

### Nodes

All nodes use **string-based NodeIds** (`ns=<idx>;s=<string>`) for stability. The expected nodes are:

| String ID                           | Data type | Writable | Purpose                                    |
| ----------------------------------- | --------- | -------- | ------------------------------------------ |
| `Lijn1_PC_nr_actieve_partij`        | Int32     | Yes      | Line 1 - active lot number (written by PC) |
| `Lijn1_OS_partij_nr_actieve_pallet` | Int32     | Yes      | Line 1 - active pallet lot (read by OS)    |
| `Lijn2_PC_nr_actieve_partij`        | Int32     | Yes      | Line 2 - active lot number (written by PC) |
| `Lijn2_OS_partij_nr_actieve_pallet` | Int32     | Yes      | Line 2 - active pallet lot (read by OS)    |
| `last_updated`                      | DateTime  | Yes      | Timestamp of last update                   |

A value of `0` means "no active lot" on that line.

### Security

Currently the connection uses **no security** (`ua.SecurityPolicyType.NoSecurity`). The `OPCConfig` has fields for certificate-based security (`use_security`, `certificate_path`, `private_key_path`) but these are not yet enabled.

## Prerequisites

1. **Network access** to the PLC. You need to be on the same network or have a route to the PLC's IP address.
2. **PLC endpoint URL**. The default is `opc.tcp://127.0.0.1:4840/potting-lines/` (local test server). For the real PLC you need the actual IP and port, e.g. `opc.tcp://192.168.1.100:4840/potting-lines/`.
3. **Python environment** with the project dependencies installed (`asyncua` in particular).

## Step-by-step field test procedure

### Step 1: Verify network connectivity

Before touching OPC/UA, make sure you can reach the PLC at the network level.

```bash
# Replace with the actual PLC IP
ping 192.168.1.100

# Check if the OPC/UA port is open
nc -zv 192.168.1.100 4840
```

If this fails, check:

- Are you on the right network / VLAN?
- Is there a firewall blocking port 4840?
- Is the PLC powered on?

### Step 2: Run the connection test script (read-only)

Start with a **dry run** to avoid writing anything to the PLC:

```bash
python scripts/plc_connection_test.py \
  --endpoint opc.tcp://192.168.1.100:4840/potting-lines/ \
  --dry-run \
  --verbose
```

This runs all 6 test phases but skips any writes. Review the output phase by phase:

#### Phase 1: Connectivity

- Confirms the TCP connection and OPC/UA handshake succeed.
- Lists the server's endpoints and security policies.

#### Phase 2: Namespace resolution

- Looks for our namespace URI (`http://wetering.potlilium.nl/potting-lines`) in the server's namespace array.
- If not found, the PLC may use a different URI. The `--verbose` flag shows all namespaces on the server so you can compare.

#### Phase 3: Node discovery

- Tries to find each of the 5 expected nodes by their string NodeId.
- With `--verbose`, also browses the full node tree so you can see what the PLC actually exposes.

#### Phase 4: Read values

- Reads the current value and data type from each node.
- Verifies that lot numbers are `Int32` and the timestamp is `DateTime`.

#### Phase 5: Write (skipped in dry-run)

- Skipped. See step 3.

#### Phase 6: Application integration

- Tests using the production `PottingLineController` class.
- Reads lot values via the same code path the web application uses.

### Step 3: Run write tests

Once reads are working, test writing. **Only do this when the line is not actively potting** to avoid interfering with production.

```bash
python scripts/plc_connection_test.py \
  --endpoint opc.tcp://192.168.1.100:4840/potting-lines/
```

This adds:

- Writing a test value (`9999`) to each lot-number node.
- Reading it back to verify the write took effect.
- Restoring the original value.

### Step 4: Run individual phases (troubleshooting)

If a specific phase fails, you can re-run just that phase:

```bash
# Only test connectivity
python scripts/plc_connection_test.py --endpoint ... --phase connectivity

# Only test namespace resolution
python scripts/plc_connection_test.py --endpoint ... --phase namespace

# Only test node discovery (with full tree browse)
python scripts/plc_connection_test.py --endpoint ... --phase discovery --verbose
```

### Step 5: Monitor live values

Once connectivity is confirmed, use the monitor script to watch values in real time:

```bash
python scripts/opc_monitor.py
```

Or set the endpoint via environment variable:

```bash
OPC_ENDPOINT=opc.tcp://192.168.1.100:4840/potting-lines/ python scripts/opc_monitor.py
```

Use `--once` to read values a single time and exit.

## Configuring the application for production

Once the field test passes, configure the production application:

### Option A: Environment variable

```bash
export OPC_ENDPOINT=opc.tcp://192.168.1.100:4840/potting-lines/
```

### Option B: Config file

Create a JSON config file with an `opc` section:

```json
{
  "opc": {
    "endpoint": "opc.tcp://192.168.1.100:4840/potting-lines/",
    "environment": "production"
  }
}
```

### Available environment variables

All settings from `OPCConfig` can be overridden via environment variables (see `src/production_control/config/opc_config.py`):

| Variable                 | Default                    | Description                            |
| ------------------------ | -------------------------- | -------------------------------------- |
| `OPC_ENDPOINT`           | `opc.tcp://127.0.0.1:4840` | PLC endpoint URL                       |
| `OPC_CONNECTION_TIMEOUT` | `10`                       | Connection timeout in seconds          |
| `OPC_WATCHDOG_INTERVAL`  | `30`                       | Watchdog interval in seconds           |
| `OPC_RETRY_ATTEMPTS`     | `3`                        | Number of retry attempts per operation |
| `OPC_RETRY_DELAY`        | `1.0`                      | Base delay between retries in seconds  |
| `ENVIRONMENT`            | `development`              | Environment name                       |

## Troubleshooting

### "Namespace not found"

The PLC does not expose `http://wetering.potlilium.nl/potting-lines`. Run with `--verbose` to see what namespaces the PLC does expose. Either:

- The PLC needs to be configured to use this namespace URI, or
- The application code needs to be updated to match the PLC's actual namespace URI (in `OPCConfig.namespace_uri` and `PottingLineController._namespace_uri`).

### "Node not found"

The namespace exists but a specific node is missing. Run with `--phase discovery --verbose` to browse the full node tree. Possible causes:

- The PLC uses different node string IDs than expected.
- The node structure is different (e.g. nested differently).
- The node exists but under a different namespace.

### Write rejected

The node exists and is readable but the PLC rejects writes. Check:

- Does the PLC allow anonymous writes, or does it require authentication?
- Is the node configured as writable on the PLC side?
- Does the PLC expect a different data type?

### Connection timeout

- Increase timeout: `--endpoint` is correct but the PLC is slow to respond. Set `OPC_CONNECTION_TIMEOUT` to a higher value.
- The path component of the endpoint URL may differ. Try without `/potting-lines/` suffix.

### "Cannot import application code" in Phase 6

The integration phase imports from `production_control`. Make sure you run the script from the project root and the package is installed:

```bash
pip install -e .
python scripts/plc_connection_test.py ...
```

## Testing locally (without a PLC)

To practice or develop without a real PLC, use the test server:

```bash
# Terminal 1: start the simulated PLC
python scripts/opc_test_server.py

# Terminal 2: run the connection test against it
python scripts/plc_connection_test.py

# Terminal 3 (optional): monitor values
python scripts/opc_monitor.py
```

The test server (`scripts/opc_test_server.py`) creates the exact same node structure that the application expects, so all test phases should pass.
