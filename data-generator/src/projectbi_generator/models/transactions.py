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


@dataclass(frozen=True)
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
        }

    def summary(self) -> dict[str, Any]:
        return {
            **self.counts(),
            "units_received": sum(row.accepted_quantity for row in self.goods_receipt_items),
            "units_fulfilled": sum(row.quantity_delta * -1 for row in self.stock_movements if row.movement_type == "fulfillment"),
            "ending_stock": sum(row.on_hand_quantity for row in self.stock_positions.values()),
            "active_reserved": sum(row.reserved_quantity for row in self.stock_positions.values()),
            "realized_cost": sum((Decimal(-row.quantity_delta) * row.unit_cost for row in self.stock_movements if row.movement_type == "fulfillment"), Decimal("0.00")),
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
