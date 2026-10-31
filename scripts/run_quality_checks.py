
from pathlib import Path
import subprocess
import sys

BASE_DIR = Path(__file__).resolve().parent.parent
DBT_DIR = BASE_DIR / "healthcare_claims"

steps = [
    (
        "Refresh dbt models",
        ["dbt", "run", "--select", "+fact_claim_risk"],
        DBT_DIR,
    ),
    (
        "Run dbt data quality tests",
        ["dbt", "test", "--select", "dim_members", "fact_claims"],
        DBT_DIR,
    ),
    (
        "Run Python automated tests",
        [sys.executable, "-m", "pytest", "tests/test_pipeline.py", "-v"],
        BASE_DIR,
    ),
]

for name, command, working_dir in steps:
    print(f"\n{'=' * 50}", flush=True)
    print(f"STARTING: {name}", flush=True)
    print(f"{'=' * 50}", flush=True)

    result = subprocess.run(command, cwd=working_dir)

    if result.returncode != 0:
        print(f"\nFAILED: {name}")
        sys.exit(result.returncode)

    print(f"PASSED: {name}", flush=True)

print("\nALL PIPELINE QUALITY CHECKS PASSED!")
