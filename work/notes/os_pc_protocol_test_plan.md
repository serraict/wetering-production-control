# Test Plan: OS-PC Protocol Verification

Simulate PC with local Python scripts to verify the protocol between
Ontstapelaar (OS) and Production Control (PC).

## Prerequisites

### Test 0a: Leuze scanner connectivity
**Script:** Read `LastScanData` from the Leuze scanner.
**Expected:** Connection succeeds, returns a string value.

### Test 0b: Omron PLC connectivity
**Script:** Read `GoodRead`, `Resultaat`, `Trigger` from the PLC.
**Expected:** Connection succeeds, returns values.

### Test 0c: PLC protocol variables exist
**Script:** Read `last_scan_data`, `actieve_partij_nummer_1`, `actieve_partij_nummer_2` from the PLC (ns=4).
**Expected:** All three exist and are readable as int32. If they don't exist yet, they need to be created on the PLC first.

---

## Protocol Tests

### Test 1: PC writes `actieve_partij_nummer`
**Script:** Write `actieve_partij_nummer_1 = 12345` and `actieve_partij_nummer_2 = 67890`, then read them back.
**Expected:** Values read back match what was written.

### Test 2: PC reads Leuze scan result
**Script:** Monitor `LastScanData` (ns=5;i=6122) on the Leuze scanner. Manually trigger a scan on the ontstapelaar.
**Expected:** `LastScanData` updates with the scanned barcode string. Verifies PC can receive scan data independently from the PLC.

**Result (2026-03-10):** Sync read works — got `https://pc.potlilium.serraict.me/potting-lots/scan/27246`.
Polling with `--watch` did not trigger on scan changes. TODO: investigate why polling misses updates (timing? value resets?).

### Test 3: PC writes and clears `actieve_partij_nummer`
**Script:** Write non-zero values, read back, then write `0` to both, read back.
**Expected:** First read returns the non-zero values, second read returns `0`. Verifies "no active batch" signal works.

### Test 4: OS signals ready (`last_scan_data = 0`)
**Script:** Read `last_scan_data` from PLC.
**Manually:** Have someone trigger the OS so it sets `last_scan_data` to 0.
**Expected:** Value is `0`, meaning OS is ready for new data.

### Test 5: PC writes scan result to PLC
**Script:** Write `last_scan_data = 42` (simulated batch number) to the PLC, then read back.
**Expected:** Value reads back as `42`.

### Test 6: Full scan cycle (end-to-end)
This is the main integration test. Run a script that:

1. **Monitor** `last_scan_data` on PLC — wait until OS sets it to `0` (OS ready)
2. **Monitor** `LastScanData` on Leuze (ns=5;i=6122) — wait for scan result
3. **Manually** trigger a scan on the ontstapelaar (scan a known barcode)
4. **Verify** Leuze `LastScanData` changes to the scanned value
5. **Parse** the batch number from the scan data
6. **Write** `last_scan_data` on PLC with the parsed batch number (non-zero int32)
7. **Read back** `last_scan_data` from PLC — verify it matches
8. **Wait** for OS to reset `last_scan_data` back to `0` (OS acknowledges)

**Expected:** Full round-trip completes. OS sees the written value and resets to 0.

### Test 7: Repeated scan cycles
**Script:** Run test 6 three times in a row with different barcodes.
**Expected:** Each cycle completes cleanly. No stale data from previous cycles.

---

## PLC Node IDs (resolved 2026-03-10)

| Protocol name | PLC NodeId | Type |
|---|---|---|
| last_scan_data | `ns=4;s=ScanResultaat` | int32 |
| actieve_partij_nummer_1 | `ns=4;s=ActievePartijnummer1` | int32 |
| actieve_partij_nummer_2 | `ns=4;s=ActievePartijnummer2` | int32 |

## Leuze scan data format (resolved 2026-03-10)

`https://pc.potlilium.serraict.me/potting-lots/scan/27246` — batch number is the last path segment.

## Open Questions

- How quickly does OS reset `ScanResultaat` to 0 after reading it? (Test 6 timing)
- Does OS poll `ScanResultaat` or subscribe to changes?
- Why does `--watch` polling miss scan changes? (see Test 2 result)
