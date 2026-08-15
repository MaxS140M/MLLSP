"""SQLAlchemy models for symbols and market observations."""

from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


class Symbol(Base):
    """A supported stock symbol."""

    # Store one row for each supported company.
    __tablename__ = "symbols"

    id: Mapped[int] = mapped_column(primary_key=True)
    ticker: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    name: Mapped[str | None] = mapped_column(String(150), nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    observations: Mapped[list["MarketObservation"]] = relationship(
        back_populates="symbol", cascade="all, delete-orphan"
    )


class MarketObservation(Base):
    """OHLCV data point associated with a symbol."""

    # Store timestamped OHLCV market records.
    __tablename__ = "market_observations"
    __table_args__ = (
        UniqueConstraint("symbol_id", "timestamp", name="uq_observation_symbol_time"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    symbol_id: Mapped[int] = mapped_column(ForeignKey("symbols.id"), index=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, index=True)
    open: Mapped[Decimal] = mapped_column(Numeric(18, 6))
    high: Mapped[Decimal] = mapped_column(Numeric(18, 6))
    low: Mapped[Decimal] = mapped_column(Numeric(18, 6))
    close: Mapped[Decimal] = mapped_column(Numeric(18, 6))
    volume: Mapped[Decimal | None] = mapped_column(Numeric(24, 6), nullable=True)

    symbol: Mapped[Symbol] = relationship(back_populates="observations")