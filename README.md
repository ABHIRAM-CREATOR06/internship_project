<div align="center">

# BankPulse

BankPulse is a Flask-based loan approval prediction web app. It loads the CSV dataset, serves dataset stats, runs the saved ML model, and returns a human-readable decision explanation.

## Project Structure

```
bankpulse/
├── backend/
│   └── app.py                  # Flask app — routes, model inference, Mistral calls
├── frontend/
│   ├── index.html              # Application UI
│   ├── style.css
│   └── script.js
├── scripts/
│   └── smoke_test.py           # End-to-end route validation
├── loan_approval_predictor.ipynb   # Training notebook (EDA → preprocessing → model)
├── loan_approval_dataset.csv       # Source dataset
├── loan_approval_model.pkl         # Serialised trained model
├── scaler.pkl                      # Fitted MinMaxScaler
├── requirements.txt
├── .env.example
└── setup.md
```

---

## Quickstart

### 1. Clone & create a virtual environment

```bash
git clone https://github.com/ABHIRAM-CREATOR06/internship_project.git
cd internship_project

python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

### 2. Install dependencies

```bash
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

### 4. Run the app

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

Validates all four API routes in one shot:

```bash
python scripts/smoke_test.py
```

Expected output:

```
[OK] /health — 200
[OK] /stats  — 200
[OK] /predict — 200
[OK] /assistant — 200
All routes passing.
```

---

## Tech Stack

- **Backend:** Python, Flask
- **ML:** scikit-learn, pandas, NumPy, joblib
- **AI:** Mistral AI API (`mistral-small-latest`)
- **Frontend:** HTML, CSS, vanilla JavaScript
- **Notebook:** Jupyter

---

## License

[MIT](LICENSE) — free to use, modify, and distribute.

---

<div align="center">
Built during internship · 2026
</div>
