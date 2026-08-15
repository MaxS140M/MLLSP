# Setup Guide

## Requirements

- Python 3.12 or newer
- A Twelve Data API key

## Install

From the repository root, create and activate a virtual environment:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Install the backend dependencies:

```powershell
python -m pip install -r src/backend/requirements.txt
```

## Configure the environment

Copy the example environment file:

```powershell
Copy-Item src/backend/.env.example src/backend/.env
```

Set `TWELVE_DATA_API_KEY` in `src/backend/.env`. The default database is SQLite at `mllsp.db`; set `DATABASE_URL` if a different database is needed.

The ingestion client validates quote and time-series responses and reports provider or malformed-data errors clearly.

## Initialize the database

```powershell
python -c "from src.backend.db import init_db; init_db()"
```

## Import historical prices

The following command imports 30 days of daily prices for AAPL:

```powershell
python -c "from src.backend.db import SessionLocal, init_db; from src.backend.ingestion import TwelveDataClient, ingest_historical_prices; init_db(); db=SessionLocal(); print('Records written:', ingest_historical_prices(db, TwelveDataClient(), 'AAPL')); db.close()"
```

## Fetch a live quote

```powershell
python -c "from src.backend.db import SessionLocal, init_db; from src.backend.ingestion import TwelveDataClient, ingest_live_quote; init_db(); db=SessionLocal(); print('Live quote:', ingest_live_quote(db, TwelveDataClient(), 'AAPL')); db.close()"
```

The local `.env` file, database, and generated model files are ignored by Git. Never commit API keys.
