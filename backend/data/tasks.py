from celery import Celery
from celery.schedules import crontab
import requests
import redis
import json
import asyncio
from fastapi.encoders import jsonable_encoder

from .load_stock_data import StockDataLoader
from core.config import settings
from api.routes.stocks import get_stock_prices_by_period
from db.session import Session
from utils.decorators import redis_client
from api.routes.stocks import get_stock_prices_by_period

sync_redis = redis.from_url(settings.REDIS_URL)

app = Celery(broker=settings.CELERY_BROKER_URL)
app.conf.enable_utc = True
app.conf.timezone = "UTC"  # type: ignore

app.conf.beat_schedule = {
    "clear-redis-stock-cache-every-afternoon": {
        "task": "data.tasks.clear_all_stock_cache",
        "schedule": crontab(minute=45, hour=17),
    },
    "download-and-load-stock-data-every-afternoon": {
        "task": "data.tasks.download_and_load_stock_data",
        "schedule": crontab(minute=0, hour=18),
    },
    "precache-stock-data-of-popular-stocks": {
        "task": "data.tasks.run_caching_stocks",
        "schedule": crontab(minute=15, hour=18),
    },
}

# Dictionary of stocks to download the latest dataset
stock_symbols = {
    # stock_symbol : dataset_filename
    "googl.us": "googl_us",
    "meta.us": "meta_us",
    "amzn.us": "amzn_us",
    "aapl.us": "aapl_us",
    "avgo.us": "avgo_us",
    "tsla.us": "tsla_us",
    "brk-b.us": "brk-b_us",
    "wmt.us": "wmt_us",
    "jpm.us": "jpm_us",
    "v.us": "v_us",
    "orcl.us": "orcl_us",
    "xom.us": "xom_us",
    "ma.us": "ma_us",
    "jnj.us": "jnj_us",
    "pltr.us": "pltr_us",
    "lly.us": "lly_us",
    "bac.us": "bac_us",
    "cost.us": "cost_us",
    "abbv.us": "abbv_us",
    "mu.us": "mu_us",
    "nflx.us": "nflx_us",
    "hd.us": "hd_us",
    "ge.us": "ge_us",
    "pg.us": "pg_us",
    "amd.us": "amd_us",
    "cvx.us": "cvx_us",
    "unh.us": "unh_us",
}


@app.task
def clear_all_stock_cache():
    sync_redis.flushdb()
    print("Redis cache fully cleared.")


def download_dataset(url, save_path):
    response = requests.get(url)

    if response.status_code == 200:
        with open(save_path, "wb") as file:
            file.write(response.content)
        print(f"Downloaded: {save_path}")
    else:
        print(f"Failed to download. Status code: {response.status_code}")


@app.task
def download_and_load_stock_data():
    for symbol, filename in stock_symbols.items():
        # Download latest version of stock data
        url = f"https://stooq.com/q/d/l/?s={symbol}&i=d"
        path = f"datasets/{filename}_d.csv"
        download_dataset(url, path)
        # Instantiate class responsible for loading historical stock data and calculating normalized price for each stock
        StockDataLoader(path, symbol.upper())


async def precache_stock_data():
    """
    Fetches most popular stocks data from DB and forces an update to Redis cache.
    """
    # S&P 500 Top 20 stocks by weight
    most_known_stock_symbols = [
        "nvda.us",
        "aapl.us",
        "msft.us",
        "amzn.us",
        "googl.us",
        "meta.us",
        "avgo.us",
        "tsla.us",
        "brk-b.us",
        "lly.us",
        "wmt.us",
        "jpm.us",
        "v.us",
        "xom.us",
        "jnj.us",
        "orcl.us",
        "ma.us",
        "mu.us",
        "cost.us",
    ]
    available_timeframes = ["1mo", "3mo", "6mo", "1y", "5y", "20y"]

    ttl = 86400
    symbols_str = ",".join(most_known_stock_symbols)

    print("Starting stock data precaching...")

    with Session() as db:
        for period in available_timeframes:
            try:
                # Fetch data directly from db
                # This returns a dict: { "SYMBOL.COUNTRY": [StockData object, ...] }
                stock_data_map = get_stock_prices_by_period(period, symbols_str, db)

                # Serialize and store in Redis
                for symbol, data_objects in stock_data_map.items():
                    cache_key = f"stock:{period}:{symbol.upper()}"

                    # Serialize data exactly as the decorator does
                    serialized_data = jsonable_encoder(data_objects)
                    json_payload = json.dumps(serialized_data)

                    # Set in Redis (async operation)
                    await redis_client.setex(cache_key, ttl, json_payload)

                print(f"Cached {period} data for {len(stock_data_map)} symbols")

            except Exception as e:
                print(f"Failed to cache timeframe {period}: {str(e)}")

    print("Precaching complete.")


@app.task
def run_caching_stocks():
    asyncio.run(precache_stock_data())
