
from pathlib import Path
import duckdb
import pytest

BASE_DIR = Path(__file__).resolve().parents[1]
DB_PATH = BASE_DIR / "warehouse" / "healthcare.duckdb"


@pytest.fixture
def db():
    con = duckdb.connect(str(DB_PATH), read_only=True)
    yield con
    con.close()


def test_claim_counts_match(db):
    tables = [
        "raw.claims",
        "main.stg_claims",
        "main.fact_claims",
        "main.fact_claim_risk",
    ]

    counts = [
        db.execute(
            f"SELECT COUNT(*) FROM {table}"
        ).fetchone()[0]
        for table in tables
    ]

    assert len(set(counts)) == 1
    assert counts[0] == 5400


def test_no_duplicate_claim_ids(db):
    duplicates = db.execute("""
        SELECT COUNT(*) - COUNT(DISTINCT claim_id)
        FROM raw.claims
    """).fetchone()[0]

    assert duplicates == 0


def test_no_invalid_claim_amounts(db):
    invalid = db.execute("""
        SELECT COUNT(*)
        FROM raw.claims
        WHERE claim_amount IS NULL
           OR claim_amount <= 0
    """).fetchone()[0]

    assert invalid == 0


def test_watermark(db):
    result = db.execute("""
        SELECT last_batch_id
        FROM audit.pipeline_watermarks
        WHERE pipeline_name = 'healthcare_claims_incremental'
    """).fetchone()

    assert result is not None
    assert result[0] == "BATCH_004"


def test_batch_004_audit(db):
    result = db.execute("""
        SELECT status, inserted_count, updated_count
        FROM audit.batch_runs
        WHERE batch_id = 'BATCH_004'
    """).fetchone()

    assert result == ("SUCCESS", 100, 20)
