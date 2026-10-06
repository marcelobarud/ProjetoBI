"""Phase 3D causal payments, logistics events, transfers, returns and refunds."""

from __future__ import annotations

from collections import defaultdict
from datetime import date, datetime, time, timedelta
from decimal import Decimal

from projectbi_generator.config import GeneratorConfig
from projectbi_generator.generators.master import FAMILIES
from projectbi_generator.generators.transactions import EventQueue, ScheduledEvent, weighted_moving_average
from projectbi_generator.models.entities import MasterData
from projectbi_generator.models.transactions import (
    FulfillmentEvent, Payment, PaymentInstallment, Refund, Return, ReturnItem,
    StockMovement, StockPosition, StockStateEvent, StockTransfer, StockTransferItem,
    TransactionData,
)
from projectbi_generator.sinks import CollectingSink, CountingDiscardingSink
from projectbi_generator.seeds import create_domain_randoms

CENT = Decimal("0.01")


def _stamp(config: GeneratorConfig, day: date, hour: int, minute: int = 0) -> datetime:
    return datetime.combine(day, time(hour, minute), tzinfo=config.timezone)


def _money(value: Decimal) -> Decimal:
    return value.quantize(CENT)


def _schedule_payments(config: GeneratorConfig, master: MasterData, data: TransactionData, queue: EventQueue) -> None:
    rng = create_domain_randoms(config.root_seed, config.generator_version)["payments"].rng
    capable = {row.code: row.is_installment_capable for row in master.payment_methods if row.is_active}
    order_customer_type = {row.code: row.customer_type for row in master.customers}
    method_by_type = {row.method_type: row.code for row in master.payment_methods if row.is_active}
    split_rate = config.generation["split_payment_rate_percent"]
    split_indices = ({42, 151, 263} if config.profile == "smoke" else
                     {index for index in range(1, len(data.sales_orders) + 1) if (index - 1) % 100 < split_rate})
    single_card_index = min(
        (index for index, row in enumerate(data.sales_orders, start=1)
         if row.status != "cancelled" and index not in split_indices
         and index % 41 != 7 and index % 97 != 43),
        key=lambda index: (data.sales_orders[index - 1].total, index),
    )

    def choose(order, index: int) -> str:
        if order.channel_type == "physical" and rng.randrange(100) < 15:
            return method_by_type["cash"]
        if order.customer_code and order_customer_type[order.customer_code] == "business" and rng.randrange(100) < 8:
            return method_by_type["bank_transfer"]
        if rng.randrange(100) < (42 if order.channel_type != "physical" else 28):
            return method_by_type["instant"]
        return method_by_type["card"]

    for index, order in enumerate(data.sales_orders, start=1):
        attempted = order.placed_at + timedelta(minutes=8 + index % 13)
        if order.status == "cancelled":
            method = choose(order, index)
            cancelled_at = order.placed_at + timedelta(hours=4, minutes=1)
            queue.push(ScheduledEvent(cancelled_at, 5, f"PAYMENT-{index:04d}-CANCELLED", "payment", {
                "order": order, "method": method, "amount": order.total, "status": "cancelled",
                "attempted_at": attempted, "authorized_at": None, "settled_at": None,
                "reference": f"PAY-SM-{index:04d}-CANCELLED", "installments": 0,
            }))
            continue

        split = index in split_indices and order.total >= Decimal("100.00")
        method = (method_by_type["card"]
                  if index == single_card_index else choose(order, index))
        if split:
            method = method_by_type["card"]
            first = _money(order.total * Decimal("0.60"))
            second = order.total - first
            for part, (part_method, amount) in enumerate(((method, first), (method_by_type["instant"], second)), start=1):
                at = attempted + timedelta(minutes=part * 2)
                queue.push(ScheduledEvent(at + timedelta(minutes=7), 5, f"PAYMENT-{index:04d}-SPLIT-{part}", "payment", {
                    "order": order, "method": part_method, "amount": amount, "status": "settled",
                    "attempted_at": at, "authorized_at": at + timedelta(minutes=2),
                    "settled_at": at + timedelta(minutes=7), "reference": f"PAY-SM-{index:04d}-SPLIT-{part}",
                    "installments": None,
                }))
            continue

        retry_kind = "declined" if index % 41 == 7 else "failed" if index % 97 == 43 else None
        if retry_kind:
            queue.push(ScheduledEvent(attempted, 5, f"PAYMENT-{index:04d}-DECLINED", "payment", {
                "order": order, "method": method, "amount": order.total, "status": retry_kind,
                "attempted_at": attempted, "authorized_at": None, "settled_at": None,
                "reference": f"PAY-SM-{index:04d}-FIRST", "installments": 0,
            }))
            retry_at = attempted + timedelta(hours=2)
            queue.push(ScheduledEvent(retry_at + timedelta(minutes=7), 5, f"PAYMENT-{index:04d}-RETRY", "payment", {
                "order": order, "method": method, "amount": order.total, "status": "settled",
                "attempted_at": retry_at, "authorized_at": retry_at + timedelta(minutes=2),
                "settled_at": retry_at + timedelta(minutes=7), "reference": f"PAY-SM-{index:04d}-RETRY",
                "installments": None,
            }))
            continue

        installments = None
        if capable.get(method, False):
            if order.total >= Decimal("12000.00"):
                installments = 6
            elif order.total >= Decimal("6000.00"):
                installments = 4
            elif order.total >= Decimal("1500.00"):
                installments = 3
            elif order.total >= Decimal("1000.00"):
                installments = 2
            else:
                installments = 1
        queue.push(ScheduledEvent(attempted + timedelta(minutes=7), 5, f"PAYMENT-{index:04d}-SETTLED", "payment", {
            "order": order, "method": method, "amount": order.total, "status": "settled",
            "attempted_at": attempted, "authorized_at": attempted + timedelta(minutes=2),
            "settled_at": attempted + timedelta(minutes=7), "reference": f"PAY-SM-{index:04d}-01",
            "installments": installments,
        }))


