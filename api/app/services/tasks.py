import sqlite3
from collections import Counter

from app.config import CLOSED_TASK_STATUSES, HIGH_TASK_PRIORITY
from app.repositories import tasks as task_repository
from app.schemas import SummaryOut, TaskCreate, TaskOut


def list_tasks(connection: sqlite3.Connection, owner: str) -> list[TaskOut]:
    return [
        _task_from_row(row)
        for row in task_repository.list_tasks(connection, owner)
    ]


def create_task(
    connection: sqlite3.Connection,
    task: TaskCreate,
    owner: str,
) -> TaskOut:
    row = task_repository.create_task(connection, task, owner)
    return _task_from_row(row)


def summarize_tasks(connection: sqlite3.Connection, owner: str) -> SummaryOut:
    rows = task_repository.get_summary_rows(connection, owner)
    status_counts = Counter(row["status"] for row in rows)
    high_priority_open_count = sum(
        row["priority"] == HIGH_TASK_PRIORITY
        and row["status"] not in CLOSED_TASK_STATUSES
        for row in rows
    )
    return SummaryOut(
        owner=owner,
        total=len(rows),
        by_status=dict(status_counts),
        high_priority_open=high_priority_open_count,
    )


def _task_from_row(row: sqlite3.Row) -> TaskOut:
    return TaskOut(
        id=row["id"],
        title=row["title"],
        description=row["description"],
        status=row["status"],
        owner=row["owner"],
        priority=row["priority"],
        created_at=row["created_at"],
    )
