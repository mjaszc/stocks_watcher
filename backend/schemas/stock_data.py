from decimal import Decimal
from datetime import datetime

from pydantic import BaseModel, Field


class StockBase(BaseModel):
    symbol: str
    date: datetime
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: int
    created_at: datetime


class StockCreate(StockBase):
    pass
