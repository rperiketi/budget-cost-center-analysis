"""
forecast.py
Forecasts each agency's ACTUAL spend for future fiscal years (FY2026, FY2027)
using Holt's linear trend method (statsmodels), then compares that forecast
against the budget NYC has already published for those years.

Why Holt's method instead of ARIMA/Prophet:
  We only have 6 annual observations per agency (FY2020-2025). That's too
  short a series for ARIMA order selection or Prophet's seasonality
  components to be meaningful. Holt's linear trend model is the
  appropriately-sized tool for a short annual series where we mainly care
  about capturing trend direction and rate of change.

Output:
  data/forecast_vs_budget.csv
"""

import pandas as pd
from statsmodels.tsa.holtwinters import Holt

DATA_DIR = "data"
MIN_YEARS_REQUIRED = 4          # don't forecast an agency with too little history
FORECAST_YEARS_AHEAD = 2        # FY2026, FY2027

# Risk thresholds for the FORECAST-vs-budget comparison (tune after reviewing output)
HIGH_RISK_THRESHOLD = 10   # % over budget
AT_RISK_THRESHOLD = 5      # % over budget


def flag_risk(pct):
    if pd.isna(pct):
        return "INSUFFICIENT DATA"
    if pct >= HIGH_RISK_THRESHOLD:
        return "HIGH RISK"
    if pct >= AT_RISK_THRESHOLD:
        return "AT RISK"
    if pct <= -HIGH_RISK_THRESHOLD:
        return "SIGNIFICANT UNDERSPEND"
    return "ON TRACK"


def main():
    history = pd.read_csv(f"{DATA_DIR}/budget_vs_actual.csv")
    future_budget = pd.read_csv(f"{DATA_DIR}/budget_by_agency_year.csv")
    future_budget = future_budget.rename(columns={
        "agency_name": "agency_name",
        "total_budget": "budget_amount",
    })

    results = []

    for agency in sorted(history["agency_name"].unique()):
        agency_hist = history[history["agency_name"] == agency].sort_values("fiscal_year")

        if len(agency_hist) < MIN_YEARS_REQUIRED:
            print(f"Skipping {agency}: only {len(agency_hist)} years of history (need {MIN_YEARS_REQUIRED}+)")
            continue

        series = agency_hist.set_index("fiscal_year")["actual_amount"]

        try:
            model = Holt(series, initialization_method="estimated").fit()
            forecast = model.forecast(FORECAST_YEARS_AHEAD)
        except Exception as e:
            print(f"  Forecast failed for {agency}: {e}")
            continue

        last_year = int(series.index.max())
        for i, forecasted_actual in enumerate(forecast, start=1):
            fy = last_year + i

            # Look up the already-published budget for that future fiscal year
            budget_row = future_budget[
                (future_budget["agency_name"] == agency) &
                (future_budget["fiscal_year"] == fy)
            ]
            budget_amount = budget_row["budget_amount"].values[0] if len(budget_row) else None

            variance_pct = None
            if budget_amount:
                variance_pct = ((forecasted_actual - budget_amount) / budget_amount) * 100

            results.append({
                "agency_name": agency,
                "fiscal_year": fy,
                "forecasted_actual": round(forecasted_actual, 2),
                "budget_amount": budget_amount,
                "forecast_variance_pct": round(variance_pct, 2) if variance_pct is not None else None,
                "risk_flag": flag_risk(variance_pct),
            })

    out = pd.DataFrame(results)
    out.to_csv(f"{DATA_DIR}/forecast_vs_budget.csv", index=False)

    print(f"\nForecast complete: {len(out)} agency-year rows -> data/forecast_vs_budget.csv")
    print("\nRisk flag summary (forecasted years):")
    print(out["risk_flag"].value_counts())


if __name__ == "__main__":
    main()