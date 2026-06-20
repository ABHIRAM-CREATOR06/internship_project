<div align="center">

# BankPulse

**A Flask-based loan approval prediction web app** — loads the dataset, serves live stats, runs a trained ML model, and returns a human-readable decision explanation powered by Mistral AI.

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-Backend-000000?style=for-the-badge&logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
[![scikit-learn](https://img.shields.io/badge/scikit--learn-ML-F7931E?style=for-the-badge&logo=scikitlearn&logoColor=white)](https://scikit-learn.org/)
[![Mistral AI](https://img.shields.io/badge/Mistral_AI-Explanations-FA520F?style=for-the-badge&logo=mistralai&logoColor=white)](https://mistral.ai/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge)](LICENSE)

[![Last Commit](https://img.shields.io/github/last-commit/ABHIRAM-CREATOR06/internship_project?style=flat-square&color=7aa2f7)](https://github.com/ABHIRAM-CREATOR06/internship_project/commits)
[![Repo Size](https://img.shields.io/github/repo-size/ABHIRAM-CREATOR06/internship_project?style=flat-square&color=bb9af7)](https://github.com/ABHIRAM-CREATOR06/internship_project)
[![Issues](https://img.shields.io/github/issues/ABHIRAM-CREATOR06/internship_project?style=flat-square&color=f7768e)](https://github.com/ABHIRAM-CREATOR06/internship_project/issues)
[![Stars](https://img.shields.io/github/stars/ABHIRAM-CREATOR06/internship_project?style=flat-square&color=e0af68)](https://github.com/ABHIRAM-CREATOR06/internship_project/stargazers)

</div>

---

## Table of Contents

- [BankPulse](#bankpulse)
  - [Table of Contents](#table-of-contents)
  - [Project Structure](#project-structure)
  - [Quickstart](#quickstart)
    - [1. Clone \& create a virtual environment](#1-clone--create-a-virtual-environment)
    - [2. Install dependencies](#2-install-dependencies)
    - [3. Configure the Mistral API](#3-configure-the-mistral-api)
    - [4. Run the app](#4-run-the-app)
  - [API Routes](#api-routes)
  - [Smoke Test](#smoke-test)
  - [Tech Stack](#tech-stack)
  - [License](#license)

---

## Project Structure

````text
bankpulse/
├── backend/
│   └── app.py                      # Flask app — routes, model inference, Mistral calls
├── frontend/
│   ├── index.html                  # Application UI
│   ├── style.css
│   └── script.js
├── scripts/
│   └── smoke_test.py               # End-to-end route validation
├── loan_approval_predictor.ipynb   # Training notebook (EDA → preprocessing → model)
├── loan_approval_dataset.csv       # Source dataset
├── loan_approval_model.pkl         # Serialised trained model
├── scaler.pkl                      # Fitted MinMaxScaler
├── requirements.txt
├── .env.example
└── setup.md
````

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

### 3. Configure the Mistral API

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

---

## API Routes

| Method | Route        | Description                                   |
|:------:|:-------------|:-----------------------------------------------|
| `GET`  | `/health`    | Liveness check                                 |
| `GET`  | `/stats`     | Dataset statistics                             |
| `POST` | `/predict`   | Runs the model, returns the approval decision  |
| `POST` | `/assistant` | Returns a Mistral-generated explanation        |

---

## Smoke Test

Validates all four API routes in one shot:

```bash
python scripts/smoke_test.py
```

Expected output:

```text
[OK] /health    — 200
[OK] /stats     — 200
[OK] /predict   — 200
[OK] /assistant — 200
All routes passing.
```

---

## Tech Stack

<div align="center">

![Python](https://img.shields.io/badge/Python-3776AB?style=flat-square&logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-000000?style=flat-square&logo=flask&logoColor=white)
![scikit-learn](https://img.shields.io/badge/scikit--learn-F7931E?style=flat-square&logo=scikitlearn&logoColor=white)
![pandas](https://img.shields.io/badge/pandas-150458?style=flat-square&logo=pandas&logoColor=white)
![NumPy](https://img.shields.io/badge/NumPy-013243?style=flat-square&logo=numpy&logoColor=white)
![Mistral AI](https://img.shields.io/badge/Mistral_AI-FA520F?style=flat-square&logo=mistralai&logoColor=white)
![HTML5](https://img.shields.io/badge/HTML5-E34F26?style=flat-square&logo=html5&logoColor=white)
![CSS3](https://img.shields.io/badge/CSS3-1572B6?style=flat-square&logo=css3&logoColor=white)
![JavaScript](https://img.shields.io/badge/JavaScript-F7DF1E?style=flat-square&logo=javascript&logoColor=black)
![Jupyter](https://img.shields.io/badge/Jupyter-F37626?style=flat-square&logo=jupyter&logoColor=white)

</div>

| Layer        | Tools                                      |
|:-------------|:--------------------------------------------|
| **Backend**  | Python, Flask                               |
| **ML**       | scikit-learn, pandas, NumPy, joblib         |
| **AI**       | Mistral AI API (`mistral-small-latest`)     |
| **Frontend** | HTML, CSS, vanilla JavaScript               |
| **Notebook** | Jupyter                                     |

---

## License

[MIT](LICENSE) — free to use, modify, and distribute.

---

<div align="center">

Built during internship · 2026

</div>