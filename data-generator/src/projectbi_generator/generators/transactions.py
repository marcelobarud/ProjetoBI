"""Event-driven smoke procurement, inventory, sales and fulfillment engine."""

from __future__ import annotations

import heapq
import random
from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta
from decimal import Decimal, ROUND_DOWN, ROUND_HALF_UP
from typing import Any

from projectbi_generator.config import GeneratorConfig
from projectbi_generator.generators.master import FAMILIES, generate_master_data
from projectbi_generator.models.entities import MasterData
from projectbi_generator.models.transactions import (
    AppliedDiscount, Fulfillment, FulfillmentItem, GoodsReceipt, GoodsReceiptItem,
    OrderStatusEvent, PurchaseOrder, PurchaseOrderItem, SaleOrder, SaleOrderItem,
    StockMovement, StockPosition, StockReservation, StockStateEvent, TransactionData,
)
from projectbi_generator.seeds import create_domain_randoms

CENT = Decimal("0.01")
COST_SCALE = Decimal("0.00000001")
CUTOFF_TIME = time(23, 59, 59)
ORDER_COUNT = 300
PARTIAL_CANCEL_INDICES = frozenset(range(37, ORDER_COUNT, 37))
FAMILY_COST_FACTORS = {
    "NOTEBOOK": (Decimal("0.67"), Decimal("0.81")),
    "DESKTOP": (Decimal("0.66"), Decimal("0.80")),
    "PROCESSOR": (Decimal("0.63"), Decimal("0.79")),
    "GRAPHICS": (Decimal("0.70"), Decimal("0.84")),
    "MEMORY": (Decimal("0.62"), Decimal("0.78")),
    "MONITOR": (Decimal("0.65"), Decimal("0.81")),
    "STORAGE": (Decimal("0.64"), Decimal("0.80")),
    "INPUT": (Decimal("0.58"), Decimal("0.78")),
    "AUDIO": (Decimal("0.62"), Decimal("0.79")),
    "NETWORK": (Decimal("0.63"), Decimal("0.80")),
    "PRINTING": (Decimal("0.68"), Decimal("0.82")),
    "ACCESSORIES": (Decimal("0.55"), Decimal("0.76")),
}


@dataclass(order=True, frozen=True)
class ScheduledEvent:
    occurred_at: datetime
    priority: int
    logical_key: str
    event_type: str = field(compare=False)
    payload: dict[str, Any] = field(compare=False)


class EventQueue:
    """Min-heap ordered by instant, event priority, then stable logical key."""

    def __init__(self) -> None:
        self._items: list[ScheduledEvent] = []
        self._keys: set[str] = set()

    def push(self, event: ScheduledEvent) -> None:
        if event.logical_key in self._keys:
            raise ValueError("Chave lógica de evento duplicada.")
        self._keys.add(event.logical_key)
        heapq.heappush(self._items, event)

    def pop(self) -> ScheduledEvent:
        return heapq.heappop(self._items)

    def __bool__(self) -> bool:
        return bool(self._items)


def _aware(config: GeneratorConfig, day: date, hour: int = 10, minute: int = 0) -> datetime:
    return datetime.combine(day, time(hour, minute), tzinfo=config.timezone)


def _money(value: Decimal) -> Decimal:
    return value.quantize(CENT, rounding=ROUND_HALF_UP)


def _cost(value: Decimal) -> Decimal:
    return value.quantize(COST_SCALE, rounding=ROUND_HALF_UP)


def weighted_moving_average(
    previous_quantity: int,
    previous_average: Decimal,
    incoming_quantity: int,
    incoming_unit_cost: Decimal,
) -> Decimal:
    if previous_quantity < 0 or incoming_quantity <= 0:
        raise ValueError("Quantidades inválidas para custo médio móvel.")
    if not isinstance(previous_average, Decimal) or not isinstance(incoming_unit_cost, Decimal):
        raise ValueError("Custos devem ser Decimal.")
    if previous_quantity == 0:
        return _cost(incoming_unit_cost)
    total_qty = previous_quantity + incoming_quantity
    return _cost(
        (Decimal(previous_quantity) * previous_average + Decimal(incoming_quantity) * incoming_unit_cost)
        / Decimal(total_qty)
    )


