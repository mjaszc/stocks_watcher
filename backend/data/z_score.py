import numpy as np
import numpy.typing as npt
from decimal import Decimal
from typing import List, Dict
from sqlalchemy.orm import Session

from services.stocks import get_stock_prices_by_period
from core.config import settings


async def extract_normalized_prices(
    timeframe: str, symbols: str, db: Session
) -> Dict[str, List[Decimal]]:

    raw_data_models = get_stock_prices_by_period(timeframe, symbols, db)

    column_name = f"norm_{timeframe}"
    results = {}

    for symbol, records in raw_data_models.items():
        price_list = []
        for record in records:
            val = getattr(record, column_name, None)

            if val is not None:
                price_list.append(Decimal(val))

        results[symbol] = price_list

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
