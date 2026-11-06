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
        self.resolve_calls.append(provider_payment_id)
        return self._result_type(provider_payment_id=provider_payment_id, status="SUCCEEDED")


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
        from app.services.payment_service import PaymentService
        from app.services.request_audit_service import RequestAuditService
        from app.services.retry_service import RetryService

        settings = make_settings(**settings_overrides)
        return SimpleNamespace(
            settings=settings, store=store, provider=provider, clock=clock,
            payments=PaymentService(store=store, provider=provider, settings=settings, clock=clock),
            retries=RetryService(store=store, provider=provider, settings=settings, clock=clock),
            audit=RequestAuditService(store=store),
        )

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


# ---------------------------------------------------------------------------
# HU-ONB (user-onboarding-mvp-completion): fixtures nuevos. Los anteriores no cambian.
# Los imports de app.* son diferidos: en fase roja fallan dentro de cada prueba.
# ---------------------------------------------------------------------------
ONB_USER = "TEST-user-1"
ONB_OTHER_USER = "TEST-user-2"
ANALYTICS_TOKEN = "TEST-analytics-token"

# Copia de prueba de la configuración de la sección 6.3 del diseño (independiente de api/config/).
ONB_EXAMPLE_FLOW = {
    "schema_version": 1,
    "flow_id": "onboarding-ejemplo",
    "approval_status": "example_not_approved",
    "label": "Ejemplo no aprobado: estos pasos son solo para demostración y pruebas; "
             "no son requisitos de KYC ni regulatorios.",
    "steps": [
        {
            "id": "datos-personales", "order": 1,
            "title": "Tus datos (ejemplo no aprobado)",
            "description": "Completa tus datos para continuar.",
            "fields": [
                {"name": "full_name", "type": "text", "label": "Nombre completo", "required": True,
                 "required_message": "Escribe tu nombre completo.",
                 "autocomplete": "name", "input_mode": "text",
                 "rules": [
                     {"kind": "max_length", "value": 100,
                      "message": "Acorta tu nombre a 100 caracteres como máximo."},
                     {"kind": "pattern", "value": "[A-Za-zÁÉÍÓÚÜÑáéíóúüñ' .-]{2,100}",
                      "message": "Usa solo letras y espacios; por ejemplo: Ana Torres."},
                 ]},
                {"name": "document_number", "type": "text", "label": "Número de documento de prueba",
                 "hint": "Formato de prueba: TEST- seguido de letras o números, por ejemplo TEST-12345.",
                 "required": True, "required_message": "Escribe el número de documento de prueba.",
                 "input_mode": "text",
                 "rules": [
                     {"kind": "max_length", "value": 25,
                      "message": "Acorta el documento a 25 caracteres como máximo."},
                     {"kind": "pattern", "value": "TEST-[A-Za-z0-9]{1,20}",
                      "message": "Escribe el documento de prueba con el formato TEST-12345."},
                 ]},
            ],
        },
        {
            "id": "contacto", "order": 2,
            "title": "Contacto (ejemplo no aprobado)",
            "fields": [
                {"name": "phone", "type": "text", "label": "Celular", "hint": "9 dígitos, sin espacios.",
                 "required": True, "required_message": "Escribe tu número de celular.",
                 "autocomplete": "tel-national", "input_mode": "tel",
                 "rules": [
                     {"kind": "max_length", "value": 9,
                      "message": "El celular tiene 9 dígitos; elimina los sobrantes."},
                     {"kind": "pattern", "value": "9[0-9]{8}",
                      "message": "Escribe 9 dígitos que empiecen con 9; por ejemplo: 912345678."},
                 ]},
            ],
        },
        {
            "id": "aceptacion", "order": 3,
            "title": "Confirmación (ejemplo no aprobado)",
            "fields": [
                {"name": "accept_terms", "type": "checkbox", "label": "Acepto los términos de ejemplo",
                 "required": True,
                 "required_message": "Marca la casilla para aceptar los términos y continuar."},
            ],
        },
    ],
}

# Valores válidos por paso para los dos flujos de prueba (ejemplo y alterno).
ONB_VALID_VALUES = {
    "datos-personales": {"full_name": "Ana Torres", "document_number": "TEST-12345"},
    "contacto": {"phone": "912345678"},
    "aceptacion": {"accept_terms": True},
    "bienvenida": {"accept_notice": True},
    "perfil": {"nickname": "ana2026"},
}


