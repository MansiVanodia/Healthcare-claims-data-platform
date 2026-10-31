
from pathlib import Path
import duckdb

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "warehouse" / "healthcare.duckdb"
BATCH_PATH = BASE_DIR / "data" / "incremental" / "claims_batch_001.csv"

con = duckdb.connect(str(DB_PATH), read_only=True)

try:
    result = con.execute("""
        SELECT
            COUNT(*) AS total_updates,
            COUNT(*) FILTER (
                WHERE r.claim_status = b.claim_status
            ) AS matching_raw,
            COUNT(*) FILTER (
                WHERE f.claim_status = UPPER(b.claim_status)
            ) AS matching_fact
        FROM read_csv_auto(?) b
        LEFT JOIN raw.claims r
            ON b.claim_id = r.claim_id
        LEFT JOIN main.fact_claims f
            ON b.claim_id = f.claim_id
        WHERE b.record_type = 'UPDATE'
    """, [str(BATCH_PATH)]).fetchone()

    total, raw_matches, fact_matches = result

    print("CLAIM STATUS UPDATE VERIFICATION")
    print("-" * 45)
    print(f"Expected updates: {total}")
    print(f"Matching RAW statuses: {raw_matches}")
    print(f"Matching FACT statuses: {fact_matches}")

    if total == 20 and raw_matches == total and fact_matches == total:
        print("SUCCESS: All 20 claim status updates verified!")
    else:
        raise ValueError("Status update verification failed.")

finally:
    con.close()
