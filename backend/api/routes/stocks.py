from fastapi import APIRouter, Depends, status, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session
from dateutil.relativedelta import relativedelta
from sqlalchemy import func
from collections import defaultdict
from typing import List, Dict, Any

from models.stock_data import StockData
from db.session import get_db, Session as s
from schemas.stock_data import (
    Stock1MoResponse,
    Stock3MoResponse,
    Stock6MoResponse,
    Stock1YResponse,
    Stock5YResponse,
)
from data.z_score import extract_normalized_prices, prices_to_numpy_arr, calc_z_score
from data.performance import get_performance_ranking
from core.metrics import REQUEST_COUNTER
from utils.decorators import cache_stock_data

router = APIRouter(prefix="/stocks", tags=["stocks"])


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


@router.get("/symbols")
def get_stock_symbols(db: Session = Depends(get_db)) -> list[str]:
    stmt = select(StockData.symbol).distinct()
    stock_data = db.execute(stmt).scalars().all()

    return list(stock_data)


@router.get("/anomalies/{timeframe}", response_model=Dict[str, List[Dict[str, Any]]])
async def get_stock_anomalies(
    timeframe: str,
    symbols: str = Query(
        ..., description="Comma-separated list of symbols (e.g. AAPL.US,MSFT.US)"
    ),
):
    """
    Analyzes stock performance for the given timeframe and returns
    statistically significant anomalies (Z-Score > 2.5).
    """
    try:
        price_data = await extract_normalized_prices(timeframe, symbols)

        if not price_data:
            return {}

        numpy_arr = prices_to_numpy_arr(price_data)
        anomalies = calc_z_score(numpy_arr)

        return anomalies

    except Exception as e:
        print(f"Analysis failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to analyze stocks data")


@router.get("/performance/{timeframe}")
async def get_market_movers(timeframe: str, symbols: str = Query(...)):
    """
    Returns the Best and Worst performing stocks for the given timeframe.
    """
    price_data = await extract_normalized_prices(timeframe, symbols)
    result = get_performance_ranking(price_data)

    return result


def get_max_date():
    """
    Find max date inside db
    """
    with s() as db:
        result = db.query(func.max(StockData.date)).scalar()
        if result is None:
            print("Could not get the max date")
        return result


def get_stock_prices_by_period(
    period: str,
    symbols: str,
    db: Session,
):
    """
    Method for getting stock data for specified symbol/s
    from pre-defined periods (1mo, 3mo, etc.)
    """
    period_mapping = {
        "1mo": relativedelta(months=1),
        "3mo": relativedelta(months=3),
        "6mo": relativedelta(months=6),
        "1y": relativedelta(years=1),
        "5y": relativedelta(years=5),
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
