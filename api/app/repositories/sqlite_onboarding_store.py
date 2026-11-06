"""Almacén SQLite del puerto OnboardingStorePort. Consultas parametrizadas; una conexión y una transacción por operación.

No persiste valores de los campos de los pasos (decisión D-5): solo el paso completado y cuándo."""
from __future__ import annotations

import sqlite3
from collections.abc import Callable
from contextlib import AbstractContextManager
from datetime import datetime, timezone

from app.errors import OnboardingNotFound
from app.ports.onboarding_store import (
    EVENT_CLOSED,
    EVENT_STARTED,
    EVENT_STEP_COMPLETED,
    EVENT_TYPES,
    NO_STEP,
    STATUS_COMPLETED,
    STATUS_IN_PROGRESS,
    WALLET_STATUS_ACTIVE,
    CloseOutcome,
    EventBoundary,
    OnboardingSession,
    StartOutcome,
    Wallet,
)
from app.repositories.sqlite_support import connection, initialize_schema, to_datetime, to_text

_EVENT_TYPE_LIST = ", ".join(f"'{event_type}'" for event_type in EVENT_TYPES)

SCHEMA = f"""
CREATE TABLE IF NOT EXISTS onboarding_sessions (
    onboarding_id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL UNIQUE,
    cohort TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('{STATUS_IN_PROGRESS}', '{STATUS_COMPLETED}')),
    started_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    closed_at TEXT
);
CREATE INDEX IF NOT EXISTS idx_onboarding_sessions_report ON onboarding_sessions(cohort, status, closed_at);

CREATE TABLE IF NOT EXISTS onboarding_step_progress (
    onboarding_id TEXT NOT NULL REFERENCES onboarding_sessions(onboarding_id),
    step_id TEXT NOT NULL,
    completed_at TEXT NOT NULL,
    PRIMARY KEY (onboarding_id, step_id)
);

CREATE TABLE IF NOT EXISTS onboarding_events (
    seq INTEGER PRIMARY KEY AUTOINCREMENT,
    onboarding_id TEXT NOT NULL REFERENCES onboarding_sessions(onboarding_id),
    user_id TEXT NOT NULL,
    cohort TEXT NOT NULL,
    event_type TEXT NOT NULL CHECK (event_type IN ({_EVENT_TYPE_LIST})),
    step_id TEXT NOT NULL DEFAULT '',
    occurred_at TEXT NOT NULL,
    UNIQUE (onboarding_id, event_type, step_id)
);
CREATE INDEX IF NOT EXISTS idx_onboarding_events_report ON onboarding_events(cohort, event_type, step_id, occurred_at);

CREATE TRIGGER IF NOT EXISTS onboarding_events_no_update BEFORE UPDATE ON onboarding_events
BEGIN SELECT RAISE(ABORT, 'onboarding_events es append-only'); END;
CREATE TRIGGER IF NOT EXISTS onboarding_events_no_delete BEFORE DELETE ON onboarding_events
BEGIN SELECT RAISE(ABORT, 'onboarding_events es append-only'); END;

CREATE TABLE IF NOT EXISTS wallets (
    user_id TEXT PRIMARY KEY,
    status TEXT NOT NULL,
    created_at TEXT NOT NULL,
    activated_at TEXT
);
"""


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _optional_datetime(text: str | None) -> datetime | None:
    return to_datetime(text) if text else None


def _session_from_row(row: sqlite3.Row) -> OnboardingSession:
    return OnboardingSession(
        onboarding_id=row["onboarding_id"], user_id=row["user_id"], cohort=row["cohort"], status=row["status"],
        started_at=to_datetime(row["started_at"]), updated_at=to_datetime(row["updated_at"]),
        closed_at=_optional_datetime(row["closed_at"]))


def _wallet_from_row(row: sqlite3.Row) -> Wallet:
    return Wallet(user_id=row["user_id"], status=row["status"], created_at=to_datetime(row["created_at"]),
                  activated_at=_optional_datetime(row["activated_at"]))


def _insert_event(con: sqlite3.Connection, onboarding_id: str, event_type: str, step_id: str,
                  occurred_at: str) -> None:
    # La identidad y la cohorte se copian de la sesión; UNIQUE + OR IGNORE deduplican en la misma transacción.
    con.execute(
        "INSERT OR IGNORE INTO onboarding_events (onboarding_id, user_id, cohort, event_type, step_id, occurred_at)"
        " SELECT onboarding_id, user_id, cohort, ?, ?, ? FROM onboarding_sessions WHERE onboarding_id = ?",
        (event_type, step_id, occurred_at, onboarding_id))


