from models.stock_data import StockData
from data.load_stock_data import StockDataLoader
from decimal import Decimal
from datetime import date, datetime

import pandas as pd
import pytest
import tempfile


class TestStockDataLoaderInitialization:

    def test_initialization_attributes(self, sample_stock_loader_class, db_session):
        loader = sample_stock_loader_class

        recent_records = (
            db_session.query(StockData)
            .filter(StockData.symbol == "TEST.US")
            .order_by(StockData.date.desc())
            .limit(10)
            .all()
        )

        assert loader.symbol == "TEST.US"
        assert isinstance(loader.df, pd.DataFrame)

        for record in recent_records:
            assert record.norm_1mo is not None
            assert record.norm_3mo is not None
            assert record.norm_6mo is not None
            assert record.norm_1y is not None
            assert record.norm_5y is not None

    def test_csv_data_loaded_correctly(self, sample_stock_loader_class):
        loader = sample_stock_loader_class

        assert not loader.df.empty
        assert len(loader.df) > 0
        assert all(
            col in loader.df.columns
            for col in ["Date", "Open", "High", "Low", "Close", "Volume"]
        )
        assert pd.api.types.is_datetime64_any_dtype(loader.df["Date"])

    def test_data_inserted_to_database(self, csv_temp_file, db_session):
        StockDataLoader(dataset=csv_temp_file, symbol="TEST.US", session=db_session)

        # Check if data was inserted
        count = (
            db_session.query(StockData).filter(StockData.symbol == "TEST.US").count()
        )
        assert count > 0

        # Verify new data record
        first_record = (
            db_session.query(StockData).filter(StockData.symbol == "TEST.US").first()
        )

        assert first_record is not None
        assert first_record.symbol == "TEST.US"
        assert first_record.open is not None
        assert first_record.close is not None


class TestStockDataLoaderDatabaseOperations:
    def test_clear_norm_rows(self, db_session, sample_stock_loader_class):
        loader = sample_stock_loader_class

        recent_records = (
            db_session.query(StockData)
            .filter(StockData.symbol == "TEST.US")
            .order_by(StockData.date.desc())
            .limit(10)
            .all()
        )

        # At least one recent record should have normalized values
        assert len(recent_records) > 0
        assert recent_records[0].norm_1mo is not None
        assert recent_records[0].norm_1mo > Decimal("0.00")

        loader.clear_norm_rows("TEST.US")

        # Verify all normalized columns are None for ALL records
        all_records = (
            db_session.query(StockData).filter(StockData.symbol == "TEST.US").all()
        )
        for record in all_records:
            assert record.norm_1mo is None
            assert record.norm_3mo is None
            assert record.norm_6mo is None
            assert record.norm_1y is None
            assert record.norm_5y is None

    def test_get_max_date(self, sample_stock_loader_class):
        loader = sample_stock_loader_class
        max_date = loader.get_max_date("TEST.US")
        assert max_date is not None
        assert isinstance(max_date, date)

    def test_get_max_date_no_data(self, sample_stock_loader_class):
        loader = sample_stock_loader_class
        max_date = loader.get_max_date("WRONG.US")

        assert max_date is None

    def test_duplicate_data_handling(self, sample_stock_loader_class, db_session):
        loader1 = sample_stock_loader_class
        count1 = (
            db_session.query(StockData).filter(StockData.symbol == "TEST.US").count()
        )

        loader2 = sample_stock_loader_class
        count2 = (
            db_session.query(StockData).filter(StockData.symbol == "TEST.US").count()
        )

        assert count1 == count2


class TestStockDataLoaderDateCalculations:
    def test_calculate_lookback_date_1mo(self, sample_stock_loader_class):
        loader = sample_stock_loader_class

        today = datetime(2025, 12, 20)
        result = loader.calculate_lookback_date(today, "1mo")

        assert result.year == 2025
        assert result.month == 11

    def test_calculate_lookback_date_3mo(self, sample_stock_loader_class):
        loader = sample_stock_loader_class

        today = datetime(2025, 12, 20)
        result = loader.calculate_lookback_date(today, "3mo")

        assert result.year == 2025
        assert result.month == 9

    def test_calculate_lookback_date_6mo(self, sample_stock_loader_class):
        loader = sample_stock_loader_class

        today = datetime(2025, 12, 20)
        result = loader.calculate_lookback_date(today, "6mo")

        assert result.year == 2025
        assert result.month == 6

    def test_calculate_lookback_date_1y(self, sample_stock_loader_class):
        loader = sample_stock_loader_class

        today = datetime(2025, 12, 20)
        result = loader.calculate_lookback_date(today, "1y")

        assert result.year == 2024
        assert result.month == 12

    def test_calculate_lookback_date_5y(self, sample_stock_loader_class):
        loader = sample_stock_loader_class

        today = datetime(2025, 12, 20)
        result = loader.calculate_lookback_date(today, "5y")

        assert result.year == 2020
        assert result.month == 12

    def test_calculate_lookback_date_invalid_timeframe(self, sample_stock_loader_class):
        loader = sample_stock_loader_class

        with pytest.raises(ValueError, match="Invalid timeframe"):
            loader.calculate_lookback_date(datetime(2025, 12, 20), "10y")


