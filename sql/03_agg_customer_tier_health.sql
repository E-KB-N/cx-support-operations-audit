-- Executive health metrics by customer tier.

CREATE OR REPLACE VIEW agg_customer_tier_health AS
WITH customer_ticket_counts AS (
    SELECT
        customer_tier,
        customer_id,
        COUNT(*) AS customer_ticket_count
    FROM stg_support_tickets
    GROUP BY
        customer_tier,
        customer_id
),
repeat_contact_metrics AS (
    SELECT
        customer_tier,
        COUNT(*) AS distinct_customers,
        SUM(CASE WHEN customer_ticket_count > 1 THEN 1 ELSE 0 END)
            AS repeat_contact_customers
    FROM customer_ticket_counts
    GROUP BY customer_tier
),
tier_ticket_metrics AS (
    SELECT
        customer_tier,
        COUNT(*) AS ticket_volume,
        AVG(csat_score) AS overall_csat_score,
        100.0 * AVG(CAST(sla_met_flag AS DOUBLE PRECISION))
            AS sla_compliance_rate_pct,
        100.0 * AVG(CAST(is_churn_risk AS DOUBLE PRECISION))
            AS churn_risk_ticket_pct
    FROM stg_support_tickets
    GROUP BY customer_tier
)
SELECT
    t.customer_tier,
    t.ticket_volume,
    r.distinct_customers,
    r.repeat_contact_customers,
    -- Share of distinct customers in the tier who contacted support more than once.
    ROUND(
        CAST(
            100.0 * r.repeat_contact_customers / NULLIF(r.distinct_customers, 0)
            AS DECIMAL(18, 4)
        ),
        2
    ) AS repeat_contact_rate_pct,
    ROUND(CAST(t.overall_csat_score AS DECIMAL(18, 4)), 2) AS overall_csat_score,
    ROUND(CAST(t.sla_compliance_rate_pct AS DECIMAL(18, 4)), 2)
        AS sla_compliance_rate_pct,
    ROUND(CAST(t.churn_risk_ticket_pct AS DECIMAL(18, 4)), 2)
        AS churn_risk_ticket_pct
FROM tier_ticket_metrics AS t
INNER JOIN repeat_contact_metrics AS r
    ON t.customer_tier = r.customer_tier;