class SqliteOnboardingStore:
    def __init__(self, db_path: str, clock: Callable[[], datetime] = _utc_now) -> None:
        self._db_path = db_path
        self._clock = clock
        initialize_schema(db_path, SCHEMA)

    def _connection(self) -> AbstractContextManager[sqlite3.Connection]:
        return connection(self._db_path)

    def start_onboarding(self, onboarding_id: str, user_id: str, cohort: str,
                         wallet_pending_status: str) -> StartOutcome:
        now = to_text(self._clock())
        with self._connection() as con:
            created = self._insert_session(con, onboarding_id, user_id, cohort, now)
            if created:
                con.execute("INSERT INTO wallets (user_id, status, created_at) VALUES (?, ?, ?)",
                            (user_id, wallet_pending_status, now))
                _insert_event(con, onboarding_id, EVENT_STARTED, NO_STEP, now)
        session = self.get_session(onboarding_id) if created else self.get_session_by_user(user_id)
        if session is None:
            raise sqlite3.IntegrityError("onboarding_id duplicado")
        return StartOutcome(session=session, created=created)

    @staticmethod
    def _insert_session(con: sqlite3.Connection, onboarding_id: str, user_id: str, cohort: str, now: str) -> bool:
        try:
            con.execute(
                "INSERT INTO onboarding_sessions (onboarding_id, user_id, cohort, status, started_at, updated_at)"
                " VALUES (?, ?, ?, ?, ?, ?)", (onboarding_id, user_id, cohort, STATUS_IN_PROGRESS, now, now))
        except sqlite3.IntegrityError:
            return False  # UNIQUE(user_id): el usuario ya tiene su sesión y se reanuda (Q-11)
        return True

    def get_session(self, onboarding_id: str) -> OnboardingSession | None:
        return self._fetch_session("onboarding_id = ?", onboarding_id)

    def get_session_by_user(self, user_id: str) -> OnboardingSession | None:
        return self._fetch_session("user_id = ?", user_id)

    def _fetch_session(self, condition: str, value: str) -> OnboardingSession | None:
        with self._connection() as con:
            row = con.execute(f"SELECT * FROM onboarding_sessions WHERE {condition}", (value,)).fetchone()
        return _session_from_row(row) if row else None

    def get_wallet(self, user_id: str) -> Wallet | None:
        with self._connection() as con:
            row = con.execute("SELECT * FROM wallets WHERE user_id = ?", (user_id,)).fetchone()
        return _wallet_from_row(row) if row else None

    def list_completed_step_ids(self, onboarding_id: str) -> list[str]:
        with self._connection() as con:
            rows = con.execute(
                "SELECT step_id FROM onboarding_step_progress WHERE onboarding_id = ? ORDER BY completed_at, rowid",
                (onboarding_id,)).fetchall()
        return [row["step_id"] for row in rows]

    def record_step_completed(self, onboarding_id: str, step_id: str) -> bool:
        now = to_text(self._clock())
        with self._connection() as con:
            inserted = con.execute(
                "INSERT OR IGNORE INTO onboarding_step_progress (onboarding_id, step_id, completed_at)"
                " VALUES (?, ?, ?)", (onboarding_id, step_id, now)).rowcount == 1
            if inserted:
                con.execute("UPDATE onboarding_sessions SET updated_at = ? WHERE onboarding_id = ?",
                            (now, onboarding_id))
                _insert_event(con, onboarding_id, EVENT_STEP_COMPLETED, step_id, now)
        return inserted

    def close_onboarding(self, onboarding_id: str) -> CloseOutcome:
        now = to_text(self._clock())
        with self._connection() as con:
            # Solo una solicitud gana la transición IN_PROGRESS -> COMPLETED; ella activa la wallet y emite el evento.
            closed_now = con.execute(
                "UPDATE onboarding_sessions SET status = ?, closed_at = ?, updated_at = ?"
                " WHERE onboarding_id = ? AND status = ?",
                (STATUS_COMPLETED, now, now, onboarding_id, STATUS_IN_PROGRESS)).rowcount == 1
            if closed_now:
                con.execute(
                    "UPDATE wallets SET status = ?, activated_at = ? WHERE user_id ="
                    " (SELECT user_id FROM onboarding_sessions WHERE onboarding_id = ?)",
                    (WALLET_STATUS_ACTIVE, now, onboarding_id))
                _insert_event(con, onboarding_id, EVENT_CLOSED, NO_STEP, now)
        session = self.get_session(onboarding_id)
        if session is None:
            raise OnboardingNotFound
        return CloseOutcome(session=session, closed_now=closed_now)

    def count_closed_between(self, cohort: str, start: datetime, end: datetime) -> int:
        with self._connection() as con:
            return con.execute(
                "SELECT COUNT(*) FROM onboarding_sessions WHERE cohort = ? AND status = ?"
                " AND closed_at >= ? AND closed_at < ?",
                (cohort, STATUS_COMPLETED, to_text(start), to_text(end))).fetchone()[0]

    def list_event_intervals(self, cohort: str, start: EventBoundary, end: EventBoundary,
                             end_from: datetime, end_to: datetime) -> list[tuple[datetime, datetime]]:
        with self._connection() as con:
            rows = con.execute(
                "SELECT s.occurred_at AS started_at, e.occurred_at AS ended_at FROM onboarding_events e"
                " JOIN onboarding_events s ON s.onboarding_id = e.onboarding_id"
                " WHERE e.cohort = ? AND e.event_type = ? AND e.step_id = ? AND s.event_type = ? AND s.step_id = ?"
                " AND e.occurred_at >= ? AND e.occurred_at < ? ORDER BY e.seq",
                (cohort, end.event_type, end.step_id, start.event_type, start.step_id,
                 to_text(end_from), to_text(end_to))).fetchall()
        return [(to_datetime(row["started_at"]), to_datetime(row["ended_at"])) for row in rows]
