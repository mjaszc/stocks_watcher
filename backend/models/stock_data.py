import uuid
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import (
    VARCHAR,
    DECIMAL,
    Date,
    DateTime,
    BigInteger,
    UniqueConstraint,
    Index,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from backend.models.base import Base


class StockData(Base):
    __tablename__ = "stock_data"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    symbol: Mapped[str] = mapped_column(VARCHAR(10), nullable=False)
    date: Mapped[datetime] = mapped_column(Date, nullable=False)
    open: Mapped[Decimal] = mapped_column(DECIMAL(12, 2), nullable=False)
    high: Mapped[Decimal] = mapped_column(DECIMAL(12, 2), nullable=False)
    low: Mapped[Decimal] = mapped_column(DECIMAL(12, 2), nullable=False)
    close: Mapped[Decimal] = mapped_column(DECIMAL(12, 2), nullable=False)
    volume: Mapped[int] = mapped_column(BigInteger, nullable=False)

    # Normalized prices for different time horizons,
    # it will be calculated after loading historical data
    norm_1m: Mapped[Decimal] = mapped_column(DECIMAL(12, 2), nullable=True)
    norm_3m: Mapped[Decimal] = mapped_column(DECIMAL(12, 2), nullable=True)
    norm_6m: Mapped[Decimal] = mapped_column(DECIMAL(12, 2), nullable=True)
    norm_1y: Mapped[Decimal] = mapped_column(DECIMAL(12, 2), nullable=True)
    norm_5y: Mapped[Decimal] = mapped_column(DECIMAL(12, 2), nullable=True)
    norm_20y: Mapped[Decimal] = mapped_column(DECIMAL(12, 2), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now(timezone.utc)
    )

    __table_args__ = (
        UniqueConstraint("symbol", "date", name="uq_symbol_date"),
        Index("idx_symbol_date", "symbol", "date"),
    )
