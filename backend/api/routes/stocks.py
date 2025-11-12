from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.models.stock_data import StockData
from backend.db.session import get_db
from backend.schemas.stock_data import StockResponse

router = APIRouter(prefix="/stocks", tags=["stocks"])


@router.get("/{symbol}", response_model=list[StockResponse])
def get_stock_data(
    symbol: str, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)
):
    stmt = (
        select(StockData)
        .where(StockData.symbol == symbol)
        .order_by(StockData.date.desc())
        .offset(skip)
        .limit(limit)
    )

    stock_data = db.execute(stmt).scalars().all()

    if not stock_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Stock Data not found",
        )
    return stock_data
