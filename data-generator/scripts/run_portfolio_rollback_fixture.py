"""Run an accepted-order Portfolio scale fixture and always roll it back."""

from __future__ import annotations

import argparse
import json
from dataclasses import replace
from pathlib import Path

from projectbi_generator.config import load_config
from projectbi_generator.database import connection_settings, run_rollback_incremental_full_smoke


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--orders", type=int, choices=(10_000, 50_000), required=True)
    args = parser.parse_args()
    base = load_config("portfolio")
    config = replace(base, generation={
        **base.generation,
        "sales_orders": args.orders,
        "estimated_order_items": args.orders * 22 // 10,
        "estimated_transaction_rows": args.orders * 20,
    })
    result = run_rollback_incremental_full_smoke(
        connection_settings(PROJECT_ROOT), config, include_completion=True,
    )
    sql_failures = {name: count for name, count in result["sql_invariant_counts"].items() if count}
    remaining_rows = sum(result["remaining"].values())
    successful = (
        result["server_version"].startswith("18.")
        and result["counts"]["sales_orders"] == args.orders
        and result["id_metrics"]["current_transaction_id_entries"] == 0
        and not sql_failures
        and remaining_rows == 0
    )
    report = {
        "result": "PASS" if successful else "FAIL",
        "target_accepted_orders": args.orders,
        "actual_accepted_orders": result["counts"]["sales_orders"],
        "server_major": result["server_version"].split(".", 1)[0],
        "sql_invariant_count": len(result["sql_invariant_counts"]),
        "sql_failures": sql_failures,
        "transaction_row_count": result["transaction_rows"],
        "scenario_table_counts": {
            name: result["counts"].get(name, 0)
            for name in (
                "sales_orders", "sales_order_item_cancellations", "payments",
                "payment_installments", "refunds", "stock_transfers", "returns",
                "stock_movements", "fulfillment_events",
            )
        },
        "sql_margin_metrics": result["sql_margin_metrics"],
        "id_registry_entries_after_generation": result["id_metrics"]["current_transaction_id_entries"],
        "empty_tables_verified": len(result["remaining"]),
        "remaining_rows_after_rollback": remaining_rows,
        "duration_seconds": round(result["duration_seconds"], 2),
        "cancellation_checks": result["cancellation_checks"],
    }
    print(json.dumps(report, ensure_ascii=False, indent=2, default=str))
    if not successful:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
