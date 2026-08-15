"""Ingest historical prices and train models for one or more symbols."""

import sys
from pathlib import Path

# Allow running directly from src/backend or the project root.
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from src.backend.db import SessionLocal, init_db
from src.backend.ingestion.client import TwelveDataClient
from src.backend.ingestion.service import ingest_historical_prices
from src.backend.training.train import train_symbol

SYMBOLS = ["AAPL", "MSFT", "GOOGL", "NVDA"]
HISTORY_DAYS = 200  # bars of daily history to fetch


def main() -> None:
    print("Initialising database...")
    init_db()
    client = TwelveDataClient()
    db = SessionLocal()
    try:
        for symbol in SYMBOLS:
            print(f"\n--- {symbol} ---")
            print(f"  Fetching {HISTORY_DAYS} days of history...")
            written = ingest_historical_prices(db, client, symbol, outputsize=HISTORY_DAYS)
            print(f"  Saved {written} observations.")

            print("  Training models...")
            result = train_symbol(db, symbol)
            print(f"  Best model: {result.best_model}")
            print(f"  Trained on {result.sample_count} samples.")
    finally:
        db.close()
    print("\nDone. Restart the API server then refresh the dashboard.")


if __name__ == "__main__":
    main()
