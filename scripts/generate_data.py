
from pathlib import Path
import random
import pandas as pd
from faker import Faker

fake = Faker()
Faker.seed(42)
random.seed(42)

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

# Generate 1,000 fictional insurance members
members = []
for i in range(1, 1001):
    members.append({
        "member_id": f"M{i:05d}",
        "age": random.randint(18, 85),
        "region": random.choice(["Ontario", "Alberta", "BC", "Quebec"]),
        "policy_id": f"P{i:05d}"
    })

members_df = pd.DataFrame(members)
members_df.to_csv(DATA_DIR / "members.csv", index=False)

# Generate 5,000 synthetic medical claims
claims = []
for i in range(1, 5001):
    member = random.choice(members)
    amount = round(random.uniform(50, 10000), 2)

    claims.append({
        "claim_id": f"C{i:06d}",
        "member_id": member["member_id"],
        "policy_id": member["policy_id"],
        "provider_id": f"H{random.randint(1, 100):04d}",
        "claim_date": fake.date_between(
            start_date="-2y",
            end_date="today"
        ).isoformat(),
        "claim_amount": amount,
        "claim_status": random.choice(
            ["Approved", "Rejected", "Pending"]
        )
    })

claims_df = pd.DataFrame(claims)
claims_df.to_csv(DATA_DIR / "claims.csv", index=False)

print("Synthetic healthcare data generated successfully!")
print(f"Members: {len(members_df)}")
print(f"Claims: {len(claims_df)}")
print(f"Saved to: {DATA_DIR}")
