"""Acceso al punto de entrada de pagos de bajo monto según el estado de la wallet (Q-1: no condiciona POST /payments)."""
from __future__ import annotations

from app.errors import WalletNotActive
from app.ports.onboarding_store import WALLET_STATUS_ACTIVE, OnboardingStorePort, Wallet


class WalletAccessService:
    def __init__(self, store: OnboardingStorePort) -> None:
        self._store = store

    def wallet_of(self, user_id: str) -> Wallet | None:
        return self._store.get_wallet(user_id)

    def is_active(self, user_id: str) -> bool:
        wallet = self.wallet_of(user_id)  # sin fila en wallets el usuario no está activo
        return wallet is not None and wallet.status == WALLET_STATUS_ACTIVE

    def require_active(self, user_id: str) -> None:
        if not self.is_active(user_id):
            raise WalletNotActive
