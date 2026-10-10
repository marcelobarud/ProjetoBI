"""Exercise the 120k Portfolio ID lifecycle through the production PostgreSQL sink.

The connection adapter returns identities and stock-position snapshots without
persisting rows. The production generator, emitter, PostgreSQL sink mappings,
ID registry, FK lookups, batch boundaries and release signals remain active.
"""

from __future__ import annotations

import ctypes
from ctypes import wintypes
from decimal import Decimal
import json
from time import monotonic, perf_counter

from projectbi_generator.config import load_config
from projectbi_generator.generators.completion import generate_full_transactions_incremental
from projectbi_generator.generators.master import generate_master_data
from projectbi_generator.models.entities import MasterData
from projectbi_generator.repositories.postgres_sink import PostgreSQLTransactionSink


class _Cursor:
    def __init__(self, rows=()):
        self.rows = list(rows)
        self.index = 0

    def executemany(self, _statement, params, *, returning=False):
        self.rows = [(next(_IDENTITIES),) for _ in params] if returning else []
        self.index = 0

    def fetchone(self):
        return self.rows[self.index] if self.index < len(self.rows) else None

    def nextset(self):
        self.index += 1
        return self.index < len(self.rows)

    def close(self):
        pass


_IDENTITIES = iter(range(1, 100_000_000))


class _ProcessMemoryCountersEx(ctypes.Structure):
    _fields_ = [
        ("cb", wintypes.DWORD),
        ("PageFaultCount", wintypes.DWORD),
        ("PeakWorkingSetSize", ctypes.c_size_t),
        ("WorkingSetSize", ctypes.c_size_t),
        ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
        ("QuotaPagedPoolUsage", ctypes.c_size_t),
        ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
        ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
        ("PagefileUsage", ctypes.c_size_t),
        ("PeakPagefileUsage", ctypes.c_size_t),
        ("PrivateUsage", ctypes.c_size_t),
    ]


def _process_memory() -> dict[str, int]:
    counters = _ProcessMemoryCountersEx()
    counters.cb = ctypes.sizeof(counters)
    psapi = ctypes.WinDLL("psapi", use_last_error=True)
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel32.GetCurrentProcess.restype = wintypes.HANDLE
    psapi.GetProcessMemoryInfo.argtypes = (
        wintypes.HANDLE, ctypes.POINTER(_ProcessMemoryCountersEx), wintypes.DWORD,
    )
    psapi.GetProcessMemoryInfo.restype = wintypes.BOOL
    ok = psapi.GetProcessMemoryInfo(
        kernel32.GetCurrentProcess(), ctypes.byref(counters), counters.cb,
    )
    if not ok:
        raise ctypes.WinError(ctypes.get_last_error())
    return {
        "working_set_bytes": int(counters.WorkingSetSize),
        "peak_working_set_bytes": int(counters.PeakWorkingSetSize),
        "private_bytes": int(counters.PrivateUsage),
        "peak_pagefile_bytes": int(counters.PeakPagefileUsage),
    }


class _IdentityOnlyConnection:
    """Identity/position adapter; no SQL is sent to a database."""

    def __init__(self):
        self.positions = {}

    def cursor(self):
        return _Cursor()

    def execute(self, statement, params=()):
        normalized = " ".join(statement.split()).upper()
        if normalized.startswith("INSERT INTO INVENTORY.STOCK_POSITIONS"):
            product_id, location_id = params[:2]
            key = (product_id, location_id)
            if "RETURNING STOCK_POSITION_ID" in normalized:
                if key in self.positions:
                    return _Cursor()
                row = (next(_IDENTITIES), 0, 0, Decimal("0"))
                self.positions[key] = row
                return _Cursor((row,))
            row = (next(_IDENTITIES), params[2], params[3], params[4])
            self.positions[key] = row
            return _Cursor()
        if normalized.startswith("SELECT STOCK_POSITION_ID"):
            product_id, location_id = params
            return _Cursor((self.positions[(product_id, location_id)],))
        raise AssertionError("SQL não suportado pelo adaptador de identidade.")


def _master_ids(master: MasterData) -> dict[str, dict[str, int]]:
    entities = {
        "stores": master.stores,
        "employees": master.employees,
        "sales_channels": master.sales_channels,
        "payment_methods": master.payment_methods,
        "suppliers": master.suppliers,
        "carriers": master.carriers,
        "products": master.products,
        "customers": master.customers,
        "customer_addresses": master.customer_addresses,
        "stock_locations": master.stock_locations,
    }
    return {
        name: {
            getattr(row, "code", getattr(row, "sku", getattr(row, "logical_key", None))): index
            for index, row in enumerate(rows, start=1)
        }
        for name, rows in entities.items()
    }


