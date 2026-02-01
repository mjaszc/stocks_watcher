from fastapi import APIRouter
from api.routes import stocks, health

api_router = APIRouter()
api_router.include_router(stocks.router)
api_router.include_router(health.router)
