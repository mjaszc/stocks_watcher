from fastapi import status, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session
from dateutil.relativedelta import relativedelta
from sqlalchemy import func
from collections import defaultdict

from models.stock_data import StockData
from db.session import Session as s


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
