"""FastAPI routes for quotes and saved model predictions."""

import json
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import Annotated

import joblib
from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db import get_db
from ..db.models import MarketObservation, Symbol
from ..features import FEATURE_COLUMNS, build_feature_frame
from ..ingestion import TwelveDataClient, TwelveDataError, ingest_live_quote

MODEL_DIR = Path(__file__).resolve().parents[1] / "training" / "models"

app = FastAPI(title="MLLSP Prediction API", version="0.4.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["GET"],
    allow_headers=["*"],
)

DatabaseSession = Annotated[Session, Depends(get_db)]


class HealthResponse(BaseModel):
    status: str


class QuoteResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    symbol: str
    company: str | None
    price: Decimal
    timestamp: datetime | None


class PredictionResponse(BaseModel):
    symbol: str
    company: str | None
    current_price: Decimal
    predicted_price: float
    model: str
    horizon: int
    as_of: datetime


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    """Confirm that the API process is running."""

    return HealthResponse(status="ok")


@app.get("/quote/{symbol}", response_model=QuoteResponse)
def quote(symbol: str, db: DatabaseSession) -> QuoteResponse:
    """Fetch and persist the latest live quote for a symbol."""

    ticker = _normalize_symbol(symbol)
    try:
        live_quote = ingest_live_quote(db, TwelveDataClient(), ticker)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except TwelveDataError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    symbol_record = db.scalar(select(Symbol).where(Symbol.ticker == ticker))
    return QuoteResponse(
        symbol=live_quote.symbol,
        company=symbol_record.name if symbol_record else live_quote.name,
        price=live_quote.price,
        timestamp=live_quote.timestamp,
    )


@app.get("/predict/{symbol}", response_model=PredictionResponse)
def predict(symbol: str, db: DatabaseSession) -> PredictionResponse:
    """Predict the next closing price using the saved model for a symbol."""

    ticker = _normalize_symbol(symbol)
    symbol_record = db.scalar(select(Symbol).where(Symbol.ticker == ticker))
    if symbol_record is None:
        raise HTTPException(status_code=404, detail=f"No data found for {ticker}")

    metadata = _load_metadata(ticker)
    observations = db.scalars(
        select(MarketObservation)
        .where(MarketObservation.symbol_id == symbol_record.id)
        .order_by(MarketObservation.timestamp)
    ).all()
    try:
        feature_frame = build_feature_frame(observations, include_target=False)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    if feature_frame.empty:
        raise HTTPException(
            status_code=422,
            detail=f"Not enough observations to predict {ticker}",
        )

    model = _load_model(metadata)
    features = feature_frame[metadata.get("feature_columns", FEATURE_COLUMNS)].tail(1)
    predicted_price = float(model.predict(features)[0])
    latest = observations[-1]
    return PredictionResponse(
        symbol=ticker,
        company=symbol_record.name,
        current_price=latest.close,
        predicted_price=predicted_price,
        model=str(metadata["best_model"]),
        horizon=int(metadata.get("horizon", 1)),
        as_of=latest.timestamp,
    )


def _normalize_symbol(symbol: str) -> str:
    ticker = symbol.strip().upper()
    if not ticker:
        raise HTTPException(status_code=400, detail="symbol must not be empty")
    return ticker


def _load_metadata(ticker: str) -> dict[str, object]:
    metadata_path = MODEL_DIR / f"{ticker}_metadata.json"
    if not metadata_path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"No trained model found for {ticker}",
        )
    try:
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise HTTPException(status_code=500, detail="Model metadata is invalid") from exc
    if not isinstance(metadata, dict) or "best_model" not in metadata:
        raise HTTPException(status_code=500, detail="Model metadata is incomplete")
    return metadata


def _load_model(metadata: dict[str, object]) -> object:
    model_file = metadata.get("model_file")
    if not isinstance(model_file, str):
        raise HTTPException(status_code=500, detail="Model filename is missing")
    model_path = MODEL_DIR / model_file
    if not model_path.exists():
        raise HTTPException(status_code=404, detail="Saved model file is missing")
    try:
        return joblib.load(model_path)
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Saved model could not be loaded") from exc