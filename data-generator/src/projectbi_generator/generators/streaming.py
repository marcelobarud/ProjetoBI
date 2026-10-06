"""Non-collecting output adapter for the causal 3C transaction engine."""

from __future__ import annotations

from collections import defaultdict
from decimal import Decimal
from typing import Any

from projectbi_generator.models.transactions import StockPosition
from projectbi_generator.sinks import TransactionBatchEmitter


DEFERRED_TABLES = {
    "stock_reservations",
    "fulfillment_items",
    "stock_transfers",
    "stock_transfer_items",
}


class _TraceOff:
    def append(self, _row: Any) -> None:
        return

    def sort(self, *_args, **_kwargs) -> None:
        return


class _StreamedRows:
    def __init__(self, owner: "StreamingCoreResult", table: str) -> None:
        self.owner = owner
        self.table = table
        self.pending: dict[str, Any] = {}
        self.count = 0

    def append(self, row: Any) -> None:
        if self.table in {"purchase_orders", "purchase_order_items", "sales_orders", "returns", "return_items", "stock_transfers", "stock_transfer_items"}:
            key = getattr(row, "key", None)
            if not key or key in self.pending:
                raise ValueError(f"Chave lógica ausente ou duplicada em {self.table}.")
            self.pending[key] = row
            self.owner._emit(self.table, row)
            return
        if self.table in DEFERRED_TABLES:
            key = getattr(row, "key", None)
            if not key or key in self.pending:
                raise ValueError(f"Chave lógica ausente ou duplicada em {self.table}.")
            self.pending[key] = row
            return
        self.owner._emit(self.table, row)

    def extend(self, rows) -> None:
        for row in rows:
            self.append(row)

    def sort(self, *_args, **_kwargs) -> None:
        # Event rows have already been emitted in causal order; no history is retained to sort.
        return

    def publish(self, key: str) -> None:
        if self.table in {"purchase_orders", "purchase_order_items", "sales_orders", "returns", "return_items", "stock_transfers", "stock_transfer_items"}:
            try:
                row = self.pending.pop(key)
            except KeyError as exc:
                raise ValueError(f"Registro ativo ausente em {self.table}.") from exc
            if self.table in {"purchase_orders", "sales_orders", "returns", "return_items"}:
                # Mutable status is finalized later; the sink treats the second
                # emission as a narrow UPDATE of the already inserted row.
                self.owner._emit_update(self.table, row)
            return
        if self.table not in DEFERRED_TABLES:
            raise ValueError(f"{self.table} não é uma coleção adiada.")
        try:
            row = self.pending.pop(key)
        except KeyError as exc:
            raise ValueError(f"Registro não ativo em {self.table}.") from exc
        self.owner._emit(self.table, row)


