
from pathlib import Path
import duckdb

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "warehouse" / "healthcare.duckdb"

con = duckdb.connect(str(DB_PATH), read_only=True)

try:
    print("BATCH AUDIT VERIFICATION")
    print("-" * 45)

    result = con.execute("""
        SELECT batch_id, status, inserted_count,
               updated_count, total_records
        FROM audit.batch_runs
        WHERE batch_id = 'BATCH_002'
    """).fetchone()

    if result is None:
        raise ValueError("BATCH_002 audit record not found.")

    print(f"Batch ID: {result[0]}")
    print(f"Status: {result[1]}")
    print(f"Inserted: {result[2]}")
    print(f"Updated: {result[3]}")
    print(f"Batch records: {result[4]}")

    for table in [
        "raw.claims",
        "main.fact_claims",
        "main.fact_claim_risk"
    ]:
        count = con.execute(
            f"SELECT COUNT(*) FROM {table}"
        ).fetchone()[0]
        print(f"{table}: {count}")

finally:
    con.close()