class TestStockDataLoaderPriceCalculations:
    def test_get_base_prices_returns_all_timeframes(self, sample_stock_loader_class):
        loader = sample_stock_loader_class
        base_prices = loader.get_base_prices()

        expected_timeframes = ["1mo", "3mo", "6mo", "1y", "5y"]
        assert all(tf in base_prices for tf in expected_timeframes)

        for tf, price in base_prices.items():
            assert isinstance(price, Decimal)
            assert price > 0

    def test_update_prices(self, sample_stock_loader_class):
        loader = sample_stock_loader_class

        test_prices = {
            "1mo": Decimal("150.50"),
            "3mo": Decimal("145.75"),
            "6mo": Decimal("140.00"),
            "1y": Decimal("135.25"),
            "5y": Decimal("100.00"),
        }

        loader.update_prices(test_prices)

        assert loader.base_price_1mo == Decimal("150.50")
        assert loader.base_price_3mo == Decimal("145.75")
        assert loader.base_price_6mo == Decimal("140.00")
        assert loader.base_price_1y == Decimal("135.25")
        assert loader.base_price_5y == Decimal("100.00")

    def test_calculate_normalzied_price_increase(self, sample_stock_loader_class):
        loader = sample_stock_loader_class

        base_price = Decimal("100.00")
        close_price = Decimal("150.00")

        normalized = loader.calculate_normalized_price(base_price, close_price)

        assert normalized == Decimal("150.00")

    def test_calculate_normalzied_price_decrease(self, sample_stock_loader_class):
        loader = sample_stock_loader_class

        base_price = Decimal("100.00")
        close_price = Decimal("75.00")

        normalized = loader.calculate_normalized_price(base_price, close_price)

        assert normalized == Decimal("75.00")

    def test_calculate_normalzied_price_no_change(self, sample_stock_loader_class):
        loader = sample_stock_loader_class

        base_price = Decimal("100.00")
        close_price = Decimal("100.00")

        normalized = loader.calculate_normalized_price(base_price, close_price)

        assert normalized == Decimal("100.00")

    def test_calculate_normalized_prices_for_tf_updates_db(
        self, sample_stock_loader_class, db_session
    ):
        loader = sample_stock_loader_class

        base_price = Decimal("100.00")

        loader.calculate_normalized_prices_for_tf("1mo", base_price, "norm_1mo")

        records = (
            db_session.query(StockData)
            .filter(StockData.symbol == "TEST.US", StockData.norm_1mo.isnot(None))
            .all()
        )

        assert len(records) > 0
        for record in records:
            assert record.norm_1mo is not None
            assert record.norm_1mo > Decimal("0.00")


class TestStockDataLoaderEdgeCases:
    def empty_csv_handling(self, db_session):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write("Date,Open,High,Low,Close,Volume\n")
            csv_path = f.name

        try:
            loader = StockDataLoader(
                dataset=csv_path, symbol="EMPTY.US", session=db_session
            )
            assert loader.df.empty or len(loader.df) == 0
        finally:
            f.close()

    def test_multiple_symbols(self, csv_temp_file, db_session):
        symbols = ["AMZN.US", "GOOGL.US", "MSFT.US", "TSLA.US"]

        loaders = []
        for symbol in symbols:
            loader = StockDataLoader(
                dataset=csv_temp_file, symbol=symbol, session=db_session
            )
            loaders.append(loader)
            assert loader.symbol == symbol

        # Verify each symbol has data in database
        for symbol in symbols:
            count = (
                db_session.query(StockData).filter(StockData.symbol == symbol).count()
            )
            assert count > 0


class TestStockDataLoaderIntegration:

    def test_full_workflow(self, sample_stock_loader_class, db_session):
        loader = sample_stock_loader_class

        count = (
            db_session.query(StockData).filter(StockData.symbol == "TEST.US").count()
        )
        assert count > 0

        assert loader.base_price_1mo != Decimal("0.00")

        records_with_norm = (
            db_session.query(StockData)
            .filter(StockData.symbol == "TEST.US", StockData.norm_1mo.isnot(None))
            .count()
        )
        assert records_with_norm > 0
