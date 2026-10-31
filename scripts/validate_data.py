
from pathlib import Path
import duckdb

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "warehouse" / "healthcare.duckdb"

con = duckdb.connect(str(DB_PATH), read_only=True)

checks = {
    "Total claims": """
        SELECT COUNT(*) FROM raw.claims
    """,
    "Duplicate claim IDs": """
        SELECT COUNT(*) - COUNT(DISTINCT claim_id)
        FROM raw.claims
    """,
    "Missing claim IDs": """
        SELECT COUNT(*)
        FROM raw.claims
        WHERE claim_id IS NULL OR TRIM(claim_id) = ''
    """,
    "Invalid claim amounts": """
        SELECT COUNT(*)
        FROM raw.claims
        WHERE claim_amount IS NULL OR claim_amount <= 0
    """,
    "Claims with unknown members": """
        SELECT COUNT(*)
        FROM raw.claims c
        LEFT JOIN raw.members m
            ON c.member_id = m.member_id
        WHERE m.member_id IS NULL
    """
}

try:
    print("\nHEALTHCARE CLAIMS DATA VALIDATION")
    print("-" * 45)

    for check_name, query in checks.items():
        result = con.execute(query).fetchone()[0]
        print(f"{check_name}: {result}")

finally:
    con.close()
