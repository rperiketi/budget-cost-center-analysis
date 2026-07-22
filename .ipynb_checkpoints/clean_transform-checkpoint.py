"""
clean_transform.py
Cleans and joins budget vs. actuals data at the agency+fiscal_year grain.

Handles:
  - Column name differences between the two source datasets
  - Agency name normalization (casing/spacing) so the join actually matches
  - Type conversion (fiscal_year as int, amounts as numeric)
  - Reports any agencies that DON'T match between budget and actuals,
    so you can manually inspect/fix them rather than silently dropping data

Output:
  data/budget_vs_actual.csv       (clean, joined, ready for SQL/Tableau)
  data/unmatched_agencies.csv     (diagnostic: agencies in one file but not the other)
"""

import pandas as pd
import re
import os

DATA_DIR = "data"


def normalize_agency(name: str) -> str:
    """Uppercase, strip punctuation/extra spaces so names compare cleanly."""
    if pd.isna(name):
        return ""
    name = str(name).upper().strip()
    name = re.sub(r"[^A-Z0-9 ]", "", name)   # drop punctuation
    name = re.sub(r"\s+", " ", name)          # collapse multiple spaces
    return name


def main():
    budget = pd.read_csv(f"{DATA_DIR}/budget_by_agency_year.csv")
    actuals = pd.read_csv(f"{DATA_DIR}/actuals_by_agency_year.csv")

    # --- Standardize column names ---
    budget = budget.rename(columns={
        "agency_name": "agency_raw",
        "fiscal_year": "fiscal_year",
        "total_budget": "budget_amount",
    })
    actuals = actuals.rename(columns={
        "agy_nm": "agency_raw",
        "fisc_yr": "fiscal_year",
        "total_actual_all_funds": "actual_amount",
    })

    # --- Types ---
    budget["fiscal_year"] = pd.to_numeric(budget["fiscal_year"], errors="coerce").astype("Int64")
    actuals["fiscal_year"] = pd.to_numeric(actuals["fiscal_year"], errors="coerce").astype("Int64")
    budget["budget_amount"] = pd.to_numeric(budget["budget_amount"], errors="coerce")

    # IMPORTANT UNIT FIX:
    # NYC's "Expense Actuals By Funding Source" dataset reports dollars IN THOUSANDS,
    # while the Expense Budget dataset reports whole dollars. Without this conversion,
    # every variance comes out as a fake ~-99.9% (actual looking ~1000x smaller than budget).
    actuals["actual_amount"] = pd.to_numeric(actuals["actual_amount"], errors="coerce") * 1000

    # --- Normalized join key ---
    budget["agency_key"] = budget["agency_raw"].apply(normalize_agency)
    actuals["agency_key"] = actuals["agency_raw"].apply(normalize_agency)

    # --- Diagnostic: which agencies don't match at all (any year) ---
    budget_agencies = set(budget["agency_key"].unique())
    actuals_agencies = set(actuals["agency_key"].unique())

    only_in_budget = budget_agencies - actuals_agencies
    only_in_actuals = actuals_agencies - budget_agencies

    unmatched = pd.DataFrame({
        "agency_key": list(only_in_budget) + list(only_in_actuals),
        "found_in": (["budget_only"] * len(only_in_budget)) + (["actuals_only"] * len(only_in_actuals)),
    })
    unmatched.to_csv(f"{DATA_DIR}/unmatched_agencies.csv", index=False)

    print(f"Agencies only in budget data: {len(only_in_budget)}")
    print(f"Agencies only in actuals data: {len(only_in_actuals)}")
    print(f"-> full list saved to data/unmatched_agencies.csv (review this)")

    # --- Join on agency_key + fiscal_year ---
    merged = pd.merge(
        budget[["agency_key", "agency_raw", "fiscal_year", "budget_amount"]],
        actuals[["agency_key", "fiscal_year", "actual_amount"]],
        on=["agency_key", "fiscal_year"],
        how="inner",  # only keep rows where both budget AND actual exist
    )

    # --- Variance calculations ---
    merged["variance_amount"] = merged["actual_amount"] - merged["budget_amount"]
    merged["variance_pct"] = (merged["variance_amount"] / merged["budget_amount"]) * 100

    # Rename agency_raw -> agency_name for clarity downstream, keep the budget-side spelling
    merged = merged.rename(columns={"agency_raw": "agency_name"})
    merged = merged.drop(columns=["agency_key"])

    merged.to_csv(f"{DATA_DIR}/budget_vs_actual.csv", index=False)
    print(f"\nJoined dataset: {len(merged)} rows -> data/budget_vs_actual.csv")
    print(f"Fiscal years covered: {sorted(merged['fiscal_year'].dropna().unique().tolist())}")


if __name__ == "__main__":
    main()