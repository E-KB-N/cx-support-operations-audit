-- Staging model for cleaned support-ticket records.
-- Expected source: raw_support_tickets, loaded from data/raw/cx_support_tickets.csv.

CREATE OR REPLACE VIEW stg_support_tickets AS
WITH typed_tickets AS (
    SELECT
        CAST(ticket_id AS VARCHAR) AS ticket_id,
        CAST(customer_id AS VARCHAR) AS customer_id,
        CAST(created_at AS TIMESTAMP) AS created_at,
        CAST(resolved_at AS TIMESTAMP) AS resolved_at,
        TRIM(CAST(channel AS VARCHAR)) AS channel,
        TRIM(CAST(category AS VARCHAR)) AS category,
        TRIM(CAST(subcategory AS VARCHAR)) AS subcategory,
        TRIM(CAST(customer_tier AS VARCHAR)) AS customer_tier,
        CAST(first_response_time_mins AS INTEGER) AS first_response_time_mins,
        CAST(resolution_time_hours AS DOUBLE PRECISION) AS resolution_time_hours,
        CAST(csat_score AS INTEGER) AS csat_score,
        TRIM(CAST(ticket_status AS VARCHAR)) AS ticket_status,
        TRIM(CAST(ticket_text AS VARCHAR)) AS ticket_text
    FROM raw_support_tickets
),
derived_metrics AS (
    SELECT
        *,
        CASE
            -- SLA thresholds reflect service commitments by customer tier.
            WHEN customer_tier = 'Enterprise' AND first_response_time_mins <= 15 THEN 1
            WHEN customer_tier = 'Premium' AND first_response_time_mins <= 30 THEN 1
            WHEN customer_tier = 'Free' AND first_response_time_mins <= 60 THEN 1
            ELSE 0
        END AS sla_met_flag,
        CASE
            -- Low CSAT or a resolution beyond 48 hours signals churn risk.
            WHEN csat_score <= 2 OR resolution_time_hours > 48 THEN 1
            ELSE 0
        END AS is_churn_risk,
        CAST(
            EXTRACT(EPOCH FROM (CURRENT_TIMESTAMP - created_at)) / 86400.0
            AS DOUBLE PRECISION
        ) AS ticket_age_days
    FROM typed_tickets
)
SELECT *
FROM derived_metrics;
