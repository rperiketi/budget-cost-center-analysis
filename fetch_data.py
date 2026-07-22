"""
fetch_data.py
Pulls agency-level (and cost-center-level) budget vs actual data from
NYC Open Data using SoQL server-side aggregation, so we don't have to
download raw line-item data.

Output:
  data/budget_by_agency_year.csv        (agency + fiscal_year + total budget)
  data/budget_by_costcenter_year.csv    (agency + responsibility_center + fiscal_year + budget)
  data/actuals_by_agency_year.csv       (agency + fiscal_year + total actual)
"""

import requests
import pandas as pd
import os

APP_TOKEN = None  # optional: paste your Socrata app token here once you have one
OUTPUT_DIR = "data"
os.makedirs(OUTPUT_DIR, exist_ok=True)

BUDGET_ID = "mwzb-yiwb"
ACTUALS_ID = "nrik-v7ws"  # Expense Actuals By Funding Source (current, updated annually)


def run_soql(dataset_id: str, soql: str, page_size: int = 5000) -> pd.DataFrame:
    """Run a SoQL query against a Socrata v3 dataset, paginating until done."""
    url = f"https://data.cityofnewyork.us/api/v3/views/{dataset_id}/query.json"
    headers = {"X-App-Token": APP_TOKEN} if APP_TOKEN else {}

    all_rows = []
    offset = 0
    while True:
        paged_query = f"{soql} LIMIT {page_size} OFFSET {offset}"
        resp = requests.get(url, params={"query": paged_query}, headers=headers, timeout=60)
        resp.raise_for_status()
        rows = resp.json()
        if not rows:
            break
        all_rows.extend(rows)
        print(f"  fetched {len(all_rows)} rows so far...")
        if len(rows) < page_size:
            break
        offset += page_size

    return pd.DataFrame(all_rows)


def main():
    # 1. Budget aggregated by agency + fiscal year + publication_date
    #    (publication_date kept so we can filter to only the LATEST snapshot
    #    per fiscal year -- NYC publishes 3 snapshots/year: Preliminary,
    #    Executive, Adopted -- summing all 3 would triple-count the budget)
    print("Fetching budget by agency/year/publication date...")
    budget_agency_query = (
        "SELECT agency_name, fiscal_year, publication_date, "
        "SUM(current_modified_budget_amount) AS total_budget "
        "GROUP BY agency_name, fiscal_year, publication_date "
        "ORDER BY fiscal_year, agency_name"
    )
    budget_agency_raw = run_soql(BUDGET_ID, budget_agency_query)
    budget_agency_raw["publication_date"] = budget_agency_raw["publication_date"].astype(str)

    # Keep only the latest publication_date per fiscal_year
    latest_pub = (
        budget_agency_raw.groupby("fiscal_year")["publication_date"].max().reset_index()
        .rename(columns={"publication_date": "latest_pub_date"})
    )
    budget_agency = budget_agency_raw.merge(latest_pub, on="fiscal_year")
    budget_agency = budget_agency[budget_agency["publication_date"] == budget_agency["latest_pub_date"]]
    budget_agency = budget_agency.drop(columns=["publication_date", "latest_pub_date"])

    budget_agency.to_csv(f"{OUTPUT_DIR}/budget_by_agency_year.csv", index=False)
    print(f"  -> saved {len(budget_agency)} rows (deduplicated to latest publication per year)")

    # 2. Budget aggregated by agency + cost center (responsibility_center) + fiscal year
    #    Same publication_date dedup logic applies here.
    print("Fetching budget by cost center/year/publication date...")
    budget_cc_query = (
        "SELECT agency_name, responsibility_center_name, fiscal_year, publication_date, "
        "SUM(current_modified_budget_amount) AS total_budget "
        "GROUP BY agency_name, responsibility_center_name, fiscal_year, publication_date "
        "ORDER BY fiscal_year, agency_name"
    )
    budget_cc_raw = run_soql(BUDGET_ID, budget_cc_query)
    budget_cc_raw["publication_date"] = budget_cc_raw["publication_date"].astype(str)

    budget_cc = budget_cc_raw.merge(latest_pub, on="fiscal_year")
    budget_cc = budget_cc[budget_cc["publication_date"] == budget_cc["latest_pub_date"]]
    budget_cc = budget_cc.drop(columns=["publication_date", "latest_pub_date"])

    budget_cc.to_csv(f"{OUTPUT_DIR}/budget_by_costcenter_year.csv", index=False)
    print(f"  -> saved {len(budget_cc)} rows (deduplicated to latest publication per year)")

    # 3. Actuals aggregated by agency + fiscal year + funding source
    #    (kept at this grain so we can compute both "all funds" and
    #    "city funds only" totals in pandas afterward)
    print("Fetching actuals by agency/year/funding source...")
    actuals_query = (
        "SELECT agy_nm, fisc_yr, fnding, "
        "SUM(amt) AS amt "
        "GROUP BY agy_nm, fisc_yr, fnding "
        "ORDER BY fisc_yr, agy_nm"
    )
    actuals_raw = run_soql(ACTUALS_ID, actuals_query)
    actuals_raw.to_csv(f"{OUTPUT_DIR}/actuals_by_agency_year_funding_raw.csv", index=False)

    # Collapse to agency+year: all-funds total, and city-funds-only total
    actuals_raw["amt"] = pd.to_numeric(actuals_raw["amt"], errors="coerce")
    all_funds = (
        actuals_raw.groupby(["agy_nm", "fisc_yr"])["amt"]
        .sum()
        .reset_index()
        .rename(columns={"amt": "total_actual_all_funds"})
    )
    city_funds = (
        actuals_raw[actuals_raw["fnding"] == "C"]
        .groupby(["agy_nm", "fisc_yr"])["amt"]
        .sum()
        .reset_index()
        .rename(columns={"amt": "total_actual_city_funds"})
    )
    actuals = pd.merge(all_funds, city_funds, on=["agy_nm", "fisc_yr"], how="left")
    actuals.to_csv(f"{OUTPUT_DIR}/actuals_by_agency_year.csv", index=False)
    print(f"  -> saved {len(actuals)} rows")

    print("\nDone. Files saved in /data")


if __name__ == "__main__":
    main()