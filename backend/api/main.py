from fastapi import APIRouter
from api.routes import stocks

api_router = APIRouter()
api_router.include_router(stocks.router)
