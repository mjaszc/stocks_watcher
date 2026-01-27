import httpx
import re
import numpy as np
import numpy.typing as npt
from decimal import Decimal
from typing import List, Dict, Any

from core.config import settings

STOCKS_API_URL = f"{settings.DOMAIN}{settings.API_V1_STR}/stocks"


async def fetch_stock_data(timeframe: str, symbols: str):
    """
    Calls the specific timeframe endpoint dynamically.
    Args:
        timeframe (str): '1mo', '3mo', '1y', etc.
        symbols (str): Comma-separated string like 'AAPL.US,TSLA.US'
    Returns:

    """
    url = f"{STOCKS_API_URL}/{timeframe}"
    params = {"symbols": symbols.strip()}

    async with httpx.AsyncClient() as client:
        response = await client.get(url, params=params)
        response.raise_for_status()
        return response.json()


async def extract_normalized_prices(
    timeframe: str, symbols
) -> Dict[str, List[Decimal]]:
    raw_data = await fetch_stock_data(timeframe, symbols)
    column_name = f"norm_{timeframe}"

    results = {}

    for symbol, records in raw_data.items():
        results[symbol] = [
            Decimal(record[column_name])
            for record in records
            if column_name in record and record[column_name] is not None
        ]

    return results


def prices_to_numpy_arr(price_data: Dict[str, List[Decimal]]) -> Dict[str, npt.NDArray]:
    parsed_stocks = {}

    for symbol, prices in price_data.items():
        parsed_stocks[symbol] = np.array(prices, dtype=np.float64)

    return parsed_stocks


def calc_z_score(numpy_prices_arr: Dict[str, npt.NDArray[np.object_]]):
    results = {}

    for symbol, prices in numpy_prices_arr.items():
        try:
            returns = np.diff(prices) / prices[:-1]
            mean_return = np.mean(returns)
            std_return = np.std(returns)

            stock_anomalies = []
            for i, daily_ret in enumerate(returns):
                if std_return == 0:
                    continue

                z_score = (daily_ret - mean_return) / std_return

                if abs(z_score) > 2.5:
                    price_index = i + 1
                    stock_anomalies.append(
                        {
                            "date_index": price_index,
                            "price": prices[price_index],
                            "return_pct": round(daily_ret * 100, 2),
                            "z_score": round(z_score, 2),
                        }
                    )
            if stock_anomalies:
                results[symbol] = stock_anomalies

        except Exception as e:
            print(f"Error parsing {symbol}: {e}")
            continue

    return results
