
{{ config(materialized='view') }}

SELECT
    TRIM(member_id) AS member_id,
    CAST(age AS INTEGER) AS age,
    TRIM(region) AS region,
    TRIM(policy_id) AS policy_id
FROM {{ source('raw', 'members') }}
