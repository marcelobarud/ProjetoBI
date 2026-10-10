"""Deterministic accepted-order quotas and bounded intention budgets."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal, ROUND_FLOOR
import random
from typing import Mapping


@dataclass(frozen=True)
class SalesIntentQuota:
    year: int
    month: int
    channel_code: str
    accepted_orders: int
    intention_limit: int


def _allocate(total: int, weights: Mapping[str, int]) -> dict[str, int]:
    if total < 0 or not weights or any(value < 0 for value in weights.values()):
        raise ValueError("Rateio de pedidos exige total e pesos não negativos.")
    weight_sum = sum(weights.values())
    if weight_sum <= 0:
        raise ValueError("Rateio de pedidos exige peso positivo.")
    keys = sorted(weights)
    raw = {key: Decimal(total) * weights[key] / weight_sum for key in keys}
    result = {key: int(value.to_integral_value(rounding=ROUND_FLOOR)) for key, value in raw.items()}
    remaining = total - sum(result.values())
    order = sorted(keys, key=lambda key: (-(raw[key] - result[key]), key))
    for key in order[:remaining]:
        result[key] += 1
    if sum(result.values()) != total:
        raise ValueError("Rateio de pedidos não conservou o total.")
    return result


def build_sales_intent_quotas(
    *,
    accepted_target: int,
    start_date: date,
    end_date: date,
    annual_shares_percent: Mapping[int, int],
    channel_shares_percent: Mapping[int, Mapping[str, int]],
    month_weights: Mapping[int, int],
    physical_attempt_multiplier_percent: Mapping[int, int],
    intention_cap: int,
) -> tuple[SalesIntentQuota, ...]:
    """Build exact accepted quotas and conservative per-cell physical attempt caps."""
    if accepted_target <= 0 or start_date > end_date or intention_cap < accepted_target:
        raise ValueError("Meta, horizonte ou limite de intenções inválido.")
    years = sorted({day.year for day in _days(start_date, end_date)})
    if set(annual_shares_percent) != set(years):
        raise ValueError("A distribuição anual deve cobrir exatamente os anos do horizonte.")
    if set(channel_shares_percent) != set(years):
        raise ValueError("A distribuição por canal deve cobrir exatamente os anos do horizonte.")
    if any(sum(channel_shares_percent[year].values()) != 100 for year in years):
        raise ValueError("Os pesos por canal devem somar 100% em cada ano.")
    if any(value <= 0 for value in month_weights.values()):
        raise ValueError("Pesos mensais devem ser positivos.")

    annual = _allocate(accepted_target, {str(year): annual_shares_percent[year] for year in years})
    quotas: list[SalesIntentQuota] = []
    for year in years:
        active_months = sorted({day.month for day in _days(start_date, end_date) if day.year == year})
        if any(month not in month_weights for month in active_months):
            raise ValueError(f"Peso mensal ausente para {year}.")
        shares = channel_shares_percent[year]
        if set(shares) != {"physical", "ecommerce", "marketplace"}:
            raise ValueError(f"Canais inválidos para {year}.")
        marketplace_split = _allocate(shares["marketplace"], {"marketplace_a": 1, "marketplace_b": 1})
        channel_weights = {
            "CH-PHYSICAL": shares["physical"],
            "CH-ECOM": shares["ecommerce"],
            "CH-MARKET-A": marketplace_split["marketplace_a"],
            "CH-MARKET-B": marketplace_split["marketplace_b"],
        }
        annual_channels = _allocate(annual[str(year)], channel_weights)
        monthly_channels = {
            (int(month), channel): quantity
            for channel, channel_total in annual_channels.items()
            for month, quantity in _allocate(
                channel_total, {str(month): month_weights[month] for month in active_months}
            ).items()
        }
        multiplier = physical_attempt_multiplier_percent.get(year)
        if multiplier is None or multiplier < 100:
            raise ValueError(f"Limite físico de tentativas inválido para {year}.")
        for month in active_months:
            for channel_code in sorted(channel_weights):
                target = monthly_channels[(month, channel_code)]
                if target <= 0:
                    continue
                attempt_limit = (
                    (target * multiplier + 99) // 100
                    if channel_code == "CH-PHYSICAL" else target
                )
                quotas.append(SalesIntentQuota(year, month, channel_code, target, attempt_limit))
    if sum(row.accepted_orders for row in quotas) != accepted_target:
        raise ValueError("Quotas mensais/por canal não reconciliaram com a meta aceita.")
    if sum(row.intention_limit for row in quotas) > intention_cap:
        raise ValueError("A soma dos limites por quota excede o teto global de intenções.")
    return tuple(quotas)


def _days(start_date: date, end_date: date):
    from datetime import timedelta

    current = start_date
    while current <= end_date:
        yield current
        current += timedelta(days=1)


class CustomerFrequencyTickets:
    """Deterministic customer assignments that preserve the approved recurrence mix."""

    def __init__(self, customer_rows, target_orders: int,
                 frequency_shares_percent: Mapping[str, Mapping[str, int]], seed: int) -> None:
        if target_orders < 0 or set(frequency_shares_percent) != {"individual", "business"}:
            raise ValueError("Plano de recorrência precisa de alvo e faixas PF/PJ.")
        buckets = {
            "one": (1, 1),
            "two_to_four": (2, 4),
            "five_to_ten": (5, 10),
            "eleven_plus": (11, 15),
        }
        rows_by_type = {
            kind: sorted(row.code for row in customer_rows if row.customer_type == kind)
            for kind in ("individual", "business")
        }
        if target_orders and any(not rows_by_type[kind] for kind in rows_by_type):
            raise ValueError("A população precisa conter clientes PF e PJ para o plano de recorrência.")
        for kind, shares in frequency_shares_percent.items():
            if (set(shares) != set(buckets) or sum(shares.values()) != 100
                    or any(not isinstance(value, int) or value < 0 for value in shares.values())):
                raise ValueError(f"Faixas de recorrência inválidas para {kind}.")

        rng = random.Random(seed)
        average_orders = {
            kind: sum(
                Decimal(frequency_shares_percent[kind][bucket]) * Decimal(low + high) / Decimal(2)
                for bucket, (low, high) in buckets.items()
            ) / Decimal(100)
            for kind in rows_by_type
        }
        type_targets = _allocate(target_orders, {
            kind: int(Decimal(len(rows_by_type[kind])) * average_orders[kind] * Decimal(10000))
            for kind in rows_by_type
        }) if target_orders else {kind: 0 for kind in rows_by_type}

        frequencies: dict[str, int] = {}
        frequency_caps: dict[str, int] = {}
        for kind in ("individual", "business"):
            target = type_targets[kind]
            if not target:
                continue
            population = rows_by_type[kind]
            active_count = min(len(population), max(1, round(Decimal(target) / average_orders[kind])))
            while True:
                bucket_counts = _allocate(active_count, frequency_shares_percent[kind])
                base_orders = sum(bucket_counts[name] * bounds[0] for name, bounds in buckets.items())
                capacity = sum(bucket_counts[name] * (bounds[1] - bounds[0]) for name, bounds in buckets.items())
                if base_orders <= target <= base_orders + capacity:
                    break
                active_count += -1 if base_orders > target else 1
                if active_count <= 0 or active_count > len(population):
                    raise ValueError(f"Não foi possível alocar frequências para {kind}.")
            rng.shuffle(population)
            cursor = 0
            adjustable: list[str] = []
            for bucket, (minimum, maximum) in buckets.items():
                codes = population[cursor:cursor + bucket_counts[bucket]]
                cursor += bucket_counts[bucket]
                rng.shuffle(codes)
                for code in codes:
                    frequencies[code] = minimum
                    frequency_caps[code] = maximum
                    if maximum > minimum:
                        adjustable.append(code)
            remaining = target - sum(frequencies[code] for code in population[:active_count])
            rng.shuffle(adjustable)
            while remaining:
                progressed = False
                for code in adjustable:
                    if frequencies[code] < frequency_caps[code]:
                        frequencies[code] += 1
                        remaining -= 1
                        progressed = True
                        if not remaining:
                            break
                if not progressed:
                    raise ValueError(f"Limite de frequência insuficiente para {kind}.")

        rounds: list[str] = []
        for ordinal in range(1, max(frequencies.values(), default=0) + 1):
            current = [code for code, frequency in frequencies.items() if frequency >= ordinal]
            rng.shuffle(current)
            rounds.extend(current)
        if len(rounds) != target_orders:
            raise ValueError("As frequências planejadas não reconciliaram com o alvo.")
        self.tickets = tuple(rounds)
        self.cursor = 0
        self.planned_by_type = type_targets

    def peek(self) -> str:
        if self.cursor >= len(self.tickets):
            raise ValueError("O limite de tickets de recorrência foi esgotado antes do fim das vendas.")
        return self.tickets[self.cursor]

    def consume(self, customer_code: str) -> None:
        if self.peek() != customer_code:
            raise ValueError("Ticket de recorrência consumido fora da ordem determinística.")
        self.cursor += 1

    @property
    def remaining(self) -> int:
        return len(self.tickets) - self.cursor
