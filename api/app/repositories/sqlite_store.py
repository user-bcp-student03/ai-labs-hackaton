"""Almacén SQLite del puerto IdempotencyStorePort. Consultas parametrizadas; una conexión por operación."""
from __future__ import annotations

import sqlite3
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from datetime import datetime, timezone

from app.ports.idempotency_store import (
    OUTCOME_CREATED,
    OUTCOME_EXISTS,
    STATUS_PENDING,
    Attempt,
    NewAttempt,
    RequestFilters,
    RequestRecord,
    ReserveOutcome,
)

BUSY_TIMEOUT_SECONDS = 10.0
MAX_LISTED_ROWS = 500
TIMESTAMP_FORMAT = "%Y-%m-%dT%H:%M:%S.%f+00:00"  # ancho fijo en UTC: el orden de texto es el orden temporal

SCHEMA = """
CREATE TABLE IF NOT EXISTS payment_attempts (
    payment_id TEXT PRIMARY KEY,
    idempotency_key TEXT NOT NULL UNIQUE,
    payer_id TEXT NOT NULL,
    amount_cents INTEGER NOT NULL,
    recipient TEXT NOT NULL,
    channel TEXT NOT NULL,
    intent_id TEXT NOT NULL,
    attempt_window_index INTEGER NOT NULL,
    status TEXT NOT NULL,
    provider_payment_id TEXT,
    retry_of_payment_id TEXT REFERENCES payment_attempts(payment_id),
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_attempts_retry_of ON payment_attempts(retry_of_payment_id);

CREATE TABLE IF NOT EXISTS payment_requests (
    seq INTEGER PRIMARY KEY AUTOINCREMENT,
    request_id TEXT NOT NULL,
    correlation_id TEXT NOT NULL,
    idempotency_key TEXT NOT NULL,
    payment_id TEXT NOT NULL,
    payer_id TEXT NOT NULL,
    request_type TEXT NOT NULL CHECK (request_type IN ('original', 'duplicate')),
    requested_at TEXT NOT NULL,
    original_requested_at TEXT NOT NULL,
    retry_of_payment_id TEXT
);
CREATE INDEX IF NOT EXISTS idx_requests_key ON payment_requests(idempotency_key);
CREATE INDEX IF NOT EXISTS idx_requests_correlation ON payment_requests(correlation_id);
CREATE INDEX IF NOT EXISTS idx_requests_requested_at ON payment_requests(requested_at);

CREATE TRIGGER IF NOT EXISTS payment_requests_no_update BEFORE UPDATE ON payment_requests
BEGIN SELECT RAISE(ABORT, 'payment_requests es append-only'); END;
CREATE TRIGGER IF NOT EXISTS payment_requests_no_delete BEFORE DELETE ON payment_requests
BEGIN SELECT RAISE(ABORT, 'payment_requests es append-only'); END;
"""

REQUEST_FILTER_COLUMNS = (
    ("idempotency_key", "idempotency_key = ?"),
    ("correlation_id", "correlation_id = ?"),
    ("request_type", "request_type = ?"),
    ("payer_id", "payer_id = ?"),
)


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _to_text(moment: datetime) -> str:
    if moment.tzinfo is None:
        moment = moment.replace(tzinfo=timezone.utc)
    return moment.astimezone(timezone.utc).strftime(TIMESTAMP_FORMAT)


def _to_datetime(text: str) -> datetime:
    return datetime.fromisoformat(text)


def _attempt_from_row(row: sqlite3.Row) -> Attempt:
    return Attempt(
        payment_id=row["payment_id"], idempotency_key=row["idempotency_key"], payer_id=row["payer_id"],
        amount_cents=row["amount_cents"], recipient=row["recipient"], channel=row["channel"],
        intent_id=row["intent_id"], attempt_window_index=row["attempt_window_index"], status=row["status"],
        provider_payment_id=row["provider_payment_id"], retry_of_payment_id=row["retry_of_payment_id"],
        created_at=_to_datetime(row["created_at"]), updated_at=_to_datetime(row["updated_at"]),
    )


def _request_from_row(row: sqlite3.Row) -> RequestRecord:
    return RequestRecord(
        request_id=row["request_id"], correlation_id=row["correlation_id"],
        idempotency_key=row["idempotency_key"], payment_id=row["payment_id"], payer_id=row["payer_id"],
        request_type=row["request_type"], requested_at=_to_datetime(row["requested_at"]),
        original_requested_at=_to_datetime(row["original_requested_at"]),
        retry_of_payment_id=row["retry_of_payment_id"],
    )


