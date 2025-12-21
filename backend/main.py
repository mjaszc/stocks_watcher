from fastapi import FastAPI
from fastapi.routing import APIRoute
from core.config import settings
from api.main import api_router
from starlette.middleware.cors import CORSMiddleware
from prometheus_client import make_asgi_app


def custom_generate_unique_id(route: APIRoute) -> str:
    return f"{route.tags[0]}-{route.name}"


app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    generate_unique_id_function=custom_generate_unique_id,
)
metrics_app = make_asgi_app()
# Prometheus metrics ep
app.mount("/metrics", metrics_app)

if settings.all_cors_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.all_cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

app.include_router(api_router, prefix=settings.API_V1_STR)
