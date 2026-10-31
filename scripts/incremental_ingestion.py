
from pathlib import Path
import duckdb

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "warehouse" / "healthcare.duckdb"
BATCH_PATH = BASE_DIR / "data" / "incremental" / "claims_batch_001.csv"

if not BATCH_PATH.exists():
    raise FileNotFoundError(f"Batch not found: {BATCH_PATH}")

con = duckdb.connect(str(DB_PATH))

try:
    # All operations succeed together or roll back together.
    con.execute("BEGIN TRANSACTION")

    con.execute("""
        CREATE TEMP TABLE incoming_claims AS
        SELECT
            CAST(claim_id AS VARCHAR) AS claim_id,
            CAST(member_id AS VARCHAR) AS member_id,
            CAST(policy_id AS VARCHAR) AS policy_id,
            CAST(provider_id AS VARCHAR) AS provider_id,
            CAST(claim_date AS DATE) AS claim_date,
            CAST(claim_amount AS DECIMAL(12,2)) AS claim_amount,
            CAST(claim_status AS VARCHAR) AS claim_status,
            CAST(record_type AS VARCHAR) AS record_type
        FROM read_csv_auto(?)
    """, [str(BATCH_PATH)])

    # Reject invalid batches before modifying RAW data.
    invalid = con.execute("""
        SELECT COUNT(*)
        FROM incoming_claims
        WHERE claim_id IS NULL
           OR TRIM(claim_id) = ''
           OR claim_amount IS NULL
           OR claim_amount <= 0
           OR record_type NOT IN ('INSERT', 'UPDATE')
           OR record_type IS NULL
    """).fetchone()[0]

    duplicates = con.execute("""
        SELECT COUNT(*) - COUNT(DISTINCT claim_id)
        FROM incoming_claims
    """).fetchone()[0]

    if invalid or duplicates:
        raise ValueError(
            f"Invalid rows: {invalid}; duplicate batch IDs: {duplicates}"
        )

    # Make sure all referenced members exist.
    unknown_members = con.execute("""
        SELECT COUNT(*)
        FROM incoming_claims i
        LEFT JOIN raw.members m ON i.member_id = m.member_id
        WHERE m.member_id IS NULL
    """).fetchone()[0]

    if unknown_members:
        raise ValueError(f"Unknown members: {unknown_members}")

    # INSERT records must not conflict with existing claim IDs.
    # Existing identical INSERT records are allowed on reruns.
    conflicts = con.execute("""
        SELECT COUNT(*)
        FROM incoming_claims i
        JOIN raw.claims r ON i.claim_id = r.claim_id
        WHERE i.record_type = 'INSERT'
          AND (
              i.member_id IS DISTINCT FROM r.member_id
              OR i.policy_id IS DISTINCT FROM r.policy_id
              OR i.provider_id IS DISTINCT FROM r.provider_id
              OR i.claim_date IS DISTINCT FROM r.claim_date
              OR i.claim_amount IS DISTINCT FROM r.claim_amount
              OR i.claim_status IS DISTINCT FROM r.claim_status
          )
    """).fetchone()[0]

    if conflicts:
        raise ValueError(f"Conflicting existing INSERT records: {conflicts}")

    # Updates must refer to existing claims.
    missing_updates = con.execute("""
        SELECT COUNT(*)
        FROM incoming_claims i
        LEFT JOIN raw.claims r ON i.claim_id = r.claim_id
        WHERE i.record_type = 'UPDATE'
          AND r.claim_id IS NULL
    """).fetchone()[0]

    if missing_updates:
        raise ValueError(f"Updates without existing claims: {missing_updates}")

    new_count = con.execute("""
        SELECT COUNT(*)
        FROM incoming_claims i
        LEFT JOIN raw.claims r ON i.claim_id = r.claim_id
        WHERE i.record_type = 'INSERT'
          AND r.claim_id IS NULL
    """).fetchone()[0]

    changed_count = con.execute("""
        SELECT COUNT(*)
        FROM incoming_claims i
        JOIN raw.claims r ON i.claim_id = r.claim_id
        WHERE i.record_type = 'UPDATE'
          AND i.claim_status IS DISTINCT FROM r.claim_status
    """).fetchone()[0]

    # DuckDB-compatible update and insert operations.
    con.execute("""
        UPDATE raw.claims AS r
        SET claim_status = i.claim_status
        FROM incoming_claims AS i
        WHERE r.claim_id = i.claim_id
          AND i.record_type = 'UPDATE'
          AND i.claim_status IS DISTINCT FROM r.claim_status
    """)

    con.execute("""
        INSERT INTO raw.claims (
            claim_id, member_id, policy_id, provider_id,
            claim_date, claim_amount, claim_status
        )
        SELECT
            i.claim_id, i.member_id, i.policy_id, i.provider_id,
            i.claim_date, i.claim_amount, i.claim_status
        FROM incoming_claims i
        LEFT JOIN raw.claims r ON i.claim_id = r.claim_id
        WHERE i.record_type = 'INSERT'
          AND r.claim_id IS NULL
    """)

    total = con.execute(
        "SELECT COUNT(*) FROM raw.claims"
    ).fetchone()[0]

    con.execute("COMMIT")

    print("Incremental ingestion completed successfully!")
    print(f"New claims inserted: {new_count}")
    print(f"Existing claims updated: {changed_count}")
    print(f"Total RAW claims: {total}")

except Exception:
    con.execute("ROLLBACK")
    raise
finally:
    con.close()
