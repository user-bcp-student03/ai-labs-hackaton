"""Rutas de wallet: GET /wallet, GET /wallet/payments-entry y la dependencia `require_active_wallet`."""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.errors import WalletNotActive
from app.routes.dependencies import RequestContext, request_context
from app.routes.onboarding import configured_service, error_detail, http_error
from app.schemas_onboarding import PaymentsEntryView, WalletView
from app.services.wallet_access_service import WalletAccessService

NEXT_ACTION_COMPLETE_ONBOARDING = "complete_onboarding"

router = APIRouter()
Context = Annotated[RequestContext, Depends(request_context)]
AccessService = Annotated[WalletAccessService, Depends(configured_service("wallet_access"))]


def require_active_wallet(access: AccessService, context: Context) -> None:
    """Dependencia reutilizable: PAYER la aplica a su punto de entrada de pagos (Q-1)."""
    try:
        access.require_active(context.payer_id)
    except WalletNotActive:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=error_detail("WALLET_NOT_ACTIVE", "Completa tu registro para acceder a los pagos.",
                                next_action=NEXT_ACTION_COMPLETE_ONBOARDING)) from None


@router.get("/wallet", response_model=WalletView)
def get_wallet(access: AccessService, context: Context):
    wallet = access.wallet_of(context.payer_id)
    if wallet is None:
        raise http_error((status.HTTP_404_NOT_FOUND, "WALLET_NOT_FOUND", "Aún no tienes una wallet."))
    return WalletView(status=wallet.status, activated_at=wallet.activated_at)


@router.get("/wallet/payments-entry", response_model=PaymentsEntryView,
            dependencies=[Depends(require_active_wallet)])
def payments_entry():
    return PaymentsEntryView(allowed=True)
