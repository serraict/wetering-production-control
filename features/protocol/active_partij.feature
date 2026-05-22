Feature: Active partij publication (PC tells OS which lots are live)

  The operator picks one or two active partijen on the potting-lots
  page. PC publishes the IDs to ActievePartijnummer1 / 2 on the PLC.
  OS uses them locally to decide vrijgave. A value of 0 means
  "no active partij" and tells OS to refuse vrijgave.

  Scenario: Operator activates a partij on line 1
    When the operator activates partij 12345 on line 1
    Then PC writes 12345 to ActievePartijnummer1

  Scenario: Operator activates a partij on line 2
    When the operator activates partij 67890 on line 2
    Then PC writes 67890 to ActievePartijnummer2
