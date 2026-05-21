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

  Scenario: Successive scans cycle through OS acknowledgement
    When a scan arrives with payload "https://pc.potlilium.serraict.me/potting-lots/scan/27246"
    Then PC writes 27246 to ScanResultaat
    When OS resets ScanResultaat to 0
    And a scan arrives with payload "https://pc.potlilium.serraict.me/potting-lots/scan/27247"
    Then PC writes 27247 to ScanResultaat

  Scenario: PC drops a scan while the previous one is still unread
    Given the PLC reports ScanResultaat = 27246
    When a scan arrives with payload "https://pc.potlilium.serraict.me/potting-lots/scan/27247"
    Then PC does not write to ScanResultaat
    And PC logs "scan dropped: guard not zero" at WARNING

  Scenario: A duplicate scan after OS ack writes again
    When a scan arrives with payload "https://pc.potlilium.serraict.me/potting-lots/scan/27246"
    Then PC writes 27246 to ScanResultaat
    When OS resets ScanResultaat to 0
    And a scan arrives with payload "https://pc.potlilium.serraict.me/potting-lots/scan/27246"
    Then PC writes 27246 to ScanResultaat