@pytest.fixture
def tests_data_dir():
    from pathlib import Path

    return Path(__file__).parent / "data"


@pytest.fixture
def example_flow_raw():
    import copy

    return copy.deepcopy(ONB_EXAMPLE_FLOW)


@pytest.fixture
def example_flow(example_flow_raw):
    from app.services.flow_config import parse_flow_definition

    return parse_flow_definition(example_flow_raw)


@pytest.fixture
def alternate_flow(tests_data_dir):
    from app.services.flow_config import load_flow_definition

    return load_flow_definition(str(tests_data_dir / "onboarding-flow-alternate.json"))


@pytest.fixture(params=["example", "alternate"])
def any_flow(request, example_flow, alternate_flow):
    return example_flow if request.param == "example" else alternate_flow


@pytest.fixture
def valid_values():
    return ONB_VALID_VALUES


@pytest.fixture
def events_of(db_path):
    """Lee onboarding_events directamente del archivo SQLite (tabla de la sección 7 del diseño)."""
    import sqlite3

    def _events(onboarding_id=None):
        con = sqlite3.connect(db_path)
        con.row_factory = sqlite3.Row
        try:
            if onboarding_id is None:
                rows = con.execute("SELECT * FROM onboarding_events ORDER BY seq").fetchall()
            else:
                rows = con.execute("SELECT * FROM onboarding_events WHERE onboarding_id = ? ORDER BY seq",
                                   (onboarding_id,)).fetchall()
        finally:
            con.close()
        return [dict(row) for row in rows]

    return _events


@pytest.fixture
def make_onboarding_world(db_path, clock, make_settings, example_flow):
    """Servicios reales de onboarding sobre SQLite real (sin doble del almacén)."""

    def _make(flow=None, onboarding_store=None, **onboarding_overrides):
        from dataclasses import replace

        from app.repositories.sqlite_onboarding_store import SqliteOnboardingStore
        from app.services.onboarding_analytics_service import OnboardingAnalyticsService
        from app.services.onboarding_service import OnboardingService
        from app.services.wallet_access_service import WalletAccessService

        flow = flow or example_flow
        base = make_settings(db_path=db_path)
        settings = replace(base, onboarding=replace(base.onboarding, **onboarding_overrides))
        onb_store = onboarding_store or SqliteOnboardingStore(db_path, clock=clock)
        return SimpleNamespace(
            settings=settings, flow=flow, store=onb_store, clock=clock, db_path=db_path,
            onboarding=OnboardingService(store=onb_store, flow=flow, settings=settings, clock=clock),
            wallet_access=WalletAccessService(store=onb_store),
            analytics=OnboardingAnalyticsService(store=onb_store, settings=settings),
        )

    return _make


@pytest.fixture
def onboarding_world(make_onboarding_world):
    return make_onboarding_world()


@pytest.fixture
def drive(valid_values):
    """Recorre el flujo con valores válidos: inicia, completa `count` pasos (todos si None) y opcionalmente cierra."""

    def _drive(world, user_id=ONB_USER, count=None, close=True, minutes_between=0):
        state = world.onboarding.start_or_resume(user_id).onboarding
        step_ids = [step.id for step in world.flow.steps]
        for step_id in step_ids if count is None else step_ids[:count]:
            world.clock.advance(minutes=minutes_between)
            state = world.onboarding.submit_step(user_id, state.onboarding_id, step_id, valid_values[step_id])
        if close:
            world.clock.advance(minutes=minutes_between)
            state = world.onboarding.close(user_id, state.onboarding_id)
        return state

    return _drive


@pytest.fixture
def make_onb_client(db_path, store, provider, clock, make_settings, example_flow):
    """Cliente HTTP con onboarding habilitado; el almacén de onboarding por defecto comparte db_path."""

    def _make(flow=None, analytics_token=ANALYTICS_TOKEN, **onboarding_overrides):
        from dataclasses import replace

        from fastapi.testclient import TestClient

        from app.main import create_app

        base = make_settings(db_path=db_path)
        onboarding = replace(base.onboarding, analytics_token=analytics_token, **onboarding_overrides)
        settings = replace(base, onboarding=onboarding)
        app = create_app(settings=settings, provider=provider, store=store, clock=clock,
                         onboarding_flow=flow or example_flow)
        return TestClient(app)

    return _make


@pytest.fixture
def onb_client(make_onb_client):
    return make_onb_client()
