
{{ config(materialized='table') }}

SELECT
    c.claim_id,
    c.member_id,
    c.policy_id,
    c.provider_id,
    c.claim_date,
    c.claim_amount,
    c.claim_status,
    m.region AS member_region
FROM {{ ref('stg_claims') }} c
LEFT JOIN {{ ref('dim_members') }} m
    ON c.member_id = m.member_id
