"""
export_for_tableau.py
Runs the risk-flagging SQL logic against budget_analysis.db and exports two
clean, ready-to-plot CSVs for Tableau Public (which has no native SQLite
connector, so this is the bridge between the SQL layer and Tableau).

Output:
  data/tableau_budget_vs_actual.csv    (historical, FY2020-2025, with risk_flag)
  data/tableau_forecast_vs_budget.csv  (forecasted, FY2026-2027, already has risk_flag)
"""

import sqlite3
import pandas as pd

DB_PATH = "budget_analysis.db"

HISTORICAL_QUERY = """
SELECT
    agency_name,
    fiscal_year,
    budget_amount,
    actual_amount,
    variance_amount,
    ROUND(variance_pct, 2) AS variance_pct,
    CASE
        WHEN variance_pct >= 15 THEN 'HIGH RISK'
        WHEN variance_pct >= 5  THEN 'AT RISK'
        WHEN variance_pct <= -15 THEN 'SIGNIFICANT UNDERSPEND'
        ELSE 'ON TRACK'
    END AS risk_flag
FROM budget_vs_actual
ORDER BY fiscal_year, agency_name;
"""


def main():
    conn = sqlite3.connect(DB_PATH)

    historical = pd.read_sql_query(HISTORICAL_QUERY, conn)
    historical.to_csv("data/tableau_budget_vs_actual.csv", index=False)
    print(f"Exported {len(historical)} rows -> data/tableau_budget_vs_actual.csv")

    forecast = pd.read_sql_query("SELECT * FROM forecast_vs_budget;", conn)
    forecast.to_csv("data/tableau_forecast_vs_budget.csv", index=False)
    print(f"Exported {len(forecast)} rows -> data/tableau_forecast_vs_budget.csv")

    conn.close()


if __name__ == "__main__":
    main()