def _installments(config: GeneratorConfig, payment: Payment, count: int, data: TransactionData) -> None:
    cents = int((payment.amount / CENT).to_integral_exact())
    quotient, remainder = divmod(cents, count)
    for number in range(1, count + 1):
        part = Decimal(quotient + (1 if number <= remainder else 0)) * CENT
        due_on = payment.settled_at.date() + timedelta(days=30 * (number - 1))
        paid_at = _stamp(config, due_on, 12) if due_on <= config.end_date else None
        status = "paid" if paid_at else "pending"
        data.payment_installments.append(PaymentInstallment(
            f"INST-{payment.key}-{number:02d}", payment.key, number, due_on, part, status, paid_at,
        ))


def _add_fulfillment_events(config: GeneratorConfig, master: MasterData, data: TransactionData, queue: EventQueue) -> None:
    rng = create_domain_randoms(config.root_seed, config.generator_version)["logistics"].rng
    employees = [row.code for row in master.employees if row.status == "active"]
    by_order = {row.key: row for row in data.sales_orders}
    for ordinal, fulfillment in enumerate(sorted(data.fulfillments, key=lambda row: (row.planned_at, row.key)), start=1):
        order = by_order[fulfillment.order_key]
        prepared_at = fulfillment.planned_at or order.placed_at
        queue.push(ScheduledEvent(prepared_at, 10, f"LOG-{ordinal:05d}-PREPARED", "fulfillment_event", {
            "fulfillment": fulfillment, "type": "prepared", "employee": employees[ordinal % len(employees)] if employees else None,
            "description": "Separação concluída no fluxo sintético.",
        }))
        if fulfillment.fulfillment_type == "store_pickup":
            picked_at = fulfillment.completed_at or (prepared_at + timedelta(hours=5))
            ready_at = min(prepared_at + timedelta(hours=1 + ordinal % 4), picked_at - timedelta(minutes=5))
            queue.push(ScheduledEvent(ready_at, 11, f"LOG-{ordinal:05d}-READY", "fulfillment_event", {
                "fulfillment": fulfillment, "type": "pickup_ready", "employee": None,
                "description": "Pedido disponível para retirada.",
            }))
            queue.push(ScheduledEvent(picked_at, 12, f"LOG-{ordinal:05d}-PICKED", "fulfillment_event", {
                "fulfillment": fulfillment, "type": "picked_up", "employee": None,
                "description": "Retirada concluída.",
            }))
        else:
            dispatched = fulfillment.dispatched_at or (prepared_at + timedelta(hours=3))
            delivered = fulfillment.completed_at or (dispatched + timedelta(days=2))
            queue.push(ScheduledEvent(dispatched, 11, f"LOG-{ordinal:05d}-DISPATCHED", "fulfillment_event", {
                "fulfillment": fulfillment, "type": "dispatched", "employee": None,
                "description": "Remessa despachada para entrega.",
            }))
            if rng.randrange(100) < 7 and delivered > dispatched + timedelta(minutes=10):
                queue.push(ScheduledEvent(dispatched + timedelta(minutes=5), 12, f"LOG-{ordinal:05d}-ATTEMPT", "fulfillment_event", {
                    "fulfillment": fulfillment, "type": "delivery_attempt", "employee": None,
                    "description": "Tentativa de entrega registrada.",
                }))
            if ordinal % 37 == 0 and delivered > dispatched + timedelta(minutes=15):
                queue.push(ScheduledEvent(dispatched + timedelta(minutes=10), 13, f"LOG-{ordinal:05d}-EXCEPTION", "fulfillment_event", {
                    "fulfillment": fulfillment, "type": "exception", "employee": None,
                    "description": "Ocorrência logística resolvida antes da entrega.",
                }))
            queue.push(ScheduledEvent(delivered, 14, f"LOG-{ordinal:05d}-DELIVERED", "fulfillment_event", {
                "fulfillment": fulfillment, "type": "delivered", "employee": None,
                "description": "Entrega confirmada.",
            }))


