"""Validated client for the Twelve Data REST API."""

import os
import time
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

import requests
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[1] / ".env")


class TwelveDataError(RuntimeError):
    """Base exception for Twelve Data client failures."""


class TwelveDataRequestError(TwelveDataError):
    """Raised when a request cannot be completed successfully."""


class TwelveDataRateLimitError(TwelveDataRequestError):
    """Raised when the Twelve Data request limit is exhausted."""


class TwelveDataResponseError(TwelveDataError):
    """Raised when Twelve Data returns an invalid or incomplete response."""


@dataclass(frozen=True)
class Quote:
    """A validated current quote."""

    symbol: str
    price: Decimal
    timestamp: datetime | None


@dataclass(frozen=True)
class PriceBar:
    """A validated OHLCV time-series observation."""

    timestamp: datetime
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: Decimal | None


class TwelveDataClient:
    """Fetch and validate market data from Twelve Data."""

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        timeout: float = 10.0,
        session: requests.Session | None = None,
        max_retries: int = 2,
        backoff_factor: float = 1.0,
    ) -> None:
        self.api_key = api_key or os.getenv("TWELVE_DATA_API_KEY")
        if not self.api_key or self.api_key == "your_twelve_data_api_key":
            raise ValueError("TWELVE_DATA_API_KEY must be configured")

        self.base_url = (base_url or "https://api.twelvedata.com").rstrip("/")
        self.timeout = timeout
        self.session = session or requests.Session()
        if max_retries < 0:
            raise ValueError("max_retries must not be negative")
        if backoff_factor < 0:
            raise ValueError("backoff_factor must not be negative")
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor

    def get_quote(self, symbol: str) -> Quote:
        """Fetch and validate the latest quote for a symbol."""

        payload = self._request("/quote", {"symbol": self._validate_symbol(symbol)})
        self._raise_for_provider_error(payload)

        price = self._decimal(payload, "close", "price")
        timestamp = self._parse_timestamp(payload.get("timestamp"))
        return Quote(
            symbol=self._required_text(payload, "symbol"),
            price=price,
            timestamp=timestamp,
        )

    def get_time_series(
        self, symbol: str, interval: str = "1day", outputsize: int = 30
    ) -> list[PriceBar]:
        """Fetch and validate OHLCV observations for a symbol."""

        if outputsize < 1 or outputsize > 5000:
            raise ValueError("outputsize must be between 1 and 5000")

        payload = self._request(
            "/time_series",
            {
                "symbol": self._validate_symbol(symbol),
                "interval": interval,
                "outputsize": outputsize,
            },
        )
        self._raise_for_provider_error(payload)

        values = payload.get("values")
        if not isinstance(values, list) or not values:
            raise TwelveDataResponseError("Twelve Data response has no values")

        bars = [self._parse_bar(value) for value in values]
        return sorted(bars, key=lambda bar: bar.timestamp)

    def _request(self, path: str, params: dict[str, Any]) -> dict[str, Any]:
        params["apikey"] = self.api_key
        for attempt in range(self.max_retries + 1):
            try:
                response = self.session.get(
                    f"{self.base_url}{path}", params=params, timeout=self.timeout
                )
                if response.status_code == 429:
                    if attempt < self.max_retries:
                        self._sleep_before_retry(response, attempt)
                        continue
                    raise TwelveDataRateLimitError(
                        "Twelve Data rate limit reached after retries"
                    )

                response.raise_for_status()
                payload = response.json()
            except TwelveDataRateLimitError:
                raise
            except requests.Timeout as exc:
                raise TwelveDataRequestError(
                    f"Twelve Data request timed out after {self.timeout} seconds"
                ) from exc
            except requests.RequestException as exc:
                raise TwelveDataRequestError(f"Twelve Data request failed: {exc}") from exc
            except ValueError as exc:
                raise TwelveDataResponseError("Twelve Data returned invalid JSON") from exc

            if not isinstance(payload, dict):
                raise TwelveDataResponseError("Twelve Data response must be a JSON object")
            if self._is_rate_limited(payload):
                if attempt < self.max_retries:
                    self._sleep_before_retry(response, attempt)
                    continue
                raise TwelveDataRateLimitError(
                    str(payload.get("message", "Twelve Data rate limit reached"))
                )
            return payload

        raise TwelveDataRateLimitError("Twelve Data rate limit reached")

    def _sleep_before_retry(self, response: requests.Response, attempt: int) -> None:
        retry_after = response.headers.get("Retry-After")
        try:
            delay = float(retry_after) if retry_after is not None else None
        except ValueError:
            delay = None
        if delay is None:
            delay = self.backoff_factor * (2**attempt)
        time.sleep(max(0.0, delay))

    @staticmethod
    def _is_rate_limited(payload: dict[str, Any]) -> bool:
        return payload.get("code") == 429 or payload.get("status") == "429"

    @staticmethod
    def _raise_for_provider_error(payload: dict[str, Any]) -> None:
        if TwelveDataClient._is_rate_limited(payload):
            raise TwelveDataRateLimitError(
                str(payload.get("message", "Twelve Data rate limit reached"))
            )
        if payload.get("status") == "error" or payload.get("code") == 401:
            message = payload.get("message", "Unknown Twelve Data error")
            raise TwelveDataResponseError(str(message))

    @staticmethod
    def _validate_symbol(symbol: str) -> str:
        normalized = symbol.strip().upper()
        if not normalized:
            raise ValueError("symbol must not be empty")
        return normalized

    @staticmethod
    def _required_text(payload: dict[str, Any], key: str) -> str:
        value = payload.get(key)
        if not isinstance(value, str) or not value.strip():
            raise TwelveDataResponseError(f"Twelve Data response is missing {key}")
        return value.strip().upper()

    @staticmethod
    def _decimal(payload: dict[str, Any], *keys: str) -> Decimal:
        for key in keys:
            value = payload.get(key)
            if value is not None:
                try:
                    return Decimal(str(value))
                except (InvalidOperation, ValueError) as exc:
                    raise TwelveDataResponseError(f"Invalid numeric field: {key}") from exc
        raise TwelveDataResponseError(f"Twelve Data response is missing {keys[0]}")

    @classmethod
    def _parse_bar(cls, value: Any) -> PriceBar:
        if not isinstance(value, dict):
            raise TwelveDataResponseError("Twelve Data observation must be an object")

        timestamp = cls._parse_timestamp(value.get("datetime"))
        if timestamp is None:
            raise TwelveDataResponseError("Twelve Data observation has no datetime")

        volume = value.get("volume")
        return PriceBar(
            timestamp=timestamp,
            open=cls._decimal(value, "open"),
            high=cls._decimal(value, "high"),
            low=cls._decimal(value, "low"),
            close=cls._decimal(value, "close"),
            volume=Decimal(str(volume)) if volume is not None else None,
        )

    @staticmethod
    def _parse_timestamp(value: Any) -> datetime | None:
        if value is None:
            return None
        try:
            if isinstance(value, (int, float)) or str(value).isdigit():
                return datetime.fromtimestamp(float(value))
            return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        except ValueError as exc:
            raise TwelveDataResponseError("Invalid timestamp in Twelve Data response") from exc