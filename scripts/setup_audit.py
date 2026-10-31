
from pathlib import Path
import duckdb

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "warehouse" / "healthcare.duckdb"

con = duckdb.connect(str(DB_PATH))

try:
    con.execute("CREATE SCHEMA IF NOT EXISTS audit")

    con.execute("""
        CREATE TABLE IF NOT EXISTS audit.batch_runs (
            batch_id VARCHAR PRIMARY KEY,
            source_file VARCHAR,
            started_at TIMESTAMP,
            completed_at TIMESTAMP,
            status VARCHAR,
            inserted_count INTEGER,
            updated_count INTEGER,
            total_records INTEGER,
            error_message VARCHAR
        )
    """)

    print("Audit schema and batch_runs table created successfully!")

finally:
    con.close()
