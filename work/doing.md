# Doing

## Implement Label Printing for Potting Lots

Similar to bulb picklist, but for potting lots (table: Productie.Oppotten.oppotlijst).

### Plan

1. Create PottingLot Model:

```python
class PottingLot(SQLModel, table=True):
    __tablename__ = "oppotlijst"
    __table_args__ = {"schema": "Productie.Oppotten"}

    # Primary key
    id: int = Field(primary_key=True, title="ID")

    # Basic info
    naam: str = Field(title="Artikel")
    bollen_code: int = Field(title="Bollen Code")
    oppot_datum: Optional[date] = Field(title="Oppot Datum")
    
    # Additional fields (shown in list but not on label)
    * productgroep_code: Optional[int] = Field(title="Productgroep Code")
    bolmaat: Optional[float] = Field(title="Bolmaat")
    bol_per_pot: Optional[float] = Field(title="Bollen per Pot")
    rij_cont: Optional[int] = Field(title="Rijen per Container")
    * olsthoorn_bollen_code: Optional[str] = Field(title="Olsthoorn Bollen Code")
    aantal_pot: Optional[int] = Field(title="Aantal Potten")
    * aantal_bol: Optional[int] = Field(title="Aantal Bollen")
    * aantal_containers_oppotten: Optional[Decimal] = Field(title="Aantal Containers")
    * water: Optional[str] = Field(title="Water")
    * fust: Optional[str] = Field(title="Fust")
    * opmerking: Optional[str] = Field(title="Opmerking")
```

*: hide for list view, but show in detail view

2. Label Layout:

```
+----------------------------------+
|  Plant Name (naam)               |
|  [QR Code]                       |
+----------------------------------+
| Potting ID     | Bulb Code      |
| (id)           | (bollen_code)   |
+----------------------------------+
| Plant Date     |                 |
| (oppot_datum)  |                 |
+----------------------------------+
```

3. Implementation Steps:

- Create potting_lots module with models.py and repositories.py
- Create label template based on existing one but with simplified layout
- Add web pages for list and detail views
- Reuse existing date formatting (%gw%V-%u) for oppot_datum
- Set up label generation with QR codes linking to detail pages

### Notes

- Use same patterns as bulb picklist feature
- Simpler label layout (no containers/pots)
- Only showing oppot_datum for now (aflever_datum to be added later)
- Using standard date format (%gw%V-%u) already in place
- All fields available in list/detail views, but only key fields on label
