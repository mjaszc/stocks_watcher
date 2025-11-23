import pytest
from sqlalchemy import inspect
from sqlalchemy.exc import IntegrityError
from models.stock_data import StockData
from decimal import Decimal
from datetime import date


def test_create_stock_data(db_session, sample_stock_data):
    for stock in sample_stock_data:
        db_session.add(stock)
    db_session.commit()

    result = db_session.query(StockData).all()
    assert len(result) == 2
    assert result[0].close == Decimal("154.00")


def test_unique_constraint(db_session):
    # Create first record
    stock1 = StockData(
        symbol="TSLA.US",
        date=date(2025, 11, 23),
        open=Decimal("200.00"),
        high=Decimal("205.00"),
        low=Decimal("199.00"),
        close=Decimal("204.00"),
        volume=500000,
    )
    db_session.add(stock1)
    db_session.commit()

    # Try to create duplicate
    stock2 = StockData(
        symbol="TSLA.US",
        date=date(2025, 11, 23),
        open=Decimal("201.00"),
        high=Decimal("206.00"),
        low=Decimal("200.00"),
        close=Decimal("205.00"),
        volume=600000,
    )
    db_session.add(stock2)

    with pytest.raises(IntegrityError):
        db_session.commit()


def test_query_by_date_range(db_session, sample_stock_data):
    for stock in sample_stock_data:
        db_session.add(stock)
    db_session.commit()

    results = (
        db_session.query(StockData)
        .filter(
            StockData.symbol == "AAPL.US",
            StockData.date >= date(2025, 11, 22),
            StockData.date <= date(2025, 11, 23),
        )
        .order_by(StockData.date)
        .all()
    )

    assert len(results) == 2
    assert results[0].date == date(2025, 11, 22)
    assert results[1].date == date(2025, 11, 23)


def test_normalized_prices_nullable(db_session):
    stock = StockData(
        symbol="MSFT.US",
        date=date(2025, 11, 23),
        open=Decimal("300.00"),
        high=Decimal("305.00"),
        low=Decimal("299.00"),
        close=Decimal("304.00"),
        volume=800000,
    )
    db_session.add(stock)
    db_session.commit()

    result = db_session.query(StockData).filter_by(symbol="MSFT.US").first()
    assert result.norm_1mo is None
    assert result.norm_3mo is None
    assert result.norm_6mo is None
    assert result.norm_1y is None
    assert result.norm_5y is None
    assert result.norm_20y is None
    assert result.close == Decimal("304.00")


def test_index_performance(test_db_engine):
    inspector = inspect(test_db_engine)
    indexes = inspector.get_indexes("stock_data")

    index_names = [idx["name"] for idx in indexes]
    assert "idx_symbol_date" in index_names
