"""Benchmark the incremental 3C core with a discarding sink; no database access."""

from __future__ import annotations

import argparse
from dataclasses import replace
import gc
import json
import time
import tracemalloc

from projectbi_generator.config import load_config
from projectbi_generator.generators.master import generate_master_data
from projectbi_generator.generators.transactions import generate_transactions_incremental
from projectbi_generator.sinks import CountingDiscardingSink
from projectbi_generator.validation.master_data import validate_master_data


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--orders", type=int, nargs="+", default=[1000])
    parser.add_argument("--batch-size", type=int, default=None)
    args = parser.parse_args()
    if any(orders <= 0 for orders in args.orders):
        parser.error("todos os valores de --orders devem ser positivos")
    if args.batch_size is not None and args.batch_size <= 0:
        parser.error("--batch-size deve ser positivo")

    config = load_config("portfolio")
    batch_size = args.batch_size or config.batch_size

    gc.collect()
    tracemalloc.start()
    master_started = time.perf_counter()
    master = generate_master_data(config)
    validate_master_data(master, config)
    gc.collect()
    master_seconds = time.perf_counter() - master_started
    baseline_bytes, _ = tracemalloc.get_traced_memory()

    def run_one(orders: int) -> dict:
        gc.collect()
        baseline, _ = tracemalloc.get_traced_memory()
        tracemalloc.reset_peak()
        current_config = replace(
            config, generation={**config.generation, "sales_orders": orders},
            order_plan={"mode": "intentions"},
        )
        sink = CountingDiscardingSink()
        transaction_started = time.perf_counter()
        result = generate_transactions_incremental(current_config, master, sink, batch_size=batch_size)
        transaction_seconds = time.perf_counter() - transaction_started
        _, peak_bytes = tracemalloc.get_traced_memory()
        output = {
            "sales_orders_override": orders,
            "sales_orders_emitted": sink.rows_by_table.get("sales_orders", 0),
            "sales_order_items_emitted": sink.rows_by_table.get("sales_order_items", 0),
            "total_rows_emitted": sink.total_rows_emitted,
            "max_buffered_rows": result.runtime_metrics["max_buffered_rows"],
            "flush_count": result.runtime_metrics["flush_count"],
            "max_active_orders": result.runtime_metrics["max_active_orders"],
            "max_active_purchase_orders": result.runtime_metrics["max_active_purchase_orders"],
            "max_future_events_3c": result.runtime_metrics["max_future_events_3c"],
            "current_future_events_3c": result.runtime_metrics["current_future_events_3c"],
            "current_active_orders": result.runtime_metrics["current_active_orders"],
            "baseline_after_master_mib": round(baseline / (1024 * 1024), 1),
            "peak_memory_mib": round(peak_bytes / (1024 * 1024), 1),
            "transaction_peak_over_master_mib": round(max(0, peak_bytes - baseline) / (1024 * 1024), 1),
            "transaction_seconds": round(transaction_seconds, 2),
            "logical_digest": sink.logical_digest,
        }
        return output

    output = {
        "profile_basis": "portfolio",
        "master_rows": sum(config.volumes.values()),
        "master_generation_and_validation_seconds": round(master_seconds, 2),
        "master_baseline_mib": round(baseline_bytes / (1024 * 1024), 1),
        "batch_size": batch_size,
        "transaction_pipeline": "incremental_3c_sink",
        "database_connected": False,
        "benchmarks": [run_one(orders) for orders in args.orders],
    }
    print(json.dumps(output, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
