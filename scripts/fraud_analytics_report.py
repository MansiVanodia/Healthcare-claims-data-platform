
from pathlib import Path
import duckdb

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "warehouse" / "healthcare.duckdb"
OUTPUT_DIR = BASE_DIR / "reports"
OUTPUT_DIR.mkdir(exist_ok=True)

con = duckdb.connect(str(DB_PATH), read_only=True)

reports = {
    "risk_summary": """
        SELECT
            risk_level,
            COUNT(*) AS total_claims,
            ROUND(SUM(claim_amount), 2) AS total_amount,
            ROUND(AVG(claim_amount), 2) AS avg_amount
        FROM main.fact_claim_risk
        GROUP BY risk_level
        ORDER BY total_claims DESC
    """,
    "high_risk_claims": """
        SELECT *
        FROM main.fact_claim_risk
        WHERE risk_level = 'HIGH'
        ORDER BY risk_score DESC, claim_amount DESC
    """,
    "provider_risk_summary": """
        SELECT
            provider_id,
            COUNT(*) AS total_claims,
            SUM(CASE WHEN risk_level = 'HIGH' THEN 1 ELSE 0 END)
                AS high_risk_claims,
            SUM(CASE WHEN risk_level = 'MEDIUM' THEN 1 ELSE 0 END)
                AS medium_risk_claims,
            ROUND(SUM(claim_amount), 2) AS total_amount
        FROM main.fact_claim_risk
        GROUP BY provider_id
        ORDER BY high_risk_claims DESC,
                 medium_risk_claims DESC
    """,
}

try:
    for name, query in reports.items():
        output_file = OUTPUT_DIR / f"{name}.csv"

        con.execute(
            f"COPY ({query}) TO '{output_file.as_posix()}' "
            "(HEADER, DELIMITER ',')"
        )

        count = con.execute(
            f"SELECT COUNT(*) FROM ({query})"
        ).fetchone()[0]

        print(f"{name}: {count} rows exported")
        print(f"Saved: {output_file}")

    print("\nFRAUD ANALYTICS REPORTS GENERATED!")

finally:
    con.close()
