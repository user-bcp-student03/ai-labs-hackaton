"""Soporte común de los almacenes SQLite: formato de fechas, conexión por operación y esquema inicial."""
from __future__ import annotations

import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import datetime, timezone

BUSY_TIMEOUT_SECONDS = 10.0
TIMESTAMP_FORMAT = "%Y-%m-%dT%H:%M:%S.%f+00:00"  # ancho fijo en UTC: el orden de texto es el orden temporal


def to_text(moment: datetime) -> str:
    if moment.tzinfo is None:
        moment = moment.replace(tzinfo=timezone.utc)
    return moment.astimezone(timezone.utc).strftime(TIMESTAMP_FORMAT)


def to_datetime(text: str) -> datetime:
    return datetime.fromisoformat(text)


@contextmanager
def connection(db_path: str) -> Iterator[sqlite3.Connection]:
    con = sqlite3.connect(db_path, timeout=BUSY_TIMEOUT_SECONDS)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys=ON")
    try:
        with con:
            yield con
    finally:
        con.close()


def initialize_schema(db_path: str, schema: str) -> None:
    with connection(db_path) as con:
        con.execute("PRAGMA journal_mode=WAL")
        con.executescript(schema)
