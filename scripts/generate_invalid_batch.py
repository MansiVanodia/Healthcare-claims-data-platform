
from pathlib import Path
import csv

BASE_DIR = Path(__file__).resolve().parent.parent
OUTPUT = BASE_DIR / "data" / "incremental" / "claims_batch_004_invalid.csv"

OUTPUT.parent.mkdir(parents=True, exist_ok=True)

with OUTPUT.open("w", newline="", encoding="utf-8") as file:
    writer = csv.writer(file)

    writer.writerow([
        "claim_id", "member_id", "policy_id",
        "provider_id", "claim_date", "claim_amount",
        "claim_status", "record_type"
    ])

    writer.writerow([
        "C005301",
        "M000001",
        "P000001",
        "PR001",
        "2026-10-31",
        -500,
        "Approved",
        "INSERT"
    ])

print("Invalid test batch created successfully.")
print(f"File: {OUTPUT}")
print("Expected validation error: negative claim amount")
