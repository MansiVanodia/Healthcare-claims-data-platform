
from pathlib import Path
import duckdb

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "warehouse" / "healthcare.duckdb"

con = duckdb.connect(str(DB_PATH))

try:
    con.execute("""
        DELETE FROM raw.claims
        WHERE claim_id IN ('TEST_DUP_001', 'TEST_DUP_002')
    """)

    remaining = con.execute("""
        SELECT COUNT(*) FROM raw.claims
    """).fetchone()[0]

    print("Controlled test claims removed successfully!")
    print(f"Remaining RAW claims: {remaining}")

finally:
    con.close()
