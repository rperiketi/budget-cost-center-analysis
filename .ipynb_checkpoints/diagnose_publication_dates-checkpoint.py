"""
diagnose_publication_dates.py
Checks how many distinct publication_date snapshots exist per fiscal_year
in the Expense Budget dataset. If this shows multiple dates per fiscal_year,
that confirms our earlier aggregation double/triple-counted the budget.
"""

import requests
import pandas as pd

BUDGET_ID = "mwzb-yiwb"
URL = f"https://data.cityofnewyork.us/api/v3/views/{BUDGET_ID}/query.json"

query = (
    "SELECT fiscal_year, publication_date, COUNT(*) AS n_rows "
    "GROUP BY fiscal_year, publication_date "
    "ORDER BY fiscal_year, publication_date"
)

resp = requests.get(URL, params={"query": query}, timeout=60)
resp.raise_for_status()
df = pd.DataFrame(resp.json())
print(df.to_string(index=False))
df.to_csv("data/publication_date_check.csv", index=False)