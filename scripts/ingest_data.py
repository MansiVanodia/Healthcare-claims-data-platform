
from pathlib import Path
import duckdb

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DB_DIR = BASE_DIR / "warehouse"
DB_DIR.mkdir(exist_ok=True)

DB_PATH = DB_DIR / "healthcare.duckdb"

con = duckdb.connect(str(DB_PATH))

try:
    con.execute("CREATE SCHEMA IF NOT EXISTS raw")

    # Load members
    con.execute(
        """
        CREATE OR REPLACE TABLE raw.members AS
        SELECT *
        FROM read_csv_auto(?)
        """,
        [str(DATA_DIR / "members.csv")]
    )

    # Load claims
    con.execute(
        """
        CREATE OR REPLACE TABLE raw.claims AS
        SELECT *
        FROM read_csv_auto(?)
        """,
        [str(DATA_DIR / "claims.csv")]
    )

    members_count = con.execute(
        "SELECT COUNT(*) FROM raw.members"
    ).fetchone()[0]

    claims_count = con.execute(
        "SELECT COUNT(*) FROM raw.claims"
    ).fetchone()[0]

    print("DuckDB RAW ingestion completed successfully!")
    print(f"Members loaded: {members_count}")
    print(f"Claims loaded: {claims_count}")
    print(f"Database: {DB_PATH}")

finally:
    con.close()