def _plan_transfer_candidates(master: MasterData, data: TransactionData, config: GeneratorConfig) -> list[tuple[str, str, str, int]]:
    if config.generation["stock_transfers"] == 0:
        return []
    products = {row.sku: row for row in master.products}
    by_sku: dict[str, list[StockPosition]] = defaultdict(list)
    for position in data.stock_positions.values():
        by_sku[position.product_sku].append(position)
    candidates = []
    for sku, positions in sorted(by_sku.items()):
        family = FAMILIES[products[sku].category_code][1]
        target = 7 if family in {"NOTEBOOK", "DESKTOP", "GRAPHICS"} else 10
        for destination in positions:
            deficit = target - destination.on_hand_quantity
            if deficit <= 0:
                continue
            for source in positions:
                surplus = source.available_quantity - 5
                if source.location_code == destination.location_code or surplus <= 0:
                    continue
                quantity = min(3, deficit, surplus)
                if quantity > 0:
                    candidates.append((sku, source.location_code, destination.location_code, quantity))
    candidates.sort(key=lambda row: (-row[3], row[0], row[2], row[1]))
    selected = []
    used_skus: set[str] = set()
    used_pairs: set[tuple[str, str]] = set()
    for row in candidates:
        if row[0] in used_skus or (row[1], row[2]) in used_pairs:
            continue
        selected.append(row)
        used_skus.add(row[0])
        used_pairs.add((row[1], row[2]))
        if len(selected) == config.generation["stock_transfers"]:
            break
    if not selected and config.profile == "smoke":
        raise ValueError("Não foi encontrada necessidade de rebalanceamento para o smoke de transferência.")
    # The destination deficit and donor surplus are derived from completed demand events.
    return selected


