
{{ config(materialized='table') }}

SELECT
    member_id,
    age,
    region,
    policy_id
FROM {{ ref('stg_members') }}
