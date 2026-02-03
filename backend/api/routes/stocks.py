from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session
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
from services.stocks import get_stock_prices_by_period

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
    symbols: str = Query(..., description="Comma-separated list of symbols"),
    db: Session = Depends(get_db),
):
    try:
        price_data = await extract_normalized_prices(timeframe, symbols, db)

        if not price_data:
            return {}

        numpy_arr = prices_to_numpy_arr(price_data)
        anomalies = calc_z_score(numpy_arr)

        return anomalies

    except Exception as e:
        print(f"Analysis failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to analyze stocks data")


@router.get("/performance/{timeframe}")
async def get_stock_performance_extremes(
    timeframe: str, symbols: str = Query(...), db: Session = Depends(get_db)
):
    """
    Returns the Best and Worst performing stocks for the given timeframe.
    """
    price_data = await extract_normalized_prices(timeframe, symbols, db)
    result = get_performance_ranking(price_data)

    return result
