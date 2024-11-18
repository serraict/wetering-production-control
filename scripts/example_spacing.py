"""Example script to demonstrate retrieving spacing data from Dremio."""

import os
from typing import Optional
from datetime import date
from decimal import Decimal
from uuid import UUID

from sqlmodel import Field, Session, SQLModel, create_engine, select
from sqlalchemy import text, Integer, bindparam
from sqlalchemy.dialects import registry
from sqlalchemy_dremio.flight import DremioDialect_flight


class CustomDremioDialect(DremioDialect_flight):
    """Custom Dremio dialect that implements import_dbapi."""

    supports_statement_cache = False

    @classmethod
    def import_dbapi(cls):
        """Import DBAPI module for Dremio."""
        return DremioDialect_flight.dbapi()


# Register our custom dialect
registry.register("dremio.flight", "production_control.products.models", "CustomDremioDialect")


class WijderzetRegistratie(SQLModel, table=True):
    """Model representing a spacing record from registratie_controle view."""

    __tablename__ = "registratie_controle"
    __table_args__ = {"schema": "Productie.Controle"}

    # Primary key
    id: UUID = Field(primary_key=True)

    # Batch information
    partij_code: str
    product_naam: str
    productgroep_naam: str
    # soort: str  # Appears to be same as product_naam

    # Planning dates
    # datum_oppot_plan: date
    # datum_uit_cel_plan: date
    # datum_wdz1_plan: date
    # datum_wdz2_plan: date
    # datum_afleveren_plan: date

    # Realization dates
    datum_oppotten_real: date
    datum_uit_cel_real: date
    datum_wdz1_real: date
    datum_wdz2_real: date
    # datum_afleveren_real: Optional[date] = None

    # Effective dates (computed?)
    # datum_oppotten: date
    # datum_uitcel: Optional[date] = None
    # datum_wdz1: Optional[date] = None
    # datum_wdz2: Optional[date] = None
    # datum_afleveren: Optional[date] = None

    # Technical dates and amounts
    # tchn_datum_1: date
    # tchn_datum_2: date
    # tchn_datum_3: Optional[date] = None
    # tchn_datum_4: Optional[date] = None
    # tchn_datum_5: Optional[date] = None
    # tchn_aantal_1: int
    # tchn_aantal_2: int

    # Plant amounts
    # aantal_planten_gepland: int
    aantal_planten_gerealiseerd: int

    # Table amounts
    # aantal_tafels_onderweg: int
    # aantal_tafels_in_kas: int
    aantal_tafels_totaal: int
    aantal_tafels_na_wdz1: int
    aantal_tafels_na_wdz2: int
    aantal_tafels_oppotten_plan: Decimal

    # Density information
    dichtheid_oppotten_plan: int
    dichtheid_wz1_plan: int
    dichtheid_wz2_plan: Optional[float] = None

    # Error tracking
    wijderzet_registratie_fout: Optional[bool] = None


def main():
    """Main function to demonstrate spacing data retrieval."""
    # Get connection string from environment variable
    conn_str = os.getenv(
        "VINEAPP_DB_CONNECTION", "dremio+flight://localhost:32010/dremio?UseEncryption=false"
    )

    # Create engine
    engine = create_engine(conn_str)

    try:
        # Create session
        with Session(engine) as session:
            # First show raw query results
            query = text(
                """
                SELECT *
                FROM "Productie.Controle"."registratie_controle"
                LIMIT 100
            """
            )
            result = session.execute(query)
            if result.returns_rows:
                row = result.first()
                if row:
                    print("\nColumns in view:")
                    for key in row._mapping.keys():
                        print(f"- {key}")
                    print("\nSample row data:")
                    for key, value in row._mapping.items():
                        print(f"{key}: {value} ({type(value).__name__})")

            # Now try using our model with SQLModel select
            print("\nTrying model-based query:")
            statement = select(WijderzetRegistratie).limit(
                bindparam("limit", type_=Integer, literal_execute=True)
            )
            results = session.exec(statement, params={"limit": 10})
            registraties = list(results)
            
            for reg in registraties:
                print(f"\nBatch {reg.partij_code} - {reg.product_naam}:")
                print(f"  Plants realized: {reg.aantal_planten_gerealiseerd}")
                print(f"  Total tables: {reg.aantal_tafels_totaal}")
                print(f"  Tables after spacing 1: {reg.aantal_tafels_na_wdz1}")
                print(f"  Tables after spacing 2: {reg.aantal_tafels_na_wdz2}")
                print(f"  Spacing error: {'Yes' if reg.wijderzet_registratie_fout else 'No'}")

    except Exception as e:
        print(f"Error: {str(e)}")


if __name__ == "__main__":
    main()
