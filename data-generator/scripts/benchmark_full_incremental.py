"""Benchmark the full incremental 3C+3D event pipeline; no database access."""

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
    parser.add_argument("--orders", type=int, nargs="+", default=[1000, 5000, 10000])
    parser.add_argument("--batch-size", type=int, default=None)
    args = parser.parse_args()
    if any(value <= 0 for value in args.orders):
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
    master_bytes, _ = tracemalloc.get_traced_memory()

    def run_one(order_count: int) -> dict:
        gc.collect()
        baseline, _ = tracemalloc.get_traced_memory()
        tracemalloc.reset_peak()
        current = replace(config, generation={**config.generation, "sales_orders": order_count})
        sink = CountingDiscardingSink()
        started = time.perf_counter()
        result = generate_transactions_incremental(
            current, master, sink, batch_size=batch_size, incremental_completion=True,
        )
        duration = time.perf_counter() - started
        _, peak = tracemalloc.get_traced_memory()
        metrics = result.runtime_metrics
        return {
            "orders": order_count,
            "rows_emitted": sink.total_rows_emitted,
            "rows_by_table": sink.rows_by_table,
            "max_buffered_rows": metrics["max_buffered_rows"],
            "flushes": metrics["flush_count"],
            "max_active_orders": metrics["max_active_orders"],
            "max_active_payments": metrics["max_active_payments"],
            "max_active_fulfillments": metrics["max_active_fulfillments"],
            "max_active_transfers": metrics["max_active_transfers"],
            "max_return_eligibility": metrics["max_return_eligibility"],
            "max_future_events": metrics["max_future_events"],
            "total_events_scheduled": metrics["total_events_scheduled"],
            "total_events_processed": metrics["total_events_processed"],
            "current_active_orders": metrics["current_active_orders"],
            "current_active_payments": metrics["current_active_payments"],
            "current_active_transfers": metrics["current_active_transfers"],
            "current_return_eligibility": metrics["current_return_eligibility"],
            "baseline_after_master_mib": round(baseline / 1024 / 1024, 1),
            "peak_memory_mib": round(peak / 1024 / 1024, 1),
            "transaction_peak_over_master_mib": round(max(0, peak - baseline) / 1024 / 1024, 1),
            "transaction_seconds": round(duration, 2),
            "logical_digest": sink.logical_digest,
        }

    print(json.dumps({
        "profile_basis": "portfolio",
        "master_rows": sum(config.volumes.values()),
        "master_generation_and_validation_seconds": round(master_seconds, 2),
        "master_baseline_mib": round(master_bytes / 1024 / 1024, 1),
        "batch_size": batch_size,
        "transaction_pipeline": "incremental_full_3c_3d_sink",
        "database_connected": False,
        "benchmarks": [run_one(value) for value in args.orders],
    }, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
