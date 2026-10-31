
{{ config(materialized='table') }}

WITH claims AS (
    SELECT *
    FROM {{ ref('fact_claims') }}
),

risk_rules AS (
    SELECT
        *,
        CASE
            WHEN claim_amount > 8000 THEN 1
            ELSE 0
        END AS high_amount_flag,

        CASE
            WHEN COUNT(*) OVER (
                PARTITION BY member_id, claim_date
            ) >= 3 THEN 1
            ELSE 0
        END AS multiple_claims_same_day_flag,

        CASE
            WHEN COUNT(*) OVER (
                PARTITION BY
                    member_id,
                    provider_id,
                    claim_date,
                    claim_amount
            ) > 1 THEN 1
            ELSE 0
        END AS duplicate_billing_flag

    FROM claims
),

scored AS (
    SELECT
        *,
        high_amount_flag
        + multiple_claims_same_day_flag
        + duplicate_billing_flag AS risk_score
    FROM risk_rules
)

SELECT
    *,
    CASE
        WHEN risk_score >= 2 THEN 'HIGH'
        WHEN risk_score = 1 THEN 'MEDIUM'
        ELSE 'LOW'
    END AS risk_level
FROM scored
