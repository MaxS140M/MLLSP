"""Services that persist market data returned by the ingestion client."""

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db.models import MarketObservation, Symbol
from .client import PriceBar, Quote, TwelveDataClient


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

    # Fetch the source data before opening the write path.
    bars = client.get_time_series(ticker, interval=interval, outputsize=outputsize)
    symbol_record = db.scalar(select(Symbol).where(Symbol.ticker == ticker))
    if symbol_record is None:
        symbol_record = Symbol(ticker=ticker)
        db.add(symbol_record)
        db.flush()

    # Upsert each bar so repeated imports stay safe.
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


def ingest_live_quote(
    db: Session,
    client: TwelveDataClient,
    symbol: str,
) -> Quote:
    """Fetch a live quote and save it as the latest market observation."""

    ticker = symbol.strip().upper()
    if not ticker:
        raise ValueError("symbol must not be empty")

    # Fetch the latest quote and attach its company name.
    quote = client.get_quote(ticker)
    timestamp = _database_timestamp(quote.timestamp or datetime.now(timezone.utc))
    symbol_record = db.scalar(select(Symbol).where(Symbol.ticker == ticker))
    if symbol_record is None:
        symbol_record = Symbol(ticker=ticker)
        db.add(symbol_record)
        db.flush()
    if quote.name:
        symbol_record.name = quote.name

    # Store the quote as a point-in-time price observation.
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

    observation.open = quote.price
    observation.high = quote.price
    observation.low = quote.price
    observation.close = quote.price
    observation.volume = None
    db.commit()
    return quote


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