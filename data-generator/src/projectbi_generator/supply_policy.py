"""Deterministic, causal supply-planning primitives for Portfolio experiments."""

from __future__ import annotations

import hashlib
from decimal import Decimal, ROUND_CEILING


def largest_remainder_allocation(
    total: int, weights: dict[str, Decimal | int], *, tie_breaker: str = "",
) -> dict[str, int]:
    """Allocate an integer total exactly; stable key order resolves equal remainders."""
    if total < 0 or not weights or any(weight < 0 for weight in weights.values()):
        raise ValueError("Rateio exige total não negativo e pesos não negativos.")
    weight_total = sum((Decimal(weight) for weight in weights.values()), Decimal(0))
    if weight_total <= 0:
        raise ValueError("Rateio exige ao menos um peso positivo.")
    keys = sorted(weights)
    raw = {key: Decimal(total) * Decimal(weights[key]) / weight_total for key in keys}
    allocation = {key: int(raw[key]) for key in keys}
    remainder = total - sum(allocation.values())
    offset = int.from_bytes(hashlib.sha256(tie_breaker.encode("utf-8")).digest()[:4], "big") % len(keys)
    key_rank = {key: (ordinal - offset) % len(keys) for ordinal, key in enumerate(keys)}
    order = sorted(keys, key=lambda key: (-(raw[key] - allocation[key]), key_rank[key]))
    for key in order[:remainder]:
        allocation[key] += 1
    if sum(allocation.values()) != total:
        raise ValueError("Rateio não conservou a quantidade total.")
    return allocation


def bootstrap_location_plan(
    total: int,
    store_codes: list[str],
    warehouse_codes: list[str],
    store_share_percent: int,
    *,
    rotation_key: str = "",
) -> list[tuple[str, int]]:
    """Spread opening units by channel mix, equally within each operational role."""
    if not 1 <= store_share_percent <= 99 or not store_codes or not warehouse_codes:
        raise ValueError("Bootstrap exige participação de loja entre 1–99% e ambos os tipos de local.")
    group_totals = largest_remainder_allocation(
        total,
        {"store": store_share_percent, "warehouse": 100 - store_share_percent},
        tie_breaker=f"{rotation_key}:groups",
    )
    allocation = largest_remainder_allocation(
        group_totals["store"], {code: 1 for code in sorted(store_codes)}, tie_breaker=f"{rotation_key}:stores",
    )
    allocation.update(largest_remainder_allocation(
        group_totals["warehouse"], {code: 1 for code in sorted(warehouse_codes)},
        tie_breaker=f"{rotation_key}:warehouses",
    ))
    return [(code, quantity) for code, quantity in allocation.items() if quantity]


def blended_daily_demand_rate(
    observed_units: int,
    observation_days: int,
    prior_units_per_day: Decimal,
    prior_strength_days: int = 60,
) -> Decimal:
    """Bayesian-style shrinkage from a causal cold-start prior to recent observations."""
    if observed_units < 0 or observation_days <= 0 or prior_units_per_day < 0 or prior_strength_days < 0:
        raise ValueError("Parâmetros de demanda devem ser não negativos e o período positivo.")
    denominator = Decimal(observation_days + prior_strength_days)
    return (Decimal(observed_units) + prior_units_per_day * prior_strength_days) / denominator


def replenishment_quantity(
    *,
    available: int,
    confirmed_inbound: int,
    backorder_units: int,
    daily_rate: Decimal,
    supplier_lead_days: int,
    review_days: int,
    safety_units: int,
) -> int:
    """Order to cover lead time plus one review interval, including open obligations once."""
    if min(available, confirmed_inbound, backorder_units, supplier_lead_days, review_days, safety_units) < 0:
        raise ValueError("Posição e parâmetros de reposição não podem ser negativos.")
    target = int((daily_rate * (supplier_lead_days + review_days) + safety_units).to_integral_value(
        rounding=ROUND_CEILING
    ))
    inventory_position = available + confirmed_inbound - backorder_units
    return max(0, target - inventory_position)


def transferable_surplus(
    *, available: int, backorder_units: int, daily_rate: Decimal, transit_days: int, safety_units: int,
) -> int:
    """Compute donor stock left after reservations, queued obligations, transit demand and safety stock."""
    if min(available, backorder_units, transit_days, safety_units) < 0 or daily_rate < 0:
        raise ValueError("Parâmetros de transferência não podem ser negativos.")
    protected = int((daily_rate * transit_days + safety_units).to_integral_value(rounding=ROUND_CEILING))
    return max(0, available - backorder_units - protected)
