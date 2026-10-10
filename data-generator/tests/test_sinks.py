from datetime import datetime, timezone
from decimal import Decimal

import pytest

from projectbi_generator.models.transactions import SaleOrder
from projectbi_generator.sinks import (
    CollectingSink,
    CountingDiscardingSink,
    TransactionBatchEmitter,
)
from projectbi_generator.repositories.postgres_sink import TransientTransactionIdRegistry


def _order(index: int) -> SaleOrder:
    at = datetime(2026, 1, 1, tzinfo=timezone.utc)
    return SaleOrder(
        key=f"ORDER-{index:05d}", number=f"SO-{index:05d}", channel_code="CH-ECOM",
        channel_type="ecommerce", customer_code="CUS-1", store_code=None,
        salesperson_code=None, address_key=None, status="confirmed", placed_at=at,
        subtotal=Decimal("10.00"), discount=Decimal("0.00"), shipping=Decimal("0.00"),
        total=Decimal("10.00"),
    )


def test_discarding_sink_digest_and_counts_are_independent_of_batch_size():
    results = []
    for size in (3, 11, 64):
        sink = CountingDiscardingSink()
        emitter = TransactionBatchEmitter(sink, size)
        for index in range(53):
            emitter.add("sales_orders", _order(index))
            if index % 4 == 0:
                emitter.add("sales_order_items", {"order": index, "quantity": 1})
        emitter.close()
        results.append((sink.rows_by_table, sink.logical_digest))
        assert emitter.max_buffered_rows <= size
        assert emitter.buffered_rows == 0
    assert results[0] == results[1] == results[2]
    assert results[0][0] == {"sales_orders": 53, "sales_order_items": 14}


def test_collecting_sink_only_retains_rows_when_explicitly_selected():
    sink = CollectingSink()
    emitter = TransactionBatchEmitter(sink, 2)
    orders = [_order(index) for index in range(4)]
    for row in orders:
        emitter.add("sales_orders", row)
    emitter.close()
    assert sink.rows_by_table["sales_orders"] == orders
    assert sink.max_batch_rows <= 2


def test_batch_emitter_rejects_nonpositive_threshold():
    with pytest.raises(ValueError, match="positivo"):
        TransactionBatchEmitter(CountingDiscardingSink(), 0)


def test_transient_id_registry_releases_5000_order_lifecycles_without_connection():
    registry = TransientTransactionIdRegistry()
    peak = 0
    for index in range(5000):
        key = f"ORDER-{index:05d}"
        registry.retain("sales_orders", key, index + 1)
        registry.retain("sales_order_items", key + "-ITEM", index + 1)
        if index >= 40:
            expired = f"ORDER-{index - 40:05d}"
            registry.release("sales_order_items", expired + "-ITEM")
            registry.release("sales_orders", expired)
        peak = max(peak, registry.current_entries)
    for index in range(4960, 5000):
        key = f"ORDER-{index:05d}"
        registry.release("sales_order_items", key + "-ITEM")
        registry.release("sales_orders", key)
    assert registry.current_entries == 0
    assert registry.current_by_type == {}
    assert registry.max_entries == 82
    assert peak == 80
    with pytest.raises(KeyError, match="inexistente"):
        registry.release("sales_orders", "missing")
    with pytest.raises(ValueError, match="duplicada"):
        registry.retain("sales_orders", "duplicate", 1)
        registry.retain("sales_orders", "duplicate", 2)
