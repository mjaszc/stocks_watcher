from backend.core.config import settings
from sqlalchemy import create_engine, event
from sqlalchemy.pool import Pool

engine = create_engine(str(settings.SQLALCHEMY_DATABASE_URI))
