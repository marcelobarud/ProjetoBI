"""Event-driven smoke procurement, inventory, sales and fulfillment engine."""

from __future__ import annotations

import heapq
import hashlib
import random
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta
from decimal import Decimal, ROUND_DOWN, ROUND_HALF_UP
from typing import Any

from projectbi_generator.config import GeneratorConfig
from projectbi_generator.cancellations import cancellation_amounts
from projectbi_generator.generators.master import FAMILIES, generate_master_data
from projectbi_generator.models.entities import MasterData
from projectbi_generator.models.transactions import (
    AppliedDiscount, Fulfillment, FulfillmentItem, GoodsReceipt, GoodsReceiptItem,
    OrderStatusEvent, PurchaseOrder, PurchaseOrderItem, SaleOrder, SaleOrderItem,
    SalesOrderItemCancellation, StockMovement, StockPosition, StockReservation, StockStateEvent, TransactionData,
)
from projectbi_generator.seeds import create_domain_randoms
from projectbi_generator.supply_policy import (
    bootstrap_location_plan,
    blended_daily_demand_rate,
    replenishment_quantity,
    transferable_surplus,
)
from projectbi_generator.sales_plan import (
    CustomerFrequencyTickets, SalesIntentQuota, build_sales_intent_quotas,
)
from projectbi_generator.generators.streaming import StreamingCoreResult
from projectbi_generator.generators.backorders import BackorderLine, StockBackorderIndex
from projectbi_generator.sinks import TransactionBatchEmitter, TransactionSink

CENT = Decimal("0.01")
COST_SCALE = Decimal("0.00000001")
CUTOFF_TIME = time(23, 59, 59)
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
        self.max_pending_events = 0
        self.total_pushed = 0
        self.total_popped = 0

    def push(self, event: ScheduledEvent) -> None:
        if event.logical_key in self._keys:
            raise ValueError("Chave lógica de evento duplicada.")
        self._keys.add(event.logical_key)
        heapq.heappush(self._items, event)
        self.total_pushed += 1
        self.max_pending_events = max(self.max_pending_events, len(self._items))

    def pop(self) -> ScheduledEvent:
        event = heapq.heappop(self._items)
        self._keys.discard(event.logical_key)
        self.total_popped += 1
        return event

    def peek(self) -> ScheduledEvent:
        return self._items[0]

    @property
    def pending_events(self) -> int:
        return len(self._items)

    def has_event_type(self, event_types: set[str]) -> bool:
        return any(row.event_type in event_types for row in self._items)

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


def _location_balanced_bootstrap_plan(
    total: int, product_index: int, store_locations: list[str], warehouse_codes: list[str]
) -> list[tuple[str, int]]:
    return bootstrap_location_plan(
        total, store_locations, warehouse_codes, 52, rotation_key=f"legacy:{product_index}"
    )


def _price_map(master: MasterData) -> dict[tuple[str, str], Decimal]:
    return {(row.product_sku, row.channel_code): row.amount for row in master.product_prices}


def _price_period_index(master: MasterData) -> dict[tuple[str, str], tuple]:
    grouped: dict[tuple[str, str], list] = {}
    for row in master.product_prices:
        grouped.setdefault((row.product_sku, row.channel_code), []).append(row)
    return {key: tuple(sorted(rows, key=lambda row: row.valid_from)) for key, rows in grouped.items()}


def _price_at(periods: dict[tuple[str, str], tuple], sku: str, channel: str, at: datetime) -> Decimal:
    for row in reversed(periods[(sku, channel)]):
        if row.valid_from <= at and (row.valid_to is None or at < row.valid_to):
            return row.amount
    raise ValueError("Não existe preço vigente para produto/canal no instante do pedido.")


def _cost_for(
    master: MasterData,
    sku: str,
    rng: random.Random,
    supplier_ordinal: int,
    period_ordinal: int,
    prices: dict[tuple[str, str], Decimal],
    products_by_sku: dict | None = None,
    *,
    at: datetime | None = None,
    price_periods: dict[tuple[str, str], tuple] | None = None,
) -> Decimal:
    product = products_by_sku[sku] if products_by_sku is not None else next(row for row in master.products if row.sku == sku)
    family = FAMILIES[product.category_code][1]
    low, high = FAMILY_COST_FACTORS[family]
    if at is not None and price_periods is not None:
        active_prices = [
            row.amount
            for channel in master.sales_channels
            for row in reversed(price_periods[(sku, channel.code)])
            if row.valid_from <= at and (row.valid_to is None or at < row.valid_to)
        ]
        if len(active_prices) != len(master.sales_channels):
            raise ValueError("Não existe preço vigente para calcular custo de aquisição no instante informado.")
        ordered_prices = sorted(active_prices)
        middle = len(ordered_prices) // 2
        retail = (ordered_prices[middle - 1] + ordered_prices[middle]) / Decimal(2) if len(ordered_prices) % 2 == 0 else ordered_prices[middle]
    else:
        retail = min(prices[(sku, channel.code)] for channel in master.sales_channels)
    factor = low + (high - low) * Decimal(rng.randrange(1001)) / Decimal(1000)
    supplier_adjustment = Decimal((supplier_ordinal % 5) - 2) / Decimal(100)
    period_adjustment = Decimal((period_ordinal % 3) - 1) / Decimal(100)
    final_factor = min(Decimal("0.90"), max(Decimal("0.50"), factor + supplier_adjustment + period_adjustment))
    return _cost(retail * final_factor)


