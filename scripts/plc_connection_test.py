#!/usr/bin/env python3
"""PLC Connection Test Script - Comprehensive test for potting line OPC/UA connection.

This script validates the OPC/UA connection to an actual PLC controlling the potting line.
Run it step by step to diagnose and verify connectivity, namespace resolution,
node discovery, reading, and writing.

Usage:
    # Run all tests against default endpoint (opc.tcp://127.0.0.1:4840)
    python scripts/plc_connection_test.py

    # Run against a specific PLC endpoint
    python scripts/plc_connection_test.py --endpoint opc.tcp://192.168.1.100:4840

    # Run against a specific PLC endpoint with a path
    python scripts/plc_connection_test.py --endpoint opc.tcp://192.168.1.100:4840/potting-lines/

    # Run only specific test phases
    python scripts/plc_connection_test.py --phase connectivity
    python scripts/plc_connection_test.py --phase namespace
    python scripts/plc_connection_test.py --phase discovery
    python scripts/plc_connection_test.py --phase read
    python scripts/plc_connection_test.py --phase write

    # Run with verbose output (shows full node trees, debug info)
    python scripts/plc_connection_test.py --verbose

    # Dry run - skip write tests (safe for production PLCs)
    python scripts/plc_connection_test.py --dry-run
"""

import argparse
import asyncio
import logging
import sys
from datetime import datetime
from typing import Optional

from asyncua import Client, ua

# ---------------------------------------------------------------------------
# Logging setup
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("plc_test")

# Suppress noisy asyncua internals (unless --verbose)
logging.getLogger("asyncua.client").setLevel(logging.WARNING)
logging.getLogger("asyncua.common").setLevel(logging.WARNING)

# ---------------------------------------------------------------------------
# Constants - must match the production code
# ---------------------------------------------------------------------------
NAMESPACE_URI = "http://wetering.potlilium.nl/potting-lines"

# Expected node string-IDs (the 's=' part of the NodeId)
EXPECTED_NODES = {
    "Lijn1_PC_nr_actieve_partij": {
        "description": "Line 1 - PC active lot number",
        "data_type": ua.VariantType.Int32,
    },
    "Lijn1_OS_partij_nr_actieve_pallet": {
        "description": "Line 1 - OS active pallet lot number",
        "data_type": ua.VariantType.Int32,
    },
    "Lijn2_PC_nr_actieve_partij": {
        "description": "Line 2 - PC active lot number",
        "data_type": ua.VariantType.Int32,
    },
    "Lijn2_OS_partij_nr_actieve_pallet": {
        "description": "Line 2 - OS active pallet lot number",
        "data_type": ua.VariantType.Int32,
    },
    "last_updated": {
        "description": "Last updated timestamp",
        "data_type": ua.VariantType.DateTime,
    },
}

# Write-test value: a recognisable number unlikely to collide with real data
WRITE_TEST_VALUE = 9999


# ---------------------------------------------------------------------------
# Result tracking
# ---------------------------------------------------------------------------
class TestResults:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.skipped = 0
        self.details: list[str] = []

    def ok(self, msg: str):
        self.passed += 1
        self.details.append(f"  PASS  {msg}")
        print(f"  PASS  {msg}")

    def fail(self, msg: str):
        self.failed += 1
        self.details.append(f"  FAIL  {msg}")
        print(f"  FAIL  {msg}")

    def skip(self, msg: str):
        self.skipped += 1
        self.details.append(f"  SKIP  {msg}")
        print(f"  SKIP  {msg}")

    def summary(self):
        total = self.passed + self.failed + self.skipped
        print("\n" + "=" * 60)
        print("TEST SUMMARY")
        print("=" * 60)
        print(f"  Total:   {total}")
        print(f"  Passed:  {self.passed}")
        print(f"  Failed:  {self.failed}")
        print(f"  Skipped: {self.skipped}")
        if self.failed == 0:
            print("\n  All tests passed.")
        else:
            print("\n  Some tests FAILED. Review output above for details.")
        print("=" * 60)
        return self.failed == 0