def _plan_return_candidates(config: GeneratorConfig, master: MasterData, data: TransactionData) -> list[tuple]:
    rng = create_domain_randoms(config.root_seed, config.generator_version)["returns"].rng
    orders = {row.key: row for row in data.sales_orders}
    items = {row.key: row for row in data.sales_order_items}
    customer_types = {row.code: row.customer_type for row in master.customers}
    products = {row.sku: row for row in master.products}
    fulfillments = {row.key: row for row in data.fulfillments}
    fulfilled = [row for row in data.fulfillment_items if row.fulfilled_quantity > 0]
    fulfilled.sort(key=lambda row: (fulfillments[row.fulfillment_key].completed_at, row.key))
    latest_request = _stamp(config, config.end_date, 23) - timedelta(days=35)
    eligible = []
    for fi in fulfilled:
        fulfillment = fulfillments[fi.fulfillment_key]
        if fulfillment.completed_at is None or fulfillment.completed_at + timedelta(days=4) > latest_request:
            continue
        order = orders[fi.order_key]
        item = items[fi.sale_item_key]
        probability = Decimal("0.045")
        if order.channel_type != "physical":
            probability += Decimal("0.020")
        if order.customer_code and customer_types[order.customer_code] == "business":
            probability -= Decimal("0.015")
        if FAMILIES[products[item.product_sku].category_code][1] in {"ACCESSORIES", "PRINTING"}:
            probability += Decimal("0.015")
        if rng.random() < probability:
            eligible.append((fi, fulfillment, order, item))
    # A narrow deterministic minimum keeps all return paths exercised by the small smoke profile.
    if len(eligible) < config.generation["minimum_returns"]:
        chosen = {row[0].key for row in eligible}
        for fi in fulfilled:
            if fi.key in chosen:
                continue
            fulfillment = fulfillments[fi.fulfillment_key]
            if fulfillment.completed_at and fulfillment.completed_at + timedelta(days=4) <= latest_request:
                eligible.append((fi, fulfillment, orders[fi.order_key], items[fi.sale_item_key]))
                chosen.add(fi.key)
                if len(eligible) == config.generation["minimum_returns"]:
                    break
    maximum = config.generation["maximum_returns"]
    return eligible[:maximum] if maximum else eligible