class StreamingCoreResult:
    """Sink-facing counters/state; it deliberately has no historical row lists."""

    TABLES = (
        "purchase_orders", "purchase_order_items", "goods_receipts", "goods_receipt_items",
        "sales_orders", "sales_order_items", "order_status_history", "applied_discounts",
        "stock_reservations", "fulfillments", "fulfillment_items", "stock_movements",
        "stock_state_events", "payments", "payment_installments", "fulfillment_events",
        "stock_transfers", "stock_transfer_items", "returns", "return_items", "refunds",
    )

    def __init__(self, emitter: TransactionBatchEmitter) -> None:
        self.emitter = emitter
        self._counts = {table: 0 for table in self.TABLES}
        for table in self.TABLES:
            setattr(self, table, _StreamedRows(self, table))
        self.event_trace = _TraceOff()
        self.stock_positions: dict[tuple[str, str], StockPosition] = {}
        self.runtime_metrics: dict[str, int] = {}
        self.aggregates: dict[str, Any] = {
            "orders": 0,
            "items": 0,
            "orders_by_channel": defaultdict(int),
            "anonymous_physical_orders": 0,
            "cancelled_orders": 0,
            "discount_count": 0,
            "purchase_orders": 0,
            "receipts": 0,
            "fulfillments": 0,
            "fulfilled_items": 0,
            "units_received": 0,
            "units_fulfilled": 0,
            "realized_cost": Decimal("0"),
            "split_fulfillments": 0,
            "ending_stock": 0,
            "payments": 0,
            "declined_or_failed": 0,
            "retries": 0,
            "split_payment_orders": 0,
            "installments": 0,
            "captured_amount": Decimal("0.00"),
            "refund_amount": Decimal("0.00"),
            "net_financial_amount": Decimal("0.00"),
            "fulfillment_event_count": 0,
            "delivery_events": 0,
            "pickup_events": 0,
            "transfers": 0,
            "transfer_items": 0,
            "returns": 0,
            "return_items": 0,
            "sellable_returns": 0,
            "non_sellable_returns": 0,
            "returned_units": 0,
            "refund_count": 0,
        }

    def _emit(self, table: str, row: Any) -> None:
        self.emitter.add(table, row)
        self._counts[table] += 1
        collection = getattr(self, table)
        collection.count += 1
        if table == "purchase_orders":
            self.aggregates["purchase_orders"] += 1
        elif table == "goods_receipts":
            self.aggregates["receipts"] += 1
        elif table == "sales_orders":
            self.aggregates["orders"] += 1
            self.aggregates["orders_by_channel"][row.channel_code] += 1
            self.aggregates["anonymous_physical_orders"] += int(
                row.channel_type == "physical" and row.customer_code is None
            )
            self.aggregates["cancelled_orders"] += int(row.status == "cancelled")
        elif table == "sales_order_items":
            self.aggregates["items"] += 1
        elif table == "applied_discounts":
            self.aggregates["discount_count"] += 1
        elif table == "fulfillments":
            self.aggregates["fulfillments"] += 1
        elif table == "fulfillment_items":
            self.aggregates["fulfilled_items"] += int(row.fulfilled_quantity > 0)
        elif table == "goods_receipt_items":
            self.aggregates["units_received"] += row.accepted_quantity
        elif table == "stock_movements" and row.movement_type == "fulfillment":
            quantity = abs(row.quantity_delta)
            self.aggregates["units_fulfilled"] += quantity
            self.aggregates["realized_cost"] += Decimal(quantity) * row.unit_cost
        elif table == "payments":
            self.aggregates["payments"] += 1
            self.aggregates["declined_or_failed"] += int(row.status in {"declined", "failed"})
            self.aggregates["retries"] += int(row.reference.endswith("-RETRY"))
            if row.status in {"captured", "settled"}:
                self.aggregates["captured_amount"] += row.amount
                self.aggregates["net_financial_amount"] += row.amount
        elif table == "payment_installments":
            self.aggregates["installments"] += 1
        elif table == "fulfillment_events":
            self.aggregates["fulfillment_event_count"] += 1
            self.aggregates["delivery_events"] += int(row.event_type in {"prepared", "dispatched", "delivery_attempt", "exception", "delivered"})
            self.aggregates["pickup_events"] += int(row.event_type in {"prepared", "pickup_ready", "picked_up"})
        elif table == "stock_transfers":
            self.aggregates["transfers"] += 1
        elif table == "stock_transfer_items":
            self.aggregates["transfer_items"] += 1
        elif table == "returns":
            self.aggregates["returns"] += 1
        elif table == "return_items":
            self.aggregates["return_items"] += 1
            self.aggregates["sellable_returns"] += int(row.stock_destination == "sellable")
            self.aggregates["non_sellable_returns"] += int(row.stock_destination in {"quarantine", "repair", "discard"})
            self.aggregates["returned_units"] += row.quantity_received if row.stock_destination == "sellable" else 0
        elif table == "refunds" and row.status == "completed":
            self.aggregates["refund_count"] += 1
            self.aggregates["refund_amount"] += row.amount
            self.aggregates["net_financial_amount"] -= row.amount

    def _emit_update(self, table: str, row: Any) -> None:
        """Emit a final mutable snapshot without counting it as a second logical row."""
        self.emitter.update(table, row)
        if table == "sales_orders":
            self.aggregates["cancelled_orders"] += int(row.status == "cancelled")
        elif table == "return_items":
            self.aggregates["sellable_returns"] += int(row.stock_destination == "sellable")
            self.aggregates["non_sellable_returns"] += int(row.stock_destination in {"quarantine", "repair", "discard"})
            self.aggregates["returned_units"] += row.quantity_received if row.stock_destination == "sellable" else 0

    def release_transaction_id(self, entity: str, key: str) -> None:
        """Forward a causal close signal alongside the next flushed batch."""
        self.emitter.release(entity, key)

    def publish(self, table: str, key: str) -> None:
        getattr(self, table).publish(key)

    def emit_final_positions(self) -> None:
        for row in self.stock_positions.values():
            self.emitter.add("stock_positions", row)
            self._counts.setdefault("stock_positions", 0)
            self._counts["stock_positions"] += 1
            self.aggregates["ending_stock"] += row.on_hand_quantity

    def close(self) -> None:
        pending = {
            table: len(getattr(self, table).pending)
            for table in (*DEFERRED_TABLES, "purchase_orders", "purchase_order_items", "sales_orders", "returns", "return_items", "stock_transfers", "stock_transfer_items")
            if getattr(self, table).pending
        }
        if pending:
            raise ValueError(f"Registros ativos 3C ao final do horizonte: {pending}.")
        self.emitter.close()
        if self.emitter.buffered_rows:
            raise ValueError("Emitter permaneceu com linhas após close.")

    def counts(self) -> dict[str, int]:
        return dict(self._counts)
