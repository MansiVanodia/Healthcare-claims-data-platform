
from pathlib import Path
from datetime import datetime
import hashlib
import duckdb

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "warehouse" / "healthcare.duckdb"
BATCH_PATH = BASE_DIR / "data" / "incremental" / "claims_batch_002.csv"

BATCH_ID = "BATCH_002"

if not BATCH_PATH.exists():
    raise FileNotFoundError(BATCH_PATH)

# Fingerprint protects against accidental batch file changes.
batch_hash = hashlib.sha256(BATCH_PATH.read_bytes()).hexdigest()

con = duckdb.connect(str(DB_PATH))

try:
    # Prevent processing a completed batch again.
    existing = con.execute("""
        SELECT status
        FROM audit.batch_runs
        WHERE batch_id = ?
    """, [BATCH_ID]).fetchone()

    if existing and existing[0] == "SUCCESS":
        print(f"{BATCH_ID} already processed successfully.")
        print("Skipping duplicate batch.")
    else:
        started_at = datetime.now()

        con.execute("BEGIN TRANSACTION")

        try:
            con.execute("""
                CREATE TEMP TABLE incoming_claims AS
                SELECT
                    claim_id,
                    member_id,
                    policy_id,
                    provider_id,
                    CAST(claim_date AS DATE) AS claim_date,
                    CAST(claim_amount AS DECIMAL(12,2)) AS claim_amount,
                    claim_status,
                    record_type
                FROM read_csv_auto(?)
            """, [str(BATCH_PATH)])

            total_records = con.execute("""
                SELECT COUNT(*) FROM incoming_claims
            """).fetchone()[0]

            invalid = con.execute("""
                SELECT COUNT(*)
                FROM incoming_claims
                WHERE claim_id IS NULL
                   OR TRIM(claim_id) = ''
                   OR member_id IS NULL
                   OR claim_amount IS NULL
                   OR claim_amount <= 0
                   OR record_type IS NULL
                   OR record_type NOT IN ('INSERT', 'UPDATE')
            """).fetchone()[0]

            duplicate_ids = con.execute("""
                SELECT COUNT(*) - COUNT(DISTINCT claim_id)
                FROM incoming_claims
            """).fetchone()[0]

            if invalid or duplicate_ids:
                raise ValueError(
                    f"Invalid rows: {invalid}, duplicate IDs: {duplicate_ids}"
                )

            unknown_members = con.execute("""
                SELECT COUNT(*)
                FROM incoming_claims i
                LEFT JOIN raw.members m
                    ON i.member_id = m.member_id
                WHERE m.member_id IS NULL
            """).fetchone()[0]

            if unknown_members:
                raise ValueError(
                    f"Unknown member references: {unknown_members}"
                )

            existing_inserts = con.execute("""
                SELECT COUNT(*)
                FROM incoming_claims i
                JOIN raw.claims r ON i.claim_id = r.claim_id
                WHERE i.record_type = 'INSERT'
            """).fetchone()[0]

            missing_updates = con.execute("""
                SELECT COUNT(*)
                FROM incoming_claims i
                LEFT JOIN raw.claims r ON i.claim_id = r.claim_id
                WHERE i.record_type = 'UPDATE'
                  AND r.claim_id IS NULL
            """).fetchone()[0]

            if existing_inserts or missing_updates:
                raise ValueError(
                    f"Existing INSERT IDs: {existing_inserts}; "
                    f"missing UPDATE IDs: {missing_updates}"
                )

            inserted_count = con.execute("""
                SELECT COUNT(*)
                FROM incoming_claims
                WHERE record_type = 'INSERT'
            """).fetchone()[0]

            updated_count = con.execute("""
                SELECT COUNT(*)
                FROM incoming_claims i
                JOIN raw.claims r ON i.claim_id = r.claim_id
                WHERE i.record_type = 'UPDATE'
                  AND i.claim_status IS DISTINCT FROM r.claim_status
            """).fetchone()[0]

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
                    claim_id, member_id, policy_id, provider_id,
                    claim_date, claim_amount, claim_status
                FROM incoming_claims
                WHERE record_type = 'INSERT'
            """)

            completed_at = datetime.now()

            # Audit log and data changes commit together.
            con.execute("""
                INSERT INTO audit.batch_runs (
                    batch_id, source_file, started_at, completed_at,
                    status, inserted_count, updated_count,
                    total_records, error_message
                )
                VALUES (?, ?, ?, ?, 'SUCCESS', ?, ?, ?, NULL)
            """, [
                BATCH_ID,
                f"{BATCH_PATH.name} | sha256:{batch_hash}",
                started_at,
                completed_at,
                inserted_count,
                updated_count,
                total_records
            ])

            con.execute("COMMIT")

            print("Batch 002 ingestion successful!")
            print(f"Inserted: {inserted_count}")
            print(f"Updated: {updated_count}")
            print(f"Batch records: {total_records}")
            print("Audit status: SUCCESS")

        except Exception:
            con.execute("ROLLBACK")
            raise

finally:
    con.close()