def _replay_extended_stock(data: TransactionData) -> None:
    positions: dict[tuple[str, str], StockPosition] = {}
    fulfillment_movements = {row.fulfillment_item_key: row for row in data.stock_movements
                             if row.movement_type == "fulfillment" and row.fulfillment_item_key}
    fulfillment_item_by_movement = {row.key: row.fulfillment_item_key for row in data.stock_movements
                                    if row.movement_type == "fulfillment" and row.fulfillment_item_key}
    return_movements = {row.return_item_key: row for row in data.stock_movements
                        if row.movement_type == "customer_return" and row.return_item_key}
    return_sources = {row.key: row.source_fulfillment_item_key for row in data.return_items}
    fulfilled_cost: dict[str, tuple[int, Decimal]] = {}
    transfer_cost: dict[str, Decimal] = {}
    transfer_movements: list[StockMovement] = []
    for event in sorted(data.stock_state_events, key=lambda row: (row.occurred_at, row.priority, row.key)):
        key = (event.product_sku, event.location_code)
        position = positions.setdefault(key, StockPosition(*key))
        if event.event_type == "receipt":
            position.average_unit_cost = weighted_moving_average(position.on_hand_quantity, position.average_unit_cost, event.quantity, event.unit_cost)
            position.on_hand_quantity += event.quantity
        elif event.event_type == "reserve":
            position.reserved_quantity += event.quantity
        elif event.event_type == "release":
            position.reserved_quantity -= event.quantity
        elif event.event_type == "fulfillment":
            if position.on_hand_quantity < event.quantity or position.reserved_quantity < event.quantity or event.movement_key is None:
                raise ValueError("Fulfillment excede o disponível no replay cronológico.")
            fulfillment_item_key = fulfillment_item_by_movement.get(event.movement_key)
            if fulfillment_item_key is None:
                raise ValueError("Evento fulfillment não referencia movimento válido.")
            event.unit_cost = position.average_unit_cost
            movement = fulfillment_movements.get(fulfillment_item_key)
            if movement is None:
                raise ValueError("Fulfillment sem movimento de estoque correspondente.")
            movement.unit_cost = event.unit_cost
            quantity, cost_total = fulfilled_cost.get(fulfillment_item_key, (0, Decimal("0")))
            fulfilled_cost[fulfillment_item_key] = (
                quantity + event.quantity, cost_total + Decimal(event.quantity) * event.unit_cost,
            )
            position.on_hand_quantity -= event.quantity
            position.reserved_quantity -= event.quantity
        elif event.event_type == "transfer_out":
            if position.available_quantity < event.quantity or event.transfer_item_key is None:
                raise ValueError("Transferência excede disponibilidade na origem.")
            event.unit_cost = position.average_unit_cost
            position.on_hand_quantity -= event.quantity
            transfer_cost[event.transfer_item_key] = event.unit_cost
            transfer_movements.append(StockMovement(
                f"MOV-TRANSFER-{event.transfer_item_key}-OUT", event.product_sku, event.location_code,
                "transfer_out", -event.quantity, event.unit_cost, event.occurred_at,
                transfer_item_key=event.transfer_item_key,
            ))
        elif event.event_type == "transfer_in":
            if event.transfer_item_key not in transfer_cost:
                raise ValueError("Transferência recebida antes da expedição correspondente.")
            event.unit_cost = transfer_cost[event.transfer_item_key]
            position.average_unit_cost = weighted_moving_average(position.on_hand_quantity, position.average_unit_cost, event.quantity, event.unit_cost)
            position.on_hand_quantity += event.quantity
            transfer_movements.append(StockMovement(
                f"MOV-TRANSFER-{event.transfer_item_key}-IN", event.product_sku, event.location_code,
                "transfer_in", event.quantity, event.unit_cost, event.occurred_at,
                transfer_item_key=event.transfer_item_key,
            ))
        elif event.event_type == "customer_return":
            source_key = return_sources.get(event.return_item_key)
            historical = fulfilled_cost.get(source_key) if source_key else None
            if not historical or historical[0] <= 0:
                raise ValueError("Retorno sellable sem custo fulfillment histórico anterior.")
            event.unit_cost = (historical[1] / historical[0]).quantize(Decimal("0.00000001"))
            movement = return_movements.get(event.return_item_key)
            if movement is None:
                raise ValueError("Retorno vendável sem movimento de estoque correspondente.")
            movement.unit_cost = event.unit_cost
            position.average_unit_cost = weighted_moving_average(position.on_hand_quantity, position.average_unit_cost, event.quantity, event.unit_cost)
            position.on_hand_quantity += event.quantity
        else:
            raise ValueError(f"Evento de estoque desconhecido: {event.event_type}")
        if position.on_hand_quantity < 0 or position.reserved_quantity < 0 or position.reserved_quantity > position.on_hand_quantity:
            raise ValueError("Replay estendido produziu posição de estoque inválida.")
    data.stock_movements.extend(transfer_movements)
    data.stock_positions = positions
    data.stock_state_events.sort(key=lambda row: (row.occurred_at, row.priority, row.key))
    data.stock_movements.sort(key=lambda row: (row.occurred_at, row.key))


