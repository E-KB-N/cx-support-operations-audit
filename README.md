# Customer Experience (CX) Support Operations & Sentiment Audit

![Domain](https://img.shields.io/badge/Domain-Customer_Experience_%26_Operations-blue)
![Stack](https://img.shields.io/badge/Stack-Python_%7C_DuckDB_%7C_SQL_%7C_NLTK_%7C_Power_BI-green)
![Status](https://img.shields.io/badge/Status-Completed-success)

## Business Overview
A growing SaaS application experienced surging customer support queue volumes and declining Customer Satisfaction (CSAT) scores. This audit evaluates **2,500 support tickets** across a 90-day window to identify operational bottlenecks, measure SLA compliance across customer tiers, and surface root-cause drivers of churn risk using natural language processing (NLP).

---

## Key Executive Findings
1. **Resolution Delays Drive CSAT Churn:** CSAT drops linearly from **3.34 (Positive Sentiment)** to **2.53 (Negative Sentiment)** as resolution time exceeds 24 hours. Tickets requiring >48 hours account for **18.2% of total churn risk**.
2. **App Bugs & Billing Bottlenecks:** `Billing/Refunds` and `App Bug` categories account for **51% of total ticket volume** but suffer the lowest SLA compliance (**62.4%**) and highest escalation rates (**14.1%**).
3. **Enterprise Retention Risk:** **14.8%** of Enterprise tier customers required repeat contacts within 90 days, primarily driven by `Login Timeout` and `Payment Failed` errors.
4. **NLP Root-Cause Identification:** Bigram text analysis revealed that **"already tried" (200 instances)** and **"page stuck" (164 instances)** are the primary textual drivers of negative sentiment, indicating UI state bugs in the checkout and login flows.

---

## Repository Architecture
```text
├── data/
│   ├── raw/                    # Synthetic telemetry generator (2,500 tickets)
│   └── processed/              # Enriched datasets (VADER sentiment & aggregated SQL models)
├── sql/                        # Modular transformation scripts (DuckDB/PostgreSQL)
│   ├── 01_stg_support_tickets.sql
│   ├── 02_agg_category_performance.sql
│   └── 03_agg_customer_tier_health.sql
├── src/                        # Production Python modules
│   ├── generate_data.py        # Reproducible synthetic data generation
│   ├── run_sql_pipeline.py     # DuckDB SQL execution & export runner
│   └── nlp_sentiment_audit.py  # NLTK VADER sentiment & bigram extraction pipeline
├── docs/                       # Summary JSON reports and metric definitions
├── requirements.txt
└── README.md