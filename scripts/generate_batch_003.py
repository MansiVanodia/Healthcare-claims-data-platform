
from pathlib import Path
from datetime import date
import random

import duckdb
import pandas as pd

random.seed(2027)

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "warehouse" / "healthcare.duckdb"
OUTPUT = BASE_DIR / "data" / "incremental" / "claims_batch_003.csv"
OUTPUT.parent.mkdir(parents=True, exist_ok=True)

con = duckdb.connect(str(DB_PATH), read_only=True)

try:
    members = con.execute("""
        SELECT member_id, policy_id
        FROM raw.members
        ORDER BY member_id
    """).fetchall()

    pending = con.execute("""
        SELECT
            claim_id, member_id, policy_id, provider_id,
            claim_date, claim_amount, claim_status
        FROM raw.claims
        WHERE claim_status = 'Pending'
        ORDER BY claim_id
        LIMIT 20
    """).df()

    existing_ids = {
        row[0] for row in con.execute(
            "SELECT claim_id FROM raw.claims"
        ).fetchall()
    }
finally:
    con.close()

if len(pending) < 20:
    raise ValueError("Not enough pending claims.")

new_claims = []

for i in range(5201, 5301):
    claim_id = f"C{i:06d}"

    if claim_id in existing_ids:
        raise ValueError(f"Claim ID already exists: {claim_id}")

    member_id, policy_id = random.choice(members)

    new_claims.append({
        "claim_id": claim_id,
        "member_id": member_id,
        "policy_id": policy_id,
        "provider_id": f"H{random.randint(1, 100):04d}",
        "claim_date": date.today().isoformat(),
        "claim_amount": round(random.uniform(100, 9000), 2),
        "claim_status": "Pending",
        "record_type": "INSERT"
    })

updates = pending.copy()
updates["claim_status"] = "Approved"
updates["record_type"] = "UPDATE"

batch = pd.concat(
    [pd.DataFrame(new_claims), updates],
    ignore_index=True
)

batch.to_csv(OUTPUT, index=False)

print("Batch 002 generated successfully!")
print("New claims: 100")
print("Status updates: 20")
print(f"Total batch records: {len(batch)}")
print(f"Saved to: {OUTPUT}")
