from decimal import Decimal
from dataclasses import replace

import pytest

from projectbi_generator.supply_policy import (
    bootstrap_location_plan,
    blended_daily_demand_rate,
    largest_remainder_allocation,
    replenishment_quantity,
    transferable_surplus,
)
from projectbi_generator.config import load_config
from projectbi_generator.generators.completion import generate_full_transactions_incremental
from projectbi_generator.generators.master import generate_master_data
from projectbi_generator.sales_plan import build_sales_intent_quotas
from projectbi_generator.sinks import CollectingSink


def test_portfolio_profile_uses_homologated_supply_defaults():
    config = load_config("portfolio")
    assert config.generation["bootstrap_location_balance"] == 65
    assert config.generation["coverage_replenishment_enabled"] == 1
    assert config.generation["coverage_safety_units"] == 3
    assert config.generation["supply_transfer_enabled"] == 0
    quotas = build_sales_intent_quotas(
        accepted_target=config.sales_order_target,
        start_date=config.start_date,
        end_date=config.end_date,
        intention_cap=config.order_plan["intention_cap"],
        annual_shares_percent=config.order_plan["annual_shares_percent"],
        channel_shares_percent=config.order_plan["channel_shares_percent"],
        month_weights=config.order_plan["month_weights"],
        physical_attempt_multiplier_percent=config.order_plan["physical_attempt_multiplier_percent"],
    )
    annual = {}
    channels = {}
    monthly = {}
    for row in quotas:
        annual[row.year] = annual.get(row.year, 0) + row.accepted_orders
        channels[(row.year, row.channel_code)] = channels.get((row.year, row.channel_code), 0) + row.accepted_orders
        monthly[(row.year, row.month)] = monthly.get((row.year, row.month), 0) + row.accepted_orders
    assert annual == {2023: 24000, 2024: 30000, 2025: 36000, 2026: 30000}
    assert sum(row.accepted_orders for row in quotas) == 120000
    assert sum(row.intention_limit for row in quotas) <= config.order_plan["intention_cap"]
    assert channels[(2023, "CH-PHYSICAL")] / annual[2023] == 0.54
    assert channels[(2026, "CH-PHYSICAL")] / annual[2026] == 0.50
    assert monthly[(2025, 11)] > monthly[(2025, 1)]
    assert monthly[(2025, 12)] > monthly[(2025, 1)]
    assert not any(row.year == 2026 and row.month > 9 for row in quotas)
    assert quotas == build_sales_intent_quotas(
        accepted_target=config.sales_order_target,
        start_date=config.start_date,
        end_date=config.end_date,
        intention_cap=config.order_plan["intention_cap"],
        annual_shares_percent=config.order_plan["annual_shares_percent"],
        channel_shares_percent=config.order_plan["channel_shares_percent"],
        month_weights=config.order_plan["month_weights"],
        physical_attempt_multiplier_percent=config.order_plan["physical_attempt_multiplier_percent"],
    )


def test_accepted_quota_engine_reaches_exact_small_target():
    base = load_config("portfolio")
    generation = {
        **base.generation,
        "sales_orders": 240,
        "estimated_order_items": 528,
        "estimated_transaction_rows": 50000,
        "batch_size": 5000,
    }
    order_plan = {
        **base.order_plan,
        "intention_cap": 10000,
        "physical_attempt_multiplier_percent": {year: 700 for year in (2023, 2024, 2025, 2026)},
    }
    config = replace(base, generation=generation, order_plan=order_plan)
    sink = CollectingSink()
    result = generate_full_transactions_incremental(config, generate_master_data(config), sink)
    assert result.counts()["sales_orders"] == 240
    assert result.runtime_metrics["sales_orders_accepted"] == 240
    assert result.runtime_metrics["sales_intentions_processed"] <= result.runtime_metrics["sales_intentions_planned"]
    assert result.runtime_metrics["sales_intentions_planned"] <= order_plan["intention_cap"]
    assert len(result.runtime_metrics["sales_orders_accepted_by_year_month_channel"]) > 0


@pytest.mark.parametrize("total", [0, 1, 3, 14, 101])
def test_largest_remainder_allocation_conserves_small_and_indivisible_totals(total):
    weights = {"a": Decimal("0.52"), "b": Decimal("0.48")}
    result = largest_remainder_allocation(total, weights)
    assert sum(result.values()) == total
    assert all(value >= 0 for value in result.values())
    assert result == largest_remainder_allocation(total, weights)


