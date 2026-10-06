"""Causal, bounded-memory Phase 3D completion for the incremental engine."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Callable

from projectbi_generator.config import GeneratorConfig
from projectbi_generator.generators.completion import _money, _stamp
from projectbi_generator.generators.master import FAMILIES
from projectbi_generator.generators.transactions import ScheduledEvent, weighted_moving_average
from projectbi_generator.models.entities import MasterData
from projectbi_generator.models.transactions import (
    Fulfillment, FulfillmentEvent, FulfillmentItem, Payment, PaymentInstallment,
    Refund, Return, ReturnItem, SaleOrderItem, SaleOrder, StockMovement, StockPosition,
    StockStateEvent, StockTransfer, StockTransferItem,
)
from projectbi_generator.seeds import create_domain_randoms

CENT = Decimal("0.01")
COST_SCALE = Decimal("0.00000001")


@dataclass
class _PaymentState:
    pending_attempts: int
    pending_fulfillment_items: int
    open_returns: int = 0
    captured: list[tuple[str, Decimal, Decimal]] = field(default_factory=list)


@dataclass
class _ReturnEligibility:
    ordinal: int
    order_key: str
    sale_item_key: str
    fulfillment_item_key: str
    product_sku: str
    location_code: str
    fulfilled_quantity: int
    fulfilled_at: datetime
    historical_cost_numerator: Decimal
    historical_cost_quantity: int
    refund_base: Decimal


@dataclass
class _ActiveReturn:
    return_row: Return
    item_row: ReturnItem
    source: _ReturnEligibility
    refund_amount: Decimal
    will_refund: bool


@dataclass
class _ActiveTransfer:
    row: StockTransfer
    item: StockTransferItem
    unit_cost: Decimal | None = None


class IncrementalCompletionState:
    """3D event handlers attached to the same queue and emitter as the 3C core."""

    def __init__(
        self,
        config: GeneratorConfig,
        master: MasterData,
        result,
        push: Callable,
        single_card_index: int | None,
        *,
        policy_preflight: bool = False,
        forced_fallback_ordinals: dict[str, int] | None = None,
    ) -> None:
        self.config = config
        self.master = master
        self.result = result
        self.push = push
        seeds = create_domain_randoms(config.root_seed, config.generator_version)
        self.payment_rng = seeds["payments"].rng
        self.logistics_rng = seeds["logistics"].rng
        self.return_rng = seeds["returns"].rng
        self.active_payments: dict[str, _PaymentState] = {}
        self.active_fulfillments: dict[str, tuple[Fulfillment, int]] = {}
        self.active_transfers: dict[str, _ActiveTransfer] = {}
        self.return_eligibility: dict[str, _ReturnEligibility] = {}
        self.active_returns: dict[int, _ActiveReturn] = {}
        self.fulfillment_ordinal = 0
        self.payment_counter = 0
        self.transfer_counter = 0
        self.return_counter = 0
        self.random_return_count = 0
        self.policy_preflight = policy_preflight
        self.forced_fallback_ordinals = forced_fallback_ordinals or {}
        self.policy_single_card: tuple[Decimal, int] | None = None
        self._fallback_candidates: list[tuple[str, str, Decimal]] = []
        self.refund_counter = 0
        self.single_card_index = single_card_index
        self.capable = {row.code: row.is_installment_capable for row in master.payment_methods if row.is_active}
        self.methods = {row.method_type: row.code for row in master.payment_methods if row.is_active}
        self.customer_types = {row.code: row.customer_type for row in master.customers}
        self.products = {row.sku: row for row in master.products}
        self.channels = {row.code: row for row in master.sales_channels}
        self.active_employees = [row.code for row in master.employees if row.status == "active"]
        self.core_on_hand: dict[tuple[str, str], int] = {}
        self.last_core_state_at: datetime | None = None
        self.transfers_scheduled = False
        self.metrics = result.runtime_metrics
        self.metrics.update({
            "current_active_payments": 0, "max_active_payments": 0,
            "current_active_fulfillments": 0, "max_active_fulfillments": 0,
            "current_active_transfers": 0, "max_active_transfers": 0,
            "current_return_eligibility": 0, "max_return_eligibility": 0,
            "current_active_returns": 0, "max_active_returns": 0,
            "total_events_scheduled": 0, "total_events_processed": 0,
        })

    def _schedule(self, at: datetime, priority: int, key: str, kind: str, payload: dict) -> None:
        self.push(at, priority, key, kind, payload)
        # The 3C engine's push drops beyond-cutoff events without inserting them.
        if at <= _stamp(self.config, self.config.end_date, 23, 59):
            self.metrics["total_events_scheduled"] += 1

    def _update_active(self, key: str, current_key: str, max_key: str, count: int) -> None:
        self.metrics[current_key] = count
        self.metrics[max_key] = max(self.metrics.get(max_key, 0), count)

    def _payment_attempts(self, order: SaleOrder, index: int, cancelled: bool) -> list[dict]:
        rng = self.payment_rng
        method_by_type = self.methods

        def choose() -> str:
            if order.channel_type == "physical" and rng.randrange(100) < 15:
                return method_by_type["cash"]
            if order.customer_code and self.customer_types[order.customer_code] == "business" and rng.randrange(100) < 8:
                return method_by_type["bank_transfer"]
            return method_by_type["instant"] if rng.randrange(100) < (42 if order.channel_type != "physical" else 28) else method_by_type["card"]

        attempted = order.placed_at + timedelta(minutes=8 + index % 13)
        if cancelled:
            cancelled_at = order.placed_at + timedelta(hours=4, minutes=1)
            return [{
                "order_key": order.key, "method": choose(), "amount": order.total, "status": "cancelled",
                "attempted_at": attempted, "authorized_at": None, "settled_at": None,
                "reference": f"PAY-SM-{index:04d}-CANCELLED", "installments": 0,
                "_event_at": cancelled_at,
            }]
        split = self.config.profile == "smoke" and index in {42, 151, 263}
        if self.config.profile != "smoke":
            split = (index - 1) % 100 < self.config.generation["split_payment_rate_percent"]
        split = split and order.total >= Decimal("100.00")
        method = self.methods["card"] if index == self.single_card_index else choose()
        if split:
            method = self.methods["card"]
            first = _money(order.total * Decimal("0.60"))
            second = order.total - first
            return [{
                "order_key": order.key, "method": part_method, "amount": amount, "status": "settled",
                "attempted_at": attempted + timedelta(minutes=part * 2),
                "authorized_at": attempted + timedelta(minutes=part * 2 + 2),
                "settled_at": attempted + timedelta(minutes=part * 2 + 7),
                "reference": f"PAY-SM-{index:04d}-SPLIT-{part}", "installments": None,
                "_event_at": attempted + timedelta(minutes=part * 2 + 7),
            } for part, (part_method, amount) in enumerate(((method, first), (self.methods["instant"], second)), start=1)]
        retry_kind = "declined" if index % 41 == 7 else "failed" if index % 97 == 43 else None
        if retry_kind:
            retry_at = attempted + timedelta(hours=2)
            return [
                {"order_key": order.key, "method": method, "amount": order.total, "status": retry_kind,
                 "attempted_at": attempted, "authorized_at": None, "settled_at": None,
                 "reference": f"PAY-SM-{index:04d}-FIRST", "installments": 0,
                 "_event_at": attempted},
                {"order_key": order.key, "method": method, "amount": order.total, "status": "settled",
                 "attempted_at": retry_at, "authorized_at": retry_at + timedelta(minutes=2),
                 "settled_at": retry_at + timedelta(minutes=7),
                 "reference": f"PAY-SM-{index:04d}-RETRY", "installments": None,
                 "_event_at": retry_at + timedelta(minutes=7)},
            ]
        installments = None
        if self.capable.get(method, False):
            installments = 6 if order.total >= Decimal("12000.00") else 4 if order.total >= Decimal("6000.00") else 3 if order.total >= Decimal("1500.00") else 2 if order.total >= Decimal("1000.00") else 1
        return [{
            "order_key": order.key, "method": method, "amount": order.total, "status": "settled",
            "attempted_at": attempted, "authorized_at": attempted + timedelta(minutes=2),
            "settled_at": attempted + timedelta(minutes=7),
            "reference": f"PAY-SM-{index:04d}-01", "installments": installments,
            "_event_at": attempted + timedelta(minutes=7),
        }]

    def on_sale(self, order: SaleOrder, index: int, cancelled: bool, pending_fulfillment_items: int) -> None:
        split_indices = {42, 151, 263} if self.config.profile == "smoke" else set()
        has_retry = index % 41 == 7 or index % 97 == 43
        if not cancelled and index not in split_indices and not has_retry:
            candidate = (order.total, index)
            if self.policy_single_card is None or candidate < self.policy_single_card:
                self.policy_single_card = candidate
        attempts = self._payment_attempts(order, index, cancelled)
        self.active_payments[order.key] = _PaymentState(len(attempts), pending_fulfillment_items)
        self._update_active(order.key, "current_active_payments", "max_active_payments", len(self.active_payments))
        split = len(attempts) == 2 and "SPLIT" in attempts[0]["reference"]
        if split:
            self.result.aggregates["split_payment_orders"] += 1
        for ordinal, payload in enumerate(attempts, start=1):
            at = payload["_event_at"]
            reference = payload["reference"]
            if reference.endswith("-CANCELLED"):
                suffix = "CANCELLED"
            elif "-SPLIT-" in reference:
                suffix = "SPLIT-" + reference.rsplit("-", 1)[-1]
            elif reference.endswith("-FIRST"):
                suffix = "DECLINED"
            elif reference.endswith("-RETRY"):
                suffix = "RETRY"
            else:
                suffix = "SETTLED"
            key = f"PAYMENT-{index:04d}-{suffix}"
            self._schedule(at, 5, key, "payment", payload)

    def on_fulfillment_created(self, fulfillment: Fulfillment) -> None:
        self.fulfillment_ordinal += 1
        ordinal = self.fulfillment_ordinal
        self.active_fulfillments[fulfillment.key] = (fulfillment, 0)
        self._update_active(fulfillment.key, "current_active_fulfillments", "max_active_fulfillments", len(self.active_fulfillments))
        prepared = fulfillment.planned_at or fulfillment.completed_at
        payload = {"fulfillment_key": fulfillment.key, "type": "prepared", "employee": self.active_employees[ordinal % len(self.active_employees)] if self.active_employees else None,
                   "description": "Separação concluída no fluxo sintético."}
        self._schedule(prepared, 10, f"LOG-{ordinal:05d}-PREPARED", "fulfillment_event", payload)
        number = 1
        if fulfillment.fulfillment_type == "store_pickup":
            picked = fulfillment.completed_at or prepared + timedelta(hours=5)
            ready = min(prepared + timedelta(hours=1 + ordinal % 4), picked - timedelta(minutes=5))
            self._schedule(ready, 11, f"LOG-{ordinal:05d}-READY", "fulfillment_event", {"fulfillment_key": fulfillment.key, "type": "pickup_ready", "employee": None, "description": "Pedido disponível para retirada."})
            self._schedule(picked, 12, f"LOG-{ordinal:05d}-PICKED", "fulfillment_event", {"fulfillment_key": fulfillment.key, "type": "picked_up", "employee": None, "description": "Retirada concluída."})
            number = 3
        else:
            dispatched = fulfillment.dispatched_at or prepared + timedelta(hours=3)
            delivered = fulfillment.completed_at or dispatched + timedelta(days=2)
            self._schedule(dispatched, 11, f"LOG-{ordinal:05d}-DISPATCHED", "fulfillment_event", {"fulfillment_key": fulfillment.key, "type": "dispatched", "employee": None, "description": "Remessa despachada para entrega."})
            number = 3
            if self.logistics_rng.randrange(100) < 7 and delivered > dispatched + timedelta(minutes=10):
                self._schedule(dispatched + timedelta(minutes=5), 12, f"LOG-{ordinal:05d}-ATTEMPT", "fulfillment_event", {"fulfillment_key": fulfillment.key, "type": "delivery_attempt", "employee": None, "description": "Tentativa de entrega registrada."})
                number += 1
            if ordinal % 37 == 0 and delivered > dispatched + timedelta(minutes=15):
                self._schedule(dispatched + timedelta(minutes=10), 13, f"LOG-{ordinal:05d}-EXCEPTION", "fulfillment_event", {"fulfillment_key": fulfillment.key, "type": "exception", "employee": None, "description": "Ocorrência logística resolvida antes da entrega."})
                number += 1
            self._schedule(delivered, 14, f"LOG-{ordinal:05d}-DELIVERED", "fulfillment_event", {"fulfillment_key": fulfillment.key, "type": "delivered", "employee": None, "description": "Entrega confirmada."})
        self.active_fulfillments[fulfillment.key] = (fulfillment, number)
        self.metrics["current_active_fulfillments"] = len(self.active_fulfillments)

    def on_core_movement(self, movement: StockMovement) -> None:
        key = (movement.product_sku, movement.location_code)
        self.core_on_hand[key] = self.core_on_hand.get(key, 0) + movement.quantity_delta

    def on_core_state(self, state: StockStateEvent) -> None:
        self.last_core_state_at = max(self.last_core_state_at or state.occurred_at, state.occurred_at)

    def on_fulfilled(
        self, fulfillment_item: FulfillmentItem, fulfillment: Fulfillment,
        order: SaleOrder, sale_item: SaleOrderItem, discount: Decimal,
        unit_cost: Decimal, at: datetime,
    ) -> None:
        order_state = self.active_payments.get(order.key)
        if order_state is None:
            raise ValueError("Estado financeiro expirou antes da elegibilidade de devolução.")
        order_state.pending_fulfillment_items -= 1
        if order_state.pending_fulfillment_items < 0:
            raise ValueError("Contador de fulfillments ativos ficou negativo.")
        latest_request = _stamp(self.config, self.config.end_date, 23) - timedelta(days=35)
        if fulfillment_item.fulfilled_quantity > 0 and at + timedelta(days=4) <= latest_request:
            probability = Decimal("0.045")
            if order.channel_type != "physical":
                probability += Decimal("0.020")
            if order.customer_code and self.customer_types[order.customer_code] == "business":
                probability -= Decimal("0.015")
            family = FAMILIES[self.products[sale_item.product_sku].category_code][1]
            if family in {"ACCESSORIES", "PRINTING"}:
                probability += Decimal("0.015")
            random_selected = self.return_rng.random() < probability
            forced_ordinal = self.forced_fallback_ordinals.get(fulfillment_item.key)
            if random_selected:
                self.random_return_count += 1
                ordinal = self.random_return_count
            elif forced_ordinal is not None:
                ordinal = forced_ordinal
            else:
                ordinal = 0
                if self.policy_preflight and len(self._fallback_candidates) < self.config.generation["minimum_returns"]:
                    reason = ("defective", "damaged", "incorrect_item", "buyer_remorse", "other")[(self.random_return_count) % 5]
                    refund_base = _money((sale_item.unit_sale_price * sale_item.quantity - discount) / Decimal(sale_item.quantity))
                    self._fallback_candidates.append((fulfillment_item.key, reason, refund_base))
            selected = random_selected or forced_ordinal is not None
            if selected:
                self.return_counter = self.random_return_count
                if ordinal > self.config.generation["maximum_returns"] > 0:
                    selected = False
                else:
                    refund_base = _money((sale_item.unit_sale_price * sale_item.quantity - discount) / Decimal(sale_item.quantity))
                    source = _ReturnEligibility(
                        ordinal, order.key, sale_item.key, fulfillment_item.key, sale_item.product_sku,
                        fulfillment.location_code, fulfillment_item.fulfilled_quantity, at,
                        Decimal(fulfillment_item.fulfilled_quantity) * unit_cost,
                        fulfillment_item.fulfilled_quantity, refund_base,
                    )
                    requested = at + timedelta(days=5 + (ordinal * 7) % 20)
                    reason = ("defective", "damaged", "incorrect_item", "buyer_remorse", "other")[(ordinal - 1) % 5]
                    is_rejected = ordinal == 4
                    decided = requested + timedelta(days=1 + ordinal % 2)
                    destination = ("sellable", "quarantine", "sellable", "discard", "repair")[ordinal % 5]
                    condition = {"sellable": "good", "quarantine": "unknown", "discard": "defective", "repair": "damaged"}[destination]
                    receive_at = decided + timedelta(days=2 + ordinal % 4)
                    will_refund = not is_rejected and ordinal not in {5, 9}
                    refund_amount = _money(refund_base * (Decimal("0.80") if ordinal == 2 else Decimal("1.00")))
                    self.return_eligibility[fulfillment_item.key] = source
                    self.metrics["current_return_eligibility"] = len(self.return_eligibility)
                    self.metrics["max_return_eligibility"] = max(self.metrics.get("max_return_eligibility", 0), len(self.return_eligibility))
                    order_state.open_returns += 1
                    payload = {"ordinal": ordinal, "source": source, "reason": reason,
                               "refund_amount": refund_amount, "will_refund": will_refund}
                    self._schedule(requested, 20, f"RETURN-{ordinal:03d}-REQUEST", "return_request", payload)
                    self._schedule(decided, 21, f"RETURN-{ordinal:03d}-DECISION", "return_decision", {"ordinal": ordinal, "rejected": is_rejected})
                    if not is_rejected:
                        self._schedule(receive_at, 22, f"RETURN-{ordinal:03d}-RECEIVE", "return_receive", {"ordinal": ordinal, "destination": destination, "condition": condition})
                        if will_refund:
                            self._schedule(receive_at + timedelta(days=1), 23, f"RETURN-{ordinal:03d}-REFUND", "refund", {"ordinal": ordinal, "amount": refund_amount})
        self._maybe_evict_payment_state(order.key)

    def _maybe_evict_payment_state(self, order_key: str) -> None:
        state = self.active_payments.get(order_key)
        if state and not state.pending_attempts and not state.pending_fulfillment_items and not state.open_returns:
            self.active_payments.pop(order_key, None)
            self.result.release_transaction_id("sales_orders", order_key)
            self.metrics["current_active_payments"] = len(self.active_payments)

    def _schedule_transfers(self, positions: dict[tuple[str, str], StockPosition]) -> None:
        if self.transfers_scheduled:
            return
        self.transfers_scheduled = True
        count = self.config.generation["stock_transfers"]
        if count <= 0:
            return
        candidates: list[tuple[str, str, str, int]] = []
        by_sku: dict[str, list[tuple[str, int]]] = {}
        for (sku, location), quantity in self.core_on_hand.items():
            by_sku.setdefault(sku, []).append((location, quantity))
        for sku, stock in sorted(by_sku.items()):
            family = FAMILIES[self.products[sku].category_code][1]
            target = 7 if family in {"NOTEBOOK", "DESKTOP", "GRAPHICS"} else 10
            for destination, on_hand in stock:
                deficit = target - on_hand
                if deficit <= 0:
                    continue
                for source, source_qty in stock:
                    surplus = source_qty - 5
                    if source == destination or surplus <= 0:
                        continue
                    qty = min(3, deficit, surplus)
                    if qty > 0:
                        candidates.append((sku, source, destination, qty))
        candidates.sort(key=lambda row: (-row[3], row[0], row[2], row[1]))
        used_skus: set[str] = set()
        used_pairs: set[tuple[str, str]] = set()
        selected = []
        for candidate in candidates:
            if candidate[0] in used_skus or (candidate[1], candidate[2]) in used_pairs:
                continue
            selected.append(candidate)
            used_skus.add(candidate[0])
            used_pairs.add((candidate[1], candidate[2]))
            if len(selected) == count:
                break
        if not selected and self.config.profile == "smoke":
            raise ValueError("Não foi encontrada necessidade de rebalanceamento para o smoke de transferência.")
        if not selected:
            return
        base_last = self.last_core_state_at
        if base_last is None:
            raise ValueError("Não há estado 3C para agendar transferências.")
        for ordinal, (sku, source, destination, quantity) in enumerate(selected, start=1):
            self.transfer_counter += 1
            number = self.transfer_counter
            requested = base_last + timedelta(minutes=20)
            dispatched = requested + timedelta(minutes=15)
            received = dispatched + timedelta(hours=6)
            transfer = StockTransfer(f"TRANSFER-{number:03d}", f"TR-SM-{number:04d}", source, destination,
                                     "completed", requested, dispatched, received)
            item = StockTransferItem(f"TRANSFER-ITEM-{number:03d}-01", transfer.key, sku, 1,
                                     quantity, quantity, quantity)
            state = _ActiveTransfer(transfer, item)
            self.active_transfers[item.key] = state
            self.result.stock_transfers.append(transfer)
            self.result.stock_transfer_items.append(item)
            self._schedule(dispatched, 30, f"TRANSFER-{number:03d}-OUT", "transfer_out", {"item_key": item.key, "sku": sku, "location": source, "quantity": quantity})
            self._schedule(received, 31, f"TRANSFER-{number:03d}-IN", "transfer_in", {"item_key": item.key, "sku": sku, "location": destination, "quantity": quantity})
        self.metrics["current_active_transfers"] = len(self.active_transfers)
        self.metrics["max_active_transfers"] = max(self.metrics.get("max_active_transfers", 0), len(self.active_transfers))

    def on_core_complete(self, positions: dict[tuple[str, str], StockPosition]) -> None:
        self._schedule_transfers(positions)

    def process_event(self, event: ScheduledEvent, positions: dict[tuple[str, str], StockPosition], append_state: Callable) -> bool:
        payload = event.payload
        kind = event.event_type
        self.metrics["total_events_processed"] += 1
        if kind == "payment":
            self.payment_counter += 1
            row = Payment(f"PAY-{self.payment_counter:05d}", payload["order_key"], payload["method"], payload["reference"], payload["status"], payload["amount"], payload["attempted_at"], payload["authorized_at"], payload["settled_at"])
            self.result.payments.append(row)
            state = self.active_payments[row.order_key]
            if row.status in {"captured", "settled"}:
                state.captured.append((row.key, row.amount, Decimal("0.00")))
            installments = payload["installments"]
            if row.status in {"captured", "settled"} and installments:
                cents = int((row.amount / CENT).to_integral_exact())
                quotient, remainder = divmod(cents, installments)
                total = Decimal("0.00")
                for number in range(1, installments + 1):
                    amount = Decimal(quotient + int(number <= remainder)) * CENT
                    total += amount
                    due_on = row.settled_at.date() + timedelta(days=30 * (number - 1))
                    paid_at = _stamp(self.config, due_on, 12) if due_on <= self.config.end_date else None
                    self.result.payment_installments.append(PaymentInstallment(f"INST-{row.key}-{number:02d}", row.key, number, due_on, amount, "paid" if paid_at else "pending", paid_at))
                if total != row.amount:
                    raise ValueError("Soma das parcelas diverge do pagamento antes da emissão.")
            state.pending_attempts -= 1
            self._maybe_evict_payment_state(row.order_key)
        elif kind == "fulfillment_event":
            row = FulfillmentEvent(payload["fulfillment_key"], payload["type"], event.occurred_at, payload["employee"], payload["description"])
            self.result.fulfillment_events.append(row)
            fulfillment, pending = self.active_fulfillments[row.fulfillment_key]
            pending -= 1
            if pending <= 0:
                self.active_fulfillments.pop(row.fulfillment_key, None)
            else:
                self.active_fulfillments[row.fulfillment_key] = (fulfillment, pending)
            self.metrics["current_active_fulfillments"] = len(self.active_fulfillments)
        elif kind == "transfer_out":
            active = self.active_transfers[payload["item_key"]]
            position = positions[(payload["sku"], payload["location"])]
            quantity = payload["quantity"]
            if position.available_quantity < quantity or position.on_hand_quantity < quantity:
                raise ValueError("Transferência excede estoque disponível na origem.")
            cost = position.average_unit_cost
            active.unit_cost = cost
            position.on_hand_quantity -= quantity
            movement_key = f"MOV-TRANSFER-{active.item.key}-OUT"
            movement = StockMovement(movement_key, payload["sku"], payload["location"], "transfer_out", -quantity, cost, event.occurred_at, transfer_item_key=active.item.key)
            self.result.stock_movements.append(movement)
            append_state(StockStateEvent(f"STATE-{event.logical_key}", event.occurred_at, "transfer_out", payload["sku"], payload["location"], quantity, 40, cost, movement_key, transfer_item_key=active.item.key))
        elif kind == "transfer_in":
            active = self.active_transfers[payload["item_key"]]
            if active.unit_cost is None:
                raise ValueError("Transferência recebida sem custo capturado na origem.")
            position = positions.setdefault((payload["sku"], payload["location"]), StockPosition(payload["sku"], payload["location"]))
            position.average_unit_cost = weighted_moving_average(position.on_hand_quantity, position.average_unit_cost, payload["quantity"], active.unit_cost)
            position.on_hand_quantity += payload["quantity"]
            movement_key = f"MOV-TRANSFER-{active.item.key}-IN"
            movement = StockMovement(movement_key, payload["sku"], payload["location"], "transfer_in", payload["quantity"], active.unit_cost, event.occurred_at, transfer_item_key=active.item.key)
            self.result.stock_movements.append(movement)
            append_state(StockStateEvent(f"STATE-{event.logical_key}", event.occurred_at, "transfer_in", payload["sku"], payload["location"], payload["quantity"], 0, active.unit_cost, movement_key, transfer_item_key=active.item.key))
            self.result.publish("stock_transfers", active.row.key)
            self.result.publish("stock_transfer_items", active.item.key)
            self.result.release_transaction_id("stock_transfer_items", active.item.key)
            self.active_transfers.pop(active.item.key, None)
            self.metrics["current_active_transfers"] = len(self.active_transfers)
        elif kind == "return_request":
            source = payload["source"]
            self.return_eligibility.pop(source.fulfillment_item_key, None)
            reason = payload["reason"]
            ret = Return(f"RETURN-{source.ordinal:03d}", source.order_key, f"RET-SM-{source.ordinal:04d}", "requested", reason, event.occurred_at, None)
            item = ReturnItem(f"RETURN-ITEM-{source.ordinal:03d}-01", ret.key, source.order_key, source.sale_item_key, source.fulfillment_item_key, 1, 0, 0, None, None, None)
            self.result.returns.append(ret)
            self.result.return_items.append(item)
            self.active_returns[source.ordinal] = _ActiveReturn(ret, item, source, payload["refund_amount"], payload["will_refund"])
            self.metrics["current_return_eligibility"] = len(self.return_eligibility)
            self.metrics["current_active_returns"] = len(self.active_returns)
            self.metrics["max_active_returns"] = max(self.metrics.get("max_active_returns", 0), len(self.active_returns))
        elif kind == "return_decision":
            active = self.active_returns[payload["ordinal"]]
            active.return_row.decided_at = event.occurred_at
            if payload["rejected"]:
                active.return_row.status = "rejected"
                self._finish_return(active)
            else:
                active.return_row.status = "approved"
                active.item_row.quantity_approved = active.item_row.quantity_requested
        elif kind == "return_receive":
            active = self.active_returns[payload["ordinal"]]
            source = active.source
            active.return_row.status = "received"
            active.item_row.quantity_approved = active.item_row.quantity_requested
            active.item_row.quantity_received = active.item_row.quantity_approved
            active.item_row.item_condition = payload["condition"]
            active.item_row.stock_destination = payload["destination"]
            active.item_row.received_at = event.occurred_at
            active.item_row.destination_location_code = source.location_code
            if payload["destination"] == "sellable":
                if source.historical_cost_quantity <= 0:
                    raise ValueError("Return sellable sem quantidade fulfillment histórica.")
                unit_cost = (source.historical_cost_numerator / source.historical_cost_quantity).quantize(COST_SCALE)
                key = (source.product_sku, source.location_code)
                position = positions[key]
                position.average_unit_cost = weighted_moving_average(position.on_hand_quantity, position.average_unit_cost, 1, unit_cost)
                position.on_hand_quantity += 1
                movement_key = f"MOV-RETURN-{source.ordinal:03d}"
                movement = StockMovement(movement_key, source.product_sku, source.location_code, "customer_return", 1, unit_cost, event.occurred_at, return_item_key=active.item_row.key)
                self.result.stock_movements.append(movement)
                append_state(StockStateEvent(f"STATE-RETURN-{source.ordinal:03d}", event.occurred_at, "customer_return", source.product_sku, source.location_code, 1, 25, unit_cost, movement_key, return_item_key=active.item_row.key))
            if not active.will_refund:
                self._finish_return(active)
        elif kind == "refund":
            active = self.active_returns[payload["ordinal"]]
            state = self.active_payments[active.source.order_key]
            remaining = payload["amount"]
            for index, (payment_key, amount, refunded) in enumerate(state.captured):
                available = amount - refunded
                part = min(remaining, available)
                if part <= 0:
                    continue
                self.refund_counter += 1
                self.result.refunds.append(Refund(f"REFUND-{active.source.ordinal:03d}-{self.refund_counter:03d}", active.source.order_key, payment_key, active.return_row.key, "completed", part, "return", event.occurred_at, event.occurred_at + timedelta(hours=2)))
                state.captured[index] = (payment_key, amount, refunded + part)
                remaining -= part
                if remaining == 0:
                    break
            if remaining:
                raise ValueError("Refund solicitado excede pagamentos capturados elegíveis.")
            if active.return_row.status == "received":
                active.return_row.status = "closed"
            self._finish_return(active)
        else:
            return False
        return True

    def _finish_return(self, active: _ActiveReturn) -> None:
        source = active.source
        self.result.publish("returns", active.return_row.key)
        self.result.publish("return_items", active.item_row.key)
        self.result.release_transaction_id("returns", active.return_row.key)
        self.result.release_transaction_id("return_items", active.item_row.key)
        self.active_returns.pop(source.ordinal, None)
        self.metrics["current_active_returns"] = len(self.active_returns)
        state = self.active_payments.get(source.order_key)
        if state:
            state.open_returns -= 1
            self._maybe_evict_payment_state(source.order_key)

    def finish(self) -> None:
        needed = max(0, self.config.generation["minimum_returns"] - self.random_return_count)
        fallback = self._fallback_candidates[:needed]
        if self.policy_preflight:
            self.result.completion_policy = {
                "single_card_index": self.policy_single_card[1] if self.policy_single_card else None,
                "random_return_count": self.random_return_count,
                "fallback_ordinals": {
                    key: self.random_return_count + index
                    for index, (key, _reason, _amount) in enumerate(fallback, start=1)
                },
            }
        if (self.config.profile == "smoke" and not self.policy_preflight
                and self.random_return_count + len(self.forced_fallback_ordinals)
                < self.config.generation["minimum_returns"]):
            raise ValueError("O fluxo incremental não atingiu o mínimo configurado de devoluções.")
        if self.active_payments or self.active_fulfillments or self.active_transfers or self.active_returns or self.return_eligibility:
            raise ValueError("Estados ativos 3D permaneceram após o cutoff.")
        if self.metrics["total_events_processed"] > self.metrics["total_events_scheduled"]:
            raise ValueError("Contagem de eventos 3D processados excede eventos agendados.")