def extend_transactions(config: GeneratorConfig, master: MasterData, data: TransactionData) -> TransactionData:
    """Extend the phase-3C output using only events caused by existing orders/fulfillments."""
    queue = EventQueue()
    _schedule_payments(config, master, data, queue)
    _add_fulfillment_events(config, master, data, queue)
    transfer_plan = _plan_transfer_candidates(master, data, config)
    return_plan = _plan_return_candidates(config, master, data)
    sale_items = {row.key: row for row in data.sales_order_items}
    orders = {row.key: row for row in data.sales_orders}
    fulfillments = {row.key: row for row in data.fulfillments}
    fulfillment_items = {row.key: row for row in data.fulfillment_items}
    by_order_payments: dict[str, list[Payment]] = defaultdict(list)
    discounts_by_item: dict[str, Decimal] = defaultdict(lambda: Decimal("0.00"))
    for discount in data.applied_discounts:
        discounts_by_item[discount.item_key] += discount.amount

    for ordinal, (fi, fulfillment, order, item) in enumerate(return_plan, start=1):
        requested_at = fulfillment.completed_at + timedelta(days=5 + (ordinal * 7) % 20)
        queue.push(ScheduledEvent(requested_at, 20, f"RETURN-{ordinal:03d}-REQUEST", "return_request", {
            "ordinal": ordinal, "fi": fi, "fulfillment": fulfillment, "order": order, "item": item,
        }))
        is_rejected = ordinal == 4
        decided_at = requested_at + timedelta(days=1 + ordinal % 2)
        queue.push(ScheduledEvent(decided_at, 21, f"RETURN-{ordinal:03d}-DECISION", "return_decision", {
            "ordinal": ordinal, "rejected": is_rejected,
        }))
        if not is_rejected:
            received_at = decided_at + timedelta(days=2 + ordinal % 4)
            destination = ("sellable", "quarantine", "sellable", "discard", "repair")[ordinal % 5]
            condition = {"sellable": "good", "quarantine": "unknown", "discard": "defective", "repair": "damaged"}[destination]
            queue.push(ScheduledEvent(received_at, 22, f"RETURN-{ordinal:03d}-RECEIVE", "return_receive", {
                "ordinal": ordinal, "destination": destination, "condition": condition,
            }))
            if ordinal not in {5, 9}:
                eligible = _money((item.unit_sale_price * item.quantity - discounts_by_item[item.key]) / Decimal(item.quantity))
                refund_amount = _money(eligible * (Decimal("0.80") if ordinal == 2 else Decimal("1.00")))
                queue.push(ScheduledEvent(received_at + timedelta(days=1), 23, f"RETURN-{ordinal:03d}-REFUND", "refund", {
                    "ordinal": ordinal, "amount": refund_amount,
                }))

    # Transfer triggers are derived from post-demand low stock and a donor's unreserved surplus.
    base_last = max(row.occurred_at for row in data.stock_state_events)
    for ordinal, (sku, source, destination, quantity) in enumerate(transfer_plan, start=1):
        requested = base_last + timedelta(minutes=20)
        dispatched = requested + timedelta(minutes=15)
        received = dispatched + timedelta(hours=6)
        transfer = StockTransfer(f"TRANSFER-{ordinal:03d}", f"TR-SM-{ordinal:04d}", source, destination,
                                 "completed", requested, dispatched, received)
        item_key = f"TRANSFER-ITEM-{ordinal:03d}-01"
        transfer_item = StockTransferItem(item_key, transfer.key, sku, 1, quantity, quantity, quantity)
        data.stock_transfers.append(transfer)
        data.stock_transfer_items.append(transfer_item)
        queue.push(ScheduledEvent(dispatched, 30, f"TRANSFER-{ordinal:03d}-OUT", "transfer_out", {
            "transfer": transfer, "item": transfer_item, "sku": sku, "location": source, "quantity": quantity,
        }))
        queue.push(ScheduledEvent(received, 31, f"TRANSFER-{ordinal:03d}-IN", "transfer_in", {
            "transfer": transfer, "item": transfer_item, "sku": sku, "location": destination, "quantity": quantity,
        }))

    return_by_ordinal: dict[int, tuple[Return, ReturnItem]] = {}
    payment_counter = 0
    refunded_by_payment: dict[str, Decimal] = defaultdict(lambda: Decimal("0.00"))
    movement_cost_by_fulfillment: dict[str, tuple[int, Decimal]] = {}
    for movement in data.stock_movements:
        if movement.movement_type == "fulfillment" and movement.fulfillment_item_key:
            quantity, cost = movement_cost_by_fulfillment.get(movement.fulfillment_item_key, (0, Decimal("0")))
            movement_cost_by_fulfillment[movement.fulfillment_item_key] = (
                quantity + abs(movement.quantity_delta), cost + Decimal(abs(movement.quantity_delta)) * movement.unit_cost,
            )
    while queue:
        event = queue.pop()
        if event.occurred_at > _stamp(config, config.end_date, 23, 59):
            continue
        payload = event.payload
        data.event_trace.append((event.occurred_at, event.event_type, event.logical_key))
        if event.event_type == "payment":
            payment_counter += 1
            order = payload["order"]
            payment = Payment(f"PAY-{payment_counter:05d}", order.key, payload["method"], payload["reference"],
                              payload["status"], payload["amount"], payload["attempted_at"], payload["authorized_at"], payload["settled_at"])
            data.payments.append(payment)
            by_order_payments[order.key].append(payment)
            installments = payload["installments"]
            if payment.status in {"captured", "settled"} and installments:
                _installments(config, payment, installments, data)
        elif event.event_type == "fulfillment_event":
            fulfillment = payload["fulfillment"]
            row = FulfillmentEvent(fulfillment.key, payload["type"], event.occurred_at,
                                   payload["employee"], payload["description"])
            data.fulfillment_events.append(row)
        elif event.event_type == "return_request":
            ordinal = payload["ordinal"]
            return_key = f"RETURN-{ordinal:03d}"
            order = payload["order"]
            reason = ("defective", "damaged", "incorrect_item", "buyer_remorse", "other")[(ordinal - 1) % 5]
            ret = Return(return_key, order.key, f"RET-SM-{ordinal:04d}", "requested", reason,
                         event.occurred_at, None)
            item = payload["item"]
            fi = payload["fi"]
            ret_item = ReturnItem(f"RETURN-ITEM-{ordinal:03d}-01", return_key, order.key, item.key, fi.key,
                                  1, 0, 0, None, None, None)
            data.returns.append(ret)
            data.return_items.append(ret_item)
            return_by_ordinal[ordinal] = (ret, ret_item)
        elif event.event_type == "return_decision":
            ordinal = payload["ordinal"]
            ret, ret_item = return_by_ordinal[ordinal]
            ret.decided_at = event.occurred_at
            if payload["rejected"]:
                ret.status = "rejected"
            else:
                ret.status = "approved"
                ret_item.quantity_approved = ret_item.quantity_requested
        elif event.event_type == "return_receive":
            ordinal = payload["ordinal"]
            ret, ret_item = return_by_ordinal[ordinal]
            fi = fulfillment_items[ret_item.source_fulfillment_item_key]
            fulfillment = fulfillments[fi.fulfillment_key]
            ret.status = "received"
            ret_item.quantity_approved = ret_item.quantity_requested
            ret_item.quantity_received = ret_item.quantity_approved
            ret_item.item_condition = payload["condition"]
            ret_item.stock_destination = payload["destination"]
            ret_item.received_at = event.occurred_at
            ret_item.destination_location_code = fulfillment.location_code
            if payload["destination"] == "sellable":
                historical = movement_cost_by_fulfillment.get(fi.key)
                if not historical or not historical[0]:
                    raise ValueError("Retorno vendável sem movimento fulfillment histórico.")
                returned_qty = ret_item.quantity_received
                weighted_cost = historical[1] / historical[0]
                historical_cost = weighted_cost.quantize(Decimal("0.00000001"))
                state_key = f"STATE-RETURN-{ordinal:03d}"
                movement_key = f"MOV-RETURN-{ordinal:03d}"
                movement = StockMovement(movement_key, sale_items[ret_item.sale_item_key].product_sku,
                                         fulfillment.location_code, "customer_return", returned_qty, historical_cost,
                                         event.occurred_at, return_item_key=ret_item.key)
                data.stock_movements.append(movement)
                data.stock_state_events.append(StockStateEvent(state_key, event.occurred_at, "customer_return",
                    movement.product_sku, fulfillment.location_code, returned_qty, 25, historical_cost,
                    movement_key, return_item_key=ret_item.key))
        elif event.event_type == "refund":
            ordinal = payload["ordinal"]
            ret, _ = return_by_ordinal[ordinal]
            order_payments = [row for row in by_order_payments[ret.order_key] if row.status in {"captured", "settled"}]
            remaining = payload["amount"]
            for payment in order_payments:
                already = refunded_by_payment.get(payment.key, Decimal("0.00"))
                available = payment.amount - already
                part = min(remaining, available)
                if part <= 0:
                    continue
                data.refunds.append(Refund(f"REFUND-{ordinal:03d}-{len(data.refunds)+1:03d}", ret.order_key,
                    payment.key, ret.key, "completed", part, "return", event.occurred_at,
                    event.occurred_at + timedelta(hours=2)))
                refunded_by_payment[payment.key] = already + part
                remaining -= part
                if remaining == 0:
                    break
            if remaining:
                raise ValueError("Refund solicitado excede pagamentos capturados elegíveis.")
            if ret.status == "received":
                ret.status = "closed"
        elif event.event_type == "transfer_out":
            transfer = payload["transfer"]
            item = payload["item"]
            data.stock_state_events.append(StockStateEvent(f"STATE-{event.logical_key}", event.occurred_at, "transfer_out",
                payload["sku"], payload["location"], payload["quantity"], 40,
                transfer_item_key=item.key))
        elif event.event_type == "transfer_in":
            transfer = payload["transfer"]
            item = payload["item"]
            data.stock_state_events.append(StockStateEvent(f"STATE-{event.logical_key}", event.occurred_at, "transfer_in",
                payload["sku"], payload["location"], payload["quantity"], 0,
                transfer_item_key=item.key))

    # The main event heap remains the source of transaction order; new inventory events are replayed together with 3C.
    _replay_extended_stock(data)
    data.runtime_metrics.update({
        "completion_events_pushed": queue.total_pushed,
        "completion_events_processed": queue.total_popped,
        "completion_max_future_events": queue.max_pending_events,
        "max_future_events": max(
            data.runtime_metrics.get("max_future_events", 0), queue.max_pending_events
        ),
    })
    return data


