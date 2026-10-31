
{{ config(materialized='view') }}

SELECT
    TRIM(claim_id) AS claim_id,
    TRIM(member_id) AS member_id,
    TRIM(policy_id) AS policy_id,
    TRIM(provider_id) AS provider_id,
    CAST(claim_date AS DATE) AS claim_date,
    CAST(claim_amount AS DECIMAL(12,2)) AS claim_amount,
    UPPER(TRIM(claim_status)) AS claim_status
FROM {{ source('raw', 'claims') }}