class SqliteIdempotencyStore:
    def __init__(self, db_path: str, clock: Callable[[], datetime] = _utc_now) -> None:
        self._db_path = db_path
        self._clock = clock
        with self._connection() as con:
            con.execute("PRAGMA journal_mode=WAL")
            con.executescript(SCHEMA)

    @contextmanager
    def _connection(self) -> Iterator[sqlite3.Connection]:
        con = sqlite3.connect(self._db_path, timeout=BUSY_TIMEOUT_SECONDS)
        con.row_factory = sqlite3.Row
        con.execute("PRAGMA foreign_keys=ON")
        try:
            with con:
                yield con
        finally:
            con.close()

    def reserve_attempt(self, attempt: NewAttempt) -> ReserveOutcome:
        created = _to_text(attempt.created_at)
        try:
            with self._connection() as con:
                con.execute(
                    "INSERT INTO payment_attempts (payment_id, idempotency_key, payer_id, amount_cents, recipient,"
                    " channel, intent_id, attempt_window_index, status, retry_of_payment_id, created_at, updated_at)"
                    " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (attempt.payment_id, attempt.idempotency_key, attempt.payer_id, attempt.amount_cents,
                     attempt.recipient, attempt.channel, attempt.intent_id, attempt.attempt_window_index,
                     STATUS_PENDING, attempt.retry_of_payment_id, created, created),
                )
        except sqlite3.IntegrityError:
            existing = self.get_attempt_by_key(attempt.idempotency_key)
            if existing is None:
                raise
            return ReserveOutcome(OUTCOME_EXISTS, existing)
        stored = self.get_attempt(attempt.payment_id)
        return ReserveOutcome(OUTCOME_CREATED, stored)

    def update_attempt(self, payment_id: str, status: str, provider_payment_id: str | None) -> None:
        # Solo avanza desde PENDING: un resultado terminal nunca se sobrescribe (principio 10).
        with self._connection() as con:
            con.execute(
                "UPDATE payment_attempts SET status = ?, provider_payment_id = COALESCE(?, provider_payment_id),"
                " updated_at = ? WHERE payment_id = ? AND status = ?",
                (status, provider_payment_id, _to_text(self._clock()), payment_id, STATUS_PENDING),
            )

    def get_attempt(self, payment_id: str) -> Attempt | None:
        return self._fetch_attempt("payment_id = ?", payment_id)

    def get_attempt_by_key(self, idempotency_key: str) -> Attempt | None:
        return self._fetch_attempt("idempotency_key = ?", idempotency_key)

    def _fetch_attempt(self, condition: str, value: str) -> Attempt | None:
        with self._connection() as con:
            row = con.execute(f"SELECT * FROM payment_attempts WHERE {condition}", (value,)).fetchone()
        return _attempt_from_row(row) if row else None

    def list_retries_of(self, payment_id: str) -> list[Attempt]:
        with self._connection() as con:
            rows = con.execute(
                "SELECT * FROM payment_attempts WHERE retry_of_payment_id = ? ORDER BY created_at, payment_id",
                (payment_id,),
            ).fetchall()
        return [_attempt_from_row(row) for row in rows]

    def count_attempts(self) -> int:
        with self._connection() as con:
            return con.execute("SELECT COUNT(*) FROM payment_attempts").fetchone()[0]

    def append_request(self, record: RequestRecord) -> None:
        with self._connection() as con:
            con.execute(
                "INSERT INTO payment_requests (request_id, correlation_id, idempotency_key, payment_id, payer_id,"
                " request_type, requested_at, original_requested_at, retry_of_payment_id)"
                " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (record.request_id, record.correlation_id, record.idempotency_key, record.payment_id,
                 record.payer_id, record.request_type, _to_text(record.requested_at),
                 _to_text(record.original_requested_at), record.retry_of_payment_id),
            )

    def list_requests(self, filters: RequestFilters) -> list[RequestRecord]:
        conditions, params = [], []
        for attribute, condition in REQUEST_FILTER_COLUMNS:
            value = getattr(filters, attribute)
            if value is not None:
                conditions.append(condition)
                params.append(value)
        if filters.date_from is not None:
            conditions.append("requested_at >= ?")
            params.append(_to_text(filters.date_from))
        if filters.date_to is not None:
            conditions.append("requested_at <= ?")
            params.append(_to_text(filters.date_to))
        where = f" WHERE {' AND '.join(conditions)}" if conditions else ""
        with self._connection() as con:
            rows = con.execute(
                f"SELECT * FROM payment_requests{where} ORDER BY seq LIMIT ?", (*params, MAX_LISTED_ROWS)
            ).fetchall()
        return [_request_from_row(row) for row in rows]
