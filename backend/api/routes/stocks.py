from fastapi import APIRouter, Depends, status, HTTPException, Query
from typing import Optional
from sqlalchemy import select
from sqlalchemy.orm import Session
from datetime import datetime
from dateutil.relativedelta import relativedelta

from backend.models.stock_data import StockData
from backend.db.session import get_db
from backend.schemas.stock_data import StockResponse

router = APIRouter(prefix="/stocks", tags=["stocks"])


@router.get("/{symbol}", response_model=list[StockResponse])
def get_stock_prices(
    symbol: str,
    period: Optional[str] = Query(None, regex="^(1mo|3mo|6mo|1y|5y|20y)$"),
    db: Session = Depends(get_db),
):
    end_date = datetime(2025, 11, 5)

    period_mapping = {
        "1mo": relativedelta(months=1),
        "3mo": relativedelta(months=3),
        "6mo": relativedelta(months=6),
        "1y": relativedelta(years=1),
        "5y": relativedelta(years=5),
        "10y": relativedelta(years=10),
        "20y": relativedelta(years=20),
    }

    if period:
        delta = period_mapping[period]
        start_date = end_date - delta
    else:
        start_date = end_date - relativedelta(years=1)

    stmt = (
        select(StockData)
        .where(
            StockData.symbol == symbol,
            StockData.date >= start_date,
            StockData.date <= end_date,
        )
        .order_by(StockData.date.desc())
    )

    stock_data = db.execute(stmt).scalars().all()

    if not stock_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Stock Data not found",
        )
    return stock_data
