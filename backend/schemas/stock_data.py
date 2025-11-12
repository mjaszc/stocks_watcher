from decimal import Decimal
from datetime import datetime
from typing import Optional

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


class StockResponse(StockBase):
    symbol: str
    date: datetime
    close: Decimal
    norm_1m: Optional[Decimal] = None
    norm_3m: Optional[Decimal] = None
    norm_6m: Optional[Decimal] = None
    norm_1y: Optional[Decimal] = None
    norm_5y: Optional[Decimal] = None
    norm_20y: Optional[Decimal] = None
