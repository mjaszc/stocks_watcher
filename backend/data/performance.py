from decimal import Decimal
from typing import List, Dict


def get_performance_ranking(price_data: Dict[str, List[Decimal]]) -> Dict[str, List]:
    """
    Calculates performance % for all stocks and identifies best/worst.
    Input prices are normalized (start at 100).
    """
    ranking = []

    for symbol, prices in price_data.items():
        if not prices:
            continue

        latest_price = prices[-1]

        perf_pct = Decimal(latest_price) - Decimal(100.0)

        ranking.append(
            {
                "symbol": symbol,
                "performance_pct": round(perf_pct, 2),
                "latest_value": Decimal(latest_price),
            }
        )
    ranking.sort(key=lambda x: x["performance_pct"], reverse=True)

    if not ranking:
        return {}

    return {
        "best": ranking[0],
        "worst": ranking[-1],
    }
