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

```
 Technical Implementation 
1. Data Pipeline & Synthetic EngineeringGenerated a realistic 2,500-ticket dataset using numpy, pandas, and faker incorporating right-skewed lognormal distributions for resolution times and Pareto distributions for repeat customer interactions.
2. SQL Analytics Engine (DuckDB)
   Staging & SLA Logic (01_stg_support_tickets.sql): Implemented tier-specific SLA thresholds (Enterprise: $\le 15$m, Premium: $\le 30$m, Free: $\le 60$m) and defined churn-risk parameters ($CSAT \le 2$ or $Resolution > 48h$).
   Category Performance (02_agg_category_performance.sql): Aggregated total volume, resolution rates, escalation ratios, and SLA compliance percentages by channel and subcategory.
   Tier Health Matrix (03_agg_customer_tier_health.sql): Calculated repeat contact percentages and churn risk exposures by customer tier.

4. NLP Sentiment Analysis & N-Gram Mining
   Utilized NLTK VADER (Valence Aware Dictionary and sEntiment Reasoner) to score ticket text sentiment on a scale from $-1.0$ to $+1.0$.
   Extracted top negative bigrams using custom regular expressions and stop-word filtering across tickets flagged with $CSAT \le 2$ or negative sentiment.

 Strategic Recommendations 
  Self-Service Knowledge Base: Deploy automated self-service workflows for "Password Reset" and "Account Locked" subcategories to clear 19% of ticket volume and reduce queue pressure. 
  Engineering Bug Prioritization: Address checkout state persistence bugs causing "page stuck loading" errors to eliminate the leading driver of customer escalations. 
  Dedicated Enterprise Routing: Route all Enterprise billing queries directly to senior support staff to preserve high-tier revenue and lower repeat contact rates below 10%. 
  
 How to Run Locally

# 1. Clone repository
git clone [https://github.com/your-username/cx-support-operations-audit.git](https://github.com/your-username/cx-support-operations-audit.git)
cd cx-support-operations-audit

# 2. Install dependencies
pip install -r requirements.txt

# 3. Generate raw dataset
python src/generate_data.py

# 4. Run DuckDB SQL pipeline
python src/run_sql_pipeline.py

# 5. Run NLP sentiment analysis
python src/nlp_sentiment_audit.py
