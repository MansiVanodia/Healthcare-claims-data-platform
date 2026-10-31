
from pathlib import Path
import duckdb

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "warehouse" / "healthcare.duckdb"

con = duckdb.connect(str(DB_PATH))

try:
    # Reuse a valid member and policy from existing data
    member_id, policy_id = con.execute("""
        SELECT member_id, policy_id
        FROM raw.members
        LIMIT 1
    """).fetchone()

    # Remove previous copies so reruns are safe
    con.execute("""
        DELETE FROM raw.claims
        WHERE claim_id IN ('TEST_DUP_001', 'TEST_DUP_002')
    """)

    con.execute("""
        INSERT INTO raw.claims (
            claim_id,
            member_id,
            policy_id,
            provider_id,
            claim_date,
            claim_amount,
            claim_status
        )
        VALUES
            (?, ?, ?, 'H0001', '2026-10-01', 9500, 'Pending'),
            (?, ?, ?, 'H0001', '2026-10-01', 9500, 'Pending')
    """, [
        'TEST_DUP_001', member_id, policy_id,
        'TEST_DUP_002', member_id, policy_id
    ])

    print("2 controlled duplicate-billing test claims inserted.")

finally:
    con.close()
