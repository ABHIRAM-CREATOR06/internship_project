python -m venv venv

Activation code in Windows

venv\Scripts\activate

Install:

pip install -r requirements.txt

Open Jupyter Notebook:

jupyter notebook
or 
py -m notebook

Run Flask Website:

1. Configure `.env`

Open `.env` and update:

MISTRAL_API_KEY=your_mistral_api_key
MODEL_PATH=loan_approval_model.pkl
SCALER_PATH=scaler.pkl
DATASET_PATH=loan_approval_dataset.csv

2. Start Flask

python backend/app.py

3. Open Website

http://127.0.0.1:5000

4. Test Backend Routes

Health:

http://127.0.0.1:5000/health

Stats:

http://127.0.0.1:5000/stats

5. Smoke Test

python scripts/smoke_test.py
