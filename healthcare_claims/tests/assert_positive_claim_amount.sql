
SELECT
    claim_id,
    claim_amount
FROM {{ ref('fact_claims') }}
WHERE claim_amount <= 0