class _LifecycleSink(PostgreSQLTransactionSink):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.sales_order_id_lookups = 0
        self.sales_order_id_releases = 0
        self.id_lookups = 0
        self._released_fulfillment_item_owners = {}
        self._next_progress_mark = 10_000
        self._started = monotonic()

    def consume(self, batch):
        super().consume(batch)
        inserted = self.metrics.sales_orders_inserted
        if inserted >= self._next_progress_mark:
            print(
                f"ID lifecycle: pedidos={inserted}; IDs ativos={self.ids.current_entries}; "
                f"pico={self.ids.max_entries}; flushes={self.metrics.flush_count}; "
                f"elapsed={monotonic() - self._started:.0f}s.",
                flush=True,
            )
            self._next_progress_mark += 10_000

    def _id(self, entity, key):
        self.id_lookups += 1
        if entity == "sales_orders":
            self.sales_order_id_lookups += 1
        try:
            return super()._id(entity, key)
        except KeyError as exc:
            if entity == "fulfillment_items":
                owner = self._released_fulfillment_item_owners.get(key, "unknown")
                raise KeyError(f"Missing fulfillment_item={key}; released_sales_order={owner}.") from exc
            raise

    def _release_id(self, entity, key):
        if entity == "sales_orders":
            self.sales_order_id_releases += 1
            for child_key in self._order_refs.get(key, {}).get("fulfillment_items", ()):
                self._released_fulfillment_item_owners[child_key] = key
        return super()._release_id(entity, key)


def main() -> None:
    config = load_config("portfolio")
    if config.sales_order_target != 120_000 or config.root_seed != 20261005:
        raise RuntimeError("Profile Portfolio não corresponde ao alvo/seed aprovado.")
    master = generate_master_data(config)
    connection = _IdentityOnlyConnection()
    sink = _LifecycleSink(connection, master, _master_ids(master), config.batch_size)
    started = perf_counter()
    result = generate_full_transactions_incremental(config, master, sink, batch_size=config.batch_size)
    elapsed = perf_counter() - started
    memory = _process_memory()
    if sink.ids.current_entries:
        raise RuntimeError(f"IDs transitórios restantes: {sink.ids.current_entries}.")
    if sink._pending_state_events or sink._pending_movements:
        raise RuntimeError("O fluxo terminou com movimentos/estados causais pendentes.")
    if result.runtime_metrics.get("current_pending_fulfillment_events", 0):
        raise RuntimeError("O fluxo terminou com eventos de fulfillment pendentes.")
    if result.counts()["sales_orders"] != 120_000:
        raise RuntimeError("A quantidade de pedidos gerados diverge de 120.000.")
    if sink.sales_order_id_releases != 120_000 or sink._order_refs:
        raise RuntimeError("Lifecycle de IDs/referências de pedidos não foi completamente encerrado.")
    print(json.dumps({
        "profile": config.profile,
        "seed": config.root_seed,
        "accepted_orders": result.counts()["sales_orders"],
        "sales_order_id_lookups": sink.sales_order_id_lookups,
        "sales_order_id_releases": sink.sales_order_id_releases,
        "id_lookups": sink.id_lookups,
        "failed_id_lookups": 0,
        "sales_order_id_peak": sink.ids.max_by_type.get("sales_orders", 0),
        "all_transient_ids_peak": sink.ids.max_entries,
        "all_transient_ids_remaining": sink.ids.current_entries,
        "pending_state_events": len(sink._pending_state_events),
        "pending_movements": len(sink._pending_movements),
        "pending_fulfillment_events": result.runtime_metrics.get("current_pending_fulfillment_events", 0),
        "flushes": sink.metrics.flush_count,
        "rows_received": sink.metrics.rows_received_from_emitter,
        "max_batch_rows": sink.metrics.max_batch_rows,
        "max_emitter_buffered_rows": result.runtime_metrics["max_buffered_rows"],
        "max_pending_events": result.runtime_metrics["max_future_events_3c"],
        "unresolved_order_ref_groups": len(sink._order_refs),
        "elapsed_seconds": round(elapsed, 2),
        "memory_bytes": memory,
    }, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
