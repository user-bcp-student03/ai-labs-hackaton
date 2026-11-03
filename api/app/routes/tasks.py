import sqlite3

from fastapi import APIRouter, Depends

from app.dependencies import get_db_connection
from app.schemas import TaskCreate, TaskOut
from app.security import legacy_identity
from app.services import tasks as task_service

router = APIRouter()


@router.get("/api/tasks", response_model=list[TaskOut])
def list_tasks(
    identity: dict[str, str] = Depends(legacy_identity),
    connection: sqlite3.Connection = Depends(get_db_connection),
) -> list[TaskOut]:
    return task_service.list_tasks(connection, identity["username"])


@router.post("/api/tasks", status_code=201, response_model=TaskOut)
def create_task(
    payload: TaskCreate,
    identity: dict[str, str] = Depends(legacy_identity),
    connection: sqlite3.Connection = Depends(get_db_connection),
) -> TaskOut:
    return task_service.create_task(connection, payload, identity["username"])
