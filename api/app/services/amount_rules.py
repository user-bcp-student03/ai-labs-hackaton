"""Regla de monto bajo por canal (OQ-15 abierta: el límite viene de configuración, sin valor fijo)."""
from __future__ import annotations

from app.config import Settings
from app.errors import AmountExceedsLimit

CENTS_PER_SOL = 100
CURRENCY_SYMBOL = "S/"


def ensure_amount_within_limit(settings: Settings, channel: str, amount_cents: int) -> None:
    limit = settings.amount_limit_for(channel)
    if limit is not None and amount_cents > limit:
        raise AmountExceedsLimit(limit)


def format_amount(cents: int) -> str:
    return f"{CURRENCY_SYMBOL} {cents // CENTS_PER_SOL}.{cents % CENTS_PER_SOL:02d}"
