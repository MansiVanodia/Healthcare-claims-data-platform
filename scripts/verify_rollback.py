
from pathlib import Path
import duckdb

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "warehouse" / "healthcare.duckdb"

con = duckdb.connect(str(DB_PATH), read_only=True)

try:
    raw_count = con.execute(
        "SELECT COUNT(*) FROM raw.claims"
    ).fetchone()[0]

    watermark = con.execute(
        "SELECT last_batch_id FROM audit.pipeline_watermarks"
    ).fetchone()[0]

    batch_count = con.execute(
        "SELECT COUNT(*) FROM audit.batch_runs WHERE batch_id = ?",
        ["BATCH_004"]
    ).fetchone()[0]

    print("ROLLBACK VERIFICATION")
    print("---------------------")
    print("RAW claims:", raw_count)
    print("Watermark:", watermark)
    print("Batch 004 audit records:", batch_count)

    if raw_count == 5300 and watermark == "BATCH_003" and batch_count == 0:
        print("RESULT: ROLLBACK VERIFIED")
    else:
        print("RESULT: CHECK REQUIRED")

finally:
    con.close()
