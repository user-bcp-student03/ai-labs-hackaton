"""Fixtures compartidas. Los imports de app.* son diferidos: en fase roja fallan con ImportError dentro de cada prueba."""
import threading
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import pytest

PAYER = "TEST-payer-1"
START = datetime(2026, 11, 6, 12, 0, 0, tzinfo=timezone.utc)


class MutableClock:
    def __init__(self, start=START):
        self.current = start

    def __call__(self):
        return self.current

    def advance(self, **kwargs):
        self.current += timedelta(**kwargs)


class FakeProvider:
    """Doble de PaymentProviderPort: cuenta llamadas y devuelve resultados programables."""

    def __init__(self):
        from app.ports.payment_provider import ProviderResult

        self._result_type = ProviderResult
        self.submit_calls = []
        self.resolve_calls = []
        self.programmed = []
        self.on_submit = None
        self.resolve_status = "PENDING"
        self.resolve_fails = False
        self._lock = threading.Lock()

    def program(self, status, with_id=True):
        self.programmed.append((status, with_id))

    def submit(self, provider_idempotency_key, wallet_id, recipient, amount_cents, channel):
        with self._lock:
            self.submit_calls.append(
                dict(key=provider_idempotency_key, wallet_id=wallet_id, recipient=recipient,
                     amount_cents=amount_cents, channel=channel)
            )
            n = len(self.submit_calls)
            status, with_id = self.programmed.pop(0) if self.programmed else ("SUCCEEDED", True)
        if self.on_submit:
            self.on_submit(provider_idempotency_key)
        return self._result_type(provider_payment_id=f"fake-pay-{n}" if with_id else None, status=status)

    def resolve(self, provider_payment_id):
        from app.errors import ProviderError

        self.resolve_calls.append(provider_payment_id)
        if self.resolve_fails:
            raise ProviderError
        return self._result_type(provider_payment_id=provider_payment_id, status=self.resolve_status)


@pytest.fixture
def clock():
    return MutableClock()


@pytest.fixture
def provider():
    return FakeProvider()


@pytest.fixture
def make_settings():
    def _make(**overrides):
        from app.config import Settings

        return Settings(**overrides)

    return _make


@pytest.fixture
def db_path(tmp_path):
    return str(tmp_path / "idem.sqlite3")


@pytest.fixture
def store(db_path):
    from app.repositories.sqlite_store import SqliteIdempotencyStore

    return SqliteIdempotencyStore(db_path)


@pytest.fixture
def make_world(store, provider, clock, make_settings):
    """Cablea servicios reales sobre SQLite real y el doble del proveedor."""

    def _make(**settings_overrides):
        from app.services.container import build_services

        settings = make_settings(**settings_overrides)
        services = build_services(store, provider, settings, clock)
        return SimpleNamespace(settings=settings, provider=provider, clock=clock, **vars(services))

    return _make


@pytest.fixture
def world(make_world):
    return make_world()


@pytest.fixture
def submit():
    """Atajo para enviar un pago con valores ficticios y sobrescribir lo necesario."""
    counter = {"n": 0}

    def _submit(world, **overrides):
        counter["n"] += 1
        params = dict(payer_id=PAYER, intent_id="intent-1", amount_cents=100, recipient="merchant-demo",
                      channel="merchant-demo", request_id=f"req-{counter['n']}",
                      correlation_id=f"corr-{counter['n']}")
        params.update(overrides)
        return world.payments.submit_payment(**params)

    return _submit


@pytest.fixture
def client(store, provider, clock, make_settings):
    from fastapi.testclient import TestClient

    from app.main import create_app

    app = create_app(settings=make_settings(), provider=provider, store=store, clock=clock)
    return TestClient(app)
