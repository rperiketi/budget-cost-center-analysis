"""
load_to_sqlite.py
Loads both:
  - data/budget_vs_actual.csv        -> table: budget_vs_actual (historical, FY2020-2025)
  - data/forecast_vs_budget.csv      -> table: forecast_vs_budget (forecasted, FY2026-2027)
into budget_analysis.db using the schema in sql/schema.sql.
"""

import sqlite3
import pandas as pd

DB_PATH = "budget_analysis.db"
HISTORY_CSV = "data/budget_vs_actual.csv"
FORECAST_CSV = "data/forecast_vs_budget.csv"
SCHEMA_PATH = "sql/schema.sql"


def main():
    history = pd.read_csv(HISTORY_CSV)
    forecast = pd.read_csv(FORECAST_CSV)

    conn = sqlite3.connect(DB_PATH)

    conn.execute("DROP TABLE IF EXISTS budget_vs_actual;")
    conn.execute("DROP TABLE IF EXISTS forecast_vs_budget;")
    with open(SCHEMA_PATH, "r") as f:
        conn.executescript(f.read())

    history.to_sql("budget_vs_actual", conn, if_exists="append", index=False)
    forecast.to_sql("forecast_vs_budget", conn, if_exists="replace", index=False)

    hist_count = conn.execute("SELECT COUNT(*) FROM budget_vs_actual;").fetchone()[0]
    fc_count = conn.execute("SELECT COUNT(*) FROM forecast_vs_budget;").fetchone()[0]
    print(f"Loaded {hist_count} rows into budget_vs_actual")
    print(f"Loaded {fc_count} rows into forecast_vs_budget")

    conn.commit()
    conn.close()


if __name__ == "__main__":
    main()