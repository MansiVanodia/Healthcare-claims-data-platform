
from pathlib import Path
from datetime import datetime
import argparse
import hashlib
import duckdb

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "warehouse" / "healthcare.duckdb"
PIPELINE = "healthcare_claims_incremental"


def run_pipeline(batch_id, batch_file):
    batch_path = Path(batch_file).resolve()

    if not batch_path.is_file():
        raise FileNotFoundError(batch_path)

    batch_hash = hashlib.sha256(
        batch_path.read_bytes()
    ).hexdigest()

    con = duckdb.connect(str(DB_PATH))

    try:
        con.execute("BEGIN TRANSACTION")

        existing = con.execute("""
            SELECT status, source_file
            FROM audit.batch_runs
            WHERE batch_id = ?
        """, [batch_id]).fetchone()

        if existing:
            if existing[0] == "SUCCESS":
                if f"sha256:{batch_hash}" not in (existing[1] or ""):
                    raise ValueError(
                        "Batch ID already exists with different file content."
                    )

                con.execute("ROLLBACK")
                print(f"{batch_id}: already processed. Skipping.")
                return

            raise ValueError(
                f"Batch ID already exists with status {existing[0]}"
            )

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
        """, [str(batch_path)])

        invalid = con.execute("""
            SELECT COUNT(*)
            FROM incoming_claims
            WHERE claim_id IS NULL
               OR TRIM(claim_id) = ''
               OR member_id IS NULL
               OR policy_id IS NULL
               OR provider_id IS NULL
               OR claim_date IS NULL
               OR claim_amount IS NULL
               OR claim_amount <= 0
               OR claim_status NOT IN (
                   'Pending', 'Approved', 'Rejected'
               )
               OR claim_status IS NULL
               OR record_type NOT IN ('INSERT', 'UPDATE')
               OR record_type IS NULL
        """).fetchone()[0]

        duplicates = con.execute("""
            SELECT COUNT(*) - COUNT(DISTINCT claim_id)
            FROM incoming_claims
        """).fetchone()[0]

        unknown_members = con.execute("""
            SELECT COUNT(*)
            FROM incoming_claims i
            LEFT JOIN raw.members m
                ON i.member_id = m.member_id
               AND i.policy_id = m.policy_id
            WHERE m.member_id IS NULL
        """).fetchone()[0]

        existing_inserts = con.execute("""
            SELECT COUNT(*)
            FROM incoming_claims i
            JOIN raw.claims r
                ON i.claim_id = r.claim_id
            WHERE i.record_type = 'INSERT'
        """).fetchone()[0]

        invalid_updates = con.execute("""
            SELECT COUNT(*)
            FROM incoming_claims i
            LEFT JOIN raw.claims r
                ON i.claim_id = r.claim_id
            WHERE i.record_type = 'UPDATE'
              AND (
                  r.claim_id IS NULL
                  OR i.member_id IS DISTINCT FROM r.member_id
                  OR i.policy_id IS DISTINCT FROM r.policy_id
                  OR i.provider_id IS DISTINCT FROM r.provider_id
                  OR i.claim_date IS DISTINCT FROM r.claim_date
                  OR i.claim_amount IS DISTINCT FROM r.claim_amount
              )
        """).fetchone()[0]

        if any([
            invalid, duplicates, unknown_members,
            existing_inserts, invalid_updates
        ]):
            raise ValueError(
                f"Validation failed: invalid={invalid}, "
                f"duplicates={duplicates}, "
                f"unknown_members={unknown_members}, "
                f"existing_inserts={existing_inserts}, "
                f"invalid_updates={invalid_updates}"
            )

        inserted = con.execute("""
            SELECT COUNT(*)
            FROM incoming_claims
            WHERE record_type = 'INSERT'
        """).fetchone()[0]

        updated = con.execute("""
            SELECT COUNT(*)
            FROM incoming_claims i
            JOIN raw.claims r
                ON i.claim_id = r.claim_id
            WHERE i.record_type = 'UPDATE'
              AND i.claim_status IS DISTINCT FROM r.claim_status
        """).fetchone()[0]

        total = con.execute("""
            SELECT COUNT(*) FROM incoming_claims
        """).fetchone()[0]

        started_at = datetime.now()

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

        con.execute("""
            INSERT INTO audit.batch_runs (
                batch_id, source_file, started_at, completed_at,
                status, inserted_count, updated_count,
                total_records, error_message
            )
            VALUES (?, ?, ?, ?, 'SUCCESS', ?, ?, ?, NULL)
        """, [
            batch_id,
            f"{batch_path.name} | sha256:{batch_hash}",
            started_at,
            completed_at,
            inserted,
            updated,
            total
        ])

        con.execute("""
            INSERT INTO audit.pipeline_watermarks (
                pipeline_name, last_batch_id, last_success_at
            )
            VALUES (?, ?, ?)
            ON CONFLICT (pipeline_name)
            DO UPDATE SET
                last_batch_id = excluded.last_batch_id,
                last_success_at = excluded.last_success_at
        """, [PIPELINE, batch_id, completed_at])

        con.execute("COMMIT")

        print("PIPELINE COMPLETED SUCCESSFULLY")
        print(f"Batch: {batch_id}")
        print(f"Inserted: {inserted}")
        print(f"Updated: {updated}")
        print(f"Total batch records: {total}")
        print(f"Watermark advanced to: {batch_id}")

    except Exception:
        con.execute("ROLLBACK")
        raise

    finally:
        con.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--batch-id", required=True)
    parser.add_argument("--file", required=True)
    args = parser.parse_args()

    run_pipeline(args.batch_id, args.file)
