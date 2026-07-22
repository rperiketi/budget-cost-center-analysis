
import requests
import json

APP_TOKEN = None 
DATASETS = {
    "expense_budget": "mwzb-yiwb",
    "expense_actuals": "7yay-m4ae",
}

def preview(name: str, dataset_id: str, limit: int = 5):
    url = f"https://data.cityofnewyork.us/api/v3/views/{dataset_id}/query.json"
    params = {
        "query": f"SELECT * LIMIT {limit}",
    }
    headers = {}
    if APP_TOKEN:
        headers["X-App-Token"] = APP_TOKEN

    resp = requests.get(url, params=params, headers=headers, timeout=30)
    resp.raise_for_status()
    rows = resp.json()

    print(f"\n{'='*60}")
    print(f"{name}  ({dataset_id})")
    print(f"{'='*60}")
    if not rows:
        print("No rows returned.")
        return
    print("COLUMNS:", list(rows[0].keys()))
    print("\nSAMPLE ROW:")
    print(json.dumps(rows[0], indent=2))


if __name__ == "__main__":
    for name, dataset_id in DATASETS.items():
        preview(name, dataset_id)