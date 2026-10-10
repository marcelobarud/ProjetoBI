"""Bounded FIFO index for digital order quantities awaiting stock."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from collections import defaultdict


@dataclass
class BackorderLine:
    order_key: str
    item_key: str
    product_sku: str
    location_code: str
    remaining_quantity: int
    placed_at: datetime
    deadline: datetime


class StockBackorderIndex:
    """Keep only open quantities, grouped by stock location and in FIFO order."""

    def __init__(self) -> None:
        self._queues: dict[tuple[str, str], list[BackorderLine]] = defaultdict(list)
        self._by_order: dict[str, list[BackorderLine]] = defaultdict(list)
        self.max_active_lines = 0

    def enqueue(self, row: BackorderLine) -> None:
        if row.remaining_quantity <= 0:
            raise ValueError("Backorder precisa de quantidade positiva.")
        queue = self._queues[(row.product_sku, row.location_code)]
        # Sale intents are processed chronologically; insertion order is FIFO.
        if queue and (row.placed_at, row.order_key, row.item_key) < (
            queue[-1].placed_at, queue[-1].order_key, queue[-1].item_key
        ):
            raise ValueError("Backorder chegou fora da ordem FIFO causal.")
        queue.append(row)
        self._by_order[row.order_key].append(row)
        self.max_active_lines = max(self.max_active_lines, self.active_lines)

    def head(self, sku: str, location: str) -> BackorderLine | None:
        queue = self._queues.get((sku, location))
        return queue[0] if queue else None

    def pending_quantity(self, sku: str, location: str) -> int:
        return sum(row.remaining_quantity for row in self._queues.get((sku, location), ()))

    def reduce(self, row: BackorderLine, quantity: int) -> bool:
        if quantity <= 0 or quantity > row.remaining_quantity:
            raise ValueError("Atendimento de backorder inválido.")
        row.remaining_quantity -= quantity
        if row.remaining_quantity:
            return False
        queue = self._queues[(row.product_sku, row.location_code)]
        if not queue or queue[0] is not row:
            raise ValueError("Backorder FIFO foi alterado fora da cabeça da fila.")
        queue.pop(0)
        if not queue:
            self._queues.pop((row.product_sku, row.location_code), None)
        rows = self._by_order[row.order_key]
        rows.remove(row)
        if not rows:
            self._by_order.pop(row.order_key, None)
        return True

    def remove_order(self, order_key: str) -> tuple[BackorderLine, ...]:
        rows = tuple(self._by_order.pop(order_key, ()))
        for row in rows:
            queue = self._queues[(row.product_sku, row.location_code)]
            queue.remove(row)
            if not queue:
                self._queues.pop((row.product_sku, row.location_code), None)
        return rows

    def all_lines(self) -> tuple[BackorderLine, ...]:
        return tuple(row for rows in self._by_order.values() for row in rows)

    @property
    def active_lines(self) -> int:
        return sum(len(rows) for rows in self._by_order.values())

    @property
    def active_orders(self) -> int:
        return len(self._by_order)
