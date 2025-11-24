import pandas as pd
import uuid
from decimal import Decimal
from datetime import datetime
from db.session import Session
from sqlalchemy import text, func
from sqlalchemy.dialects.postgresql import insert
from models.stock_data import StockData


class StockDataLoader:
    def __init__(self, dataset: str, symbol: str, session=None):
        # Needed for testing on test db session
        self.session = session

        # Base prices for base100 normalized price calculation for all time horizons
        self.base_price_1mo = Decimal("0.00")
        self.base_price_3mo = Decimal("0.00")
        self.base_price_6mo = Decimal("0.00")
        self.base_price_1y = Decimal("0.00")
        self.base_price_5y = Decimal("0.00")
        self.base_price_20y = Decimal("0.00")

        self.symbol = symbol
        self.df = pd.read_csv(dataset, parse_dates=["Date"], dayfirst=False)
        data_to_insert = []
        for _, row in self.df.iterrows():
            data_to_insert.append(
                {
                    "id": uuid.uuid4(),
                    "symbol": symbol,
                    "date": row["Date"],
                    "open": row["Open"],
                    "high": row["High"],
                    "low": row["Low"],
                    "close": row["Close"],
                    "volume": row["Volume"],
                }
            )

        # Put historical stock data read from csv file
        if self.session:
            # Use provided session (for testing or dependency injection)
            stmt = insert(StockData).values(data_to_insert)
            stmt = stmt.on_conflict_do_nothing(constraint="uq_symbol_date")
            self.session.execute(stmt)
            self.session.commit()
        else:
            # Create and use a new session for production
            db = Session()
            try:
                stmt = insert(StockData).values(data_to_insert)
                stmt = stmt.on_conflict_do_nothing(constraint="uq_symbol_date")
                db.execute(stmt)
                db.commit()
            except Exception as e:
                db.rollback()
                raise
            finally:
                db.close()

        # Clear normalized prices data from previous day for easier updates
        self.clear_norm_rows(symbol.upper())
        self.max_date = self.get_max_date(symbol.upper())

        # Perform calculations for normalization prices
        extracted_base_prices = self.get_base_prices()
        self.update_prices(extracted_base_prices)

        self.calculate_normalized_prices_for_tf("1mo", self.base_price_1mo, "norm_1mo")
        self.calculate_normalized_prices_for_tf("3mo", self.base_price_3mo, "norm_3mo")
        self.calculate_normalized_prices_for_tf("6mo", self.base_price_6mo, "norm_6mo")
        self.calculate_normalized_prices_for_tf("1y", self.base_price_1y, "norm_1y")
        self.calculate_normalized_prices_for_tf("5y", self.base_price_5y, "norm_5y")
        self.calculate_normalized_prices_for_tf("20y", self.base_price_20y, "norm_20y")

    def clear_norm_rows(self, symbol: str):
        if self.session:
            db = self.session
        else:
            db = Session()

        try:
            db.query(StockData).filter(StockData.symbol == symbol).update(
                {
                    StockData.norm_1mo: None,
                    StockData.norm_3mo: None,
                    StockData.norm_6mo: None,
                    StockData.norm_1y: None,
                    StockData.norm_5y: None,
                    StockData.norm_20y: None,
                },
                synchronize_session=False,
            )
            db.commit()
        finally:
            if not self.session:
                db.close()

    def get_max_date(self, symbol: str):
        if self.session:
            db = self.session
        else:
            db = Session()

        try:
            result = (
                db.query(func.max(StockData.date))
                .filter(StockData.symbol == symbol)
                .scalar()
            )
            if result is None:
                print("Could not get the max date, no data in database")
            return result
        finally:
            if not self.session:
                db.close()

    def calculate_lookback_date(self, today_date: datetime, timeframe: str) -> datetime:
        timeframe_map = {
            "1mo": pd.DateOffset(months=1),
            "3mo": pd.DateOffset(months=3),
            "6mo": pd.DateOffset(months=6),
            "1y": pd.DateOffset(years=1),
            "5y": pd.DateOffset(years=5),
            "20y": pd.DateOffset(years=20),
        }

        if timeframe not in timeframe_map:
            raise ValueError(
                f"Invalid timeframe: {timeframe}. Valid options are: {', '.join(timeframe_map.keys())}"
            )

        return today_date - timeframe_map[timeframe]

    def get_base_prices(self) -> dict[str, Decimal]:
        """Get base prices for calculating normalized price for each stock."""
        timeframes = ["1mo", "3mo", "6mo", "1y", "5y", "20y"]

        base_prices = {}
        for tf in timeframes:
            target_date = pd.to_datetime(
                self.calculate_lookback_date(self.max_date, tf)
            )
            df_dates = pd.to_datetime(self.df["Date"])

            # Find nearest date
            self.df["date_diff"] = abs(df_dates - target_date)
            nearest_idx = self.df["date_diff"].idxmin()
            self.df.drop("date_diff", axis=1, inplace=True)

            price = self.df.loc[nearest_idx, "Close"]
            base_prices[tf] = Decimal(str(price))

        return base_prices

    def update_prices(self, prices_dict: dict[str, Decimal]) -> None:
        """Pass updated base prices dictionary to update Class base prices"""
        for tf, close_price in prices_dict.items():
            # Convert timeframe to attribute name (e.g., "1mo" -> "base_price_1mo")
            attr_name = f"base_price_{tf}"

            # Set the attribute if it exists on this object
            if hasattr(self, attr_name):
                setattr(self, attr_name, Decimal(close_price))

    def calculate_normalized_price(
        self, base_price: Decimal, close_price: Decimal
    ) -> Decimal:
        normalized_price = (close_price / base_price) * 100
        return normalized_price

    def calculate_normalized_prices_for_tf(
        self,
        timeframe: str,
        base_price: Decimal,
        column_name: str,
    ) -> None:
        offset_map = {
            "1mo": pd.DateOffset(months=1),
            "3mo": pd.DateOffset(months=3),
            "6mo": pd.DateOffset(months=6),
            "1y": pd.DateOffset(years=1),
            "5y": pd.DateOffset(years=5),
            "20y": pd.DateOffset(years=20),
        }

        self.df["Date"] = pd.to_datetime(self.df["Date"])
        cutoff_date = pd.Timestamp(self.max_date) - offset_map[timeframe]
        recent_dates = self.df[self.df["Date"] >= cutoff_date]

        if self.session:
            db = self.session
        else:
            db = Session()

        try:
            for _, row in recent_dates.iterrows():
                close_price = Decimal(str(row["Close"]))
                normalized_price: Decimal = self.calculate_normalized_price(
                    base_price, close_price
                )
                db.execute(
                    text(
                        f"""
                        UPDATE stock_data
                        SET {column_name} = :normalized_price
                        WHERE "date" = :date AND symbol = :symbol
                        """
                    ),
                    {
                        "normalized_price": normalized_price,
                        "date": row["Date"],
                        "symbol": self.symbol,
                    },
                )
            db.commit()
        except Exception as e:
            print(f"Error updating database: {e}")
            db.rollback()
            raise
        finally:
            if not self.session:
                db.close()
