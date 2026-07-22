"""
preview_new_actuals.py
Quick check of the CURRENT actuals dataset (Expense Actuals By Funding Source,
nrik-v7ws) before we swap it into the main pipeline.
"""

import requests
import json

DATASET_ID = "nrik-v7ws"

def preview(limit: int = 5):
    url = f"https://data.cityofnewyork.us/api/v3/views/{DATASET_ID}/query.json"
    resp = requests.get(url, params={"query": f"SELECT * LIMIT {limit}"}, timeout=30)
    resp.raise_for_status()
    rows = resp.json()
    print("COLUMNS:", list(rows[0].keys()))
    print("\nSAMPLE ROW:")
    print(json.dumps(rows[0], indent=2))

    # also check the range of fiscal years available
    fy_url = url
    fy_query = "SELECT fiscal_year, COUNT(*) AS n GROUP BY fiscal_year ORDER BY fiscal_year"
    # NOTE: field might not be literally 'fiscal_year' -- if this errors,
    # check the COLUMNS output above and adjust the field name below.
    try:
        resp2 = requests.get(fy_url, params={"query": fy_query}, timeout=30)
        resp2.raise_for_status()
        print("\nFISCAL YEARS PRESENT:")
        for row in resp2.json():
            print(row)
    except Exception as e:
        print(f"\n(Could not auto-check fiscal year range: {e})")
        print("Check the COLUMNS list above for the correct year field name.")

if __name__ == "__main__":
    preview()