"""Run reproducible in-memory supply-policy variants; never opens a database."""

from __future__ import annotations

import argparse
import json
from dataclasses import replace
from decimal import Decimal

from projectbi_generator.config import load_config
from projectbi_generator.generators.completion import generate_full_transactions_incremental
from projectbi_generator.generators.master import generate_master_data
from projectbi_generator.sinks import CollectingSink


_CONTROL = {
    "bootstrap_location_balance": 0,
    "supply_transfer_enabled": 0,
    "coverage_replenishment_enabled": 0,
    "coverage_safety_units": 1,
}


def _policy(**overrides: int) -> dict[str, int]:
    return {**_CONTROL, **overrides}


VARIANTS = {
    "control": _policy(),
    "bootstrap_40_store_share": _policy(bootstrap_location_balance=40),
    "bootstrap_52_store_share": _policy(bootstrap_location_balance=52),
    "bootstrap_65_store_share": _policy(bootstrap_location_balance=65),
    "bootstrap_plus_transfers": _policy(bootstrap_location_balance=52, supply_transfer_enabled=1),
    "bootstrap_plus_coverage": _policy(bootstrap_location_balance=52, coverage_replenishment_enabled=1),
    "bootstrap_65_plus_coverage": _policy(bootstrap_location_balance=65, coverage_replenishment_enabled=1),
    "bootstrap_65_coverage_safety2": _policy(
        bootstrap_location_balance=65, coverage_replenishment_enabled=1, coverage_safety_units=2,
    ),
    "bootstrap_65_coverage_safety3": _policy(
        bootstrap_location_balance=65, coverage_replenishment_enabled=1, coverage_safety_units=3,
    ),
    "bootstrap_65_coverage_safety4": _policy(
        bootstrap_location_balance=65, coverage_replenishment_enabled=1, coverage_safety_units=4,
    ),
    "bootstrap_65_plus_transfers": _policy(bootstrap_location_balance=65, supply_transfer_enabled=1),
    "bootstrap_65_combined": _policy(
        bootstrap_location_balance=65, supply_transfer_enabled=1, coverage_replenishment_enabled=1,
    ),
    "bootstrap_65_combined_safety2": _policy(
        bootstrap_location_balance=65, supply_transfer_enabled=1,
        coverage_replenishment_enabled=1, coverage_safety_units=2,
    ),
    "combined": _policy(
        bootstrap_location_balance=52, supply_transfer_enabled=1, coverage_replenishment_enabled=1,
    ),
}


