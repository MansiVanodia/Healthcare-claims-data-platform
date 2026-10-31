
from pathlib import Path
import duckdb

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "warehouse" / "healthcare.duckdb"

con = duckdb.connect(str(DB_PATH), read_only=True)

try:
    print("\nHEALTHCARE CLAIMS PIPELINE MONITOR")
    print("=" * 65)

    rows = con.execute("""
        SELECT
            batch_id,
            status,
            inserted_count,
            updated_count,
            total_records,
            ROUND(
                date_diff(
                    'millisecond',
                    started_at,
                    completed_at
                ) / 1000.0, 2
            ) AS duration_seconds
        FROM audit.batch_runs
        ORDER BY completed_at DESC
    """).fetchall()

    for row in rows:
        print(f"\nBatch: {row[0]}")
        print(f"Status: {row[1]}")
        print(f"Inserted: {row[2]}")
        print(f"Updated: {row[3]}")
        print(f"Total records: {row[4]}")
        print(f"Duration: {row[5]} seconds")

    watermark = con.execute("""
        SELECT last_batch_id
        FROM audit.pipeline_watermarks
        WHERE pipeline_name = 'healthcare_claims_incremental'
    """).fetchone()

    print("\n" + "=" * 65)
    print(
        "Latest watermark:",
        watermark[0] if watermark else "Not set"
    )

finally:
    con.close()
