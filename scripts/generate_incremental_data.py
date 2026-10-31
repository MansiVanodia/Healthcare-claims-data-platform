
from pathlib import Path
from datetime import date
import random
import pandas as pd
import duckdb

random.seed(42)

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "warehouse" / "healthcare.duckdb"
BATCH_DIR = BASE_DIR / "data" / "incremental"
BATCH_DIR.mkdir(parents=True, exist_ok=True)

con = duckdb.connect(str(DB_PATH), read_only=True)

try:
    # Existing claims eligible for status updates
    existing = con.execute("""
        SELECT claim_id, member_id, policy_id,
               provider_id, claim_date, claim_amount,
               claim_status
        FROM raw.claims
        WHERE claim_status = 'Pending'
        ORDER BY claim_id
        LIMIT 20
    """).df()

    # Valid members for new claims
    members = con.execute("""
        SELECT member_id, policy_id
        FROM raw.members
        ORDER BY member_id
    """).fetchall()

finally:
    con.close()

if len(existing) < 20:
    raise ValueError("Not enough pending claims for updates.")

new_claims = []

for i in range(5001, 5101):
    member_id, policy_id = random.choice(members)

    new_claims.append({
        "claim_id": f"C{i:06d}",
        "member_id": member_id,
        "policy_id": policy_id,
        "provider_id": f"H{random.randint(1, 100):04d}",
        "claim_date": date.today().isoformat(),
        "claim_amount": round(random.uniform(100, 9000), 2),
        "claim_status": "Pending",
        "record_type": "INSERT"
    })

updates = existing.copy()
updates["claim_status"] = "Approved"
updates["record_type"] = "UPDATE"

batch_df = pd.concat(
    [pd.DataFrame(new_claims), updates],
    ignore_index=True
)

output_path = BATCH_DIR / "claims_batch_001.csv"
batch_df.to_csv(output_path, index=False)

print("Incremental batch generated successfully!")
print("New claims: 100")
print("Claim status updates: 20")
print(f"Total batch records: {len(batch_df)}")
print(f"Saved to: {output_path}")
