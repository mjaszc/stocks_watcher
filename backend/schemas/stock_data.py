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


class StockResponse(BaseModel):
    symbol: str
    date: datetime
    close: Decimal
    norm_1m: Optional[Decimal] = None
    norm_3m: Optional[Decimal] = None
    norm_6m: Optional[Decimal] = None
    norm_1y: Optional[Decimal] = None
    norm_5y: Optional[Decimal] = None
    norm_20y: Optional[Decimal] = None


class Stock1MResponse(BaseModel):
    symbol: str
    date: datetime
    norm_1m: Optional[Decimal] = None


class Stock3MResponse(BaseModel):
    symbol: str
    date: datetime
    norm_3m: Optional[Decimal] = None


class Stock6MResponse(BaseModel):
    symbol: str
    date: datetime
    norm_6m: Optional[Decimal] = None


class Stock1YResponse(BaseModel):
    symbol: str
    date: datetime
    norm_1y: Optional[Decimal] = None


class Stock5YResponse(BaseModel):
    symbol: str
    date: datetime
    norm_5y: Optional[Decimal] = None


class Stock20YResponse(BaseModel):
    symbol: str
    date: datetime
    norm_20y: Optional[Decimal] = None
