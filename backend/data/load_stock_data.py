import pandas as pd
import uuid
from decimal import Decimal
from datetime import datetime
from backend.db.engine import engine
from backend.db.session import Session
from sqlalchemy import text
from sqlalchemy.dialects.postgresql import insert
from backend.models.stock_data import StockData

# Example dataset
df = pd.read_csv("backend/datasets/googl_us_d.csv", parse_dates=["Date"], dayfirst=True)


# Initial loading historical data to database
data_to_insert = []
for _, row in df.iterrows():
    data_to_insert.append(
        {
            "id": uuid.uuid4(),
            "symbol": "GOOGL.US",
            "date": row["Date"].strftime("%Y-%m-%d"),
            "open": row["Open"],
            "high": row["High"],
            "low": row["Low"],
            "close": row["Close"],
            "volume": row["Volume"],
        }
    )

with engine.begin() as conn:
    stmt = insert(StockData).values(data_to_insert)
    stmt = stmt.on_conflict_do_nothing(constraint="uq_symbol_date")
    result = conn.execute(stmt)


def calculate_lookback_date(today_date: datetime, timeframe: str) -> datetime:
    match timeframe:
        case "1m":
            lookback_date = today_date - pd.DateOffset(months=1)
            return lookback_date
        case "3m":
            lookback_date = today_date - pd.DateOffset(months=3)
            return lookback_date
        case "6m":
            lookback_date = today_date - pd.DateOffset(months=6)
            return lookback_date
        case "1y":
            lookback_date = today_date - pd.DateOffset(years=1)
            return lookback_date
        case "5y":
            lookback_date = today_date - pd.DateOffset(years=5)
            return lookback_date
        case "20y":
            lookback_date = today_date - pd.DateOffset(years=20)
            return lookback_date
        case _:
            raise ValueError("Wrong today's date")


def get_base_prices() -> dict[str, Decimal]:
    today_date = datetime(2025, 11, 5)

    timeframes = ["1m", "3m", "6m", "1y", "5y", "20y"]

    base_prices = {}
    for tf in timeframes:
        target_date = pd.to_datetime(calculate_lookback_date(today_date, tf))
        df_dates = pd.to_datetime(df["Date"])

        # Find nearest date
        df["date_diff"] = abs(df_dates - target_date)
        nearest_idx = df["date_diff"].idxmin()
        df.drop("date_diff", axis=1, inplace=True)

        price = df.loc[nearest_idx, "Close"]
        base_prices[tf] = Decimal(str(price))

    return base_prices


# Base prices for base100 normalized price calculation for all time horizons
base_price_1m = Decimal("0.00")
base_price_3m = Decimal("0.00")
base_price_6m = Decimal("0.00")
base_price_1y = Decimal("0.00")
base_price_5y = Decimal("0.00")
base_price_20y = Decimal("0.00")


def update_prices(prices_dict: dict[str, Decimal]) -> None:
    global base_price_1m, base_price_3m, base_price_6m, base_price_1y, base_price_5y, base_price_20y

    for tf, close_price in prices_dict.items():
        if tf == "1m":
            base_price_1m = Decimal(close_price)
        elif tf == "3m":
            base_price_3m = Decimal(close_price)
        elif tf == "6m":
            base_price_6m = Decimal(close_price)
        elif tf == "1y":
            base_price_1y = Decimal(close_price)
        elif tf == "5y":
            base_price_5y = Decimal(close_price)
        elif tf == "20y":
            base_price_20y = Decimal(close_price)


def calculate_normalized_price(base_price: Decimal, close_price: Decimal) -> Decimal:
    normalized_price = (close_price / base_price) * 100
    return normalized_price


# Calculate normalized prices for dates less than or equal 30 days
def calculate_normalized_prices_for_1m_tf() -> None:
    today_date = datetime(2025, 11, 5)

    df["Date"] = pd.to_datetime(df["Date"])
    thirty_days_ago = pd.Timestamp(today_date) - pd.Timedelta(days=30)

    recent_dates = df[df["Date"] >= thirty_days_ago]
    # print(recent_dates[["Date", "Close"]])

    with Session() as db:
        try:
            for _, row in recent_dates.iterrows():
                close_price = Decimal(str(row["Close"]))

                normalized_price: Decimal = calculate_normalized_price(
                    base_price_1m, close_price
                )
                db.execute(
                    text(
                        """
                        UPDATE stock_data
                        SET norm_1m = :norm_1m_price
                        WHERE "date" = :date
                        """
                    ),
                    {"norm_1m_price": normalized_price, "date": row["Date"]},
                )
                db.commit()
        except Exception as e:
            print(f"Error updating database: {e}")
            db.rollback()
            raise


extracted_base_prices = get_base_prices()
update_prices(extracted_base_prices)
calculate_normalized_prices_for_1m_tf()