def allocate_cents(amount: Decimal, eligible: list[Decimal]) -> list[Decimal]:
    """Allocate an order discount proportionally, then distribute residual cents by line order."""
    if not isinstance(amount, Decimal) or any(not isinstance(value, Decimal) for value in eligible):
        raise ValueError("Rateio de desconto exige Decimal.")
    if amount < 0 or any(value < 0 for value in eligible) or amount > sum(eligible, Decimal("0.00")):
        raise ValueError("Desconto excede a base elegível.")
    if not eligible:
        if amount:
            raise ValueError("Não há linhas elegíveis para o desconto.")
        return []
    total = sum(eligible, Decimal("0.00"))
    if not total:
        if amount:
            raise ValueError("Base de desconto igual a zero.")
        return [Decimal("0.00") for _ in eligible]
    allocations = [(amount * value / total).quantize(CENT, rounding=ROUND_DOWN) for value in eligible]
    cents_left = int(((amount - sum(allocations, Decimal("0.00"))) / CENT).to_integral_exact())
    for index in range(cents_left):
        allocations[index % len(allocations)] += CENT
    if any(part > base for part, base in zip(allocations, eligible)):
        raise ValueError("Rateio tornou uma linha comercial líquida negativa.")
    return allocations


def _line_count(index: int) -> int:
    return (1, 1, 1, 2, 2, 2, 2, 3, 3, 4)[index % 10]


def _price_map(master: MasterData) -> dict[tuple[str, str], Decimal]:
    return {(row.product_sku, row.channel_code): row.amount for row in master.product_prices}


def _cost_for(
    master: MasterData,
    sku: str,
    rng: random.Random,
    supplier_ordinal: int,
    period_ordinal: int,
    prices: dict[tuple[str, str], Decimal],
) -> Decimal:
    product = next(row for row in master.products if row.sku == sku)
    family = FAMILIES[product.category_code][1]
    low, high = FAMILY_COST_FACTORS[family]
    retail = min(prices[(sku, channel.code)] for channel in master.sales_channels)
    factor = low + (high - low) * Decimal(rng.randrange(1001)) / Decimal(1000)
    supplier_adjustment = Decimal((supplier_ordinal % 5) - 2) / Decimal(100)
    period_adjustment = Decimal((period_ordinal % 3) - 1) / Decimal(100)
    final_factor = min(Decimal("0.90"), max(Decimal("0.50"), factor + supplier_adjustment + period_adjustment))
    return _cost(retail * final_factor)


