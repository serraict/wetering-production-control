Feature: Scan cycle (PC acknowledges scans from OS)

  PC observes Leuze scans, parses the partij from the scan URL, and
  writes it to ScanResultaat — but only after observing the field equals
  0. OS resets the field to 0 once it has read the value; the guard
  protects against overwriting an unread scan.

  Background:
    Given the PLC reports ScanResultaat = 0

  Scenario: PC publishes a parsed partij when the guard allows
    When a scan arrives with payload "https://pc.potlilium.serraict.me/potting-lots/scan/27246"
    Then PC writes 27246 to ScanResultaat