# ---------------------------------------------------------------------------
# Phase 1: Connectivity
# ---------------------------------------------------------------------------
async def phase_connectivity(endpoint: str, results: TestResults, verbose: bool) -> Optional[Client]:
    """Test basic TCP + OPC/UA connectivity to the PLC."""
    print("\n" + "-" * 60)
    print("PHASE 1: CONNECTIVITY")
    print("-" * 60)
    print(f"  Endpoint: {endpoint}")

    client = Client(url=endpoint)
    client.request_timeout = 10_000  # 10s timeout for the test

    # --- 1a. TCP connection ---
    try:
        await client.connect()
        results.ok(f"Connected to {endpoint}")
    except Exception as e:
        results.fail(f"Cannot connect to {endpoint}: {e}")
        print("\n  Troubleshooting tips:")
        print("    - Is the PLC powered on and network-reachable?")
        print(f"    - Can you ping the host? (try: ping {endpoint.split('//')[1].split(':')[0]})")
        print("    - Is port 4840 open? (try: nc -zv <host> 4840)")
        print("    - Is the OPC/UA server running on the PLC?")
        print("    - Check firewall rules on both sides.")
        return None

    # --- 1b. Server info ---
    try:
        endpoints = await client.get_endpoints()
        results.ok(f"Server exposes {len(endpoints)} endpoint(s)")
        if verbose:
            for ep in endpoints:
                print(f"    - {ep.EndpointUrl}  security={ep.SecurityPolicyUri}")
    except Exception as e:
        results.fail(f"Cannot list server endpoints: {e}")

    return client


# ---------------------------------------------------------------------------
# Phase 2: Namespace resolution
# ---------------------------------------------------------------------------
async def phase_namespace(client: Client, results: TestResults, verbose: bool) -> Optional[int]:
    """Verify our namespace URI is registered on the PLC and resolve its index."""
    print("\n" + "-" * 60)
    print("PHASE 2: NAMESPACE RESOLUTION")
    print("-" * 60)
    print(f"  Expected URI: {NAMESPACE_URI}")

    try:
        ns_array = await client.get_namespace_array()
        results.ok(f"Server has {len(ns_array)} namespace(s)")

        if verbose:
            for i, ns in enumerate(ns_array):
                marker = " <-- OURS" if ns == NAMESPACE_URI else ""
                print(f"    ns={i}  {ns}{marker}")

        if NAMESPACE_URI in ns_array:
            ns_idx = ns_array.index(NAMESPACE_URI)
            results.ok(f"Namespace resolved to index {ns_idx}")
            return ns_idx
        else:
            results.fail(f"Namespace URI '{NAMESPACE_URI}' not found on server")
            print("\n  Troubleshooting tips:")
            print("    - The PLC must expose a namespace with this exact URI.")
            print("    - Check PLC OPC/UA server configuration.")
            print(f"    - Available namespaces: {ns_array}")
            print("    - The namespace URI in code may need updating to match the PLC.")
            return None

    except Exception as e:
        results.fail(f"Cannot read namespace array: {e}")
        return None


# ---------------------------------------------------------------------------
# Phase 3: Node discovery
# ---------------------------------------------------------------------------
async def phase_discovery(
    client: Client, ns_idx: int, results: TestResults, verbose: bool
) -> dict:
    """Discover and validate all expected OPC nodes on the PLC."""
    print("\n" + "-" * 60)
    print("PHASE 3: NODE DISCOVERY")
    print("-" * 60)

    found_nodes = {}

    for node_str_id, info in EXPECTED_NODES.items():
        node_id = f"ns={ns_idx};s={node_str_id}"
        try:
            node = client.get_node(node_id)
            # Try to read the node class to confirm it exists
            node_class = await node.read_node_class()
            browse_name = await node.read_browse_name()
            results.ok(f"Found node {node_str_id} (class={node_class}, name={browse_name})")
            found_nodes[node_str_id] = node
        except Exception as e:
            results.fail(f"Node not found: {node_str_id} ({node_id}): {e}")
            print(f"    Expected: {info['description']}")

    # --- Optionally browse the full tree ---
    if verbose:
        print("\n  Full node tree under Objects:")
        try:
            objects = client.get_objects_node()
            await _browse_recursive(objects, indent=4, max_depth=4)
        except Exception as e:
            print(f"    (browse failed: {e})")

    return found_nodes