def test_bootstrap_spreads_units_by_roles_and_preserves_exact_total():
    result = bootstrap_location_plan(11, ["S2", "S1"], ["W2", "W1"], 52)
    assert sum(quantity for _, quantity in result) == 11
    assert {location for location, _ in result} == {"S1", "S2", "W1", "W2"}
    assert result == bootstrap_location_plan(11, ["S1", "S2"], ["W1", "W2"], 52)


def test_bootstrap_group_shares_use_deterministic_weighted_rounding_for_indivisible_totals():
    assert largest_remainder_allocation(17, {"store": 65, "warehouse": 35}) == {
        "store": 11, "warehouse": 6,
    }
    plan = bootstrap_location_plan(3, ["S1", "S2", "S3", "S4"], ["W1", "W2"], 65)
    assert sum(quantity for _, quantity in plan) == 3
    assert all(quantity > 0 for _, quantity in plan)


def test_bootstrap_rotates_indivisible_location_remainders_by_seed_and_sku():
    stores = ["S1", "S2", "S3", "S4"]
    warehouses = ["W1", "W2"]
    first = bootstrap_location_plan(9, stores, warehouses, 65, rotation_key="seed:sku-a")
    repeated = bootstrap_location_plan(9, stores, warehouses, 65, rotation_key="seed:sku-a")
    second = bootstrap_location_plan(9, stores, warehouses, 65, rotation_key="seed:sku-b")
    assert first == repeated
    assert first != second
    assert sum(quantity for _, quantity in first) == sum(quantity for _, quantity in second) == 9


@pytest.mark.parametrize("args", [
    (-1, ["s"], ["w"], 52),
    (1, [], ["w"], 52),
    (1, ["s"], [], 52),
    (1, ["s"], ["w"], 0),
    (1, ["s"], ["w"], 100),
])
def test_bootstrap_rejects_invalid_inputs(args):
    with pytest.raises(ValueError):
        bootstrap_location_plan(*args)


def test_cold_start_rate_moves_gradually_toward_observed_demand():
    prior = Decimal("0.02")
    initial = blended_daily_demand_rate(0, 90, prior)
    updated = blended_daily_demand_rate(9, 90, prior)
    assert initial == prior * Decimal(60) / Decimal(150)
    assert updated > initial
    assert updated < Decimal("0.10")


def test_reorder_position_counts_inbound_and_open_backorders_once():
    quantity = replenishment_quantity(
        available=3, confirmed_inbound=4, backorder_units=2,
        daily_rate=Decimal("0.1"), supplier_lead_days=8, review_days=14, safety_units=2,
    )
    assert quantity == 0
    assert replenishment_quantity(
        available=0, confirmed_inbound=0, backorder_units=3,
        daily_rate=Decimal("0.1"), supplier_lead_days=8, review_days=14, safety_units=2,
    ) == 8


def test_transfer_surplus_protects_backorders_demand_during_transit_and_safety():
    assert transferable_surplus(
        available=20, backorder_units=4, daily_rate=Decimal("0.5"), transit_days=4, safety_units=3,
    ) == 11
    assert transferable_surplus(
        available=7, backorder_units=4, daily_rate=Decimal("0.5"), transit_days=4, safety_units=3,
    ) == 0


def test_combined_supply_policy_is_deterministic_across_batch_sizes():
    base = load_config("portfolio")
    master = generate_master_data(base)
    outputs = []
    for batch_size in (73, 127):
        generation = {
            **base.generation,
            "sales_orders": 1000,
            "estimated_order_items": 2200,
            "estimated_transaction_rows": 20000,
            "batch_size": batch_size,
            "bootstrap_location_balance": 65,
            "supply_transfer_enabled": 1,
            "coverage_replenishment_enabled": 1,
            "coverage_safety_units": 2,
        }
        config = replace(base, generation=generation, order_plan={"mode": "intentions"})
        sink = CollectingSink()
        result = generate_full_transactions_incremental(config, master, sink, batch_size=batch_size)
        assert result.runtime_metrics["max_buffered_rows"] <= batch_size
        assert result.runtime_metrics["unassigned_reservation_keys_final"] == 0
        outputs.append((sink.rows_by_table, result.counts()))
    assert outputs[0] == outputs[1]
