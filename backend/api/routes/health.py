import time
from fastapi import APIRouter, HTTPException
from sqlalchemy import text

from db.session import Session

router = APIRouter(prefix="/health", tags=["health"])


@router.get("/", status_code=200)
async def health_check():
    start_time = time.time()

    with Session() as db:
        try:
            db.execute(text("SELECT 1"))
            db.close()
        except Exception as e:
            raise HTTPException(status_code=503, detail="Db unreachable")

    return {"status": "ready", "duration": f"{time.time() - start_time:.3f}s"}
