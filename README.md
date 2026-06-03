# BankPulse

BankPulse is a Flask-based loan approval prediction web app. It loads the CSV dataset, serves dataset stats, runs the saved ML model, and returns a human-readable decision explanation.

## Project Structure

```text
backend/
  app.py
frontend/
  index.html
  style.css
  script.js
scripts/
  smoke_test.py
loan_approval_dataset.csv
loan_approval_model.pkl
scaler.pkl
requirements.txt
```

## Setup

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

## Mistral API

Edit the local `.env` file before starting Flask:

```text
MISTRAL_API_KEY=your_mistral_key
MISTRAL_MODEL=mistral-small-latest
MODEL_PATH=loan_approval_model.pkl
SCALER_PATH=scaler.pkl
```

The frontend only calls Flask routes such as `/predict` and `/assistant`. The Mistral key is read by `backend/app.py` on the server and is never sent to the browser. `MISTRAL_MAX_TOKENS`, `MISTRAL_TEMPERATURE`, and `MISTRAL_TIMEOUT_SECONDS` keep generated explanations short and lower-cost.

## Run

```bash
python backend/app.py
```

Open:

```text
http://127.0.0.1:5000
```

## API Routes

```text
GET  /health
GET  /stats
POST /predict
POST /assistant
```

## Smoke Test

```bash
python scripts/smoke_test.py
```
