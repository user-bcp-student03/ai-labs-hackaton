"""Acceso al punto de entrada de pagos de bajo monto según el estado de la wallet (tarea 4.2; req. 'Activación').
No se condiciona POST /payments (decisión Q-1): solo se entrega el servicio y la dependencia require_active_wallet."""
from types import SimpleNamespace

import pytest

USER = "TEST-user-1"
OTHER = "TEST-user-2"


def test_usuario_sin_onboarding_ni_wallet_no_esta_activo(onboarding_world):
    # Diseño 7.1: un usuario sin fila en wallets se trata como no activo
    assert onboarding_world.wallet_access.is_active(USER) is False


def test_wallet_pendiente_no_da_acceso(onboarding_world):
    # Escenario: Onboarding incompleto (denegado)
    from app.errors import WalletNotActive

    onboarding_world.onboarding.start_or_resume(USER)
    assert onboarding_world.wallet_access.is_active(USER) is False
    with pytest.raises(WalletNotActive):
        onboarding_world.wallet_access.require_active(USER)


def test_wallet_activa_da_acceso(onboarding_world, drive):
    # Escenario: Acceso al punto de entrada de pagos de bajo monto (permitido)
    drive(onboarding_world)
    assert onboarding_world.wallet_access.is_active(USER) is True
    assert onboarding_world.wallet_access.require_active(USER) is None


def test_pasos_completados_sin_cierre_no_dan_acceso(onboarding_world, drive):
    # Escenario: Onboarding incompleto / La wallet no pasa a activo mientras el onboarding no finalice
    from app.errors import WalletNotActive

    drive(onboarding_world, close=False)
    with pytest.raises(WalletNotActive):
        onboarding_world.wallet_access.require_active(USER)


def test_el_acceso_es_por_usuario(onboarding_world, drive):
    # Principio 17: autorización ligada a la identidad
    drive(onboarding_world, user_id=USER)
    onboarding_world.onboarding.start_or_resume(OTHER)
    assert onboarding_world.wallet_access.is_active(USER) is True
    assert onboarding_world.wallet_access.is_active(OTHER) is False


def test_estado_previo_configurable_tampoco_da_acceso(make_onboarding_world):
    # OQ-23: solo el estado 'activo' (fijo por la spec) habilita el acceso
    world = make_onboarding_world(wallet_pending_status="en-revision")
    world.onboarding.start_or_resume(USER)
    assert world.wallet_access.is_active(USER) is False


def _probe_app(wallet_access):
    from fastapi import Depends, FastAPI

    from app.routes.wallet import require_active_wallet

    app = FastAPI()
    app.state.services = SimpleNamespace(wallet_access=wallet_access)

    @app.get("/probe", dependencies=[Depends(require_active_wallet)])
    def probe():
        return {"ok": True}

    return app


def test_dependencia_require_active_wallet_permite_con_wallet_activa(onboarding_world, drive):
    # Tarea 4.2: la dependencia que PAYER aplicará a su punto de entrada
    from fastapi.testclient import TestClient

    drive(onboarding_world)
    response = TestClient(_probe_app(onboarding_world.wallet_access)).get("/probe", headers={"X-Payer-Id": USER})
    assert response.status_code == 200


def test_dependencia_require_active_wallet_responde_403_sin_wallet_activa(onboarding_world):
    from fastapi.testclient import TestClient

    onboarding_world.onboarding.start_or_resume(USER)
    client = TestClient(_probe_app(onboarding_world.wallet_access))
    for user in (USER, "TEST-sin-onboarding"):
        response = client.get("/probe", headers={"X-Payer-Id": user})
        assert response.status_code == 403
        assert response.json()["detail"]["code"] == "WALLET_NOT_ACTIVE"
        assert response.json()["detail"]["next_action"] == "complete_onboarding"


def test_dependencia_require_active_wallet_exige_identidad(onboarding_world):
    from fastapi.testclient import TestClient

    response = TestClient(_probe_app(onboarding_world.wallet_access)).get("/probe")
    assert response.status_code == 401
