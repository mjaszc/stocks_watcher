from fastapi import APIRouter, Depends, status, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session
from dateutil.relativedelta import relativedelta
from sqlalchemy import func
from collections import defaultdict

from models.stock_data import StockData
from db.session import get_db, Session as s
from schemas.stock_data import (
    Stock1MoResponse,
    Stock3MoResponse,
    Stock6MoResponse,
    Stock1YResponse,
    Stock5YResponse,
    Stock20YResponse,
)
from core.metrics import REQUEST_COUNTER
from utils.decorators import cache_stock_data

router = APIRouter(prefix="/stocks", tags=["stocks"])


def get_max_date():
    with s() as db:
        result = db.query(func.max(StockData.date)).scalar()
        if result is None:
            print("Could not get the max date")
        return result


@router.get("/1mo")
@cache_stock_data(ttl=86400)
async def get_stocks_1m(
    symbols: str = Query(..., description="Comma-separated list of stock symbols"),
    db: Session = Depends(get_db),
) -> dict[str, list[Stock1MoResponse]]:
    REQUEST_COUNTER.labels(endpoint="/stocks/1mo").inc()
    return get_stock_prices_by_period("1mo", symbols, db)


@router.get("/3mo")
@cache_stock_data(ttl=86400)
async def get_stocks_3m(
    symbols: str = Query(..., description="Comma-separated list of stock symbols"),
    db: Session = Depends(get_db),
) -> dict[str, list[Stock3MoResponse]]:
    REQUEST_COUNTER.labels(endpoint="/stocks/3mo").inc()
    return get_stock_prices_by_period("3mo", symbols, db)


@router.get("/6mo")
@cache_stock_data(ttl=86400)
async def get_stocks_6m(
    symbols: str = Query(..., description="Comma-separated list of stock symbols"),
    db: Session = Depends(get_db),
) -> dict[str, list[Stock6MoResponse]]:
    REQUEST_COUNTER.labels(endpoint="/stocks/6mo").inc()
    return get_stock_prices_by_period("6mo", symbols, db)


@router.get("/1y")
@cache_stock_data(ttl=86400)
async def get_stocks_1y(
    symbols: str = Query(..., description="Comma-separated list of stock symbols"),
    db: Session = Depends(get_db),
) -> dict[str, list[Stock1YResponse]]:
    REQUEST_COUNTER.labels(endpoint="/stocks/1y").inc()
    return get_stock_prices_by_period("1y", symbols, db)


@router.get("/5y")
@cache_stock_data(ttl=86400)
async def get_stocks_5y(
    symbols: str = Query(..., description="Comma-separated list of stock symbols"),
    db: Session = Depends(get_db),
) -> dict[str, list[Stock5YResponse]]:
    REQUEST_COUNTER.labels(endpoint="/stocks/5y").inc()
    return get_stock_prices_by_period("5y", symbols, db)


@router.get("/20y")
@cache_stock_data(ttl=86400)
async def get_stocks_20y(
    symbols: str = Query(..., description="Comma-separated list of stock symbols"),
    db: Session = Depends(get_db),
) -> dict[str, list[Stock20YResponse]]:
    REQUEST_COUNTER.labels(endpoint="/stocks/20y").inc()
    return get_stock_prices_by_period("20y", symbols, db)


def get_stock_prices_by_period(
    period: str,
    symbols: str,
    db: Session,
):
    period_mapping = {
        "1mo": relativedelta(months=1),
        "3mo": relativedelta(months=3),
        "6mo": relativedelta(months=6),
        "1y": relativedelta(years=1),
        "5y": relativedelta(years=5),
        "10y": relativedelta(years=10),
        "20y": relativedelta(years=20),
    }

    if period not in period_mapping:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid period. Must be one of: {', '.join(period_mapping.keys())}",
        )

    symbol_list = [s.strip().upper() for s in symbols.split(",")]

    if not symbol_list:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one symbol must be provided",
        )

    end_date = get_max_date()
    delta = period_mapping[period]
    start_date = end_date - delta

    stmt = (
        select(StockData)
        .where(
            StockData.symbol.in_(symbol_list),
            StockData.date >= start_date,
            StockData.date <= end_date,
        )
        .order_by(StockData.symbol, StockData.date)
    )

    stock_data = db.execute(stmt).scalars().all()

    result = defaultdict(list)
    for data in stock_data:
        result[data.symbol].append(data)

    return result


@router.get("/symbols")
def get_stock_symbols(db: Session = Depends(get_db)) -> list[str]:
    stmt = select(StockData.symbol).distinct()
    stock_data = db.execute(stmt).scalars().all()

    return list(stock_data)
