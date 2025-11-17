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
    norm_1mo: Optional[Decimal] = None
    norm_3mo: Optional[Decimal] = None
    norm_6mo: Optional[Decimal] = None
    norm_1y: Optional[Decimal] = None
    norm_5y: Optional[Decimal] = None
    norm_20y: Optional[Decimal] = None


class Stock1MoResponse(BaseModel):
    symbol: str
    date: datetime
    norm_1mo: Optional[Decimal] = None


class Stock3MoResponse(BaseModel):
    symbol: str
    date: datetime
    norm_3mo: Optional[Decimal] = None


class Stock6MoResponse(BaseModel):
    symbol: str
    date: datetime
    norm_6mo: Optional[Decimal] = None


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


class StockSymbolsResponse(BaseModel):
    symbols: list[str]
