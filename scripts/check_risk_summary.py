
from pathlib import Path
import duckdb

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "warehouse" / "healthcare.duckdb"

con = duckdb.connect(str(DB_PATH), read_only=True)

try:
    result = con.execute("""
        SELECT
            risk_level,
            COUNT(*) AS total_claims,
            ROUND(AVG(claim_amount), 2) AS avg_claim_amount
        FROM main.fact_claim_risk
        GROUP BY risk_level
        ORDER BY risk_level
    """).fetchall()

    print("CLAIM RISK SUMMARY")
    print("-" * 50)

    for risk_level, count, avg_amount in result:
        print(
            f"{risk_level}: {count} claims "
            f"| Avg Amount: ${avg_amount}"
        )

finally:
    con.close()
