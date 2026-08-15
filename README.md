# MLLSP
Machine Learning Live Stocks Prediction

## Backend setup

1. Create and activate a virtual environment from the repository root:

	```bash
	python -m venv .venv
	.venv\Scripts\activate
	```

2. Install the backend dependencies:

	```bash
	pip install -r src/backend/requirements.txt
	```

3. Copy `src/backend/.env.example` to `src/backend/.env` and set `TWELVE_DATA_API_KEY` to your Twelve Data API key. The default database is SQLite at `mllsp.db`; change `DATABASE_URL` if needed. The ingestion client validates quote and time-series responses and raises clear errors for provider failures or malformed data.

4. Initialize the database tables:

	```bash
	python -c "from src.backend.db import init_db; init_db()"
	```

5. Import 30 days of daily prices for a symbol:

	```bash
	python -c "from src.backend.db import SessionLocal, init_db; from src.backend.ingestion import TwelveDataClient, ingest_historical_prices; init_db(); db=SessionLocal(); print('Records written:', ingest_historical_prices(db, TwelveDataClient(), 'AAPL')); db.close()"
	```

The `.env` file and local database are ignored by Git. Never commit API keys or generated model files.
