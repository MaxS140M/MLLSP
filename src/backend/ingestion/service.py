"""Services that persist market data returned by the ingestion client."""

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db.models import MarketObservation, Symbol
from .client import PriceBar, TwelveDataClient


def ingest_historical_prices(
    db: Session,
    client: TwelveDataClient,
    symbol: str,
    interval: str = "1day",
    outputsize: int = 30,
) -> int:
    """Fetch historical prices and insert or update their database records.

    Returns the number of observations written. Existing observations are
    updated so the operation can safely be run again for the same date range.
    """

    ticker = symbol.strip().upper()
    if not ticker:
        raise ValueError("symbol must not be empty")

    bars = client.get_time_series(ticker, interval=interval, outputsize=outputsize)
    symbol_record = db.scalar(select(Symbol).where(Symbol.ticker == ticker))
    if symbol_record is None:
        symbol_record = Symbol(ticker=ticker)
        db.add(symbol_record)
        db.flush()

    written = 0
    for bar in bars:
        timestamp = _database_timestamp(bar.timestamp)
        observation = db.scalar(
            select(MarketObservation).where(
                MarketObservation.symbol_id == symbol_record.id,
                MarketObservation.timestamp == timestamp,
            )
        )
        if observation is None:
            observation = MarketObservation(
                symbol_id=symbol_record.id,
                timestamp=timestamp,
            )
            db.add(observation)

        _update_observation(observation, bar)
        written += 1

    db.commit()
    return written


def _update_observation(observation: MarketObservation, bar: PriceBar) -> None:
    observation.open = bar.open
    observation.high = bar.high
    observation.low = bar.low
    observation.close = bar.close
    observation.volume = bar.volume


def _database_timestamp(value: datetime) -> datetime:
    """Store timestamps as UTC without timezone metadata for SQLite."""

    if value.tzinfo is None:
        return value
    return value.astimezone(timezone.utc).replace(tzinfo=None)