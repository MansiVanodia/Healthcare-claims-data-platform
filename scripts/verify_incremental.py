
from pathlib import Path
import duckdb

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "warehouse" / "healthcare.duckdb"

con = duckdb.connect(str(DB_PATH), read_only=True)

try:
    tables = [
        "raw.claims",
        "main.stg_claims",
        "main.fact_claims",
        "main.fact_claim_risk"
    ]

    print("INCREMENTAL INGESTION VERIFICATION")
    print("-" * 45)

    for table in tables:
        count = con.execute(
            f"SELECT COUNT(*) FROM {table}"
        ).fetchone()[0]
        print(f"{table}: {count}")

    new_claims = con.execute("""
        SELECT COUNT(*)
        FROM raw.claims
        WHERE claim_id BETWEEN 'C005001' AND 'C005100'
    """).fetchone()[0]

    print(f"New batch claim IDs found: {new_claims}")

finally:
    con.close()
