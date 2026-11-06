"""Puerto del proveedor de pagos (riel). Cualquier implementación debe respetar este contrato."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

PROVIDER_PENDING = "PENDING"
PROVIDER_SUCCEEDED = "SUCCEEDED"
PROVIDER_REJECTED = "REJECTED"
PROVIDER_UNCERTAIN = "UNCERTAIN"


@dataclass(frozen=True)
class ProviderResult:
    provider_payment_id: str | None
    status: str


class PaymentProviderPort(Protocol):
    def submit(self, provider_idempotency_key: str, wallet_id: str, recipient: str,
               amount_cents: int, channel: str) -> ProviderResult: ...

    def resolve(self, provider_payment_id: str) -> ProviderResult: ...
