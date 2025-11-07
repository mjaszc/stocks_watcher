import pandas as pd
import uuid
from backend.db.engine import engine
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
