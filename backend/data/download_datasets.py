import requests
from .load_stock_data import StockDataLoader
from db.session import Session
from sqlalchemy import func, inspect
from models.stock_data import StockData

# List of stocks to download the latest dataset
stock_symbols = {
    # stock_symbol : dataset_filename
    "googl.us": "googl_us",
    "meta.us": "meta_us",
    "amzn.us": "amzn_us",
    "aapl.us": "aapl_us",
}


def download_dataset(url, save_path):
    response = requests.get(url)

    if response.status_code == 200:
        with open(save_path, "wb") as file:
            file.write(response.content)
        print(f"Downloaded: {save_path}")
    else:
        print(f"Failed to download. Status code: {response.status_code}")


# Clear normalized price rows
def clear_norm_rows():
    with Session() as db:
        db.query(StockData).update(
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


def get_max_date():
    with Session() as db:
        result = db.query(func.max(StockData.date)).scalar()
        if result is None:
            print("Could not get the max date, no data in database")
        return result


max_dt = get_max_date()
if max_dt is not None:
    clear_norm_rows()

# Downloading latest version of stock data
# TODO: Add scheduling
for symbol, filename in stock_symbols.items():
    url = f"https://stooq.com/q/d/l/?s={symbol}&i=d"
    path = f"datasets/{filename}_d.csv"
    download_dataset(url, path)
    StockDataLoader(path, symbol.upper(), max_dt)