def generate_full_transactions_incremental(
    config: GeneratorConfig,
    master: MasterData,
    sink,
    *,
    batch_size: int | None = None,
):
    """Generate 3C+3D through one chronological event queue and one sink.

    Smoke uses a bounded preflight pass that retains only the legacy payment
    selector's single winning order index. No transaction collection is kept.
    The actual full output is then generated once with 3C and 3D events sharing
    the same queue and emitter.
    """
    from projectbi_generator.generators.transactions import generate_transactions_incremental
    from projectbi_generator.validation.completion import validate_completed_data
    from projectbi_generator.validation.transactions import validate_transactional_data

    single_card_index = None
    fallback_ordinals = None
    if config.profile == "smoke":
        policy = generate_transactions_incremental(
            config, master, CountingDiscardingSink(), batch_size=batch_size,
            incremental_completion=True, policy_preflight=True,
        ).completion_policy
        single_card_index = policy["single_card_index"]
        fallback_ordinals = policy["fallback_ordinals"]
        if single_card_index is None:
            raise ValueError("Não foi possível resolver o pagamento smoke de cartão sem estado histórico.")
    result = generate_transactions_incremental(
        config, master, sink, batch_size=batch_size, incremental_completion=True,
        single_card_index=single_card_index, forced_fallback_ordinals=fallback_ordinals,
    )
    if isinstance(sink, CollectingSink):
        data = transaction_data_from_collected_stream(result, sink)
        validate_transactional_data(data, master, config)
        validate_completed_data(data, master, config)
    return result


def transaction_data_from_collected_stream(result, sink: CollectingSink) -> TransactionData:
    """Materialize only an explicitly collecting (smoke-sized) sink for legacy validators."""
    table_fields = (
        "purchase_orders", "purchase_order_items", "goods_receipts", "goods_receipt_items",
        "sales_orders", "sales_order_items", "order_status_history", "applied_discounts",
        "stock_reservations", "fulfillments", "fulfillment_items", "stock_movements",
        "stock_state_events", "payments", "payment_installments", "fulfillment_events",
        "stock_transfers", "stock_transfer_items", "returns", "return_items", "refunds",
    )
    data = TransactionData()
    for name in table_fields:
        setattr(data, name, list(sink.rows_by_table.get(name, ())))
    data.stock_positions = {
        (row.product_sku, row.location_code): row
        for row in sink.rows_by_table.get("stock_positions", ())
    }
    data.runtime_metrics = dict(result.runtime_metrics)
    return data
