from sqlalchemy.orm import sessionmaker, scoped_session
from db.engine import engine

Session = sessionmaker(bind=engine, expire_on_commit=False)


def get_db():
    """Dependency for getting database session."""
    db = Session()
    try:
        db.commit()
        yield db
    finally:
        db.close()
