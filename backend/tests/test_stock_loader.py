from models.stock_data import StockData
from data.load_stock_data import StockDataLoader

import pandas as pd


class TestStockDataLoaderInitialization:

    def test_initialization_attributes(self, csv_temp_file, db_session):
        """Test that StockDataLoader initializes with correct default attributes."""
        loader = StockDataLoader(
            dataset=csv_temp_file, symbol="TEST.US", session=db_session
        )

        assert loader.symbol == "TEST.US"
        assert isinstance(loader.df, pd.DataFrame)

    def test_csv_data_loaded_correctly(self, csv_temp_file, db_session):
        """Test that CSV data is properly parsed into DataFrame."""
        loader = StockDataLoader(
            dataset=csv_temp_file, symbol="TEST.US", session=db_session
        )

        assert not loader.df.empty
        assert len(loader.df) > 0
        assert all(
            col in loader.df.columns
            for col in ["Date", "Open", "High", "Low", "Close", "Volume"]
        )
        assert pd.api.types.is_datetime64_any_dtype(loader.df["Date"])

    def test_data_inserted_to_database(self, csv_temp_file, db_session):
        """Test that data from CSV is inserted into the database."""
        StockDataLoader(dataset=csv_temp_file, symbol="INSERT.US", session=db_session)

        # Check if data was inserted
        count = (
            db_session.query(StockData).filter(StockData.symbol == "INSERT.US").count()
        )
        assert count > 0

        # Verify new data record
        first_record = (
            db_session.query(StockData).filter(StockData.symbol == "INSERT.US").first()
        )

        assert first_record is not None
        assert first_record.symbol == "INSERT.US"
        assert first_record.open is not None
        assert first_record.close is not None
