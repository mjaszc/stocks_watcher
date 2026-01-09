from celery import Celery
from celery.schedules import crontab
import requests
import redis

from .load_stock_data import StockDataLoader
from core.config import settings
from utils.decorators import redis_client

sync_redis = redis.from_url(settings.REDIS_URL)

app = Celery(broker=settings.CELERY_BROKER_URL)
app.conf.enable_utc = True
app.conf.timezone = "UTC"  # type: ignore

app.conf.beat_schedule = {
    "download-and-load-stock-data-every-afternoon": {
        "task": "data.tasks.download_and_load_stock_data",
        "schedule": crontab(minute=0, hour=18),
    },
    "clear-redis-stock-cache-every-afternoon": {
        "task": "data.tasks.clear_all_stock_cache",
        "schedule": crontab(minute=45, hour=17),
    },
}

# Dictionary of stocks to download the latest dataset
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


@app.task
def clear_all_stock_cache():
    sync_redis.flushdb()
    print("Redis cache fully cleared.")


@app.task
def download_and_load_stock_data():
    for symbol, filename in stock_symbols.items():
        # Download latest version of stock data
        url = f"https://stooq.com/q/d/l/?s={symbol}&i=d"
        path = f"datasets/{filename}_d.csv"
        download_dataset(url, path)
        # Instantiate class responsible for loading historical stock data and calculating normalized price for each stock
        StockDataLoader(path, symbol.upper())
