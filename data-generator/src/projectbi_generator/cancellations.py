"""Deterministic item-cancellation money and captured-payment allocation."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP
from collections.abc import Iterable

CENT = Decimal("0.01")


def money(value: Decimal) -> Decimal:
    return value.quantize(CENT, rounding=ROUND_HALF_UP)


def discount_slice(total_discount: Decimal, original_quantity: int, offset: int, quantity: int) -> Decimal:
    """Allocate cents to stable unit ordinals, then return one contiguous slice."""
    if original_quantity <= 0 or offset < 0 or quantity <= 0 or offset + quantity > original_quantity:
        raise ValueError("Faixa de unidades inválida para rateio do desconto.")
    cents = int((money(total_discount) * 100).to_integral_value(rounding=ROUND_HALF_UP))
    if cents < 0:
        raise ValueError("Desconto original não pode ser negativo.")
    base, remainder = divmod(cents, original_quantity)
    extra_start, extra_end = max(offset, 0), min(offset + quantity, remainder)
    extra = max(0, extra_end - extra_start)
    return Decimal(base * quantity + extra).scaleb(-2).quantize(CENT)


def cancellation_amounts(
    unit_price: Decimal,
    original_quantity: int,
    total_discount: Decimal,
    offset: int,
    quantity: int,
) -> tuple[Decimal, Decimal, Decimal]:
    if unit_price < 0:
        raise ValueError("Preço unitário não pode ser negativo.")
    gross = money(unit_price * quantity)
    discount = discount_slice(total_discount, original_quantity, offset, quantity)
    if discount > gross:
        raise ValueError("Desconto rateado excede o bruto cancelado.")
    return gross, discount, money(gross - discount)


def allocate_refund(
    amount: Decimal,
    captured: Iterable[tuple[str, Decimal, Decimal, datetime]],
) -> list[tuple[str, Decimal]]:
    """Consume refundable capture balances by capture time, then stable payment key."""
    remaining = money(amount)
    if remaining < 0:
        raise ValueError("Valor de refund não pode ser negativo.")
    candidates = sorted(captured, key=lambda row: (row[3], row[0]))
    allocations: list[tuple[str, Decimal]] = []
    for payment_key, captured_amount, already_refunded, _captured_at in candidates:
        available = money(captured_amount - already_refunded)
        part = min(remaining, available)
        if part > 0:
            allocations.append((payment_key, part))
            remaining = money(remaining - part)
        if remaining == 0:
            break
    if remaining:
        raise ValueError("Refund solicitado excede os saldos capturados reembolsáveis.")
    return allocations
