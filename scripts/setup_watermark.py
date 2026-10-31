
from pathlib import Path
import duckdb

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "warehouse" / "healthcare.duckdb"

con = duckdb.connect(str(DB_PATH))

try:
    con.execute("""
        CREATE TABLE IF NOT EXISTS audit.pipeline_watermarks (
            pipeline_name VARCHAR PRIMARY KEY,
            last_batch_id VARCHAR,
            last_success_at TIMESTAMP
        )
    """)

    # Initialize from the actual successful audit record.
    con.execute("""
        INSERT INTO audit.pipeline_watermarks
        SELECT
            'healthcare_claims_incremental',
            batch_id,
            completed_at
        FROM audit.batch_runs
        WHERE batch_id = 'BATCH_002'
          AND status = 'SUCCESS'
        ON CONFLICT (pipeline_name)
        DO NOTHING
    """)

    result = con.execute("""
        SELECT pipeline_name, last_batch_id, last_success_at
        FROM audit.pipeline_watermarks
        WHERE pipeline_name = 'healthcare_claims_incremental'
    """).fetchone()

    if result is None:
        raise ValueError(
            "No successful BATCH_002 audit record found."
        )

    print("WATERMARK SETUP SUCCESSFUL")
    print(f"Pipeline: {result[0]}")
    print(f"Last successful batch: {result[1]}")
    print(f"Last success time: {result[2]}")

finally:
    con.close()
