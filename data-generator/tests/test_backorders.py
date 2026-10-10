from datetime import datetime, timezone

import pytest

from projectbi_generator.generators.backorders import BackorderLine, StockBackorderIndex


def _line(order: str, item: str, placed_at: datetime, quantity: int = 3) -> BackorderLine:
    return BackorderLine(order, item, "SKU-1", "LOC-1", quantity, placed_at,
                         placed_at.replace(day=placed_at.day + 1))


def test_backorders_are_fifo_and_can_be_partially_reduced():
    index = StockBackorderIndex()
    first = _line("ORDER-1", "ITEM-1", datetime(2026, 1, 1, tzinfo=timezone.utc))
    second = _line("ORDER-2", "ITEM-2", datetime(2026, 1, 2, tzinfo=timezone.utc))
    index.enqueue(first)
    index.enqueue(second)

    assert index.head("SKU-1", "LOC-1") is first
    assert index.pending_quantity("SKU-1", "LOC-1") == 6
    assert index.reduce(first, 2) is False
    assert first.remaining_quantity == 1
    assert index.head("SKU-1", "LOC-1") is first
    assert index.reduce(first, 1) is True
    assert index.head("SKU-1", "LOC-1") is second
    assert index.active_orders == 1
    assert index.active_lines == 1


def test_backorder_index_rejects_non_fifo_insert_and_removes_order_lines():
    index = StockBackorderIndex()
    later = _line("ORDER-2", "ITEM-2", datetime(2026, 1, 2, tzinfo=timezone.utc))
    earlier = _line("ORDER-1", "ITEM-1", datetime(2026, 1, 1, tzinfo=timezone.utc))
    index.enqueue(later)

    with pytest.raises(ValueError, match="fora da ordem FIFO"):
        index.enqueue(earlier)

    assert index.remove_order("ORDER-2") == (later,)
    assert index.head("SKU-1", "LOC-1") is None
    assert index.active_orders == 0
