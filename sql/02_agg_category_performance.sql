-- Operational performance by issue type and contact channel.

CREATE OR REPLACE VIEW agg_category_performance AS
WITH category_metrics AS (
    SELECT
        category,
        subcategory,
        channel,
        COUNT(*) AS total_tickets,
        -- Resolved and Closed both represent completed support work.
        SUM(CASE WHEN ticket_status IN ('Resolved', 'Closed') THEN 1 ELSE 0 END)
            AS resolved_tickets,
        100.0 * AVG(CASE WHEN ticket_status = 'Escalated' THEN 1.0 ELSE 0.0 END)
            AS escalation_rate_pct,
        AVG(first_response_time_mins) AS avg_first_response_mins,
        AVG(resolution_time_hours) AS avg_resolution_hours,
        AVG(csat_score) AS avg_csat_score,
        -- A survey response is any ticket with a recorded CSAT score.
        100.0 * AVG(CASE WHEN csat_score IS NOT NULL THEN 1.0 ELSE 0.0 END)
            AS survey_response_rate_pct,
        100.0 * AVG(CAST(sla_met_flag AS DOUBLE PRECISION))
            AS sla_compliance_rate_pct
    FROM stg_support_tickets
    GROUP BY
        category,
        subcategory,
        channel
)
SELECT
    category,
    subcategory,
    channel,
    total_tickets,
    resolved_tickets,
    ROUND(CAST(escalation_rate_pct AS DECIMAL(18, 4)), 2) AS escalation_rate_pct,
    ROUND(CAST(avg_first_response_mins AS DECIMAL(18, 4)), 2)
        AS avg_first_response_mins,
    ROUND(CAST(avg_resolution_hours AS DECIMAL(18, 4)), 2) AS avg_resolution_hours,
    ROUND(CAST(avg_csat_score AS DECIMAL(18, 4)), 2) AS avg_csat_score,
    ROUND(CAST(survey_response_rate_pct AS DECIMAL(18, 4)), 2)
        AS survey_response_rate_pct,
    ROUND(CAST(sla_compliance_rate_pct AS DECIMAL(18, 4)), 2)
        AS sla_compliance_rate_pct
FROM category_metrics;
