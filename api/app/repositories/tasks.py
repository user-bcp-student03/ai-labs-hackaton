import sqlite3

from app.config import (
    DEFAULT_TASK_PRIORITY,
    DEFAULT_TASK_STATUS,
    HIGH_TASK_PRIORITY,
    IN_PROGRESS_TASK_STATUS,
    LOW_TASK_PRIORITY,
)
from app.schemas import TaskCreate

TASKS_BY_OWNER_QUERY = (
    "SELECT id, title, description, status, owner, priority, created_at "
    "FROM tasks WHERE owner = ? ORDER BY id"
)
TASK_BY_ID_QUERY = (
    "SELECT id, title, description, status, owner, priority, created_at "
    "FROM tasks WHERE id = ?"
)

SEED_TASKS = (
    (
        "Refactor login",
        "Separar responsabilidades en frontend",
        DEFAULT_TASK_STATUS,
        "student",
        HIGH_TASK_PRIORITY,
    ),
    (
        "Review API",
        "Revisar seguridad de endpoints",
        IN_PROGRESS_TASK_STATUS,
        "student",
        DEFAULT_TASK_PRIORITY,
    ),
    (
        "Trainer notes",
        "Preparar retrospectiva",
        DEFAULT_TASK_STATUS,
        "trainer",
        LOW_TASK_PRIORITY,
    ),
)


def initialize_tasks(connection: sqlite3.Connection) -> None:
    connection.execute(
        "CREATE TABLE IF NOT EXISTS tasks ("
        "id INTEGER PRIMARY KEY AUTOINCREMENT, "
        "title TEXT NOT NULL, "
        "description TEXT NOT NULL, "
        "status TEXT NOT NULL, "
        "owner TEXT NOT NULL, "
        "priority TEXT NOT NULL, "
        "created_at TEXT NOT NULL)"
    )
    existing_count = connection.execute(
        "SELECT COUNT(*) AS total FROM tasks"
    ).fetchone()["total"]
    if existing_count == 0:
        seed_tasks(connection)


def seed_tasks(connection: sqlite3.Connection) -> None:
    for title, description, status, owner, priority in SEED_TASKS:
        connection.execute(
            "INSERT INTO tasks "
            "(title, description, status, owner, priority, created_at) "
            "VALUES (?, ?, ?, ?, ?, datetime('now'))",
            (title, description, status, owner, priority),
        )
    connection.commit()


def list_tasks(connection: sqlite3.Connection, owner: str) -> list[sqlite3.Row]:
    return connection.execute(
        TASKS_BY_OWNER_QUERY,
        (owner,),
    ).fetchall()


def create_task(
    connection: sqlite3.Connection,
    task: TaskCreate,
    owner: str,
) -> sqlite3.Row:
    cursor = connection.execute(
        "INSERT INTO tasks "
        "(title, description, status, owner, priority, created_at) "
        "VALUES (?, ?, ?, ?, ?, datetime('now'))",
        (task.title, task.description, task.status, owner, task.priority),
    )
    connection.commit()
    row = connection.execute(
        TASK_BY_ID_QUERY,
        (cursor.lastrowid,),
    ).fetchone()
    if row is None:
        raise RuntimeError("The created task could not be retrieved")
    return row


def get_summary_rows(
    connection: sqlite3.Connection,
    owner: str,
) -> list[sqlite3.Row]:
    return connection.execute(
        "SELECT status, priority FROM tasks WHERE owner = ?",
        (owner,),
    ).fetchall()