async def _browse_recursive(node, indent: int = 0, max_depth: int = 3, depth: int = 0):
    """Recursively browse and print the OPC node tree."""
    if depth > max_depth:
        return
    try:
        children = await node.get_children()
        for child in children:
            try:
                browse_name = await child.read_browse_name()
                node_id = child.nodeid
                print(f"{' ' * indent}{browse_name.Name}  ({node_id})")
                await _browse_recursive(child, indent + 2, max_depth, depth + 1)
            except Exception:
                pass
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Phase 4: Read values
# ---------------------------------------------------------------------------
async def phase_read(
    _client: Client, _ns_idx: int, found_nodes: dict, results: TestResults, verbose: bool
):
    """Read current values from all discovered nodes."""
    print("\n" + "-" * 60)
    print("PHASE 4: READ VALUES")
    print("-" * 60)

    for node_str_id, node in found_nodes.items():
        expected_type = EXPECTED_NODES[node_str_id]["data_type"]
        try:
            value = await node.read_value()
            data_value = await node.read_data_value()

            # Check data type
            actual_variant_type = data_value.Value.VariantType if data_value.Value else None

            type_match = actual_variant_type == expected_type if actual_variant_type else False

            # Format for display
            if isinstance(value, datetime):
                display = value.strftime("%Y-%m-%d %H:%M:%S")
            else:
                display = str(value)

            if type_match:
                results.ok(f"{node_str_id} = {display} (type={actual_variant_type})")
            else:
                results.fail(
                    f"{node_str_id} = {display} "
                    f"(type={actual_variant_type}, expected {expected_type})"
                )

            if verbose:
                print(f"    StatusCode: {data_value.StatusCode}")
                print(f"    SourceTimestamp: {data_value.SourceTimestamp}")
                print(f"    ServerTimestamp: {data_value.ServerTimestamp}")

        except Exception as e:
            results.fail(f"Cannot read {node_str_id}: {e}")


# ---------------------------------------------------------------------------
# Phase 5: Write + read-back verification
# ---------------------------------------------------------------------------
async def phase_write(
    _client: Client,
    _ns_idx: int,
    found_nodes: dict,
    results: TestResults,
    verbose: bool,
    dry_run: bool,
):
    """Write a test value and verify it reads back correctly."""
    print("\n" + "-" * 60)
    print("PHASE 5: WRITE + READ-BACK VERIFICATION")
    print("-" * 60)

    if dry_run:
        results.skip("Write tests skipped (--dry-run)")
        return

    # We only test writing to the Int32 lot-number nodes, not the timestamp
    write_targets = [
        nid for nid in found_nodes if nid != "last_updated"
    ]

    for node_str_id in write_targets:
        node = found_nodes[node_str_id]

        try:
            # Save original value
            original_value = await node.read_value()
            if verbose:
                print(f"  {node_str_id}: original value = {original_value}")

            # Write test value
            await node.write_value(WRITE_TEST_VALUE, ua.VariantType.Int32)
            results.ok(f"Wrote {WRITE_TEST_VALUE} to {node_str_id}")

            # Read back
            await asyncio.sleep(0.2)  # small delay for PLC processing
            read_back = await node.read_value()

            if int(read_back) == WRITE_TEST_VALUE:
                results.ok(f"Read-back verified for {node_str_id} (got {read_back})")
            else:
                results.fail(
                    f"Read-back mismatch for {node_str_id}: "
                    f"wrote {WRITE_TEST_VALUE}, got {read_back}"
                )

            # Restore original value
            await node.write_value(int(original_value), ua.VariantType.Int32)
            if verbose:
                print(f"  {node_str_id}: restored to {original_value}")

        except ua.UaStatusCodeError as e:
            results.fail(f"Write to {node_str_id} rejected by PLC: {e}")
            print("    The node may not be writable on this PLC.")
            print("    Check PLC access control / user permissions.")
        except Exception as e:
            results.fail(f"Write test failed for {node_str_id}: {e}")


# ---------------------------------------------------------------------------
# Phase 6: Application-level integration test
# ---------------------------------------------------------------------------
async def phase_integration(endpoint: str, results: TestResults, verbose: bool, dry_run: bool):
    """Test using the production PottingLineController class."""
    print("\n" + "-" * 60)
    print("PHASE 6: APPLICATION INTEGRATION (PottingLineController)")
    print("-" * 60)

    try:
        from production_control.config import OPCConfig
        from production_control.potting_lots.line_controller import PottingLineController
    except ImportError as e:
        results.skip(f"Cannot import application code: {e}")
        print("    Run from project root or install the package first.")
        return

    config = OPCConfig(endpoint=endpoint)
    controller = PottingLineController(config=config)

    # Test reading via the controller
    for line in [1, 2]:
        for component in ["PC", "OS"]:
            value = await controller.get_active_lot(line, component)
            if value is not None:
                results.ok(f"Controller.get_active_lot(line={line}, {component}) = {value}")
            else:
                results.fail(f"Controller.get_active_lot(line={line}, {component}) returned None")

    if dry_run:
        results.skip("Controller write test skipped (--dry-run)")
        return

    # Test writing via the controller (write + restore)
    for line in [1, 2]:
        original = await controller.get_active_lot(line, "PC")
        success = await controller.set_active_lot(line, WRITE_TEST_VALUE)
        if success:
            read_back = await controller.get_active_lot(line, "PC")
            if read_back == WRITE_TEST_VALUE:
                results.ok(f"Controller round-trip write/read on line {line}")
            else:
                results.fail(
                    f"Controller read-back mismatch on line {line}: "
                    f"expected {WRITE_TEST_VALUE}, got {read_back}"
                )
            # Restore
            await controller.set_active_lot(line, original or 0)
        else:
            results.fail(f"Controller.set_active_lot(line={line}) failed")


