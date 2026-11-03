import sqlite3

from fastapi import APIRouter, Depends

from app.dependencies import get_db_connection
from app.schemas import SummaryOut
from app.security import legacy_identity
from app.services import tasks as task_service

router = APIRouter()


@router.get("/api/summary", response_model=SummaryOut)
def get_summary(
    identity: dict[str, str] = Depends(legacy_identity),
    connection: sqlite3.Connection = Depends(get_db_connection),
) -> SummaryOut:
    return task_service.summarize_tasks(connection, identity["username"])
