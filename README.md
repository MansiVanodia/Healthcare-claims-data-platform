
# Healthcare Claims Data Platform

### End-to-End Data Engineering & Fraud Risk Analytics Project

A portfolio project that demonstrates a healthcare insurance claims data pipeline using Python, DuckDB, dbt, SQL, automated data quality checks, incremental ingestion, audit logging, and Power BI.

All data used in this project is synthetic.

## Project Overview

This project processes synthetic healthcare insurance claims to support:

- Claims ingestion and validation
- Incremental batch processing
- Insert and update handling
- Duplicate prevention and idempotency
- Transaction rollback on validation failure
- Pipeline audit logging
- Watermark tracking
- Data transformation using dbt
- Rule-based fraud risk indicators
- Power BI analytics and reporting


## Key Project Highlights

- Built an end-to-end healthcare claims data pipeline using Python, DuckDB, dbt, and SQL.
- Processed 1,000 synthetic members and 5,000 initial healthcare claims.
- Implemented incremental batch ingestion with insert/update handling and idempotent processing.
- Added transaction rollback, watermark tracking, and pipeline audit logging.
- Developed dbt staging, dimension, fact, and fraud risk analytics models.
- Implemented automated data quality checks using dbt tests and pytest.
- Created a Power BI dashboard to monitor claims performance and fraud risk indicators.
- Published project documentation, architecture, and dashboard preview on GitHub.

## Technology Stack

| Component | Technology |
|---|---|
| Programming | Python |
| Database | DuckDB |
| Transformations | dbt, SQL |
| Data Processing | Pandas |
| Data Generation | Faker |
| Testing | dbt tests, pytest |
| Visualization | Power BI |
| Development | VS Code, Git |


## Data Architecture

The Healthcare Claims Data Engineering Platform uses Python, DuckDB, dbt, and Power BI to process synthetic healthcare claims, perform incremental ingestion, and generate fraud risk analytics.

### End-to-End Architecture

![Healthcare Claims Data Engineering Architecture](docs/healthcare_architecture.png)

### Pipeline Reliability & Data Quality

The pipeline implements incremental watermark tracking, audit logging, idempotent upserts, transaction rollback on validation failure, automated dbt tests, and pytest validation.


## Power BI Dashboard Preview

![Healthcare Claims Analytics Dashboard](dashboard/dashboard_preview.png)


## Getting Started

### Prerequisites

- Python 3.10 or later (compatible version)
- Git
- DuckDB
- dbt-duckdb
- Power BI Desktop (optional, for dashboard viewing)

### 1. Clone the Repository

```bash
git clone https://github.com/MansiVanodia/Healthcare-claims-data-platform.git
cd Healthcare-claims-data-platform
```

### 2. Create a Virtual Environment

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 3. Install Dependencies

```powershell
pip install -r requirements.txt
```

### 4. Generate Data and Initialize DuckDB

From the project root, run:

```powershell
python scripts\generate_data.py
python scripts\ingest_data.py
```

This generates 1,000 synthetic members and 5,000 claims, then creates the DuckDB database and raw tables.

### 5. Configure dbt

Copy `profiles.yml.example` to your dbt profiles directory (`~/.dbt/profiles.yml`).

In PowerShell, set the database path:

```powershell
$env:HEALTHCARE_DB_PATH = (Resolve-Path ".\warehouse\healthcare.duckdb").Path
```

The environment variable must be set in the terminal session where dbt runs.


### 6. Run dbt Transformations

Navigate to the dbt project directory:

```powershell
cd healthcare_claims
dbt debug
dbt run
dbt test
```

### 7. Run Pipeline Monitoring and Quality Checks

Return to the project root:

```powershell
cd ..
python scripts\pipeline_monitor.py
python scripts\run_quality_checks.py
```

### 8. View the Power BI Dashboard

Open the Power BI project file:

`dashboard/Healthcare_Claims_Fraud_Analytics.pbix`

The dashboard presents claims volume, total claim amount, fraud risk distribution, and high-risk claims indicators.

> **Note:** This project uses synthetic healthcare data. The initial database and raw tables must be created before running dbt transformations.
