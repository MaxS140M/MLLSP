# Setup Guide

## Prerequisites

- Python 3.11+
- A free [Twelve Data](https://twelvedata.com) API key (800 requests/day on the free tier)

---

## 1. Clone and create a virtual environment

```powershell
cd C:\Users\maxsl\Desktop\MLLSP
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

---

## 2. Install dependencies

```powershell
cd src\backend
pip install -r requirements.txt
```

Key packages installed:

| Package | Purpose |
|---------|---------|
| `fastapi` / `uvicorn` | REST API server |
| `SQLAlchemy` | SQLite ORM |
| `pandas` / `numpy` / `scikit-learn` | Feature engineering and model training |
| `papermill` | Execute the Jupyter notebook with a custom symbol parameter |
| `nbconvert` + `mistune<3` | Convert the executed notebook to HTML for the dashboard |
| `matplotlib>=3.9` | Plots rendered inside the notebook (non-interactive Agg backend) |
| `python-dotenv` | Load API keys from `.env` |

---

## 3. Configure environment variables

```powershell
Copy-Item .env.example .env
```

Open `src\backend\.env` and set your Twelve Data API key:

```
TWELVE_DATA_API_KEY=your_key_here
DATABASE_URL=sqlite:///./mllsp.db
API_HOST=127.0.0.1
API_PORT=8000
```

The `.env` file is git-ignored 

---

## 4. Ingest historical data and train models

Run this once from the **project root** to populate the database and train the prediction models for AAPL and MSFT:

```powershell
cd C:\Users\maxsl\Desktop\MLLSP
python src/backend/setup_data.py
```

To add more symbols, edit `SYMBOLS` at the top of `src/backend/setup_data.py`.

---

## 5. Start the backend API

Run from the **project root** (not from `src\backend`):

```powershell
cd C:\Users\maxsl\Desktop\MLLSP
.\.venv\Scripts\Activate.ps1
python -m uvicorn src.backend.api.main:app --reload
```

The API will be available at `http://127.0.0.1:8000`.  
Interactive docs: `http://127.0.0.1:8000/docs`

---

## 6. Start the frontend

In a second terminal:

```powershell
cd C:\Users\maxsl\Desktop\MLLSP\src\Frontend
python -m http.server 8080
```

Open `http://localhost:8080/index.html` in a browser.

---

## 7. Using the dashboard

| Action | What happens |
|--------|-------------|
| **Refresh data** | Fetches a live quote, runs the prediction model, and updates the price history chart |
| **Run Analysis** | Executes the Jupyter notebook (`docs/notebooks/MLLSP.ipynb`) with the selected symbol injected as a parameter, then renders the full notebook output inline |

The first **Run Analysis** call takes 30–60 seconds while papermill executes the notebook. A live second counter shows progress.

---

## API endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | Server liveness check |
| `GET` | `/quote/{symbol}` | Fetch and persist a live quote |
| `GET` | `/predict/{symbol}` | Next-close prediction from the saved model |
| `GET` | `/history/{symbol}` | Stored closing prices for the chart |
| `GET` | `/analyze/{symbol}` | Execute the notebook and return HTML output |

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `ImportError: attempted relative import beyond top-level package` | Run uvicorn from the project root, not from `src\backend` |
| `TWELVE_DATA_API_KEY must be configured` | Add your key to `src\backend\.env` |
| `No trained model found for {symbol}` | Run `setup_data.py` first |
| `No data found for {symbol}` | Run `setup_data.py` first |
| Analysis button stays disabled | Reload the page; a previous execution may still be running |
| `MathBlockParser` / mistune error | Ensure `mistune>=2.0.3,<3.0` is installed: `pip install "mistune>=2.0.3,<3.0"` then restart the server |
| matplotlib `backend2gui` ImportError | Ensure `matplotlib>=3.9` is installed: `pip install "matplotlib>=3.9"` |
