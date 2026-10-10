"""Measure incremental Portfolio Python-heap use without retaining transaction rows."""

from __future__ import annotations

import gc
import json
import platform
import tracemalloc
from dataclasses import replace
from time import perf_counter

from projectbi_generator.config import load_config
from projectbi_generator.generators.completion import generate_full_transactions_incremental
from projectbi_generator.generators.master import generate_master_data


VARIANTS = {
    "control": {
        "bootstrap_location_balance": 0,
        "supply_transfer_enabled": 0,
        "coverage_replenishment_enabled": 0,
        "coverage_safety_units": 1,
    },
    "bootstrap_65": {
        "bootstrap_location_balance": 65,
        "supply_transfer_enabled": 0,
        "coverage_replenishment_enabled": 0,
        "coverage_safety_units": 1,
    },
    "coverage_safety_1": {
        "bootstrap_location_balance": 65,
        "supply_transfer_enabled": 0,
        "coverage_replenishment_enabled": 1,
        "coverage_safety_units": 1,
    },
    "coverage_safety_2": {
        "bootstrap_location_balance": 65,
        "supply_transfer_enabled": 0,
        "coverage_replenishment_enabled": 1,
        "coverage_safety_units": 2,
    },
    "coverage_safety_3": {
        "bootstrap_location_balance": 65,
        "supply_transfer_enabled": 0,
        "coverage_replenishment_enabled": 1,
        "coverage_safety_units": 3,
    },
    "coverage_safety_4": {
        "bootstrap_location_balance": 65,
        "supply_transfer_enabled": 0,
        "coverage_replenishment_enabled": 1,
        "coverage_safety_units": 4,
    },
    "coverage_safety_2_with_transfers": {
        "bootstrap_location_balance": 65,
        "coverage_replenishment_enabled": 1,
        "coverage_safety_units": 2,
        "supply_transfer_enabled": 1,
    },
}


class DiscardingMetricsSink:
    """Observe batch size while dropping every batch immediately."""

    def __init__(self) -> None:
        self.max_batch_rows = 0
        self.rows_received = 0
        self.updates_received = 0

    def consume(self, batch) -> None:
        self.max_batch_rows = max(self.max_batch_rows, batch.row_count)
        self.rows_received += sum(len(rows) for rows in batch.rows_by_table.values())
        self.updates_received += sum(len(rows) for rows in (batch.updates_by_table or {}).values())


def benchmark_variant(base_config, master, name: str, overrides: dict, orders: int) -> dict:
    generation = {
        **base_config.generation,
        "sales_orders": orders,
        "estimated_order_items": orders * 2.2,
        "estimated_transaction_rows": max(20_000, orders * 18),
        "stock_audit": 0,
        **overrides,
    }
    config = replace(base_config, generation=generation, order_plan={"mode": "intentions"})
    sink = DiscardingMetricsSink()
    gc.collect()
    baseline_bytes, _ = tracemalloc.get_traced_memory()
    tracemalloc.reset_peak()
    started = perf_counter()
    result = generate_full_transactions_incremental(
        config, master, sink, batch_size=config.batch_size,
    )
    elapsed_seconds = perf_counter() - started
    current_bytes, peak_bytes = tracemalloc.get_traced_memory()
    metrics = result.runtime_metrics
    return {
        "variant": name,
        "overrides": overrides,
        "intents": orders,
        "accepted_orders": result.counts()["sales_orders"],
        "physical_intents_unconverted": metrics.get("physical_intents_unconverted", 0),
        "policy_transfer_items": metrics.get("supply_policy_transfers", 0),
        "policy_transfer_units": metrics.get("supply_policy_transfer_units", 0),
        "intention_digest": metrics.get("sales_intention_digest"),
        "elapsed_seconds": round(elapsed_seconds, 2),
        "python_heap_peak_delta_bytes": max(0, peak_bytes - baseline_bytes),
        "python_heap_current_delta_bytes": current_bytes - baseline_bytes,
        "rows_received_by_discarding_sink": sink.rows_received,
        "updates_received_by_discarding_sink": sink.updates_received,
        "max_batch_rows": sink.max_batch_rows,
        "max_pending_events": metrics.get("transaction_events_max_pending", 0),
        "max_active_orders": metrics.get("max_active_orders", 0),
        "max_active_backorder_orders": metrics.get("max_stock_backorder_orders", 0),
        "max_active_transfers": metrics.get("max_active_transfers", 0),
        "current_active_orders": metrics.get("current_active_orders", 0),
        "current_active_transfers": metrics.get("current_active_transfers", 0),
    }


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--orders", type=int, default=10_000)
    parser.add_argument("--only", choices=tuple(VARIANTS), action="append")
    args = parser.parse_args()
    if args.orders <= 0:
        parser.error("--orders deve ser positivo")

    base_config = load_config("portfolio")
    tracemalloc.start()
    master_started = perf_counter()
    master = generate_master_data(base_config)
    master_seconds = perf_counter() - master_started
    master_current_bytes, master_peak_bytes = tracemalloc.get_traced_memory()
    selected = args.only or list(VARIANTS)
    report = [benchmark_variant(base_config, master, name, VARIANTS[name], args.orders)
              for name in selected]
    tracemalloc.stop()
    if len({row["intention_digest"] for row in report}) != 1:
        raise ValueError("O universo de intenções de venda divergiu entre variantes.")
    print(json.dumps({
        "python": platform.python_version(),
        "orders": args.orders,
        "master_generation_seconds": round(master_seconds, 2),
        "master_python_heap_current_bytes": master_current_bytes,
        "master_python_heap_peak_bytes": master_peak_bytes,
        "memory_scope": "tracemalloc Python heap; master is retained, transaction rows are discarded per batch; stock audit disabled",
        "variants": report,
    }, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
