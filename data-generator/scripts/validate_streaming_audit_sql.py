"""Compare the discarded logical audit with SQL results in a rollback-only fixture."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from projectbi_generator.config import load_config
from projectbi_generator.database import connection_settings, run_rollback_incremental_full_smoke
from projectbi_generator.generators.completion import generate_full_transactions_incremental
from projectbi_generator.generators.master import generate_master_data

from benchmark_accepted_orders import DiscardingSink


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SQL_GATE_MAP = {
    "order_item_and_discount_totals": (
        "sales.order_total_reconciliation", "sales.discount_amount_cap",
    ),
    "fulfillment_and_cancellation_quantities": (
        "logistics.fulfillment_quantity_cap", "sales.item_resolution_cache",
        "sales.item_quantity_balance", "sales.completed_order_resolved",
        "sales.cancelled_order_integrity",
    ),
    "payment_installment_reconciliation": (
        "payments.installment_total_reconciliation", "payments.installment_method_eligibility",
    ),
    "payment_and_refund_reconciliation": (
        "payments.capture_order_reconciliation", "payments.refund_cap",
    ),
    "returns_against_original_fulfillment": (
        "returns.fulfillment_source_quantity", "returns.cumulative_fulfilled_quantity",
        "returns.inventory_destination",
    ),
    "completed_fulfillment_event_lifecycle": ("logistics.event_cutoff_state",),
    "refund_links_and_cancellation_amounts": (
        "payments.cancellation_refund_origin", "payments.cancellation_refund_reconciliation",
        "sales.cancellation_amount_reconciliation", "sales.cancellation_discount_allocation",
    ),
    "margin_cogs_and_return_loss_no_double_count": (),
    "transfer_movement_pairs": ("inventory.transfer_movement_pair",),
}


def main() -> None:
    config = load_config("smoke")
    db_result = run_rollback_incremental_full_smoke(
        connection_settings(PROJECT_ROOT), config, include_completion=True,
    )

    master = generate_master_data(config)
    sink = DiscardingSink(master)
    streamed = generate_full_transactions_incremental(config, master, sink, batch_size=config.batch_size)
    portfolio_audit = sink.summary()
    logical_audit = portfolio_audit["logical_audit"]

    count_matches = streamed.counts() == db_result["counts"]
    sql_counts = db_result["sql_invariant_counts"]
    sql_gate_results = {}
    for gate_name, check_names in SQL_GATE_MAP.items():
        missing = [name for name in check_names if name not in sql_counts]
        values = {name: sql_counts[name] for name in check_names if name in sql_counts}
        sql_gate_results[gate_name] = {
            "result": "PASS" if not missing and all(value == 0 for value in values.values()) else "FAIL",
            "checks": values,
            "missing_checks": missing,
        }

    finance_matches = {
        key: str(portfolio_audit[key]) == str(db_result["sql_margin_metrics"].get(key))
        for key in db_result["sql_margin_metrics"]
    }
    all_sql_zero = all(value == 0 for value in sql_counts.values())
    remaining_rows = sum(db_result["remaining"].values())
    result = "PASS" if (
        db_result["server_version"].startswith("18.")
        and count_matches
        and logical_audit["result"] == "PASS"
        and all(item["result"] == "PASS" for item in sql_gate_results.values())
        and all(finance_matches.values())
        and all_sql_zero
        and remaining_rows == 0
    ) else "FAIL"
    print(json.dumps({
        "result": result,
        "fixture_profile": config.profile,
        "server_major": db_result["server_version"].split(".", 1)[0],
        "accepted_orders": db_result["counts"]["sales_orders"],
        "generator_count_matches_sql_fixture": count_matches,
        "streaming_logical_audit": logical_audit,
        "sql_gate_results": sql_gate_results,
        "margin_metric_matches": finance_matches,
        "all_sql_invariants_zero": all_sql_zero,
        "sql_invariant_count": len(sql_counts),
        "remaining_rows_after_rollback": remaining_rows,
        "fixture_duration_seconds": round(db_result["duration_seconds"], 2),
    }, ensure_ascii=False, indent=2, default=str))
    if result != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
