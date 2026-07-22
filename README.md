# NYC Budget Variance & Forecast Dashboard

A full SQL + Python + Tableau pipeline that tracks budget vs. actual spending
across NYC government agencies, flags at-risk departments, and forecasts
future spend using a statistical trend model.

**Live dashboard:** _https://public.tableau.com/app/profile/renusri.periketi4831/viz/NYCBudgetvsForecast2020-2027/NYCBudgetVarianceForecastDashboard_

---

## Business Problem

Simulates a real cost-center monitoring workflow: track how each department's
actual spend compares to its budget, flag departments trending over/under
budget, and forecast whether currently-published future budgets look
realistic given historical spending patterns.

## Data Sources

Real, public NYC Open Data (Socrata API), not synthetic data:
- **Expense Budget** (`mwzb-yiwb`) — line-item budget data by agency, updated
  3x/year (Preliminary, Executive, Adopted).
- **Expense Actuals By Funding Source** (`nrik-v7ws`) — actual spend by
  agency and funding source.

An earlier candidate actuals dataset (`7yay-m4ae`) was identified as stale
(last updated 2017) during initial exploration and swapped out before
building the pipeline — see `preview_actuals.py` for that exploration.

## Pipeline

```
fetch_data.py          -> pulls aggregated budget & actuals from NYC's SODA API
clean_transform.py      -> normalizes agency names, joins budget+actuals, computes variance
load_to_sqlite.py       -> loads clean data into SQLite (budget_analysis.db)
sql/analysis_queries.sql -> variance analysis, risk-tier flagging (SQL)
forecast.py             -> Holt's linear trend forecast of future actual spend
export_for_tableau.py   -> exports SQL query results as Tableau-ready CSVs
build_timeseries.py     -> builds a combined long-format CSV for trend visualization
```

## Data Quality Issues Found & Fixed

Two real bugs surfaced during development, both fixed before analysis:

1. **Triple-counted budget totals.** NYC's Expense Budget dataset contains
   3 publication snapshots per fiscal year (Preliminary, Executive, Adopted).
   An initial aggregation grouped only by agency + fiscal year, silently
   summing all 3 snapshots together and inflating budget totals ~3x. Fixed by
   filtering to only the latest `publication_date` per fiscal year.
2. **Unit mismatch.** The actuals dataset reports dollars **in thousands**;
   the budget dataset reports **whole dollars**. Uncorrected, this produced a
   uniform, implausible ~-99.9% "underspend" across every agency. Fixed by
   scaling actuals by 1,000 before comparison.

## SQL Analysis (`sql/analysis_queries.sql`)

Core variance and risk-tier logic:
- Variance % = (actual - budget) / budget
- Risk tiers: HIGH RISK (≥15%), AT RISK (≥5%), ON TRACK, SIGNIFICANT
  UNDERSPEND (≤-15%) — thresholds tuned against the real data distribution
- FY2025 result: **17 agencies tracked → 10 On Track, 6 At Risk, 1 High Risk**

## Forecasting (`forecast.py`)

Forecasts FY2026-2027 actual spend per agency using **Holt's linear trend
method** (`statsmodels`), then compares that forecast to NYC's already-
published future budget for those years.

**Why Holt instead of ARIMA/Prophet:** each agency has only 6 annual
observations (FY2020-2025) — too short a series for meaningful ARIMA order
selection or Prophet's seasonality components. Holt's method is the
appropriately-sized tool for capturing trend direction on a short annual
series.

Result: 16 of 17 agencies had sufficient history to forecast (1 skipped,
insufficient data) → **22 agency-years On Track, 5 At Risk, 3 High Risk, 2
Significant Underspend** across FY2026-2027.

**Notable finding:** Department of Small Business Services shows the most
volatile variance in both the historical data (+64% in FY2022, -46% in
FY2021) and the forecast (-25% projected for FY2026) — suggesting either a
genuine structural pattern or that its smaller budget size makes it more
sensitive to year-to-year noise.

## Dashboard (Tableau Public)

- **Variance by Agency** — historical budget vs. actual variance, color-coded
  by risk tier, filterable by fiscal year
- **Risk Flag Summary** — count of agencies per risk tier per year
- **Budget vs Forecast Trend** — per-agency time series showing historical
  actual/budget trend continuing into the forecasted years
- Dashboard actions link the risk-tier and variance charts together for
  drill-down exploration

## Tech Stack

Python (pandas, statsmodels, requests) · SQL (SQLite) · Tableau Public

## Running This Project

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python3 fetch_data.py
python3 clean_transform.py
python3 load_to_sqlite.py
python3 forecast.py
python3 export_for_tableau.py
python3 build_timeseries.py
```
Then open the CSVs in `data/` with Tableau Public.