def run_variant(base_config, master, name: str, overrides: dict, orders: int) -> dict:
    generation = {
        **base_config.generation,
        "sales_orders": orders,
        "estimated_order_items": orders * 2.2,
        "estimated_transaction_rows": max(20000, orders * 18),
        "stock_audit": 1,
        **overrides,
    }
    config = replace(base_config, generation=generation, order_plan={"mode": "intentions"})
    sink = CollectingSink()
    result = generate_full_transactions_incremental(config, master, sink, batch_size=config.batch_size)
    metrics = result.runtime_metrics
    audit = metrics["stock_audit_summary"]
    statuses = {status: sum(order.status == status for order in sink.rows_by_table["sales_orders"])
                for status in ("completed", "cancelled", "confirmed")}
    order_by_key = {row.key: row for row in sink.rows_by_table["sales_orders"]}
    fulfilled_by_order: dict[str, int] = {}
    for item in sink.rows_by_table["fulfillment_items"]:
        fulfilled_by_order[item.order_key] = fulfilled_by_order.get(item.order_key, 0) + item.fulfilled_quantity
    cancelled_order_keys = {row.order_key for row in sink.rows_by_table.get("sales_order_item_cancellations", ())}
    fulfilled_and_cancelled = {key for key in cancelled_order_keys if fulfilled_by_order.get(key, 0) > 0}
    movement_types: dict[str, int] = {}
    for row in sink.rows_by_table["stock_movements"]:
        movement_types[row.movement_type] = movement_types.get(row.movement_type, 0) + 1
    opening_by_sku = {}
    opening_by_role = {"store": 0, "warehouse": 0}
    location_type = {row.code: row.location_type for row in master.stock_locations}
    receipts = {row.key: row for row in sink.rows_by_table["goods_receipts"]}
    purchase_items = {row.key: row for row in sink.rows_by_table["purchase_order_items"]}
    purchases = {row.key: row for row in sink.rows_by_table["purchase_orders"]}
    for row in sink.rows_by_table["goods_receipt_items"]:
        receipt = receipts.get(row.receipt_key)
        po_item = purchase_items.get(row.order_item_key)
        purchase = purchases.get(po_item.order_key) if po_item else None
        if receipt and purchase and receipt.received_at.date() < config.start_date:
            opening_by_sku[po_item.product_sku] = opening_by_sku.get(po_item.product_sku, 0) + row.accepted_quantity
            opening_by_role[location_type[receipt.location_code]] += row.accepted_quantity

    return {
        "variant": name,
        "overrides": overrides,
        "orders_target_intentions": orders,
        "orders_accepted": result.counts()["sales_orders"],
        "orders_by_status": statuses,
        "sales_intention_digest": metrics.get("sales_intention_digest"),
        "physical_intents_unconverted": metrics.get("physical_intents_unconverted", 0),
        "physical_lost_units": sum(row.get("physical_demand_lost_units", 0) for row in audit["by_year_channel"]),
        "physical_lost_by_store": [row for row in audit["by_store"] if row.get("physical_demand_lost_units", 0)],
        "physical_lost_by_year_channel": [row for row in audit["by_year_channel"]
                                          if row.get("physical_demand_lost_units", 0)],
        "partial_backorder_orders_expired": metrics.get("stock_wait_expired_partial_orders", 0),
        "partial_backorder_units_expired": metrics.get("cancelled_backorder_units", 0),
        "backorder_units_fulfilled": metrics.get("stock_backorder_units_fulfilled", 0),
        "backorder_orders_at_cutoff": metrics.get("stock_backorder_orders_at_cutoff", 0),
        "full_stock_timeout_orders": metrics.get("stock_wait_expired_orders", 0),
        "cancelled_item_rows": result.counts()["sales_order_item_cancellations"],
        "orders_with_partial_fulfillment_and_cancel": len(fulfilled_and_cancelled),
        "completed_orders_with_partial_fulfillment_and_cancel": sum(
            order_by_key[key].status == "completed" for key in fulfilled_and_cancelled
        ),
        "transfer_rows": result.counts()["stock_transfer_items"],
        "policy_transfer_rows": metrics.get("supply_policy_transfers", 0),
        "policy_transfer_units": metrics.get("supply_policy_transfer_units", 0),
        "transfer_days_total": metrics.get("supply_policy_transfer_days_total", 0),
        "movement_types": movement_types,
        "purchases": result.counts()["purchase_orders"],
        "receipts": result.counts()["goods_receipts"],
        "purchase_units_ordered": sum(row.quantity_ordered for row in sink.rows_by_table["purchase_order_items"]),
        "receipt_units_accepted": sum(row.accepted_quantity for row in sink.rows_by_table["goods_receipt_items"]),
        "bootstrap_opening_units": audit["total_opening_units"],
        "bootstrap_opening_units_by_sku": opening_by_sku,
        "bootstrap_opening_units_by_role": opening_by_role,
        "ending_on_hand_units": audit["total_ending_on_hand"],
        "unused_ending_units": audit["unused_ending_available_units"],
        "average_available_units": audit["average_available_units"],
        "stockout_days_sum": audit["total_stockout_days"],
        "stockout_episodes": audit["stockout_episode_count"],
        "mean_supplier_lead_days": audit["total_supplier_lead_time_mean_days"],
        "max_supplier_lead_days": audit["total_supplier_lead_time_max_days"],
        "max_active_backorder_orders": metrics.get("max_stock_backorder_orders", 0),
        "max_active_orders": metrics.get("max_active_orders", 0),
        "max_active_transfers": metrics.get("max_active_transfers", 0),
        "max_events": metrics.get("transaction_events_max_pending", 0),
        "aggregates": {key: value for key, value in result.aggregates.items()
                       if isinstance(value, (int, float, Decimal))},
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--orders", type=int, default=10000)
    args = parser.parse_args()
    if args.orders <= 0:
        parser.error("--orders deve ser positivo")
    config = load_config("portfolio")
    master = generate_master_data(config)
    report = [run_variant(config, master, name, overrides, args.orders)
              for name, overrides in VARIANTS.items()]
    baseline_opening = report[0]["bootstrap_opening_units_by_sku"]
    intention_digests = {result["sales_intention_digest"] for result in report}
    if len(intention_digests) != 1:
        raise ValueError("O universo de intenções de venda divergiu entre variantes.")
    for result in report:
        if result["variant"].startswith("bootstrap_") or result["variant"] == "combined":
            if result["bootstrap_opening_units_by_sku"] != baseline_opening:
                raise ValueError(f"Bootstrap por SKU divergiu do controle em {result['variant']}.")
    print(json.dumps(report, ensure_ascii=False, indent=2, default=str))


if __name__ == "__main__":
    main()
