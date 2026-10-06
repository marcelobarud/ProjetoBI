"""Logical-key transaction records produced by the chronological engine."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal
from typing import Any


@dataclass
class PurchaseOrder:
    key: str
    number: str
    supplier_code: str
    responsible_employee_code: str | None
    status: str
    ordered_at: datetime
    expected_on: date
    currency_code: str = "BRL"


@dataclass
class PurchaseOrderItem:
    key: str
    order_key: str
    line_number: int
    product_sku: str
    quantity_ordered: int
    unit_cost_ordered: Decimal


@dataclass
class GoodsReceipt:
    key: str
    order_key: str
    location_code: str
    checked_by_employee_code: str | None
    number: str
    status: str
    received_at: datetime


@dataclass
class GoodsReceiptItem:
    key: str
    order_item_key: str
    receipt_key: str
    quantity_received: int
    accepted_quantity: int
    rejected_quantity: int
    unit_acquisition_cost: Decimal


@dataclass
class SaleOrder:
    key: str
    number: str
    channel_code: str
    channel_type: str
    customer_code: str | None
    store_code: str | None
    salesperson_code: str | None
    address_key: str | None
    status: str
    placed_at: datetime
    subtotal: Decimal
    discount: Decimal
    shipping: Decimal
    total: Decimal
    address_snapshot: tuple[str, ...] | None = None


@dataclass
class SaleOrderItem:
    key: str
    order_key: str
    line_number: int
    product_sku: str
    quantity: int
    unit_sale_price: Decimal


@dataclass
class OrderStatusEvent:
    order_key: str
    status: str
    occurred_at: datetime
    changed_by_employee_code: str | None = None
    reason: str | None = None


@dataclass
class AppliedDiscount:
    key: str
    order_key: str
    item_key: str
    scope: str
    amount: Decimal
    code: str
    description: str
    created_at: datetime


@dataclass
class StockReservation:
    key: str
    order_key: str
    item_key: str
    product_sku: str
    location_code: str
    quantity: int
    status: str
    reserved_at: datetime
    released_at: datetime | None = None


@dataclass
class Fulfillment:
    key: str
    order_key: str
    number: str
    fulfillment_type: str
    status: str
    location_code: str | None
    pickup_store_code: str | None
    carrier_code: str | None
    planned_at: datetime
    dispatched_at: datetime | None = None
    completed_at: datetime | None = None


@dataclass
class FulfillmentItem:
    key: str
    order_key: str
    fulfillment_key: str
    sale_item_key: str
    quantity_allocated: int
    fulfilled_quantity: int = 0


@dataclass
class StockMovement:
    key: str
    product_sku: str
    location_code: str
    movement_type: str
    quantity_delta: int
    unit_cost: Decimal
    occurred_at: datetime
    receipt_item_key: str | None = None
    fulfillment_item_key: str | None = None
    return_item_key: str | None = None
    transfer_item_key: str | None = None


@dataclass
class StockStateEvent:
    key: str
    occurred_at: datetime
    event_type: str
    product_sku: str
    location_code: str
    quantity: int
    priority: int = 0
    unit_cost: Decimal | None = None
    movement_key: str | None = None
    reservation_key: str | None = None
    return_item_key: str | None = None
    transfer_item_key: str | None = None


@dataclass
class Payment:
    key: str
    order_key: str
    method_code: str
    reference: str
    status: str
    amount: Decimal
    attempted_at: datetime
    authorized_at: datetime | None = None
    settled_at: datetime | None = None


@dataclass
class PaymentInstallment:
    key: str
    payment_key: str
    number: int
    due_on: date
    amount: Decimal
    status: str
    paid_at: datetime | None


@dataclass
class FulfillmentEvent:
    fulfillment_key: str
    event_type: str
    occurred_at: datetime
    recorded_by_employee_code: str | None = None
    description: str | None = None


@dataclass
class StockTransfer:
    key: str
    number: str
    source_location_code: str
    destination_location_code: str
    status: str
    requested_at: datetime
    dispatched_at: datetime
    received_at: datetime


@dataclass
class StockTransferItem:
    key: str
    transfer_key: str
    product_sku: str
    line_number: int
    quantity_planned: int
    quantity_dispatched: int
    quantity_received: int


@dataclass
class Return:
    key: str
    order_key: str
    number: str
    status: str
    reason_code: str
    requested_at: datetime
    decided_at: datetime | None


@dataclass
class ReturnItem:
    key: str
    return_key: str
    order_key: str
    sale_item_key: str
    source_fulfillment_item_key: str
    quantity_requested: int
    quantity_approved: int
    quantity_received: int
    item_condition: str | None
    stock_destination: str | None
    received_at: datetime | None
    destination_location_code: str | None = None


@dataclass
class Refund:
    key: str
    order_key: str
    payment_key: str
    return_key: str | None
    status: str
    amount: Decimal
    reason_code: str
    requested_at: datetime
    processed_at: datetime | None


@dataclass
class StockPosition:
    product_sku: str
    location_code: str
    on_hand_quantity: int = 0
    reserved_quantity: int = 0
    average_unit_cost: Decimal = Decimal("0.00000000")

    @property
    def available_quantity(self) -> int:
        return self.on_hand_quantity - self.reserved_quantity


@dataclass
class TransactionData:
    purchase_orders: list[PurchaseOrder] = field(default_factory=list)
    purchase_order_items: list[PurchaseOrderItem] = field(default_factory=list)
    goods_receipts: list[GoodsReceipt] = field(default_factory=list)
    goods_receipt_items: list[GoodsReceiptItem] = field(default_factory=list)
    sales_orders: list[SaleOrder] = field(default_factory=list)
    sales_order_items: list[SaleOrderItem] = field(default_factory=list)
    order_status_history: list[OrderStatusEvent] = field(default_factory=list)
    applied_discounts: list[AppliedDiscount] = field(default_factory=list)
    stock_reservations: list[StockReservation] = field(default_factory=list)
    fulfillments: list[Fulfillment] = field(default_factory=list)
    fulfillment_items: list[FulfillmentItem] = field(default_factory=list)
    stock_movements: list[StockMovement] = field(default_factory=list)
    stock_positions: dict[tuple[str, str], StockPosition] = field(default_factory=dict)
    event_trace: list[tuple[datetime, str, str]] = field(default_factory=list)
    stock_state_events: list[StockStateEvent] = field(default_factory=list)
    payments: list[Payment] = field(default_factory=list)
    payment_installments: list[PaymentInstallment] = field(default_factory=list)
    fulfillment_events: list[FulfillmentEvent] = field(default_factory=list)
    stock_transfers: list[StockTransfer] = field(default_factory=list)
    stock_transfer_items: list[StockTransferItem] = field(default_factory=list)
    returns: list[Return] = field(default_factory=list)
    return_items: list[ReturnItem] = field(default_factory=list)
    refunds: list[Refund] = field(default_factory=list)
    runtime_metrics: dict[str, int] = field(default_factory=dict)

    def counts(self) -> dict[str, int]:
        return {
            "purchase_orders": len(self.purchase_orders),
            "purchase_order_items": len(self.purchase_order_items),
            "goods_receipts": len(self.goods_receipts),
            "goods_receipt_items": len(self.goods_receipt_items),
            "sales_orders": len(self.sales_orders),
            "sales_order_items": len(self.sales_order_items),
            "discounts": len(self.applied_discounts),
            "reservations": len(self.stock_reservations),
            "fulfillments": len(self.fulfillments),
            "fulfillment_items": len(self.fulfillment_items),
            "stock_movements": len(self.stock_movements),
            "stock_positions": len(self.stock_positions),
            "payments": len(self.payments),
            "payment_installments": len(self.payment_installments),
            "fulfillment_events": len(self.fulfillment_events),
            "stock_transfers": len(self.stock_transfers),
            "stock_transfer_items": len(self.stock_transfer_items),
            "returns": len(self.returns),
            "return_items": len(self.return_items),
            "refunds": len(self.refunds),
        }

    def summary(self) -> dict[str, Any]:
        return {
            **self.counts(),
            "units_received": sum(row.accepted_quantity for row in self.goods_receipt_items),
            "units_fulfilled": sum(row.quantity_delta * -1 for row in self.stock_movements if row.movement_type == "fulfillment"),
            "ending_stock": sum(row.on_hand_quantity for row in self.stock_positions.values()),
            "active_reserved": sum(row.reserved_quantity for row in self.stock_positions.values()),
            "realized_cost": sum((Decimal(-row.quantity_delta) * row.unit_cost for row in self.stock_movements if row.movement_type == "fulfillment"), Decimal("0.00")),
            "refund_amount": sum((row.amount for row in self.refunds if row.status == "completed"), Decimal("0.00")),
            "captured_amount": sum((row.amount for row in self.payments if row.status in {"captured", "settled"}), Decimal("0.00")),
            "net_financial_amount": sum((row.amount for row in self.payments if row.status in {"captured", "settled"}), Decimal("0.00")) - sum((row.amount for row in self.refunds if row.status == "completed"), Decimal("0.00")),
            "declined_attempts": sum(row.status in {"declined", "failed"} for row in self.payments),
            "payment_retries": sum(row.reference.endswith("-RETRY") for row in self.payments),
            "split_payment_orders": self._split_order_count(),
            "orders_by_channel": {
                code: sum(order.channel_code == code for order in self.sales_orders)
                for code in sorted({order.channel_code for order in self.sales_orders})
            },
            "anonymous_physical_orders": sum(order.channel_type == "physical" and order.customer_code is None for order in self.sales_orders),
            "cancelled_orders": sum(order.status == "cancelled" for order in self.sales_orders),
            "split_orders": sum(count > 1 for count in self._fulfillments_per_order().values()),
            "cutoff": max((event[0] for event in self.event_trace), default=None),
        }

    def _fulfillments_per_order(self) -> dict[str, int]:
        result: dict[str, int] = {}
        for row in self.fulfillments:
            result[row.order_key] = result.get(row.order_key, 0) + 1
        return result

    def _split_order_count(self) -> int:
        by_order: dict[str, list[Payment]] = {}
        for row in self.payments:
            if row.status in {"captured", "settled"}:
                by_order.setdefault(row.order_key, []).append(row)
        return sum(len(rows) > 1 for rows in by_order.values())
