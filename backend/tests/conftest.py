import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from models.stock_data import StockData
from core.config import settings

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
        result = conn.execute(
            text("SELECT 1 FROM pg_database WHERE datname = :db_name"),
            {"db_name": test_db_name},
        )
        db_exists = result.fetchone() is not None

        # If not, create a new one
        if not db_exists:
            conn.execute(text(f"CREATE DATABASE {test_db_name}"))

    # Connect to test db
    test_engine = create_engine(str(settings.TEST_SQLALCHEMY_DATABASE_URI))
    StockData.metadata.create_all(test_engine)

    yield test_engine

    test_engine.dispose()

    with engine.connect() as conn:
        # Terminate all connections to test db
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
    Session = sessionmaker(bind=test_db_engine)
    session = Session()

    yield session

    session.rollback()
    session.close()


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
            symbol="META.US",
            date=date(2025, 11, 22),
            open=Decimal("154.00"),
            high=Decimal("156.00"),
            low=Decimal("153.00"),
            close=Decimal("155.50"),
            volume=1500000,
        ),
    ]
