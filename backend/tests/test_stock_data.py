from models.stock_data import StockData
from decimal import Decimal


def test_create_stock_data(db_session, sample_stock_data):
    for stock in sample_stock_data:
        db_session.add(stock)
    db_session.commit()

    result = db_session.query(StockData).all()
    assert len(result) == 2
    assert result[0].close == Decimal("154.00")