# ---------------------------------------------------------------------------
# Main orchestrator
# ---------------------------------------------------------------------------
async def run_tests(endpoint: str, phase: Optional[str], verbose: bool, dry_run: bool):
    results = TestResults()
    all_phases = phase is None

    print("=" * 60)
    print("PLC CONNECTION TEST")
    print("=" * 60)
    print(f"  Endpoint:  {endpoint}")
    print(f"  Time:      {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  Phase:     {phase or 'all'}")
    print(f"  Dry-run:   {dry_run}")
    print(f"  Verbose:   {verbose}")

    client = None
    ns_idx = None
    found_nodes = {}

    try:
        # Phase 1 - always needed
        if all_phases or phase == "connectivity":
            client = await phase_connectivity(endpoint, results, verbose)
            if client is None:
                results.summary()
                return not results.failed

        # For later phases, connect if we haven't yet
        if client is None:
            client = Client(url=endpoint)
            client.request_timeout = 10_000
            await client.connect()

        # Phase 2
        if all_phases or phase == "namespace":
            ns_idx = await phase_namespace(client, results, verbose)
            if ns_idx is None and (all_phases or phase in ("discovery", "read", "write")):
                print("\n  Cannot continue without namespace resolution.")
                results.summary()
                return not results.failed

        # Resolve ns_idx if skipped phase 2
        if ns_idx is None:
            ns_array = await client.get_namespace_array()
            if NAMESPACE_URI in ns_array:
                ns_idx = ns_array.index(NAMESPACE_URI)
            else:
                results.fail("Namespace not found (needed for later phases)")
                results.summary()
                return not results.failed

        # Phase 3
        if all_phases or phase == "discovery":
            found_nodes = await phase_discovery(client, ns_idx, results, verbose)

        # Discover nodes if skipped phase 3
        if not found_nodes and phase in ("read", "write"):
            for node_str_id in EXPECTED_NODES:
                node_id = f"ns={ns_idx};s={node_str_id}"
                try:
                    node = client.get_node(node_id)
                    await node.read_node_class()
                    found_nodes[node_str_id] = node
                except Exception:
                    pass

        # Phase 4
        if all_phases or phase == "read":
            await phase_read(client, ns_idx, found_nodes, results, verbose)

        # Phase 5
        if all_phases or phase == "write":
            await phase_write(client, ns_idx, found_nodes, results, verbose, dry_run)

        # Phase 6
        if all_phases:
            await phase_integration(endpoint, results, verbose, dry_run)

    finally:
        if client:
            try:
                await client.disconnect()
            except Exception:
                pass

    return results.summary()


def main():
    parser = argparse.ArgumentParser(
        description="Test OPC/UA connection to a potting line PLC.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--endpoint",
        default="opc.tcp://127.0.0.1:4840/potting-lines/",
        help="OPC/UA endpoint URL (default: opc.tcp://127.0.0.1:4840/potting-lines/)",
    )
    parser.add_argument(
        "--phase",
        choices=["connectivity", "namespace", "discovery", "read", "write"],
        help="Run only a specific test phase (default: all)",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Show detailed output (full node trees, timestamps, etc.)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Skip write tests (safe for production PLCs)",
    )
    args = parser.parse_args()

    if args.verbose:
        logging.getLogger("asyncua.client").setLevel(logging.DEBUG)
        logging.getLogger("asyncua.common").setLevel(logging.DEBUG)

    print("PLC Connection Test Script")
    print(f"Testing potting line OPC/UA connection\n")

    success = asyncio.run(run_tests(args.endpoint, args.phase, args.verbose, args.dry_run))
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
