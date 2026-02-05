import json
from functools import wraps
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session
import redis.asyncio as redis

from core.config import settings

redis_client = redis.Redis(
    host=settings.REDIS_HOST, port=6379, db=0, decode_responses=True
)


def cache_stock_data(ttl: int = 86400):
    def decorator(func):
        @wraps(func)
        async def wrapper(symbols: str, db: Session, *args, **kwargs):
            symbol_list = sorted([s.strip().upper() for s in symbols.split(",")])
            period = func.__name__.split("_")[-1]

            final_response = {}
            missing_from_cache = []

            for symbol in symbol_list:
                cache_key = f"stock:{period}:{symbol}"
                cached_data = await redis_client.get(cache_key)

                if cached_data:
                    final_response[symbol] = json.loads(cached_data)
                else:
                    missing_from_cache.append(symbol)

            if missing_from_cache:
                missing_symbols_str = ",".join(missing_from_cache)
                db_results = await func(missing_symbols_str, db, *args, **kwargs)

                for symbol, data in db_results.items():
                    serialized = jsonable_encoder(data)
                    await redis_client.setex(
                        f"stock:{period}:{symbol}", ttl, json.dumps(serialized)
                    )
                    final_response[symbol] = serialized

            return final_response

        return wrapper

    return decorator
