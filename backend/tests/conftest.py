import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from models.stock_data import StockData
from core.config import settings
from data.load_stock_data import StockDataLoader

import pandas as pd
import tempfile
from datetime import date
from decimal import Decimal


@pytest.fixture(scope="session")
def test_db_engine():
    engine = create_engine(
        "postgresql+psycopg2://postgres:postgres@localhost:5432/postgres",
        isolation_level="AUTOCOMMIT",
    )

    test_db_name = settings.TEST_POSTGRES_DB

    # Check if db exists
    with engine.connect() as conn:
        conn.execute(text(f"CREATE DATABASE {test_db_name}"))
        conn.execute(
            text(f"GRANT ALL PRIVILEGES ON DATABASE {test_db_name} TO postgres")
        )

    # Connect to test db
    test_engine = create_engine(
        f"postgresql+psycopg2://postgres:postgres@localhost:5432/{test_db_name}"
    )
    StockData.metadata.create_all(test_engine)

    yield test_engine

    test_engine.dispose()

    with engine.connect() as conn:
        # Terminate all connections to test db and delete db
        conn.execute(
            text(
                f"""
            SELECT pg_terminate_backend(pg_stat_activity.pid)
            FROM pg_stat_activity
            WHERE pg_stat_activity.datname = '{test_db_name}'
            AND pid <> pg_backend_pid()
        """
            )
        )
        conn.execute(text(f"DROP DATABASE {test_db_name}"))

    engine.dispose()


@pytest.fixture
def db_session(test_db_engine):
    connection = test_db_engine.connect()
    transaction = connection.begin()

    Session = sessionmaker(bind=connection)
    session = Session()

    yield session

    session.close()

    if transaction.is_active:
        transaction.rollback()

    connection.close()


@pytest.fixture
def sample_stock_data():
    return [
        StockData(
            symbol="AAPL.US",
            date=date(2025, 11, 22),
            open=Decimal("150.00"),
            high=Decimal("155.00"),
            low=Decimal("149.00"),
            close=Decimal("154.00"),
            volume=1000000,
        ),
        StockData(
            symbol="AAPL.US",
            date=date(2025, 11, 23),
            open=Decimal("154.00"),
            high=Decimal("156.00"),
            low=Decimal("153.00"),
            close=Decimal("155.50"),
            volume=1500000,
        ),
    ]


@pytest.fixture
def sample_csv_data():
    """Generate sample csv data in 20 years range for full testing"""
    dates = pd.date_range(start="2005-01-01", end="2025-01-01")
    data = {
        "Date": dates,
        "Open": [100 + i * 0.05 for i in range(len(dates))],
        "High": [101 + i * 0.05 for i in range(len(dates))],
        "Low": [99 + i * 0.05 for i in range(len(dates))],
        "Close": [100.5 + i * 0.05 for i in range(len(dates))],
        "Volume": [1000000 + i * 100 for i in range(len(dates))],
    }
    return pd.DataFrame(data)


@pytest.fixture
def csv_temp_file(sample_csv_data):
    """Create temporary file with generated csv data"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
        sample_csv_data.to_csv(f.name, index=False)
        yield f.name

    # cleanup
    f.close()


@pytest.fixture
def populated_db(db_session, csv_temp_file):
    """Feed temporary data to the testing database"""
    loader = StockDataLoader(dataset=csv_temp_file, symbol="AAPL.US")
    yield loader

    db_session.session.query(StockData).filter(StockData.symbol == "AAPL.US").delete()
    db_session.commit()
