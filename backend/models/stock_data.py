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

from models.base import Base


class StockData(Base):
    __tablename__ = "stock_data"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    symbol: Mapped[str] = mapped_column(VARCHAR(10), nullable=False)
    date: Mapped[datetime] = mapped_column(Date, nullable=False)
    open: Mapped[Decimal] = mapped_column(DECIMAL(12, 5), nullable=False)
    high: Mapped[Decimal] = mapped_column(DECIMAL(12, 5), nullable=False)
    low: Mapped[Decimal] = mapped_column(DECIMAL(12, 5), nullable=False)
    close: Mapped[Decimal] = mapped_column(DECIMAL(12, 5), nullable=False)
    volume: Mapped[int] = mapped_column(BigInteger, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now(timezone.utc)
    )

    __table_args__ = (
        UniqueConstraint("symbol", "date", name="uq_symbol_date"),
        Index("idx_symbol_date", "symbol", "date"),
    )
