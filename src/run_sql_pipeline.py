"""Execute SQL transformations using DuckDB against raw CSV data."""
from pathlib import Path
import duckdb

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_RAW = PROJECT_ROOT / "data" / "raw" / "cx_support_tickets.csv"
DATA_PROCESSED = PROJECT_ROOT / "data" / "processed"
SQL_DIR = PROJECT_ROOT / "sql"


def main():
    con = duckdb.connect(database=":memory:")

    # 1. Register raw CSV as a table
    print("Loading raw CSV into DuckDB...")
    con.execute(
        f"CREATE TABLE raw_support_tickets AS SELECT * FROM read_csv_auto('{DATA_RAW.as_posix()}')"
    )

    # 2. Execute SQL scripts in order
    sql_files = [
        "01_stg_support_tickets.sql",
        "02_agg_category_performance.sql",
        "03_agg_customer_tier_health.sql",
    ]

    for sql_file in sql_files:
        path = SQL_DIR / sql_file
        print(f"Executing {sql_file}...")
        with open(path, "r", encoding="utf-8") as f:
            query = f.read()
        con.execute(query)

    # 3. Export aggregated outputs to data/processed/
    DATA_PROCESSED.mkdir(parents=True, exist_ok=True)

    print("\nExporting processed views to data/processed/...")
    con.execute(
        f"COPY (SELECT * FROM agg_category_performance) TO '{(DATA_PROCESSED / 'category_performance.csv').as_posix()}' (HEADER, DELIMITER ',')"
    )
    con.execute(
        f"COPY (SELECT * FROM agg_customer_tier_health) TO '{(DATA_PROCESSED / 'customer_tier_health.csv').as_posix()}' (HEADER, DELIMITER ',')"
    )

    # Display preview of results
    print("\n--- Category Performance Preview ---")
    print(
        con.execute(
            "SELECT category, subcategory, total_tickets, avg_csat_score, sla_compliance_rate_pct FROM agg_category_performance LIMIT 5"
        ).fetchdf()
    )

    print("\n--- Customer Tier Health Preview ---")
    print(con.execute("SELECT * FROM agg_customer_tier_health").fetchdf())


if __name__ == "__main__":
    main()