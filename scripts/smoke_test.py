import sys
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from backend.app import app


client = app.test_client()

print("health", client.get("/health").status_code, client.get("/health").json)
print("stats", client.get("/stats").status_code, client.get("/stats").json)

payload = {
    "education": "Graduate",
    "self_employed": "No",
    "income_annum": 900000,
    "loan_amount": 3000000,
    "loan_term": 12,
    "cibil_score": 780,
    "residential_assets_value": 1000000,
    "commercial_assets_value": 500000,
    "luxury_assets_value": 300000,
    "bank_asset_value": 600000,
}

response = client.post("/predict", json=payload)
print("predict", response.status_code, response.json)