def generate_transactions(
    config: GeneratorConfig,
    master: MasterData | None = None,
    *,
    sink: TransactionSink | None = None,
    batch_size: int | None = None,
    incremental_completion: bool = False,
    single_card_index: int | None = None,
    policy_preflight: bool = False,
    forced_fallback_ordinals: dict[str, int] | None = None,
) -> TransactionData | StreamingCoreResult:
    """Generate causal 3C facts; an optional sink selects non-collecting streaming output."""
    master = master or generate_master_data(config)
    prices = _price_map(master)
    price_periods = _price_period_index(master)
    randoms = create_domain_randoms(config.root_seed, config.generator_version)
    procurement_rng = randoms["procurement"].rng
    sales_rng = randoms["sales"].rng
    sales_content_seed = randoms["sales"].seed
    sales_intent_rng = randoms["sales_intents"].rng
    inventory_rng = randoms["inventory"].rng
    queue = EventQueue()
    emitter = TransactionBatchEmitter(sink, batch_size or config.batch_size) if sink is not None else None
    result = StreamingCoreResult(emitter) if emitter is not None else TransactionData()
    if incremental_completion and not isinstance(result, StreamingCoreResult):
        raise ValueError("A extensão incremental exige TransactionSink.")
    cutoff = _aware(config, config.end_date, CUTOFF_TIME.hour, CUTOFF_TIME.minute)
    products = {row.sku: row for row in master.products}
    product_skus = tuple(sorted(products))
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
    pending_restock: dict[tuple[str, str], int] = {}
    pending_transfer_in: dict[tuple[str, str], int] = {}
    pending_transfer_out: dict[tuple[str, str], int] = {}
    active_supply_transfer_edges: set[tuple[str, str, str]] = set()
    supply_transfer_edge_by_item: dict[str, tuple[str, str, str]] = {}
    recent_demand: dict[tuple[str, str], deque[tuple[date, int]]] = defaultdict(deque)
    supply_transfer_enabled = bool(config.generation.get("supply_transfer_enabled", 0))
    coverage_replenishment_enabled = bool(config.generation.get("coverage_replenishment_enabled", 0))
    if supply_transfer_enabled and not incremental_completion:
        raise ValueError("Transferências da política de abastecimento exigem o fluxo incremental 3D.")
    result_by_order: dict[str, SaleOrder] = {}
    reservations_by_order: dict[str, list[StockReservation]] = {}
    unassigned_reservations: dict[tuple[str, str, str], deque[str]] = defaultdict(deque)
    reservations_by_fulfillment_item: dict[str, list[str]] = {}
    fulfillments_by_key: dict[str, Fulfillment] = {}
    fulfillment_items_by_key: dict[str, FulfillmentItem] = {}
    sale_item_by_key: dict[str, SaleOrderItem] = {}
    sale_item_keys_by_order: dict[str, list[str]] = {}
    fulfillment_keys_by_order: dict[str, list[str]] = {}
    pending_fulfillments_by_order: dict[str, int] = {}
    fulfillment_count_by_order: dict[str, int] = {}
    outstanding_lines_by_order: dict[str, int] = {}
    backorders = StockBackorderIndex()
    backorder_expired_partial: set[str] = set()
    expired_partial_samples: list[dict[str, Any]] = []
    order_index_by_key: dict[str, int] = {}
    fulfillment_type_by_order: dict[str, str] = {}
    ordered_quantity_by_order: dict[str, int] = {}
    fulfilled_quantity_by_order: dict[str, int] = {}
    fulfilled_quantity_by_item: dict[str, int] = {}
    cancelled_quantity_by_item: dict[str, int] = {}
    po_by_key: dict[str, PurchaseOrder] = {}
    po_item_by_key: dict[str, PurchaseOrderItem] = {}
    received_by_po_item: dict[str, int] = {}
    state_counter = 0
    max_active_purchase_orders = 0
    movement_counter = 0
    purchase_counter = 0
    restock_request_counter = 0
    receipt_counter = 0
    order_counter = 0
    accepted_orders_by_plan_cell: dict[tuple[int, int, str], int] = defaultdict(int)
    customer_frequency_tickets: CustomerFrequencyTickets | None = None
    sales_intentions_processed = 0
    reservation_counter = 0
    fulfillment_counter = 0
    fulfillment_item_counter = 0
    discount_counter = 0
    cancellation_counter = 0
    discount_by_item: dict[str, Decimal] = {}
    completion_state = None
    stock_audit_enabled = bool(config.generation.get("stock_audit", 0))
    stock_audit_rows: dict[tuple[int, str, str, str, str, str], dict[str, int]] = {}
    stock_audit_periods: dict[tuple[int, str, str], dict[str, int]] = {}
    stock_audit_events: list[StockStateEvent] | None = [] if stock_audit_enabled else None
    sales_intention_digest = hashlib.sha256()
    if isinstance(result, StreamingCoreResult):
        result.runtime_metrics.update({
            "current_stock_backorder_orders": 0,
            "max_stock_backorder_orders": 0,
            "stock_backorder_lines_resolved": 0,
            "stock_backorder_units_fulfilled": 0,
            "stock_wait_expired_orders": 0,
            "stock_wait_expired_partial_orders": 0,
            "stock_backorder_orders_at_cutoff": 0,
            "stock_replenishment_requests_beyond_cutoff": 0,
            "stock_replenishment_units_beyond_cutoff": 0,
            "supply_policy_transfers": 0,
            "supply_policy_transfer_units": 0,
            "supply_policy_transfer_days_total": 0,
            "supply_policy_procurement_units": 0,
            "supply_policy_demand_observed_units": 0,
        })

    def audit_add(key: tuple[int, str, str, str, str, str], measure: str, amount: int) -> None:
        if not stock_audit_enabled or not amount:
            return
        metrics = stock_audit_rows.setdefault(key, {})
        metrics[measure] = metrics.get(measure, 0) + amount

    def audit_period_add(year: int, channel_type: str, channel_code: str, measure: str, amount: int = 1) -> None:
        if not stock_audit_enabled:
            return
        metrics = stock_audit_periods.setdefault((year, channel_type, channel_code), {})
        metrics[measure] = metrics.get(measure, 0) + amount

    def audit_key(year: int, channel_type: str, channel_code: str, store_code: str | None,
                  sku: str, location: str) -> tuple[int, str, str, str, str, str]:
        return (year, channel_type, channel_code, store_code or "", sku, location)

    def push(at: datetime, priority: int, key: str, event_type: str, payload: dict[str, Any]) -> None:
        if at > cutoff:
            return
        queue.push(ScheduledEvent(at, priority, key, event_type, payload))

    if incremental_completion:
        from projectbi_generator.generators.completion_stream import IncrementalCompletionState
        completion_state = IncrementalCompletionState(
            config, master, result, push, single_card_index,
            policy_preflight=policy_preflight,
            forced_fallback_ordinals=forced_fallback_ordinals,
        )

    def append_stock_state(row: StockStateEvent) -> None:
        result.stock_state_events.append(row)
        if stock_audit_events is not None:
            stock_audit_events.append(row)
        if completion_state is not None:
            completion_state.on_core_state(row)

    def publish(table: str, key: str) -> None:
        collection = getattr(result, table)
        if hasattr(collection, "publish"):
            collection.publish(key)
            if table in {"purchase_orders", "purchase_order_items"} and isinstance(result, StreamingCoreResult):
                result.release_transaction_id(table, key)

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
        nonlocal movement_counter, state_counter
        movement_counter += 1
        key = f"MOV-SM-{movement_counter:06d}"
        movement = StockMovement(key, sku, location, kind, qty_delta, unit_cost, at, receipt_item_key, fulfillment_item_key)
        result.stock_movements.append(movement)
        if completion_state is not None and kind in {"receipt", "fulfillment"}:
            completion_state.on_core_movement(movement)
        state_counter += 1
        state_key = f"STATE-{state_counter:06d}"
        priority = 0 if kind == "receipt" else 30
        append_stock_state(StockStateEvent(state_key, at, kind, sku, location, abs(qty_delta), priority, unit_cost, key, reservation_key))
        return key

    def create_purchase(payload: dict[str, Any], at: datetime) -> tuple[str, str]:
        nonlocal purchase_counter, max_active_purchase_orders
        purchase_counter += 1
        po_key = f"PO-KEY-{purchase_counter:04d}"
        number = f"PO-SM-{purchase_counter:04d}"
        po = PurchaseOrder(po_key, number, payload["supplier_code"], payload.get("employee_code"), "submitted", at, payload["expected_on"])
        result.purchase_orders.append(po)
        po_by_key[po_key] = po
        item_key = f"POI-KEY-{purchase_counter:04d}-01"
        line = PurchaseOrderItem(item_key, po_key, 1, payload["sku"], payload["quantity"], payload["unit_cost"])
        result.purchase_order_items.append(line)
        audit_add(audit_key(at.year, "supply", "procurement", None, payload["sku"], payload["location"]),
                  "purchase_units_ordered", payload["quantity"])
        if payload.get("bootstrap_core") and at.date() < config.start_date:
            audit_add(audit_key(config.start_date.year, "bootstrap", "core", None,
                                payload["sku"], payload["location"]),
                      "bootstrap_core_units", payload["quantity"])
        po_item_by_key[item_key] = line
        received_by_po_item[item_key] = 0
        max_active_purchase_orders = max(max_active_purchase_orders, len(po_by_key))
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
            balance_setting = config.generation.get("bootstrap_location_balance", 0)
            share_percent = 52 if balance_setting == 1 else balance_setting
            if index == 0:
                plans = [(warehouse_codes[0], 2), (warehouse_codes[1], 2)]
            elif index == 1:
                plans = [(warehouse_codes[0], 12)]
            else:
                quantity_override = config.generation.get("bootstrap_quantity_by_sku")
                quantity = (quantity_override[sku] if quantity_override is not None
                            else procurement_rng.randint(9, 15))
                if config.profile != "smoke" and share_percent:
                    plans = bootstrap_location_plan(
                        quantity, list(store_locations.values()), warehouse_codes, int(share_percent),
                        rotation_key=f"{config.root_seed}:{sku}",
                    )
                else:
                    plans = [(location_codes[(index - 2) % len(location_codes)], quantity)]
            distributed = (config.profile != "smoke" and index >= 2
                           and bool(config.generation.get("bootstrap_location_balance", 0)))
            # Keep one bootstrap cost draw per original SKU plan; variants therefore
            # do not perturb the procurement RNG used by later replenishments.
            base_part = 1
            base_cost = (_cost_for(
                master, sku, procurement_rng, base_part + index, index + base_part, price_rng, products,
                at=_aware(config, config.bootstrap_start_date, 9) if config.profile != "smoke" else None,
                price_periods=price_periods if config.profile != "smoke" else None,
            ) if distributed else None)
            for part, (location, quantity) in enumerate(plans, start=1):
                effective_part = base_part if distributed else part
                order_day = config.bootstrap_start_date + timedelta(days=(index * 2 + effective_part) % 42)
                ordered_at = _aware(config, order_day, 9 + (index % 7), index % 60)
                partial = index == 1
                lead1 = 5 + (index + effective_part) % 6
                first_arrival = ordered_at + timedelta(days=lead1)
                second_arrival = first_arrival + timedelta(days=4)
                final_arrival = second_arrival if partial else first_arrival
                # The two split-source receipts for SKU 001 guarantee the first split fulfillment.
                if index == 0:
                    first_arrival = ordered_at + timedelta(days=5 + part)
                    final_arrival = first_arrival
                cost = base_cost if distributed else _cost_for(
                    master, sku, procurement_rng, part + index, index + part, price_rng, products,
                    at=ordered_at if config.profile != "smoke" else None,
                    price_periods=price_periods if config.profile != "smoke" else None,
                )
                reject_one = index == 2 and (not distributed or part == 1)
                payload = {
                    "sku": sku, "location": location, "quantity": quantity,
                    "supplier_code": link.supplier_code,
                    "employee_code": None,
                    "expected_on": final_arrival.date(), "unit_cost": cost,
                    "partial": partial, "reject_one": reject_one, "arrival": first_arrival,
                    "bootstrap_core": True,
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
            cost = _cost_for(master, sku, procurement_rng, index + 3, index + 2, price_rng, products,
                             at=ordered_at if config.profile != "smoke" else None,
                             price_periods=price_periods if config.profile != "smoke" else None)
            payload = {"sku": sku, "location": location, "quantity": 3 + index, "supplier_code": link.supplier_code,
                       "employee_code": None, "expected_on": arrival.date(), "unit_cost": cost,
                       "partial": False, "arrival": arrival, "second_arrival": None}
            push(ordered_at, 1, f"BOOTSTRAP-EXTRA-{index:02d}", "purchase_order", payload)

    def observe_demand(sku: str, location: str, at: datetime, quantity: int) -> None:
        if quantity <= 0:
            return
        key = (sku, location)
        day = at.date()
        rows = recent_demand[key]
        rows.append((day, quantity))
        cutoff_day = day - timedelta(days=89)
        while rows and rows[0][0] < cutoff_day:
            rows.popleft()
        if isinstance(result, StreamingCoreResult):
            result.runtime_metrics["supply_policy_demand_observed_units"] += quantity

    def estimated_daily_demand(sku: str, location: str, at: datetime) -> Decimal:
        day = at.date()
        key = (sku, location)
        rows = recent_demand[key]
        window_start = day - timedelta(days=89)
        while rows and rows[0][0] < window_start:
            rows.popleft()
        elapsed_days = max(1, min(90, (day - config.start_date).days + 1))
        observed_units = sum(quantity for _observed_day, quantity in rows)
        is_store = location in store_locations.values()
        active_stores = max(1, sum(store.opened_on <= day for store in stores.values()))
        location_count = active_stores if is_store else max(1, len(warehouse_codes))
        channel_share = Decimal("0.52") if is_store else Decimal("0.48")
        horizon_days = max(1, (config.end_date - config.start_date).days + 1)
        expected_lines = Decimal("2.1")  # exact mean of the deterministic line-count cycle
        prior_rate = (
            Decimal(config.sales_order_target) * expected_lines * channel_share
            / Decimal(horizon_days * max(1, len(products)) * location_count)
        )
        return blended_daily_demand_rate(observed_units, elapsed_days, prior_rate, prior_strength_days=60)

    def schedule_supply_transfer(
        sku: str, destination: str, at: datetime, requested_quantity: int, supplier_lead_days: int,
    ) -> int:
        if completion_state is None or requested_quantity <= 0:
            return 0
        family = FAMILIES[products[sku].category_code][1]
        safety_units = (2 if family in {"NOTEBOOK", "DESKTOP", "GRAPHICS"} else 1) * int(
            config.generation.get("coverage_safety_units", 1)
        )
        # requested_quantity is already the net deficit after confirmed inbound
        # (purchase orders and transfers) was included in the inventory position.
        destination_key = (sku, destination)
        quantity_left = requested_quantity
        if not quantity_left:
            return 0
        candidates: list[tuple[int, int, str, datetime, datetime, int]] = []
        for source in warehouse_codes:
            if source == destination:
                continue
            edge = (sku, source, destination)
            if edge in active_supply_transfer_edges:
                continue
            digest = hashlib.sha256(f"{config.root_seed}:{sku}:{source}:{destination}".encode("utf-8")).digest()
            transit_days = 2 + digest[0] % 4
            dispatched_at = at + timedelta(hours=8)
            received_at = dispatched_at + timedelta(days=transit_days)
            if received_at > cutoff or received_at > at + timedelta(days=supplier_lead_days):
                continue
            key = (sku, source)
            position = positions.get(key)
            available = max(0, (position.available_quantity if position else 0)
                            - pending_transfer_out.get(key, 0))
            source_rate = estimated_daily_demand(sku, source, at)
            surplus = transferable_surplus(
                available=available,
                backorder_units=backorders.pending_quantity(sku, source),
                daily_rate=source_rate,
                transit_days=transit_days,
                safety_units=safety_units,
            )
            if surplus:
                candidates.append((transit_days, -surplus, source, dispatched_at, received_at, surplus))
        moved = 0
        for _days, _negative_surplus, source, dispatched_at, received_at, surplus in sorted(candidates):
            quantity = min(quantity_left, surplus)
            item_key = completion_state.schedule_supply_transfer(
                sku=sku, source=source, destination=destination, quantity=quantity,
                requested_at=at, dispatched_at=dispatched_at, received_at=received_at,
            )
            edge = (sku, source, destination)
            active_supply_transfer_edges.add(edge)
            supply_transfer_edge_by_item[item_key] = edge
            source_key = (sku, source)
            pending_transfer_out[source_key] = pending_transfer_out.get(source_key, 0) + quantity
            pending_transfer_in[destination_key] = pending_transfer_in.get(destination_key, 0) + quantity
            moved += quantity
            quantity_left -= quantity
            if quantity_left <= 0:
                break
        return moved

    def schedule_restock(sku: str, location: str, at: datetime, requested_quantity: int = 0) -> None:
        nonlocal restock_request_counter
        key = (sku, location)
        if config.profile == "smoke" and key in pending_restock:
            return
        lead_days = 6 + inventory_rng.randrange(6)
        arrival = at + timedelta(days=lead_days)
        link = preferred_supplier(sku)
        position = positions.setdefault(key, StockPosition(sku, location))
        if coverage_replenishment_enabled and config.profile != "smoke":
            rate = estimated_daily_demand(sku, location, at)
            family = FAMILIES[products[sku].category_code][1]
            safety_units = 2 if family in {"NOTEBOOK", "DESKTOP", "GRAPHICS"} else 1
            backorder_units = backorders.pending_quantity(sku, location)
            quantity = replenishment_quantity(
                available=max(0, position.available_quantity - pending_transfer_out.get(key, 0)),
                confirmed_inbound=pending_restock.get(key, 0) + pending_transfer_in.get(key, 0),
                backorder_units=backorder_units,
                daily_rate=rate,
                supplier_lead_days=lead_days,
                review_days=int(config.generation.get("coverage_review_days", 14)),
                safety_units=int(config.generation.get("coverage_safety_units", 1)) * safety_units,
            )
            quantity = max(quantity, requested_quantity)
        else:
            target = 7 if FAMILIES[products[sku].category_code][1] in {"NOTEBOOK", "DESKTOP", "GRAPHICS"} else 10
            stock_basis = position.on_hand_quantity if config.profile == "smoke" else max(
                0, position.available_quantity - pending_transfer_out.get(key, 0)
            )
            desired = (max(3, target - stock_basis) if config.profile == "smoke"
                       else max(3, target - stock_basis, requested_quantity))
            quantity = max(0, desired - pending_restock.get(key, 0) - pending_transfer_in.get(key, 0))
        if quantity == 0:
            return
        if supply_transfer_enabled and config.profile != "smoke" and location in store_locations.values():
            transferred = schedule_supply_transfer(sku, location, at, quantity, lead_days)
            quantity -= transferred
        if quantity <= 0:
            return
        if arrival > cutoff:
            if isinstance(result, StreamingCoreResult):
                result.runtime_metrics["stock_replenishment_requests_beyond_cutoff"] += 1
                result.runtime_metrics["stock_replenishment_units_beyond_cutoff"] += quantity
            return
        purchase_counter_hint = purchase_counter + 1
        cost = _cost_for(master, sku, procurement_rng, purchase_counter_hint, at.month, prices, products,
                         at=at if config.profile != "smoke" else None,
                         price_periods=price_periods if config.profile != "smoke" else None)
        restock_request_counter += 1
        restock_suffix = "" if config.profile == "smoke" else f"-{restock_request_counter:07d}"
        payload = {"sku": sku, "location": location, "quantity": quantity, "supplier_code": link.supplier_code,
                   "employee_code": None, "expected_on": arrival.date(), "unit_cost": cost,
                   "partial": False, "arrival": arrival, "second_arrival": None,
                   "restock_key": f"RESTOCK-{sku}-{location}-{at.strftime('%Y%m%d%H%M%S')}{restock_suffix}"}
        pending_restock[key] = pending_restock.get(key, 0) + quantity
        if isinstance(result, StreamingCoreResult):
            result.runtime_metrics["supply_policy_procurement_units"] += quantity
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
        if payload["accepted"] + payload["rejected"] != payload["received"]:
            raise ValueError("Quantidade aceita e rejeitada deve totalizar o recebimento.")
        row = GoodsReceiptItem(receipt_item_key, item.key, receipt_key, payload["received"], payload["accepted"], payload["rejected"], payload["cost"])
        result.goods_receipt_items.append(row)
        supply_key = audit_key(at.year, "supply", "procurement", None, item.product_sku, payload["location"])
        audit_add(supply_key, "units_received", payload["accepted"])
        audit_add(supply_key, "supplier_lead_time_count", 1)
        lead_minutes = int((at - po.ordered_at).total_seconds() // 60)
        audit_add(supply_key, "supplier_lead_time_minutes_total", lead_minutes)
        if stock_audit_enabled:
            audit_metric = stock_audit_rows.setdefault(supply_key, {})
            audit_metric["supplier_lead_time_minutes_max"] = max(audit_metric.get("supplier_lead_time_minutes_max", 0), lead_minutes)
        if at.date() < config.start_date:
            audit_add(audit_key(config.start_date.year, "opening", "bootstrap", None,
                                item.product_sku, payload["location"]), "opening_units", payload["accepted"])
        received_by_po_item[item.key] += payload["received"]
        if received_by_po_item[item.key] > item.quantity_ordered:
            raise ValueError("Recebimento supera a quantidade do item de compra.")
        position_key = (item.product_sku, payload["location"])
        position = positions.setdefault(position_key, StockPosition(*position_key))
        if payload["accepted"]:
            position.average_unit_cost = weighted_moving_average(position.on_hand_quantity, position.average_unit_cost, payload["accepted"], payload["cost"])
            position.on_hand_quantity += payload["accepted"]
            add_movement(item.product_sku, payload["location"], "receipt", payload["accepted"], payload["cost"], at, receipt_item_key=receipt_item_key)
        if received_by_po_item[item.key] == item.quantity_ordered:
            po.status = "received"
            publish("purchase_orders", po.key)
            publish("purchase_order_items", item.key)
            po_by_key.pop(po.key, None)
            po_item_by_key.pop(item.key, None)
            received_by_po_item.pop(item.key, None)
        elif received_by_po_item[item.key] > 0:
            po.status = "partially_received"
        result.event_trace.append((at, "receipt", receipt_key))
        if payload.get("restock_key"):
            if config.profile == "smoke":
                pending_restock.pop(position_key, None)
            else:
                remaining_inbound = pending_restock.get(position_key, 0) - payload["accepted"]
                if remaining_inbound > 0:
                    pending_restock[position_key] = remaining_inbound
                else:
                    pending_restock.pop(position_key, None)
        elif payload.get("partial") and payload["suffix"] == "A":
            return
        if payload["accepted"]:
            wake_backorders(item.product_sku, payload["location"], at)

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

    def allocate_order_discount(order_key: str, items: list[SaleOrderItem], at: datetime, gross: list[Decimal], index: int) -> tuple[Decimal, list[AppliedDiscount]]:
        nonlocal discount_counter
        emitted_rows: list[AppliedDiscount] = []
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
                is_black_friday = config.profile != "smoke" and at.month == 11 and at.year in {2023, 2024, 2025}
                ratio = Decimal(5 + index % 8 if is_black_friday else 3 + index % 6) / Decimal(100)
                amount = min(_money(sum(gross, Decimal("0.00")) * ratio), sum(gross, Decimal("0.00")))
            allocations = allocate_cents(amount, gross)
            scope = "order_allocation"
            code = "SM-ORDER-ALLOC"
        for item, allocation in zip(items, allocations):
            discount_by_item[item.key] = allocation
            if allocation > 0:
                discount_counter += 1
                emitted_rows.append(AppliedDiscount(
                    f"DISC-SM-{discount_counter:05d}", order_key, item.key, scope, allocation,
                    code, "Desconto sintético smoke", at,
                ))
        return amount, emitted_rows

    def finalize_order_3c(order_key: str) -> None:
        order = result_by_order.pop(order_key, None)
        if order is None:
            return
        publish("sales_orders", order_key)
        for reservation in reservations_by_order.pop(order_key, []):
            publish("stock_reservations", reservation.key)
        if isinstance(result, StreamingCoreResult):
            if completion_state is None:
                result.release_transaction_id("sales_orders", order_key)
            else:
                completion_state.on_core_order_finalized(order_key)
        for reservation_key in [key for key in unassigned_reservations if key[0] == order_key]:
            unassigned_reservations.pop(reservation_key, None)
        for item_key in sale_item_keys_by_order.pop(order_key, []):
            sale_item_by_key.pop(item_key, None)
            fulfilled_quantity_by_item.pop(item_key, None)
            cancelled_quantity_by_item.pop(item_key, None)
        for fulfillment_key in fulfillment_keys_by_order.pop(order_key, []):
            fulfillments_by_key.pop(fulfillment_key, None)
        ordered_quantity_by_order.pop(order_key, None)
        fulfilled_quantity_by_order.pop(order_key, None)
        pending_fulfillments_by_order.pop(order_key, None)
        fulfillment_count_by_order.pop(order_key, None)
        outstanding_lines_by_order.pop(order_key, None)
        order_index_by_key.pop(order_key, None)
        fulfillment_type_by_order.pop(order_key, None)
        if isinstance(result, StreamingCoreResult):
            result.runtime_metrics["current_active_orders"] = len(result_by_order)

    def schedule_fulfillment(order: SaleOrder, line_allocations: list[tuple[SaleOrderItem, int]],
                             location: str, at: datetime, index: int) -> bool:
        nonlocal fulfillment_counter, fulfillment_item_counter
        if not line_allocations or any(quantity <= 0 for _item, quantity in line_allocations):
            return False
        # A six hour minimum service interval keeps receipts near the cutoff pending.
        if config.profile != "smoke" and at + timedelta(hours=6) > cutoff:
            return False
        fulfillment_counter += 1
        fulfillment_key = f"FUL-KEY-{fulfillment_counter:05d}"
        delivery_at = min(at + timedelta(hours=6 + (index + fulfillment_counter) % 18), cutoff)
        fulfillment_type = fulfillment_type_by_order[order.key]
        store_pickup = fulfillment_type == "store_pickup"
        pickup_store_code = (order.store_code or master.stores[index % len(master.stores)].code) if store_pickup else None
        fulfillment = Fulfillment(
            fulfillment_key, order.key, f"FUL-SM-{fulfillment_counter:05d}", fulfillment_type,
            "completed", location, pickup_store_code,
            None if store_pickup else master.carriers[(index + fulfillment_counter) % len(master.carriers)].code,
            at + timedelta(hours=2), delivery_at - timedelta(hours=1) if not store_pickup else None, delivery_at,
        )
        result.fulfillments.append(fulfillment)
        if completion_state is not None:
            completion_state.on_fulfillment_created(fulfillment)
        fulfillments_by_key[fulfillment_key] = fulfillment
        fulfillment_keys_by_order[order.key].append(fulfillment_key)
        fulfillment_count_by_order[order.key] += 1
        if fulfillment_count_by_order[order.key] == 2 and isinstance(result, StreamingCoreResult):
            result.aggregates["split_fulfillments"] += 1
        for sale_item, quantity in line_allocations:
            fulfillment_item_counter += 1
            fi_key = f"FULI-KEY-{fulfillment_item_counter:05d}"
            fulfillment_item = FulfillmentItem(fi_key, order.key, fulfillment_key, sale_item.key, quantity, 0)
            result.fulfillment_items.append(fulfillment_item)
            fulfillment_items_by_key[fi_key] = fulfillment_item
            reservation_key_list = unassigned_reservations.pop((order.key, sale_item.key, location), deque())
            assigned_reservations: list[str] = []
            reserved_quantity = 0
            while reserved_quantity < quantity and reservation_key_list:
                reservation_key = reservation_key_list.popleft()
                reservation = next((row for row in reservations_by_order[order.key]
                                    if row.key == reservation_key), None)
                if reservation is None or reservation.status != "active":
                    continue
                assigned_reservations.append(reservation_key)
                reserved_quantity += reservation.quantity
            if reserved_quantity != quantity:
                raise ValueError(
                    "Agendamento de fulfillment não corresponde às reservas ativas: "
                    f"order={order.key}, sale_item={sale_item.key}, location={location}, "
                    f"allocated={quantity}, reserved={reserved_quantity}."
                )
            reservations_by_fulfillment_item[fi_key] = assigned_reservations
            pending_fulfillments_by_order[order.key] += 1
            push(delivery_at, 30, f"FULFILL-{fi_key}", "fulfill", {"fulfillment_item_key": fi_key})
        return True

    def update_backorder_metrics() -> None:
        if isinstance(result, StreamingCoreResult):
            result.runtime_metrics["current_stock_backorder_orders"] = backorders.active_orders
            result.runtime_metrics["max_stock_backorder_orders"] = max(
                result.runtime_metrics.get("max_stock_backorder_orders", 0), backorders.active_orders
            )

    def stock_audit_summary() -> dict[str, Any] | None:
        if not stock_audit_enabled:
            return None
        period_summary = []
        for (year, channel_type, channel_code), measures in sorted(stock_audit_periods.items()):
            item_measures: dict[str, int] = {}
            for key, row_measures in stock_audit_rows.items():
                if key[:3] == (year, channel_type, channel_code):
                    for name, amount in row_measures.items():
                        item_measures[name] = item_measures.get(name, 0) + amount
            period_summary.append({"year": year, "channel_type": channel_type, "channel": channel_code,
                                   **measures, **item_measures})
        bootstrap_units_by_sku: dict[str, int] = {}
        for key, measures in stock_audit_rows.items():
            if measures.get("bootstrap_core_units", 0):
                sku = key[4]
                bootstrap_units_by_sku[sku] = bootstrap_units_by_sku.get(sku, 0) + measures["bootstrap_core_units"]

        def grouped_summary(group_key, *, sales_only: bool = False) -> list[dict[str, Any]]:
            grouped: dict[str, dict[str, int]] = {}
            for key, measures in stock_audit_rows.items():
                _year, channel_type, _channel, store, sku, location = key
                if sales_only and channel_type == "supply":
                    continue
                label = group_key(key, products[sku].category_code)
                metrics = grouped.setdefault(label, {})
                for name, amount in measures.items():
                    metrics[name] = metrics.get(name, 0) + amount
            return [{"group": label, **metrics} for label, metrics in sorted(
                grouped.items(), key=lambda pair: (-pair[1].get("physical_demand_lost_units", 0),
                                                   -pair[1].get("backorder_units_expired", 0), pair[0]))]

        by_location: dict[tuple[str, str], dict[str, int]] = {}
        demand_by_sku_location: dict[tuple[str, str], int] = {}
        opening_by_sku_location: dict[tuple[str, str], int] = {}
        for key, measures in stock_audit_rows.items():
            _year, channel_type, _channel, _store, sku, location = key
            loc = by_location.setdefault((sku, location), {})
            for name, amount in measures.items():
                loc[name] = loc.get(name, 0) + amount
            if channel_type != "supply":
                demand_by_sku_location[(sku, location)] = demand_by_sku_location.get((sku, location), 0) + measures.get("demand_units", 0)
            opening_by_sku_location[(sku, location)] = opening_by_sku_location.get((sku, location), 0) + measures.get("opening_units", 0)

        loss_rows = []
        overdue_rows = []
        for key, measures in stock_audit_rows.items():
            year, channel_type, channel, store, sku, location = key
            record = {"year": year, "channel_type": channel_type, "channel": channel,
                      "store": store, "sku": sku, "category": products[sku].category_code,
                      "location": location, **measures}
            if measures.get("physical_demand_lost_units", 0):
                loss_rows.append(record)
            if measures.get("backorder_units_expired", 0):
                overdue_rows.append(record)
        loss_rows.sort(key=lambda row: (-row["physical_demand_lost_units"], row["year"], row["sku"], row["location"]))
        overdue_rows.sort(key=lambda row: (-row["backorder_units_expired"], row["year"], row["sku"], row["location"]))

        ending = []
        for (sku, location), position in positions.items():
            measures = by_location.get((sku, location), {})
            row = {"sku": sku, "category": products[sku].category_code, "location": location,
                   "opening_units": opening_by_sku_location.get((sku, location), 0),
                   "demand_units": demand_by_sku_location.get((sku, location), 0),
                   "received_units": measures.get("units_received", 0),
                   "purchase_units_ordered": measures.get("purchase_units_ordered", 0),
                   "fulfilled_units": measures.get("fulfilled_units", 0),
                   "backorder_units_fulfilled": measures.get("backorder_units_fulfilled", 0),
                   "backorder_units_expired": measures.get("backorder_units_expired", 0),
                   "ending_on_hand": position.on_hand_quantity,
                   "ending_reserved": position.reserved_quantity,
                   "ending_available": position.available_quantity,
                   "unused_ending_available": position.available_quantity if demand_by_sku_location.get((sku, location), 0) == 0 else 0}
            ending.append(row)
        ending.sort(key=lambda row: (-row["ending_available"], row["sku"], row["location"]))

        state: dict[tuple[str, str], list[int]] = {}
        event_rows = sorted(stock_audit_events or (), key=lambda row: (row.occurred_at, row.priority, row.key))
        replay_positions: dict[tuple[str, str], StockPosition] = {}
        for event in event_rows:
            key = (event.product_sku, event.location_code)
            position = replay_positions.setdefault(key, StockPosition(*key))
            if event.event_type in {"receipt", "transfer_in", "customer_return"}:
                if event.quantity <= 0 or not isinstance(event.unit_cost, Decimal) or event.unit_cost < 0:
                    raise ValueError(f"Entrada de estoque inválida no replay causal: {event.key}.")
                position.average_unit_cost = weighted_moving_average(
                    position.on_hand_quantity, position.average_unit_cost, event.quantity, event.unit_cost,
                )
                position.on_hand_quantity += event.quantity
            elif event.event_type in {"fulfillment", "transfer_out"}:
                if event.quantity <= 0 or event.unit_cost != position.average_unit_cost:
                    raise ValueError(f"Saída de estoque usa custo médio inválido no replay causal: {event.key}.")
                if event.quantity > position.on_hand_quantity:
                    raise ValueError(f"Saída supera o saldo físico no replay causal: {event.key}.")
                if event.event_type == "fulfillment":
                    if event.quantity > position.reserved_quantity:
                        raise ValueError(f"Fulfillment supera reserva no replay causal: {event.key}.")
                    position.reserved_quantity -= event.quantity
                elif event.quantity > position.available_quantity:
                    raise ValueError(f"Transferência supera saldo disponível no replay causal: {event.key}.")
                position.on_hand_quantity -= event.quantity
            elif event.event_type == "reserve":
                if event.quantity <= 0 or event.quantity > position.available_quantity:
                    raise ValueError(f"Reserva excede disponibilidade no replay causal: {event.key}.")
                position.reserved_quantity += event.quantity
            elif event.event_type in {"release", "expire"}:
                if event.quantity <= 0 or event.quantity > position.reserved_quantity:
                    raise ValueError(f"Liberação excede reserva no replay causal: {event.key}.")
                position.reserved_quantity -= event.quantity
            else:
                raise ValueError(f"Tipo de evento desconhecido no replay causal: {event.event_type}.")
            if position.on_hand_quantity < 0 or not 0 <= position.reserved_quantity <= position.on_hand_quantity:
                raise ValueError(f"Posição inválida no replay causal: {event.key}.")
        replay_mismatches = []
        for key, position in positions.items():
            replayed = replay_positions.get(key, StockPosition(*key))
            if (replayed.on_hand_quantity, replayed.reserved_quantity, replayed.average_unit_cost) != (
                position.on_hand_quantity, position.reserved_quantity, position.average_unit_cost
            ):
                replay_mismatches.append((key, replayed.on_hand_quantity, replayed.reserved_quantity,
                                          replayed.average_unit_cost, position.on_hand_quantity,
                                          position.reserved_quantity, position.average_unit_cost))
                if len(replay_mismatches) == 10:
                    break
        if replay_mismatches or not set(replay_positions).issubset(positions):
            raise ValueError(
                "Replay causal de estoque diverge das posições finais (quantidade, reserva ou custo médio); "
                f"amostras (sku,local,replay_qty,replay_reserva,replay_custo,engine_qty,engine_reserva,engine_custo): {replay_mismatches}."
            )
        start = _aware(config, config.start_date, 0, 0)
        end = cutoff
        stockout_seconds: dict[tuple[str, str], int] = {}
        stockout_periods: dict[tuple[str, str], int] = {}
        zero_since: dict[tuple[str, str], datetime] = {}
        for sku, location in positions:
            state[(sku, location)] = [0, 0]
        for event in event_rows:
            key = (event.product_sku, event.location_code)
            balances = state.setdefault(key, [0, 0])
            if event.occurred_at < start:
                if event.event_type in {"receipt", "transfer_in", "customer_return"}:
                    balances[0] += event.quantity
                elif event.event_type in {"transfer_out", "fulfillment"}:
                    balances[0] -= event.quantity
                    if event.event_type == "fulfillment":
                        balances[1] = max(0, balances[1] - event.quantity)
                elif event.event_type == "reserve":
                    balances[1] += event.quantity
                elif event.event_type in {"release", "expire"}:
                    balances[1] = max(0, balances[1] - event.quantity)
                continue
        for key, balances in state.items():
            if balances[0] - balances[1] <= 0:
                zero_since[key] = start

        available_total = sum(on_hand - reserved for on_hand, reserved in state.values())
        total_available_unit_seconds = 0
        last_global = start
        for event in event_rows:
            if event.occurred_at < start or event.occurred_at > end:
                continue
            total_available_unit_seconds += available_total * int((event.occurred_at - last_global).total_seconds())
            last_global = event.occurred_at
            key = (event.product_sku, event.location_code)
            balances = state.setdefault(key, [0, 0])
            before = balances[0] - balances[1]
            if event.event_type in {"receipt", "transfer_in", "customer_return"}:
                balances[0] += event.quantity
            elif event.event_type in {"transfer_out", "fulfillment"}:
                balances[0] -= event.quantity
                if event.event_type == "fulfillment":
                    balances[1] = max(0, balances[1] - event.quantity)
            elif event.event_type == "reserve":
                balances[1] += event.quantity
            elif event.event_type in {"release", "expire"}:
                    balances[1] = max(0, balances[1] - event.quantity)
            after = balances[0] - balances[1]
            available_total += after - before
            if before > 0 and after <= 0:
                zero_since[key] = event.occurred_at
            elif before <= 0 and after > 0 and key in zero_since:
                duration = int((event.occurred_at - zero_since.pop(key)).total_seconds())
                stockout_seconds[key] = stockout_seconds.get(key, 0) + duration
                stockout_periods[key] = stockout_periods.get(key, 0) + 1
        total_available_unit_seconds += available_total * int((end - last_global).total_seconds())
        for key, started in zero_since.items():
            stockout_seconds[key] = stockout_seconds.get(key, 0) + int((end - started).total_seconds())
            stockout_periods[key] = stockout_periods.get(key, 0) + 1
        stockout_rows = [{"sku": sku, "category": products[sku].category_code, "location": location,
                          "periods_without_available_stock": stockout_periods.get((sku, location), 0),
                          "days_without_available_stock": round(stockout_seconds.get((sku, location), 0) / 86400, 2)}
                         for sku, location in set(stockout_seconds) | set(stockout_periods)]
        stockout_rows.sort(key=lambda row: (-row["days_without_available_stock"], -row["periods_without_available_stock"], row["sku"], row["location"]))
        return {
            "by_year_channel": period_summary,
            "by_store": grouped_summary(lambda key, _category: key[3] or "DIGITAL", sales_only=True),
            "by_stock_location": grouped_summary(lambda key, _category: key[5]),
            "by_sku_top": grouped_summary(lambda key, _category: key[4])[:25],
            "sku_group_count": len({key[4] for key in stock_audit_rows}),
            "bootstrap_core_units_by_sku": bootstrap_units_by_sku,
            "by_category": grouped_summary(lambda _key, category: category, sales_only=True),
            "physical_lost_sales_top": loss_rows[:25],
            "expired_backorders_top": overdue_rows[:25],
            "stockout_periods_top": stockout_rows[:25],
            "stockout_location_count": len(stockout_rows),
            "total_stockout_days": round(sum(stockout_seconds.values()) / 86400, 2),
            "stockout_episode_count": sum(stockout_periods.values()),
            "ending_inventory_top": ending[:25],
            "sku_location_count": len(ending),
            "total_opening_units": sum(row["opening_units"] for row in ending),
            "total_ending_on_hand": sum(row["ending_on_hand"] for row in ending),
            "total_ending_available": sum(row["ending_available"] for row in ending),
            "unused_ending_available_units": sum(row["unused_ending_available"] for row in ending),
            "stock_position_replay_mismatches": 0,
            "average_available_units": round(total_available_unit_seconds / max(1, int((end - start).total_seconds())), 2),
            "total_supplier_lead_time_mean_days": round(
                sum(m.get("supplier_lead_time_minutes_total", 0) for m in stock_audit_rows.values())
                / max(1, sum(m.get("supplier_lead_time_count", 0) for m in stock_audit_rows.values())) / 1440, 2),
            "total_supplier_lead_time_max_days": round(
                max((m.get("supplier_lead_time_minutes_max", 0) for m in stock_audit_rows.values()), default=0) / 1440, 2),
            "active_backorders_top": sorted(({
                "order": line.order_key, "sku": line.product_sku, "category": products[line.product_sku].category_code,
                "location": line.location_code, "remaining_quantity": line.remaining_quantity,
                "age_days_at_cutoff": (config.end_date - line.placed_at.date()).days,
                "days_to_deadline_after_cutoff": (line.deadline.date() - config.end_date).days,
            } for line in backorders.all_lines()), key=lambda row: (-row["remaining_quantity"], row["sku"], row["order"]))[:25],
        }

    def wake_backorders(sku: str, location: str, at: datetime) -> None:
        nonlocal reservation_counter, state_counter
        position = positions.get((sku, location))
        while position is not None and position.available_quantity > 0:
            waiting = backorders.head(sku, location)
            if waiting is None:
                break
            order = result_by_order.get(waiting.order_key)
            item = sale_item_by_key.get(waiting.item_key)
            if order is None or item is None:
                backorders.remove_order(waiting.order_key)
                continue
            available = max(0, position.available_quantity - pending_transfer_out.get((sku, location), 0))
            quantity = min(waiting.remaining_quantity, available)
            if quantity <= 0:
                break
            if at + timedelta(hours=6) > cutoff:
                break
            position.reserved_quantity += quantity
            reservation_counter += 1
            reservation_key = f"RES-KEY-{reservation_counter:05d}"
            reservation = StockReservation(reservation_key, order.key, item.key, sku, location,
                                           quantity, "active", at)
            result.stock_reservations.append(reservation)
            reservations_by_order.setdefault(order.key, []).append(reservation)
            unassigned_reservations[(order.key, item.key, location)].append(reservation_key)
            state_counter += 1
            append_stock_state(StockStateEvent(f"STATE-{state_counter:06d}", at,
                "reserve", sku, location, quantity, 27, reservation_key=reservation_key))
            if not schedule_fulfillment(order, [(item, quantity)], location, at, order_index_by_key[order.key]):
                position.reserved_quantity -= quantity
                reservations_by_order[order.key].pop()
                raise RuntimeError("Reserva de backorder sem fulfillment programável antes do cutoff.")
            if completion_state is not None:
                completion_state.on_backorder_fulfillment_scheduled(order.key)
            resolved = backorders.reduce(waiting, quantity)
            audit_key_value = audit_key(waiting.placed_at.year, order.channel_type, order.channel_code,
                                        order.store_code, sku, location)
            audit_add(audit_key_value, "backorder_units_fulfilled", quantity)
            if isinstance(result, StreamingCoreResult):
                result.runtime_metrics["stock_backorder_units_fulfilled"] += quantity
                if resolved:
                    result.runtime_metrics["stock_backorder_lines_resolved"] += 1
            if resolved:
                outstanding_lines_by_order[order.key] -= 1
                if completion_state is not None:
                    completion_state.on_backorder_resolved(order.key)
            update_backorder_metrics()


    def create_sale(event: ScheduledEvent) -> None:
        nonlocal order_counter, reservation_counter, fulfillment_counter, fulfillment_item_counter, state_counter
        nonlocal sales_intentions_processed
        idx = event.payload["index"]
        at = event.occurred_at
        sales_intentions_processed += 1
        if isinstance(result, StreamingCoreResult):
            result.runtime_metrics["sales_intentions_processed"] = sales_intentions_processed
        content_seed = int.from_bytes(hashlib.sha256(
            f"{sales_content_seed}:sale-content:{idx}".encode("utf-8")
        ).digest()[:8], "big")
        sale_rng = sales_rng if config.profile == "smoke" else random.Random(content_seed)
        is_cancelled = idx in cancelled_indices
        order_ordinal = order_counter + 1
        order_key = f"ORDER-KEY-{order_ordinal:04d}"
        order_number = f"SO-SM-{order_ordinal:04d}"
        channel_code = event.payload["channel_code"]
        channel_type = channels[channel_code].channel_type
        store_code = event.payload["store_code"]
        customer_code = event.payload["customer_code"]
        uses_customer_frequency_ticket = False
        if (customer_frequency_tickets is not None and customer_code is not None
                and not is_cancelled and customer_frequency_tickets.remaining):
            customer_code = customer_frequency_tickets.peek()
            uses_customer_frequency_ticket = True
        address = addresses.get(customer_code) if customer_code and channel_type != "physical" else None
        address_key = address.logical_key if address else None
        snapshot = None if address is None else (
            address.recipient_name, address.postal_code, address.street, address.street_number,
            address.complement, address.district, address.city, address.state_code, address.country_code,
        )
        salesperson = suitable_salesperson(store_code, at) if channel_type == "physical" and store_code else None
        count = _line_count(idx)
        selected_skus = [master.products[0].sku] if idx == 0 else []
        while len(selected_skus) < count:
            candidate = product_skus[sale_rng.randrange(len(product_skus))]
            if candidate not in selected_skus:
                selected_skus.append(candidate)
        sale_items: list[SaleOrderItem] = []
        gross: list[Decimal] = []
        for line_no, sku in enumerate(selected_skus, start=1):
            item_key = f"{order_key}-LINE-{line_no:02d}"
            if idx == 0 and line_no == 1:
                quantity = 5
            elif customers.get(customer_code) and customers[customer_code].customer_type == "business":
                double_quantity_rate = config.generation.get("business_item_double_quantity_percent", 35)
                double_quantity = (
                    sale_rng.random() < Decimal("0.35") if config.profile == "smoke"
                    else sale_rng.randrange(100) < double_quantity_rate
                )
                quantity = 2 if double_quantity else 1
            else:
                quantity = 1
            price = _price_at(price_periods, sku, channel_code, at)
            sale_item = SaleOrderItem(item_key, order_key, line_no, sku, quantity, price)
            sale_items.append(sale_item)
            gross.append(_money(price * quantity))
        sales_intention_digest.update("\x1f".join((
            str(idx), at.isoformat(), channel_code, store_code or "", customer_code or "",
            *(f"{item.product_sku}:{item.quantity}" for item in sale_items),
        )).encode("utf-8") + b"\n")
        if config.profile != "smoke" and channel_type == "physical":
            location = store_locations.get(store_code)
            if location is None or any(
                positions.get((item.product_sku, location), StockPosition(item.product_sku, location)).available_quantity < item.quantity
                for item in sale_items
            ):
                audit_period_add(at.year, channel_type, channel_code, "physical_intents_lost")
                if location is not None:
                    for item in sale_items:
                        position = positions.get((item.product_sku, location))
                        available = position.available_quantity if position else 0
                        if not is_cancelled:
                            observe_demand(item.product_sku, location, at, item.quantity)
                        audit_add(audit_key(at.year, channel_type, channel_code, store_code,
                                            item.product_sku, location), "physical_demand_lost_units", item.quantity)
                        if available < item.quantity:
                            schedule_restock(item.product_sku, location, at + timedelta(minutes=2), item.quantity - available)
                if isinstance(result, StreamingCoreResult):
                    result.runtime_metrics["physical_intents_unconverted"] = result.runtime_metrics.get("physical_intents_unconverted", 0) + 1
                result.event_trace.append((at, "physical_intent_without_stock", event.logical_key))
                return
        order_counter += 1
        if uses_customer_frequency_ticket:
            customer_frequency_tickets.consume(customer_code)
        if order_counter != order_ordinal:
            raise ValueError("Contador de pedidos aceitos divergiu da chave lógica provisionada.")
        quota_cell = event.payload.get("accepted_quota_cell")
        if quota_cell is not None:
            accepted_orders_by_plan_cell[tuple(quota_cell)] += 1
        audit_period_add(at.year, channel_type, channel_code, "orders_created")
        subtotal = sum(gross, Decimal("0.00"))
        discount = Decimal("0.00")
        discount_rate = config.generation.get("discount_incidence_percent", 38)
        if config.profile != "smoke" and at.month == 11 and at.year in {2023, 2024, 2025}:
            discount_rate = config.generation.get("black_friday_discount_incidence_percent", 55)
        discount_selected = idx in {1, 2, 3}
        if not discount_selected and idx % 100 != 0:
            discount_selected = (
                sale_rng.random() < Decimal("0.38") if config.profile == "smoke"
                else sale_rng.randrange(100) < discount_rate
            )
        pending_discount_rows: list[AppliedDiscount] = []
        if discount_selected:
            discount, pending_discount_rows = allocate_order_discount(order_key, sale_items, at, gross, idx)
        fulfillment_type = "store_pickup" if channel_type == "physical" or (idx % 13 == 0 and channel_type == "ecommerce") else "delivery"
        fulfillment_type_by_order[order_key] = fulfillment_type
        order_index_by_key[order_key] = idx
        shipping = Decimal("0.00") if fulfillment_type == "store_pickup" else Decimal("14.90")
        total = _money(subtotal - discount + shipping)
        order = SaleOrder(order_key, order_number, channel_code, channel_type, customer_code, store_code,
                          salesperson, address_key, "placed", at, subtotal, discount, shipping, total, snapshot)
        result.sales_orders.append(order)
        ordered_quantity_by_order[order_key] = sum(row.quantity for row in sale_items)
        fulfilled_quantity_by_order[order_key] = 0
        for sale_item in sale_items:
            fulfilled_quantity_by_item[sale_item.key] = 0
            cancelled_quantity_by_item[sale_item.key] = 0
        result_by_order[order_key] = order
        sale_item_keys_by_order[order_key] = [row.key for row in sale_items]
        sale_item_by_key.update((row.key, row) for row in sale_items)
        fulfillment_keys_by_order[order_key] = []
        pending_fulfillments_by_order[order_key] = 0
        fulfillment_count_by_order[order_key] = 0
        outstanding_lines_by_order[order_key] = 0
        if isinstance(result, StreamingCoreResult):
            result.runtime_metrics["current_active_orders"] = len(result_by_order)
            result.runtime_metrics["max_active_orders"] = max(
                result.runtime_metrics.get("max_active_orders", 0), len(result_by_order)
            )
        result.sales_order_items.extend(sale_items)
        # Discounts reference both parent and item IDs. Publish them only after
        # those rows have entered the shared emitter, so a batch boundary cannot
        # make a discount arrive before its dependencies.
        result.applied_discounts.extend(pending_discount_rows)
        result.order_status_history.extend((
            OrderStatusEvent(order_key, "draft", at - timedelta(minutes=5), salesperson),
            OrderStatusEvent(order_key, "placed", at, salesperson),
        ))

        # Allocate current availability. Digital shortages remain queued by SKU/location.
        allocations_by_location: dict[str, list[tuple[SaleOrderItem, int]]] = {}
        waiting_lines: list[tuple[SaleOrderItem, int, str]] = []
        for sale_item in sale_items:
            remaining = sale_item.quantity
            candidates = available_locations(channel_type, store_code)
            candidates = sorted(candidates, key=lambda code: (-max(
                0, positions.get((sale_item.product_sku, code), StockPosition(sale_item.product_sku, code)).available_quantity
                - pending_transfer_out.get((sale_item.product_sku, code), 0)
            ), code))
            for location in candidates:
                position = positions.get((sale_item.product_sku, location))
                available = max(0, position.available_quantity - pending_transfer_out.get((sale_item.product_sku, location), 0)) if position else 0
                if position is None or available <= 0 or remaining <= 0:
                    continue
                take = min(remaining, available)
                remaining -= take
                if not is_cancelled:
                    observe_demand(sale_item.product_sku, location, at, take)
                position.reserved_quantity += take
                reservation_counter += 1
                reservation_key = f"RES-KEY-{reservation_counter:05d}"
                reservation = StockReservation(reservation_key, order_key, sale_item.key, sale_item.product_sku,
                                               location, take, "active", at + timedelta(minutes=2))
                result.stock_reservations.append(reservation)
                reservations_by_order.setdefault(order_key, []).append(reservation)
                unassigned_reservations[(order_key, sale_item.key, location)].append(reservation_key)
                state_counter += 1
                append_stock_state(StockStateEvent(f"STATE-{state_counter:06d}", at + timedelta(minutes=2),
                    "reserve", sale_item.product_sku, location, take, 10, reservation_key=reservation_key))
                allocations_by_location.setdefault(location, []).append((sale_item, take))
                if position.available_quantity <= 2:
                    schedule_restock(sale_item.product_sku, location, at + timedelta(minutes=2))
            if remaining:
                if config.profile == "smoke":
                    continue
                if channel_type == "physical":
                    raise ValueError("Venda física sem disponibilidade suficiente após preflight.")
                wait_location = candidates[0] if candidates else warehouse_codes[0]
                if not is_cancelled:
                    observe_demand(sale_item.product_sku, wait_location, at, remaining)
                waiting_lines.append((sale_item, remaining, wait_location))
                schedule_restock(sale_item.product_sku, wait_location, at + timedelta(minutes=2), remaining)

        fulfillment_groups = sorted(allocations_by_location.items()) if not is_cancelled else ()
        for location, line_allocations in fulfillment_groups:
            for sale_item, quantity in line_allocations:
                audit_add(audit_key(at.year, channel_type, channel_code, store_code,
                                    sale_item.product_sku, location), "demand_units", quantity)
            schedule_fulfillment(order, line_allocations, location, at, idx)

        if not is_cancelled and waiting_lines:
            deadline = at + timedelta(days=config.generation["max_stock_wait_days"])
            if deadline <= cutoff:
                push(deadline, 25, f"STOCK-WAIT-{order_key}", "stock_wait_deadline", {"order_key": order_key})
            for item, quantity, location in waiting_lines:
                audit_add(audit_key(at.year, channel_type, channel_code, store_code,
                                    item.product_sku, location), "demand_units", quantity)
                audit_add(audit_key(at.year, channel_type, channel_code, store_code,
                                    item.product_sku, location), "backorder_units_created", quantity)
                backorders.enqueue(BackorderLine(order_key, item.key, item.product_sku, location,
                                                 quantity, at, deadline))
                outstanding_lines_by_order[order_key] += 1
                schedule_restock(item.product_sku, location, at + timedelta(minutes=2),
                                 0 if coverage_replenishment_enabled else backorders.pending_quantity(
                                     item.product_sku, location
                                 ))
            update_backorder_metrics()

        if is_cancelled:
            if allocations_by_location:
                result.order_status_history.append(OrderStatusEvent(order_key, "confirmed", at + timedelta(minutes=3), salesperson))
                order.status = "confirmed"
            cancel_at = at + timedelta(hours=4)
            push(cancel_at, 20, f"CANCEL-{order_key}", "cancel", {"order_key": order_key})
        else:
            result.order_status_history.append(OrderStatusEvent(order_key, "confirmed", at + timedelta(minutes=3), salesperson))
            order.status = "confirmed"
        if completion_state is not None:
            completion_state.on_sale(order, order_counter, is_cancelled, pending_fulfillments_by_order[order_key],
                                     pending_stock_items=outstanding_lines_by_order[order_key])
        result.event_trace.append((at, "sale", order_key))
        if not is_cancelled and pending_fulfillments_by_order[order_key] == 0 and outstanding_lines_by_order[order_key] == 0:
            finalize_order_3c(order_key)

    def cancel_order(order_key: str, at: datetime) -> None:
        nonlocal state_counter
        order = result_by_order[order_key]
        removed_lines = backorders.remove_order(order_key)
        outstanding_lines_by_order[order_key] = 0
        update_backorder_metrics()
        for reservation in reservations_by_order.get(order_key, []):
            if reservation.status != "active":
                continue
            reservation.status = "released"
            reservation.released_at = at
            position = positions[(reservation.product_sku, reservation.location_code)]
            position.reserved_quantity -= reservation.quantity
            state_counter += 1
            state_key = f"STATE-{state_counter:06d}"
            append_stock_state(StockStateEvent(state_key, at, "release", reservation.product_sku,
                reservation.location_code, reservation.quantity, 20, reservation_key=reservation.key))
        order.status = "cancelled"
        reason = "Cancelamento por falta de estoque após prazo de espera" if order_key in stock_wait_expirations else "Cancelamento anterior ao fulfillment"
        result.order_status_history.append(OrderStatusEvent(order_key, "cancelled", at, order.salesperson_code, reason))
        result.event_trace.append((at, "cancel", order_key))
        if completion_state is not None:
            if order_key not in stock_wait_expirations:
                completion_state.on_order_cancelled(order_key)
        finalize_order_3c(order_key)

    stock_wait_expirations: set[str] = set()

    def record_stock_timeout_cancellations(order_key: str, lines: list[BackorderLine], at: datetime,
                                           *, full_order: bool) -> list[SalesOrderItemCancellation]:
        nonlocal cancellation_counter
        order = result_by_order[order_key]
        cancellations: list[SalesOrderItemCancellation] = []
        shipping_to_refund = order.shipping if full_order else Decimal("0.00")
        for line in sorted(lines, key=lambda row: (sale_item_by_key[row.item_key].line_number, row.item_key)):
            item = sale_item_by_key.get(line.item_key)
            quantity = line.remaining_quantity
            if item is None or quantity <= 0:
                raise ValueError("Saldo de backorder inválido ao registrar cancelamento parcial.")
            fulfilled = fulfilled_quantity_by_item.get(item.key, 0)
            previously_cancelled = cancelled_quantity_by_item.get(item.key, 0)
            offset = fulfilled + previously_cancelled
            if offset + quantity > item.quantity:
                raise ValueError("Cancelamento excede o saldo não expedido do item.")
            gross, discount, net = cancellation_amounts(
                item.unit_sale_price, item.quantity, discount_by_item.get(item.key, Decimal("0.00")),
                offset, quantity,
            )
            cancellation_counter += 1
            cancellation = SalesOrderItemCancellation(
                f"CANCEL-KEY-{cancellation_counter:07d}", order_key, item.key, quantity,
                "stock_timeout", at, gross, discount, net, shipping_to_refund,
                f"STOCK-TIMEOUT-{order.number}-{item.line_number:03d}",
            )
            shipping_to_refund = Decimal("0.00")
            cancellations.append(cancellation)
            result.sales_order_item_cancellations.append(cancellation)
            cancelled_quantity_by_item[item.key] = previously_cancelled + quantity
        if not cancellations:
            raise ValueError("Expiração de backorder sem quantidade cancelável.")
        if completion_state is not None:
            completion_state.on_stock_timeout_cancellations(order_key, cancellations, at)
        return cancellations

    def expire_stock_wait(order_key: str, at: datetime) -> None:
        if order_key not in result_by_order:
            return
        if outstanding_lines_by_order.get(order_key, 0) == 0:
            return
        removed_lines = backorders.remove_order(order_key)
        update_backorder_metrics()
        if (fulfilled_quantity_by_order[order_key] == 0
                and pending_fulfillments_by_order[order_key] == 0):
            cancellations = record_stock_timeout_cancellations(order_key, removed_lines, at, full_order=True)
            order = result_by_order[order_key]
            order_cancelled_quantity = sum(row.cancelled_quantity for row in cancellations)
            if order_cancelled_quantity != ordered_quantity_by_order[order_key]:
                raise ValueError("Cancelamento integral por estoque não cobre as quantidades originais.")
            stock_wait_expirations.add(order_key)
            if isinstance(result, StreamingCoreResult):
                result.runtime_metrics["stock_wait_expired_orders"] += 1
            cancel_order(order_key, at)
            stock_wait_expirations.discard(order_key)
            return
        backorder_expired_partial.add(order_key)
        for line in removed_lines:
            expired_order = result_by_order[order_key]
            audit_add(audit_key(line.placed_at.year, expired_order.channel_type, expired_order.channel_code,
                                expired_order.store_code, line.product_sku, line.location_code),
                      "backorder_units_expired", line.remaining_quantity)
            if len(expired_partial_samples) < 10:
                expired_partial_samples.append({
                    "order": order_key,
                    "item": line.item_key,
                    "sku": line.product_sku,
                    "location": line.location_code,
                    "unfulfilled_quantity": line.remaining_quantity,
                    "placed_at": line.placed_at.isoformat(),
                    "deadline": line.deadline.isoformat(),
                    "fulfilled_units": fulfilled_quantity_by_order[order_key],
                    "fulfillment_items_in_flight": pending_fulfillments_by_order[order_key],
                    "ordered_units": ordered_quantity_by_order[order_key],
                })
        if isinstance(result, StreamingCoreResult):
            result.runtime_metrics["stock_wait_expired_partial_orders"] += 1
        cancellations = record_stock_timeout_cancellations(order_key, removed_lines, at, full_order=False)
        outstanding_lines_by_order[order_key] = 0
        update_backorder_metrics()
        if isinstance(result, StreamingCoreResult):
            result.runtime_metrics["cancelled_backorder_units"] = result.runtime_metrics.get("cancelled_backorder_units", 0) + sum(
                row.cancelled_quantity for row in cancellations
            )
            result.runtime_metrics["stock_wait_expired_partial_orders_resolved"] = result.runtime_metrics.get(
                "stock_wait_expired_partial_orders_resolved", 0
            ) + 1
        order = result_by_order[order_key]
        if fulfilled_quantity_by_order[order_key] + sum(cancelled_quantity_by_item.get(key, 0) for key in sale_item_keys_by_order[order_key]) == ordered_quantity_by_order[order_key] and pending_fulfillments_by_order[order_key] == 0:
            order.status = "completed"
            result.order_status_history.append(OrderStatusEvent(
                order_key, "completed", at, order.salesperson_code,
                "Obrigação encerrada após cancelamento do saldo por prazo de estoque",
            ))
            finalize_order_3c(order_key)

    def fulfill(fulfillment_item_key: str, at: datetime) -> None:
        fi = fulfillment_items_by_key[fulfillment_item_key]
        fulfillment = fulfillments_by_key[fi.fulfillment_key]
        sale_item = sale_item_by_key[fi.sale_item_key]
        reservation_keys = reservations_by_fulfillment_item.pop(fi.key, [])
        reservation_by_key = {row.key: row for row in reservations_by_order[fi.order_key]}
        reservations = [reservation_by_key[key] for key in reservation_keys
                        if key in reservation_by_key and reservation_by_key[key].status == "active"]
        quantity = fi.quantity_allocated
        if sum(row.quantity for row in reservations) < quantity:
            raise ValueError(
                "Fulfillment sem reserva ativa suficiente: "
                f"item={fi.key}, order={fi.order_key}, sale_item={sale_item.key}, "
                f"location={fulfillment.location_code}, allocated={quantity}, "
                f"active_reserved={sum(row.quantity for row in reservations)}, "
                f"reservation_keys={reservation_keys}."
            )
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
        fulfilled_quantity_by_order[fi.order_key] += quantity
        fulfilled_quantity_by_item[sale_item.key] = fulfilled_quantity_by_item.get(sale_item.key, 0) + quantity
        # The movement emitted below references this identity. Publish the
        # fulfilled snapshot first so a batch boundary cannot send the movement
        # before its fulfillment-item ID exists in the sink.
        publish("fulfillment_items", fi.key)
        fulfillment_items_by_key.pop(fi.key, None)
        audit_order = result_by_order[fi.order_key]
        audit_add(audit_key(audit_order.placed_at.year, audit_order.channel_type, audit_order.channel_code,
                            audit_order.store_code, sale_item.product_sku,
                            fulfillment.location_code), "fulfilled_units", quantity)
        add_movement(sale_item.product_sku, fulfillment.location_code, "fulfillment", -quantity, cost, at,
                     fulfillment_item_key=fi.key, reservation_key=reservations[0].key)
        order = result_by_order[fi.order_key]
        if completion_state is not None:
            completion_state.on_fulfilled(
                fi, fulfillment, order, sale_item, discount_by_item.get(sale_item.key, Decimal("0.00")), cost, at,
            )
        result.event_trace.append((at, "fulfillment", fi.key))
        fulfilled = fulfilled_quantity_by_order[fi.order_key]
        ordered = ordered_quantity_by_order[fi.order_key]
        cancelled = sum(cancelled_quantity_by_item.get(key, 0) for key in sale_item_keys_by_order[fi.order_key])
        if fulfilled + cancelled == ordered and outstanding_lines_by_order[fi.order_key] == 0 and order.status not in {"cancelled", "completed"}:
            order.status = "completed"
            result.order_status_history.append(OrderStatusEvent(order.key, "completed", at, order.salesperson_code))
        pending_fulfillments_by_order[fi.order_key] -= 1
        if pending_fulfillments_by_order[fi.order_key] == 0 and outstanding_lines_by_order[fi.order_key] == 0:
            finalize_order_3c(fi.order_key)

    # Bootstrap procurement is represented as purchase-order and receipt events.
    bootstrap_plan()
    sales_start = config.start_date + timedelta(days=1)
    sales_last = config.end_date - timedelta(days=1)
    span = (sales_last - sales_start).days
    channel_codes = {"physical": "CH-PHYSICAL", "ecommerce": "CH-ECOM", "marketplace_a": "CH-MARKET-A", "marketplace_b": "CH-MARKET-B"}
    order_count = config.sales_order_target
    order_plan_mode = config.order_plan.get("mode", "intentions")
    accepted_quotas: tuple[SalesIntentQuota, ...] = ()
    if order_plan_mode == "accepted_quotas":
        accepted_quotas = build_sales_intent_quotas(
            accepted_target=order_count,
            start_date=config.start_date,
            end_date=config.end_date,
            annual_shares_percent=config.order_plan["annual_shares_percent"],
            channel_shares_percent=config.order_plan["channel_shares_percent"],
            month_weights=config.order_plan["month_weights"],
            physical_attempt_multiplier_percent=config.order_plan["physical_attempt_multiplier_percent"],
            intention_cap=config.order_plan["intention_cap"],
        )
        accepted_target_by_cell = {
            (row.year, row.month, row.channel_code): row.accepted_orders for row in accepted_quotas
        }
        sales_intentions_planned = sum(row.intention_limit for row in accepted_quotas)
        intention_cap = config.order_plan["intention_cap"]
        physical_accepted_target = sum(
            row.accepted_orders for row in accepted_quotas if row.channel_code == "CH-PHYSICAL"
        )
        anonymous_target = round(
            physical_accepted_target * config.generation.get("physical_anonymous_rate_percent", 30) / 100
        )
        recurrence_target = round((order_count - anonymous_target) * 36 / 37)
        recurrence_seed = int.from_bytes(hashlib.sha256(
            f"{sales_content_seed}:customer-recurrence-plan:v1".encode("utf-8")
        ).digest()[:8], "big")
        if order_count >= 10_000:
            customer_frequency_tickets = CustomerFrequencyTickets(
                master.customers, recurrence_target,
                config.order_plan["customer_frequency_shares_percent"], recurrence_seed,
            )
        if isinstance(result, StreamingCoreResult) and customer_frequency_tickets is not None:
            result.runtime_metrics["customer_frequency_tickets_planned"] = len(customer_frequency_tickets.tickets)
            result.runtime_metrics["customer_frequency_orders_by_type_planned"] = customer_frequency_tickets.planned_by_type
    else:
        accepted_target_by_cell = {}
        sales_intentions_planned = order_count
        intention_cap = order_count
    intention_limit = sales_intentions_planned
    cancelled_indices = set(range(37, intention_limit, 37))

    def create_sale_intent(
        index: int,
        rng: random.Random,
        *,
        planned_day: date | None = None,
        planned_at: datetime | None = None,
        planned_channel: str | None = None,
        accepted_quota_cell: tuple[int, int, str] | None = None,
    ) -> ScheduledEvent:
        day = planned_day or sales_start + timedelta(days=(span * index // max(1, intention_limit - 1)))
        hour = 9 + (index * 7) % 10
        minute = (index * 17) % 60
        if planned_channel is not None:
            channel_code = planned_channel
        elif index == 0:
            channel_code = "CH-ECOM"
        else:
            roll = rng.randrange(100)
            channel_code = channel_codes["physical"] if roll < 52 else channel_codes["ecommerce"] if roll < 80 else channel_codes["marketplace_a"] if roll < 90 else channel_codes["marketplace_b"]
        channel_type = channels[channel_code].channel_type
        open_stores = sorted((row for row in master.stores if row.opened_on <= day), key=lambda row: row.code)
        store_code = open_stores[index % len(open_stores)].code if channel_type == "physical" and open_stores else None
        anonymous_rate = config.generation.get("physical_anonymous_rate_percent", 30)
        is_anonymous_physical = channel_type == "physical" and (
            (rng.randrange(100) < anonymous_rate) if config.profile != "smoke" else index % 10 < 3
        )
        if is_anonymous_physical:
            customer_code = None
        else:
            customer_code = master.customers[rng.randrange(len(master.customers))].code
        return ScheduledEvent(planned_at or _aware(config, day, hour, minute), 10,
                              f"SALE-INTENT-{index + 1:07d}", "sale", {
            "index": index, "channel_code": channel_code, "store_code": store_code,
            "customer_code": customer_code,
            "accepted_quota_cell": accepted_quota_cell,
        })

    def iter_sale_intents_by_day():
        """Emit chronological intents, with bounded per-period budgets for accepted quotas."""
        if not accepted_quotas:
            current_day = None
            day_events: list[ScheduledEvent] = []
            for index in range(order_count):
                event = create_sale_intent(index, sales_intent_rng)
                event_day = event.occurred_at.date()
                if current_day is not None and event_day != current_day:
                    yield from sorted(day_events)
                    day_events.clear()
                current_day = event_day
                day_events.append(event)
            if day_events:
                yield from sorted(day_events)
            return

        import calendar

        intent_heap: list[tuple[datetime, int, str, int, int, ScheduledEvent]] = []
        next_index = 0

        def make_cell_event(cell_index: int, attempt_index: int, row: SalesIntentQuota) -> ScheduledEvent:
            nonlocal next_index
            month_start = date(row.year, row.month, 1)
            month_end = date(row.year, row.month, calendar.monthrange(row.year, row.month)[1])
            first_day = max(sales_start, month_start)
            last_day = min(sales_last, month_end)
            if first_day > last_day:
                raise ValueError(f"Quota de venda fora do horizonte comercial: {row.year}-{row.month:02d}.")
            day_span = (last_day - first_day).days
            day = first_day + timedelta(
                days=(day_span * attempt_index // max(1, row.intention_limit - 1))
            )
            if day_span:
                denominator = max(1, row.intention_limit - 1)
                day_offset = (day - first_day).days
                first_index = (day_offset * denominator + day_span - 1) // day_span
                after_last_index = ((day_offset + 1) * denominator + day_span - 1) // day_span
                last_index = min(row.intention_limit - 1, after_last_index - 1)
            else:
                first_index = 0
                last_index = row.intention_limit - 1
            attempts_today = max(1, last_index - first_index + 1)
            slot_today = attempt_index - first_index
            minute_of_day = 9 * 60 + slot_today * (12 * 60) // attempts_today
            planned_at = _aware(config, day, minute_of_day // 60, minute_of_day % 60)
            event = create_sale_intent(
                next_index, sales_intent_rng, planned_day=day, planned_at=planned_at,
                planned_channel=row.channel_code,
                accepted_quota_cell=(row.year, row.month, row.channel_code),
            )
            next_index += 1
            heapq.heappush(intent_heap, (
                event.occurred_at, event.priority, event.logical_key, cell_index, attempt_index, event,
            ))
            return event

        for cell_index, row in enumerate(accepted_quotas):
            make_cell_event(cell_index, 0, row)
        while intent_heap:
            _at, _priority, _key, cell_index, attempt_index, event = heapq.heappop(intent_heap)
            yield event
            row = accepted_quotas[cell_index]
            following = attempt_index + 1
            if following < row.intention_limit:
                make_cell_event(cell_index, following, row)

    def quota_already_full(event: ScheduledEvent) -> bool:
        cell = event.payload.get("accepted_quota_cell")
        if cell is None:
            return False
        cell = tuple(cell)
        return accepted_orders_by_plan_cell[cell] >= accepted_target_by_cell[cell]

    def sales_goal_reached() -> bool:
        return (
            sum(accepted_orders_by_plan_cell.values()) == order_count
            if accepted_quotas else sales_intentions_processed >= intention_limit
        )

    next_sale_intent = None
    sale_intent_iter = None
    if config.profile == "smoke":
        # Preserve the historical smoke random-call order and therefore its exact regression output.
        for index in range(order_count):
            event = create_sale_intent(index, sales_rng)
            push(event.occurred_at, event.priority, event.logical_key, event.event_type, event.payload)
    else:
        sale_intent_iter = iter(iter_sale_intents_by_day())
        next_sale_intent = next(sale_intent_iter, None)

    last_event_day = None
    core_completion_scheduled = False
    while queue or next_sale_intent is not None:
        while next_sale_intent is not None and quota_already_full(next_sale_intent):
            if isinstance(result, StreamingCoreResult):
                result.runtime_metrics["sales_intentions_skipped_filled_quota"] = (
                    result.runtime_metrics.get("sales_intentions_skipped_filled_quota", 0) + 1
                )
            next_sale_intent = next(sale_intent_iter, None)
        if next_sale_intent is not None and (not queue or next_sale_intent < queue.peek()):
            event = next_sale_intent
            next_sale_intent = next(sale_intent_iter, None)
        else:
            event = queue.pop()
        event_day = event.occurred_at.date()
        if emitter is not None and last_event_day is not None and event_day != last_event_day:
            emitter.flush()
        last_event_day = event_day
        if event.occurred_at > cutoff:
            raise ValueError("Evento ultrapassa o cutoff comercial.")
        result.event_trace.append((event.occurred_at, event.event_type, event.logical_key))
        if event.event_type == "purchase_order":
            po_key, item_key = create_purchase(event.payload, event.occurred_at)
            if event.payload.get("restock_key"):
                key = (event.payload["sku"], event.payload["location"])
                pending_restock.setdefault(key, event.payload["quantity"])
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
        elif event.event_type == "stock_wait_deadline":
            expire_stock_wait(event.payload["order_key"], event.occurred_at)
        elif event.event_type == "fulfill":
            fulfill(event.payload["fulfillment_item_key"], event.occurred_at)
        elif event.event_type in {"transfer_out", "transfer_in"} and event.payload.get("supply_policy"):
            sku, location, quantity = event.payload["sku"], event.payload["location"], event.payload["quantity"]
            key = (sku, location)
            if event.event_type == "transfer_out":
                remaining = pending_transfer_out.get(key, 0) - quantity
                if remaining < 0:
                    raise ValueError("Saída transferida supera a quantidade de transferência reservada.")
                if remaining:
                    pending_transfer_out[key] = remaining
                else:
                    pending_transfer_out.pop(key, None)
            else:
                remaining = pending_transfer_in.get(key, 0) - quantity
                if remaining < 0:
                    raise ValueError("Entrada transferida supera a quantidade em trânsito.")
                if remaining:
                    pending_transfer_in[key] = remaining
                else:
                    pending_transfer_in.pop(key, None)
                edge = supply_transfer_edge_by_item.pop(event.payload["item_key"], None)
                if edge is not None:
                    active_supply_transfer_edges.discard(edge)
            if completion_state is None or not completion_state.process_event(
                event, positions, append_stock_state, wake_backorders
            ):
                raise ValueError("Evento de transferência da política sem handler incremental.")
        elif completion_state is not None and completion_state.process_event(
            event, positions, append_stock_state, wake_backorders
        ):
            pass
        else:
            raise ValueError(f"Tipo de evento não suportado: {event.event_type}")
        if (completion_state is not None and not core_completion_scheduled
                and sales_goal_reached()
                and next_sale_intent is None
                and not queue.has_event_type({"purchase_order", "receipt", "sale", "cancel", "fulfill"})):
            completion_state.on_core_complete(positions)
            core_completion_scheduled = True

    if accepted_quotas:
        incomplete = {
            f"{year}-{month:02d}:{channel}": {
                "accepted": accepted_orders_by_plan_cell[(year, month, channel)], "target": target,
            }
            for (year, month, channel), target in accepted_target_by_cell.items()
            if accepted_orders_by_plan_cell[(year, month, channel)] != target
        }
        if incomplete:
            raise ValueError(
                "A geração não atingiu todas as quotas de pedidos aceitos dentro do limite determinístico "
                f"de intenções ({sales_intentions_planned} planejadas, {sales_intentions_processed} processadas, "
                f"teto global {intention_cap}); primeiras quotas pendentes: {dict(list(incomplete.items())[:12])}."
            )
        result.runtime_metrics.update({
            "sales_orders_target": order_count,
            "sales_orders_accepted": order_counter,
            "sales_intentions_planned": sales_intentions_planned,
            "sales_intentions_processed": sales_intentions_processed,
            "sales_intentions_remaining": sales_intentions_planned - sales_intentions_processed,
            "sales_intention_cap": intention_cap,
            "sales_orders_accepted_by_year_month_channel": {
                f"{year}-{month:02d}:{channel}": quantity
                for (year, month, channel), quantity in sorted(accepted_orders_by_plan_cell.items())
            },
        })
    result.runtime_metrics["partially_fulfilled_deadline_exceeded"] = len(backorder_expired_partial)
    result.runtime_metrics["expired_partial_order_samples"] = expired_partial_samples

    # Orders whose 14-day stock deadline extends beyond the commercial cutoff
    # remain confirmed with their actual pending quantity; no post-cutoff event is emitted.
    for order_key in list(result_by_order):
        if backorders.remove_order(order_key):
            outstanding_lines_by_order[order_key] = 0
            if completion_state is not None:
                completion_state.on_stock_wait_closed_at_cutoff(order_key)
            if isinstance(result, StreamingCoreResult):
                result.runtime_metrics["stock_backorder_orders_at_cutoff"] += 1
            if pending_fulfillments_by_order[order_key] == 0:
                finalize_order_3c(order_key)
    update_backorder_metrics()
    unassigned_reservation_count = sum(len(rows) for rows in unassigned_reservations.values())
    result.runtime_metrics["unassigned_reservation_keys_final"] = unassigned_reservation_count
    if unassigned_reservation_count:
        raise ValueError(f"Reservas sem fulfillment associado ao fim do horizonte: {unassigned_reservation_count}.")

    result.stock_positions = positions
    result.stock_state_events.sort(key=lambda row: (row.occurred_at, row.priority, row.key))
    result.event_trace.sort(key=lambda row: (row[0], row[1], row[2]))
    result.runtime_metrics.update({
        "transaction_events_pushed": queue.total_pushed,
        "transaction_events_processed": queue.total_popped,
        "transaction_events_max_pending": queue.max_pending_events,
        "total_events_scheduled": queue.total_pushed,
        "total_events_processed": queue.total_popped,
        "current_future_events_3c": queue.pending_events,
        "max_future_events": queue.max_pending_events,
        "max_active_purchase_orders": max_active_purchase_orders,
        "sales_intention_digest": sales_intention_digest.hexdigest(),
    })
    if isinstance(result, StreamingCoreResult):
        result.runtime_metrics["confirmed_stock_pending_at_cutoff"] = result.runtime_metrics.get(
            "stock_backorder_orders_at_cutoff", 0
        )
        if completion_state is not None:
            completion_state.finish()
        if stock_audit_enabled:
            result.runtime_metrics["stock_audit_summary"] = stock_audit_summary()
        result.emit_final_positions()
        result.close()
        if result_by_order:
            raise ValueError(f"Pedidos 3C ainda ativos no fim do horizonte: {len(result_by_order)}.")
        result.runtime_metrics.update({
            "max_buffered_rows": emitter.max_buffered_rows,
            "flush_count": emitter.flush_count,
            "total_rows_emitted": emitter.total_rows_emitted,
            "max_active_purchase_orders": max_active_purchase_orders,
            "max_future_events_3c": queue.max_pending_events,
            "current_active_orders": len(result_by_order),
            "current_active_purchase_orders": len(po_by_key),
            "current_future_events_3c": queue.pending_events,
        })
        if customer_frequency_tickets is not None:
            result.runtime_metrics["customer_frequency_orders_remaining"] = customer_frequency_tickets.remaining
    return result


def generate_transactions_incremental(
    config: GeneratorConfig,
    master: MasterData,
    sink: TransactionSink,
    *,
    batch_size: int | None = None,
    incremental_completion: bool = False,
    single_card_index: int | None = None,
    policy_preflight: bool = False,
    forced_fallback_ordinals: dict[str, int] | None = None,
) -> StreamingCoreResult:
    """Run the shared 3C causal engine without retaining historical transaction rows."""
    result = generate_transactions(
        config, master, sink=sink, batch_size=batch_size,
        incremental_completion=incremental_completion,
        single_card_index=single_card_index,
        policy_preflight=policy_preflight,
        forced_fallback_ordinals=forced_fallback_ordinals,
    )
    if not isinstance(result, StreamingCoreResult):
        raise RuntimeError("O caminho incremental não inicializou o resultado de streaming.")
    return result
