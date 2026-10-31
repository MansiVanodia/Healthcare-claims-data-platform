
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

    print("FINAL PIPELINE VERIFICATION")
    print("-" * 40)

    all_counts_valid = True

    for table in tables:
        count = con.execute(
            f"SELECT COUNT(*) FROM {table}"
        ).fetchone()[0]

        print(f"{table}: {count}")

        if count != 5400:
            all_counts_valid = False

    watermark = con.execute("""
        SELECT last_batch_id
        FROM audit.pipeline_watermarks
        WHERE pipeline_name = 'healthcare_claims_incremental'
    """).fetchone()

    latest_batch = watermark[0] if watermark else None
    print(f"Latest watermark: {latest_batch}")

    audit = con.execute("""
        SELECT status, inserted_count, updated_count
        FROM audit.batch_runs
        WHERE batch_id = 'BATCH_004'
    """).fetchone()

    print(f"Batch 004 audit: {audit}")

    if (
        all_counts_valid
        and latest_batch == "BATCH_004"
        and audit is not None
        and audit[0] == "SUCCESS"
        and audit[1] == 100
        and audit[2] == 20
    ):
        print("RESULT: ALL CHECKS PASSED")
    else:
        print("RESULT: VERIFICATION REQUIRED")

finally:
    con.close()
