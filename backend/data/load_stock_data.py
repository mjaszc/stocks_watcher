import pandas as pd
import uuid
from decimal import Decimal
from datetime import datetime
from backend.db.engine import engine
from backend.db.session import Session
from sqlalchemy import text
from sqlalchemy.dialects.postgresql import insert
from backend.models.stock_data import StockData


class StockDataLoader:
    # Base prices for base100 normalized price calculation for all time horizons
    base_price_1m = Decimal("0.00")
    base_price_3m = Decimal("0.00")
    base_price_6m = Decimal("0.00")
    base_price_1y = Decimal("0.00")
    base_price_5y = Decimal("0.00")
    base_price_20y = Decimal("0.00")

    def __init__(self, dataset: str, symbol: str):
        self.df = pd.read_csv(dataset, parse_dates=["Date"], dayfirst=True)
        data_to_insert = []
        for _, row in self.df.iterrows():
            data_to_insert.append(
                {
                    "id": uuid.uuid4(),
                    "symbol": symbol,
                    "date": row["Date"].strftime("%Y-%m-%d"),
                    "open": row["Open"],
                    "high": row["High"],
                    "low": row["Low"],
                    "close": row["Close"],
                    "volume": row["Volume"],
                }
            )

        # Put historical stock data read from csv file
        with engine.begin() as conn:
            stmt = insert(StockData).values(data_to_insert)
            stmt = stmt.on_conflict_do_nothing(constraint="uq_symbol_date")
            conn.execute(stmt)

        # Perform calculations for normalization prices
        extracted_base_prices = self.get_base_prices()
        self.update_prices(extracted_base_prices)
        self.calculate_normalized_prices_for_tf("1m", self.base_price_1m, "norm_1m")
        self.calculate_normalized_prices_for_tf("3m", self.base_price_3m, "norm_3m")
        self.calculate_normalized_prices_for_tf("6m", self.base_price_6m, "norm_6m")
        self.calculate_normalized_prices_for_tf("1y", self.base_price_1y, "norm_1y")
        self.calculate_normalized_prices_for_tf("5y", self.base_price_5y, "norm_5y")
        self.calculate_normalized_prices_for_tf("20y", self.base_price_20y, "norm_20y")

    def calculate_lookback_date(self, today_date: datetime, timeframe: str) -> datetime:
        timeframe_map = {
            "1m": pd.DateOffset(months=1),
            "3m": pd.DateOffset(months=3),
            "6m": pd.DateOffset(months=6),
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
        today_date = datetime(2025, 11, 5)

        timeframes = ["1m", "3m", "6m", "1y", "5y", "20y"]

        base_prices = {}
        for tf in timeframes:
            target_date = pd.to_datetime(self.calculate_lookback_date(today_date, tf))
            df_dates = pd.to_datetime(self.df["Date"])

            # Find nearest date
            self.df["date_diff"] = abs(df_dates - target_date)
            nearest_idx = self.df["date_diff"].idxmin()
            self.df.drop("date_diff", axis=1, inplace=True)

            price = self.df.loc[nearest_idx, "Close"]
            base_prices[tf] = Decimal(str(price))

        return base_prices

    def update_prices(self, prices_dict: dict[str, Decimal]) -> None:
        for tf, close_price in prices_dict.items():
            # Convert timeframe to attribute name (e.g., "1m" -> "base_price_1m")
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
        today_date: datetime = datetime(2025, 11, 5),
    ) -> None:
        offset_map = {
            "1m": pd.DateOffset(months=1),
            "3m": pd.DateOffset(months=3),
            "6m": pd.DateOffset(months=6),
            "1y": pd.DateOffset(years=1),
            "5y": pd.DateOffset(years=5),
            "20y": pd.DateOffset(years=20),
        }

        self.df["Date"] = pd.to_datetime(self.df["Date"])
        cutoff_date = pd.Timestamp(today_date) - offset_map[timeframe]
        recent_dates = self.df[self.df["Date"] >= cutoff_date]

        with Session() as db:
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
                            WHERE "date" = :date
                            """
                        ),
                        {"normalized_price": normalized_price, "date": row["Date"]},
                    )
                    db.commit()
            except Exception as e:
                print(f"Error updating database: {e}")
                db.rollback()
                raise


StockDataLoader("backend/datasets/googl_us_d.csv", "GOOGL.US")