def generate_transactions(
    config: GeneratorConfig,
    master: MasterData | None = None,
) -> TransactionData:
    """Generate smoke operations through a deterministic, causal chronological queue."""
    if config.profile != "smoke":
        raise ValueError("A engine transacional desta fase aceita somente o profile smoke.")
    master = master or generate_master_data(config)
    prices = _price_map(master)
    randoms = create_domain_randoms(config.root_seed, config.generator_version)
    procurement_rng = randoms["procurement"].rng
    sales_rng = randoms["sales"].rng
    inventory_rng = randoms["inventory"].rng
    queue = EventQueue()
    result = TransactionData()
    cutoff = _aware(config, config.end_date, CUTOFF_TIME.hour, CUTOFF_TIME.minute)
    products = {row.sku: row for row in master.products}
    channels = {row.code: row for row in master.sales_channels}
    customers = {row.code: row for row in master.customers}
    addresses = {row.customer_code: row for row in master.customer_addresses if row.is_default and row.is_active}
    employees = {row.code: row for row in master.employees}
    stores = {row.code: row for row in master.stores}
    links_by_product: dict[str, list] = {}
    for link in master.product_suppliers:
        links_by_product.setdefault(link.product_sku, []).append(link)
    roles = {row.code for row in master.employee_roles}
    sales_assignments = [row for row in master.employee_assignments if row.role_code == "SALES"]
    location_codes = [row.code for row in master.stock_locations]
    store_locations = {row.store_code: row.code for row in master.stock_locations if row.store_code}
    warehouse_codes = sorted(row.code for row in master.stock_locations if row.location_type == "warehouse")
    if len(warehouse_codes) < 2 or len(store_locations) != len(master.stores):
        raise ValueError("Profile smoke requer dois armazéns e estoque associado a cada loja.")
    positions: dict[tuple[str, str], StockPosition] = {}
    pending_restock: set[tuple[str, str]] = set()
    result_by_order: dict[str, SaleOrder] = {}
    items_by_order: dict[str, list[SaleOrderItem]] = {}
    reservations_by_order: dict[str, list[StockReservation]] = {}
    fulfillments_by_key: dict[str, Fulfillment] = {}
    fulfillment_items_by_key: dict[str, FulfillmentItem] = {}
    fulfilled_by_item: dict[str, int] = {}
    item_product: dict[str, str] = {}
    item_order: dict[str, str] = {}
    po_by_key: dict[str, PurchaseOrder] = {}
    po_item_by_key: dict[str, PurchaseOrderItem] = {}
    received_by_po_item: dict[str, int] = {}
    movement_counter = 0
    purchase_counter = 0
    receipt_counter = 0
    order_counter = 0
    reservation_counter = 0
    fulfillment_counter = 0
    fulfillment_item_counter = 0
    discount_counter = 0

    def push(at: datetime, priority: int, key: str, event_type: str, payload: dict[str, Any]) -> None:
        if at > cutoff:
            return
        queue.push(ScheduledEvent(at, priority, key, event_type, payload))

    def add_movement(
        sku: str,
        location: str,
        kind: str,
        qty_delta: int,
        unit_cost: Decimal,
        at: datetime,
        receipt_item_key: str | None = None,
        fulfillment_item_key: str | None = None,
        reservation_key: str | None = None,
    ) -> str:
        nonlocal movement_counter
        movement_counter += 1
        key = f"MOV-SM-{movement_counter:06d}"
        result.stock_movements.append(StockMovement(key, sku, location, kind, qty_delta, unit_cost, at, receipt_item_key, fulfillment_item_key))
        state_key = f"STATE-{len(result.stock_state_events) + 1:06d}"
        priority = 0 if kind == "receipt" else 30
        result.stock_state_events.append(StockStateEvent(state_key, at, kind, sku, location, abs(qty_delta), priority, unit_cost, key, reservation_key))
        return key

    def create_purchase(payload: dict[str, Any], at: datetime) -> tuple[str, str]:
        nonlocal purchase_counter
        purchase_counter += 1
        po_key = f"PO-KEY-{purchase_counter:04d}"
        number = f"PO-SM-{purchase_counter:04d}"
        po = PurchaseOrder(po_key, number, payload["supplier_code"], payload.get("employee_code"), "submitted", at, payload["expected_on"])
        result.purchase_orders.append(po)
        po_by_key[po_key] = po
        item_key = f"POI-KEY-{purchase_counter:04d}-01"
        line = PurchaseOrderItem(item_key, po_key, 1, payload["sku"], payload["quantity"], payload["unit_cost"])
        result.purchase_order_items.append(line)
        po_item_by_key[item_key] = line
        received_by_po_item[item_key] = 0
        return po_key, item_key

    def schedule_receipt(
        po_key: str,
        item_key: str,
        location: str,
        at: datetime,
        qty_received: int,
        accepted: int,
        rejected: int,
        cost: Decimal,
        suffix: str,
    ) -> None:
        push(at, 2, f"RECEIVE-{po_key}-{suffix}", "receipt", {
            "po_key": po_key, "item_key": item_key, "location": location,
            "received": qty_received, "accepted": accepted, "rejected": rejected,
            "cost": cost, "suffix": suffix,
        })

    def preferred_supplier(sku: str):
        preferred = sorted(
            (row for row in links_by_product[sku] if row.is_active and row.is_preferred),
            key=lambda row: (row.supplier_code, row.supplier_product_code),
        )
        if not preferred:
            raise ValueError("Produto não possui fornecedor preferencial associado.")
        return preferred[0]

    def bootstrap_plan() -> None:
        products_order = [row.sku for row in master.products]
        price_rng = prices
        for index, sku in enumerate(products_order):
            link = preferred_supplier(sku)
            if index == 0:
                plans = [(warehouse_codes[0], 2), (warehouse_codes[1], 2)]
            elif index == 1:
                plans = [(warehouse_codes[0], 12)]
            else:
                plans = [(location_codes[(index - 2) % len(location_codes)], procurement_rng.randint(9, 15))]
            for part, (location, quantity) in enumerate(plans, start=1):
                order_day = config.bootstrap_start_date + timedelta(days=(index * 2 + part) % 42)
                ordered_at = _aware(config, order_day, 9 + (index % 7), index % 60)
                partial = index == 1
                lead1 = 5 + (index + part) % 6
                first_arrival = ordered_at + timedelta(days=lead1)
                second_arrival = first_arrival + timedelta(days=4)
                final_arrival = second_arrival if partial else first_arrival
                # The two split-source receipts for SKU 001 guarantee the first split fulfillment.
                if index == 0:
                    first_arrival = ordered_at + timedelta(days=5 + part)
                    final_arrival = first_arrival
                cost = _cost_for(master, sku, procurement_rng, part + index, index + part, price_rng)
                payload = {
                    "sku": sku, "location": location, "quantity": quantity,
                    "supplier_code": link.supplier_code,
                    "employee_code": None,
                    "expected_on": final_arrival.date(), "unit_cost": cost,
                    "partial": partial, "reject_one": index == 2, "arrival": first_arrival,
                    "second_arrival": second_arrival,
                }
                key = f"BOOTSTRAP-PO-{index + 1:03d}-{part}"
                push(ordered_at, 1, key, "purchase_order", payload)
        # Five extra bootstrap orders add realistic supplier/date variation without a product×location grid.
        for index, sku in enumerate((products_order[2], products_order[5], products_order[9], products_order[14], products_order[20]), start=1):
            link = preferred_supplier(sku)
            order_day = date(2022, 12, 1) + timedelta(days=index * 3)
            ordered_at = _aware(config, order_day, 11, index * 7)
            arrival = ordered_at + timedelta(days=7 + index)
            location = warehouse_codes[index % len(warehouse_codes)]
            cost = _cost_for(master, sku, procurement_rng, index + 3, index + 2, price_rng)
            payload = {"sku": sku, "location": location, "quantity": 3 + index, "supplier_code": link.supplier_code,
                       "employee_code": None, "expected_on": arrival.date(), "unit_cost": cost,
                       "partial": False, "arrival": arrival, "second_arrival": None}
            push(ordered_at, 1, f"BOOTSTRAP-EXTRA-{index:02d}", "purchase_order", payload)

    def schedule_restock(sku: str, location: str, at: datetime) -> None:
        key = (sku, location)
        if key in pending_restock:
            return
        lead_days = 6 + inventory_rng.randrange(6)
        arrival = at + timedelta(days=lead_days)
        if arrival > cutoff:
            return
        link = preferred_supplier(sku)
        position = positions[key]
        target = 7 if FAMILIES[products[sku].category_code][1] in {"NOTEBOOK", "DESKTOP", "GRAPHICS"} else 10
        quantity = max(3, target - position.on_hand_quantity)
        purchase_counter_hint = len(result.purchase_orders) + 1
        cost = _cost_for(master, sku, procurement_rng, purchase_counter_hint, at.month, prices)
        payload = {"sku": sku, "location": location, "quantity": quantity, "supplier_code": link.supplier_code,
                   "employee_code": None, "expected_on": arrival.date(), "unit_cost": cost,
                   "partial": False, "arrival": arrival, "second_arrival": None,
                   "restock_key": f"RESTOCK-{sku}-{location}-{at.strftime('%Y%m%d%H%M%S')}"}
        pending_restock.add(key)
        push(at, 1, payload["restock_key"] + "-ORDER", "purchase_order", payload)

    def receive(payload: dict[str, Any], at: datetime) -> None:
        nonlocal receipt_counter
        po = po_by_key[payload["po_key"]]
        item = po_item_by_key[payload["item_key"]]
        receipt_counter += 1
        receipt_key = f"GR-KEY-{receipt_counter:04d}"
        receipt_number = f"GR-SM-{receipt_counter:04d}"
        receipt = GoodsReceipt(receipt_key, po.key, payload["location"], None, receipt_number, "completed", at)
        result.goods_receipts.append(receipt)
        receipt_item_key = f"GRI-KEY-{receipt_counter:04d}-01"
        row = GoodsReceiptItem(receipt_item_key, item.key, receipt_key, payload["received"], payload["accepted"], payload["rejected"], payload["cost"])
        result.goods_receipt_items.append(row)
        received_by_po_item[item.key] += payload["received"]
        position_key = (item.product_sku, payload["location"])
        position = positions.setdefault(position_key, StockPosition(*position_key))
        if payload["accepted"]:
            position.average_unit_cost = weighted_moving_average(position.on_hand_quantity, position.average_unit_cost, payload["accepted"], payload["cost"])
            position.on_hand_quantity += payload["accepted"]
            add_movement(item.product_sku, payload["location"], "receipt", payload["accepted"], payload["cost"], at, receipt_item_key=receipt_item_key)
        if received_by_po_item[item.key] == item.quantity_ordered:
            po.status = "received"
        elif received_by_po_item[item.key] > 0:
            po.status = "partially_received"
        result.event_trace.append((at, "receipt", receipt_key))
        if payload.get("restock_key"):
            pending_restock.discard(position_key)
        elif payload.get("partial") and payload["suffix"] == "A":
            return

    def suitable_salesperson(store_code: str, at: datetime) -> str | None:
        day = at.date()
        candidates = sorted({
            row.employee_code for row in sales_assignments
            if (row.store_code is None or row.store_code == store_code)
            and row.valid_from <= day and (row.valid_to is None or row.valid_to >= day)
            and row.employee_code in employees and employees[row.employee_code].status == "active"
            and employees[row.employee_code].hired_on <= day
            and (employees[row.employee_code].terminated_on is None or employees[row.employee_code].terminated_on >= day)
        })
        return candidates[sales_rng.randrange(len(candidates))] if candidates else None

    def available_locations(channel_type: str, store_code: str | None) -> list[str]:
        if channel_type == "physical":
            return [store_locations[store_code]] if store_code else []
        return warehouse_codes

    def allocate_order_discount(order_key: str, items: list[SaleOrderItem], at: datetime, gross: list[Decimal], index: int) -> Decimal:
        nonlocal discount_counter
        if index == 1:
            amount = _money(gross[0] * Decimal("0.05"))
            if amount < CENT:
                amount = CENT
            allocations = [amount if i == 0 else Decimal("0.00") for i in range(len(items))]
            scope = "line"
            code = "SM-LINE-05"
        else:
            if index == 2:
                amount = CENT
            elif index == 3:
                amount = CENT * 2
            else:
                ratio = Decimal(3 + index % 6) / Decimal(100)
                amount = min(_money(sum(gross, Decimal("0.00")) * ratio), sum(gross, Decimal("0.00")))
            allocations = allocate_cents(amount, gross)
            scope = "order_allocation"
            code = "SM-ORDER-ALLOC"
        for item, allocation in zip(items, allocations):
            if allocation > 0:
                discount_counter += 1
                result.applied_discounts.append(AppliedDiscount(
                    f"DISC-SM-{discount_counter:05d}", order_key, item.key, scope, allocation,
                    code, "Desconto sintético smoke", at,
                ))
        return amount

    def create_sale(event: ScheduledEvent) -> None:
        nonlocal order_counter, reservation_counter, fulfillment_counter, fulfillment_item_counter
        idx = event.payload["index"]
        at = event.occurred_at
        order_counter += 1
        order_key = f"ORDER-KEY-{order_counter:04d}"
        order_number = f"SO-SM-{order_counter:04d}"
        channel_code = event.payload["channel_code"]
        channel_type = channels[channel_code].channel_type
        store_code = event.payload["store_code"]
        customer_code = event.payload["customer_code"]
        address = addresses.get(customer_code) if customer_code and channel_type != "physical" else None
        address_key = address.logical_key if address else None
        snapshot = None if address is None else (
            address.recipient_name, address.postal_code, address.street, address.street_number,
            address.complement, address.district, address.city, address.state_code, address.country_code,
        )
        salesperson = suitable_salesperson(store_code, at) if channel_type == "physical" and store_code else None
        count = _line_count(idx)
        selected_skus = ["SKU-NOT-001"] if idx == 0 else []
        while len(selected_skus) < count:
            candidate = sorted(products)[sales_rng.randrange(len(products))]
            if candidate not in selected_skus:
                selected_skus.append(candidate)
        sale_items: list[SaleOrderItem] = []
        gross: list[Decimal] = []
        for line_no, sku in enumerate(selected_skus, start=1):
            item_key = f"{order_key}-LINE-{line_no:02d}"
            quantity = 5 if idx == 0 and line_no == 1 else (2 if customers.get(customer_code) and customers[customer_code].customer_type == "business" and sales_rng.random() < 0.35 else 1)
            price = prices[(sku, channel_code)]
            sale_item = SaleOrderItem(item_key, order_key, line_no, sku, quantity, price)
            sale_items.append(sale_item)
            gross.append(_money(price * quantity))
            item_product[item_key] = sku
            item_order[item_key] = order_key
        subtotal = sum(gross, Decimal("0.00"))
        discount = Decimal("0.00")
        if idx in {1, 2, 3} or (idx % 100 != 0 and sales_rng.random() < Decimal("0.38")):
            discount = allocate_order_discount(order_key, sale_items, at, gross, idx)
        is_cancelled = idx in PARTIAL_CANCEL_INDICES
        fulfillment_type = "store_pickup" if channel_type == "physical" or (idx % 13 == 0 and channel_type == "ecommerce") else "delivery"
        shipping = Decimal("0.00") if fulfillment_type == "store_pickup" else Decimal("14.90")
        total = _money(subtotal - discount + shipping)
        order = SaleOrder(order_key, order_number, channel_code, channel_type, customer_code, store_code,
                          salesperson, address_key, "placed", at, subtotal, discount, shipping, total, snapshot)
        result.sales_orders.append(order)
        result_by_order[order_key] = order
        items_by_order[order_key] = sale_items
        result.sales_order_items.extend(sale_items)
        result.order_status_history.extend((
            OrderStatusEvent(order_key, "draft", at - timedelta(minutes=5), salesperson),
            OrderStatusEvent(order_key, "placed", at, salesperson),
        ))

        # Reserve only current availability; no event inspects future orders or receipts.
        allocations_by_location: dict[str, list[tuple[SaleOrderItem, int]]] = {}
        for sale_item in sale_items:
            remaining = sale_item.quantity
            candidates = available_locations(channel_type, store_code)
            candidates = sorted(candidates, key=lambda code: (-positions.get((sale_item.product_sku, code), StockPosition(sale_item.product_sku, code)).available_quantity, code))
            for location in candidates:
                position = positions.get((sale_item.product_sku, location))
                if position is None or position.available_quantity <= 0 or remaining <= 0:
                    continue
                take = min(remaining, position.available_quantity)
                remaining -= take
                position.reserved_quantity += take
                reservation_counter += 1
                reservation_key = f"RES-KEY-{reservation_counter:05d}"
                reservation = StockReservation(reservation_key, order_key, sale_item.key, sale_item.product_sku,
                                               location, take, "active", at + timedelta(minutes=2))
                result.stock_reservations.append(reservation)
                reservations_by_order.setdefault(order_key, []).append(reservation)
                state_counter_local = len(result.stock_state_events) + 1
                result.stock_state_events.append(StockStateEvent(f"STATE-{state_counter_local:06d}", at + timedelta(minutes=2),
                    "reserve", sale_item.product_sku, location, take, 10, reservation_key=reservation_key))
                allocations_by_location.setdefault(location, []).append((sale_item, take))
                if position.available_quantity <= 2:
                    schedule_restock(sale_item.product_sku, location, at + timedelta(minutes=2))

        fulfillment_groups = sorted(allocations_by_location.items()) if not is_cancelled else ()
        for location, line_allocations in fulfillment_groups:
            fulfillment_counter += 1
            fulfillment_key = f"FUL-KEY-{fulfillment_counter:05d}"
            delivery_at = at + timedelta(hours=6 + (idx + fulfillment_counter) % 18)
            delivery_at = min(delivery_at, cutoff)
            store_pickup = fulfillment_type == "store_pickup"
            pickup_store_code = (store_code or master.stores[idx % len(master.stores)].code) if store_pickup else None
            fulfillment = Fulfillment(
                fulfillment_key, order_key, f"FUL-SM-{fulfillment_counter:05d}", fulfillment_type,
                "completed", location, pickup_store_code,
                None if store_pickup else master.carriers[(idx + fulfillment_counter) % len(master.carriers)].code,
                at + timedelta(hours=2), delivery_at - timedelta(hours=1) if not store_pickup else None, delivery_at,
            )
            result.fulfillments.append(fulfillment)
            fulfillments_by_key[fulfillment_key] = fulfillment
            for sale_item, quantity in line_allocations:
                fulfillment_item_counter += 1
                fi_key = f"FULI-KEY-{fulfillment_item_counter:05d}"
                fulfillment_item = FulfillmentItem(fi_key, order_key, fulfillment_key, sale_item.key, quantity, 0)
                result.fulfillment_items.append(fulfillment_item)
                fulfillment_items_by_key[fi_key] = fulfillment_item
                push(delivery_at, 30, f"FULFILL-{fi_key}", "fulfill", {"fulfillment_item_key": fi_key})

        if is_cancelled:
            if allocations_by_location:
                result.order_status_history.append(OrderStatusEvent(order_key, "confirmed", at + timedelta(minutes=3), salesperson))
                order.status = "confirmed"
            cancel_at = at + timedelta(hours=4)
            push(cancel_at, 20, f"CANCEL-{order_key}", "cancel", {"order_key": order_key})
        else:
            result.order_status_history.append(OrderStatusEvent(order_key, "confirmed", at + timedelta(minutes=3), salesperson))
            order.status = "confirmed"
        result.event_trace.append((at, "sale", order_key))

    def cancel_order(order_key: str, at: datetime) -> None:
        order = result_by_order[order_key]
        for reservation in reservations_by_order.get(order_key, []):
            if reservation.status != "active":
                continue
            reservation.status = "released"
            reservation.released_at = at
            position = positions[(reservation.product_sku, reservation.location_code)]
            position.reserved_quantity -= reservation.quantity
            state_key = f"STATE-{len(result.stock_state_events) + 1:06d}"
            result.stock_state_events.append(StockStateEvent(state_key, at, "release", reservation.product_sku,
                reservation.location_code, reservation.quantity, 20, reservation_key=reservation.key))
        order.status = "cancelled"
        result.order_status_history.append(OrderStatusEvent(order_key, "cancelled", at, order.salesperson_code, "Cancelamento anterior ao fulfillment"))
        result.event_trace.append((at, "cancel", order_key))

    def fulfill(fulfillment_item_key: str, at: datetime) -> None:
        fi = fulfillment_items_by_key[fulfillment_item_key]
        fulfillment = fulfillments_by_key[fi.fulfillment_key]
        sale_item = next(row for row in items_by_order[fi.order_key] if row.key == fi.sale_item_key)
        reservations = [row for row in reservations_by_order[fi.order_key]
                       if row.item_key == sale_item.key and row.location_code == fulfillment.location_code and row.status == "active"]
        quantity = fi.quantity_allocated
        if sum(row.quantity for row in reservations) < quantity:
            raise ValueError("Fulfillment sem reserva ativa suficiente.")
        position = positions[(sale_item.product_sku, fulfillment.location_code)]
        if quantity > position.on_hand_quantity or quantity > position.reserved_quantity:
            raise ValueError("Fulfillment excede estoque físico ou reservado.")
        cost = position.average_unit_cost
        for reservation in reservations:
            reservation.status = "consumed"
            reservation.released_at = at
        position.on_hand_quantity -= quantity
        position.reserved_quantity -= quantity
        fi.fulfilled_quantity = quantity
        add_movement(sale_item.product_sku, fulfillment.location_code, "fulfillment", -quantity, cost, at,
                     fulfillment_item_key=fi.key, reservation_key=reservations[0].key)
        result.event_trace.append((at, "fulfillment", fi.key))
        order = result_by_order[fi.order_key]
        fulfilled = sum(row.fulfilled_quantity for row in result.fulfillment_items if row.order_key == fi.order_key)
        ordered = sum(row.quantity for row in items_by_order[fi.order_key])
        if fulfilled == ordered and order.status not in {"cancelled", "completed"}:
            order.status = "completed"
            if not any(row.status == "completed" for row in result.order_status_history if row.order_key == order.key):
                result.order_status_history.append(OrderStatusEvent(order.key, "completed", at, order.salesperson_code))

    # Bootstrap procurement is represented as purchase-order and receipt events.
    bootstrap_plan()
    days = (config.end_date - config.start_date).days - 1
    sales_start = config.start_date + timedelta(days=1)
    sales_last = config.end_date - timedelta(days=1)
    span = (sales_last - sales_start).days
    channel_codes = {"physical": "CH-PHYSICAL", "ecommerce": "CH-ECOM", "marketplace_a": "CH-MARKET-A", "marketplace_b": "CH-MARKET-B"}
    for index in range(ORDER_COUNT):
        # Uniformly spread intents across the full commercial horizon, with stable within-day times.
        day = sales_start + timedelta(days=(span * index // (ORDER_COUNT - 1)))
        hour = 9 + (index * 7) % 10
        minute = (index * 17) % 60
        if index == 0:
            channel_code = "CH-ECOM"
        else:
            roll = sales_rng.randrange(100)
            channel_code = channel_codes["physical"] if roll < 52 else channel_codes["ecommerce"] if roll < 80 else channel_codes["marketplace_a"] if roll < 90 else channel_codes["marketplace_b"]
        channel_type = channels[channel_code].channel_type
        open_stores = sorted((row for row in master.stores if row.opened_on <= day), key=lambda row: row.code)
        store_code = open_stores[index % len(open_stores)].code if channel_type == "physical" and open_stores else None
        if channel_type == "physical" and index % 10 < 3:
            customer_code = None
        else:
            customer_code = master.customers[sales_rng.randrange(len(master.customers))].code
        push(_aware(config, day, hour, minute), 10, f"SALE-INTENT-{index + 1:04d}", "sale", {
            "index": index, "channel_code": channel_code, "store_code": store_code,
            "customer_code": customer_code,
        })

    while queue:
        event = queue.pop()
        if event.occurred_at > cutoff:
            raise ValueError("Evento ultrapassa o cutoff comercial.")
        result.event_trace.append((event.occurred_at, event.event_type, event.logical_key))
        if event.event_type == "purchase_order":
            po_key, item_key = create_purchase(event.payload, event.occurred_at)
            if event.payload.get("restock_key"):
                pending_restock.add((event.payload["sku"], event.payload["location"]))
            arrival = event.payload["arrival"]
            if event.payload.get("partial"):
                first_qty, second_qty = 4, event.payload["quantity"] - 4
                schedule_receipt(po_key, item_key, event.payload["location"], arrival, first_qty, first_qty, 0,
                                 event.payload["unit_cost"], "A")
                second_cost = _cost(event.payload["unit_cost"] * Decimal("1.025"))
                schedule_receipt(po_key, item_key, event.payload["location"], event.payload["second_arrival"],
                                 second_qty, second_qty - 1, 1, second_cost, "B")
            elif event.payload.get("reject_one") and event.payload.get("restock_key") is None:
                qty = event.payload["quantity"]
                schedule_receipt(po_key, item_key, event.payload["location"], arrival, qty, qty - 1, 1,
                                 event.payload["unit_cost"], "A")
            else:
                qty = event.payload["quantity"]
                schedule_receipt(po_key, item_key, event.payload["location"], arrival, qty, qty, 0,
                                 event.payload["unit_cost"], "A")
        elif event.event_type == "receipt":
            receive(event.payload, event.occurred_at)
        elif event.event_type == "sale":
            create_sale(event)
        elif event.event_type == "cancel":
            cancel_order(event.payload["order_key"], event.occurred_at)
        elif event.event_type == "fulfill":
            fulfill(event.payload["fulfillment_item_key"], event.occurred_at)
        else:
            raise ValueError(f"Tipo de evento não suportado: {event.event_type}")

    result.stock_positions = positions
    result.stock_state_events.sort(key=lambda row: (row.occurred_at, row.priority, row.key))
    result.event_trace.sort(key=lambda row: (row[0], row[1], row[2]))
    return result
