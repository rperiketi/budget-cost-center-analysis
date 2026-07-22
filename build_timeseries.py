"""
build_timeseries.py
Combines historical (budget_vs_actual.csv) and forecasted (forecast_vs_budget.csv)
data into one long/tidy CSV spanning all years, for a single line chart with
Budget and Actual/Forecast as two colored lines per agency.

Output columns:
  agency_name, fiscal_year, metric, value, is_forecast
    metric: "Budget" or "Actual"
    is_forecast: "Forecast" for FY2026-2027 actual line, "Historical" otherwise
"""

import pandas as pd

historical = pd.read_csv("data/budget_vs_actual.csv")
forecast = pd.read_csv("data/forecast_vs_budget.csv")

rows = []

# Historical: Budget + Actual, both "Historical"
for _, r in historical.iterrows():
    rows.append({"agency_name": r["agency_name"], "fiscal_year": r["fiscal_year"],
                 "metric": "Budget", "value": r["budget_amount"], "is_forecast": "Historical"})
    rows.append({"agency_name": r["agency_name"], "fiscal_year": r["fiscal_year"],
                 "metric": "Actual", "value": r["actual_amount"], "is_forecast": "Historical"})

# Forecast years: Budget (already real/published) + Forecasted Actual ("Forecast")
for _, r in forecast.iterrows():
    if pd.notna(r["budget_amount"]):
        rows.append({"agency_name": r["agency_name"], "fiscal_year": r["fiscal_year"],
                     "metric": "Budget", "value": r["budget_amount"], "is_forecast": "Historical"})
    rows.append({"agency_name": r["agency_name"], "fiscal_year": r["fiscal_year"],
                 "metric": "Actual", "value": r["forecasted_actual"], "is_forecast": "Forecast"})

out = pd.DataFrame(rows).sort_values(["agency_name", "fiscal_year", "metric"])
out.to_csv("data/timeseries_budget_actual.csv", index=False)
print(f"Saved {len(out)} rows -> data/timeseries_budget_actual.csv")
print(f"Years covered: {sorted(out['fiscal_year'].unique())}")