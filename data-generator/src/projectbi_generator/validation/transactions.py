"""In-memory invariants for procurement, stock, sales and fulfillment events."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable
from itertools import pairwise
from datetime import datetime, timedelta
from decimal import Decimal

from projectbi_generator.config import GeneratorConfig
from projectbi_generator.cancellations import discount_slice
from projectbi_generator.generators.transactions import weighted_moving_average
from projectbi_generator.models.entities import MasterData
from projectbi_generator.models.transactions import StockPosition, TransactionData
from projectbi_generator.validation.order_history import validate_order_history


def _unique(label: str, values: Iterable[str]) -> None:
    seen: set[str] = set()
    for value in values:
        if value in seen:
            raise ValueError(f"Chave lógica duplicada em {label}.")
        seen.add(value)


def validate_transactional_data(data: TransactionData, master: MasterData, config: GeneratorConfig) -> None:
    """Raise ValueError when event-derived rows violate the approved operational rules."""
    cutoff = datetime.combine(config.end_date, datetime.max.time(), tzinfo=config.timezone)
    earliest = datetime.combine(config.bootstrap_start_date, datetime.min.time(), tzinfo=config.timezone)
    latest_bootstrap = datetime.combine(config.bootstrap_end_date, datetime.max.time(), tzinfo=config.timezone)
    products = {row.sku: row for row in master.products}
    channels = {row.code: row for row in master.sales_channels}
    customers = {row.code: row for row in master.customers}
    stores = {row.code: row for row in master.stores}
    employees = {row.code: row for row in master.employees}
    assignments = master.employee_assignments
    addresses = {row.logical_key: row for row in master.customer_addresses}
    suppliers = {row.code for row in master.suppliers}
    suppliers_by_product: dict[str, set[str]] = defaultdict(set)
    for link in master.product_suppliers:
        if link.is_active:
            suppliers_by_product[link.product_sku].add(link.supplier_code)
    prices: dict[tuple[str, str], list] = defaultdict(list)
    for row in master.product_prices:
        prices[(row.product_sku, row.channel_code)].append(row)
    for rows in prices.values():
        rows.sort(key=lambda row: row.valid_from)

    _unique("purchase orders", (row.key for row in data.purchase_orders))
    _unique("purchase order numbers", (row.number for row in data.purchase_orders))
    _unique("purchase items", (row.key for row in data.purchase_order_items))
    _unique("receipts", (row.key for row in data.goods_receipts))
    _unique("receipt items", (row.key for row in data.goods_receipt_items))
    _unique("sales orders", (row.key for row in data.sales_orders))
    _unique("order numbers", (row.number for row in data.sales_orders))
    _unique("sales items", (row.key for row in data.sales_order_items))
    _unique("sales item cancellations", (row.key for row in data.sales_order_item_cancellations))
    _unique("reservations", (row.key for row in data.stock_reservations))
    _unique("fulfillments", (row.key for row in data.fulfillments))
    _unique("fulfillment items", (row.key for row in data.fulfillment_items))
    _unique("stock movements", (row.key for row in data.stock_movements))

    pos = {row.key: row for row in data.purchase_orders}
    poi = {row.key: row for row in data.purchase_order_items}
    receipts = {row.key: row for row in data.goods_receipts}
    receipt_items = {row.key: row for row in data.goods_receipt_items}
    orders = {row.key: row for row in data.sales_orders}
    items = {row.key: row for row in data.sales_order_items}
    fulfillments = {row.key: row for row in data.fulfillments}
    fulfillment_items = {row.key: row for row in data.fulfillment_items}
    reservations = {row.key: row for row in data.stock_reservations}
    movements = {row.key: row for row in data.stock_movements}
    movements_by_receipt_item: dict[str, list] = defaultdict(list)
    movements_by_fulfillment_item: dict[str, list] = defaultdict(list)
    for movement in data.stock_movements:
        if movement.receipt_item_key:
            movements_by_receipt_item[movement.receipt_item_key].append(movement)
        if movement.fulfillment_item_key:
            movements_by_fulfillment_item[movement.fulfillment_item_key].append(movement)

    received_by_item: dict[str, int] = defaultdict(int)
    for row in data.purchase_order_items:
        order = pos.get(row.order_key)
        if order is None or row.product_sku not in products or row.quantity_ordered <= 0:
            raise ValueError("Item de compra com referência ou quantidade inválida.")
        if order.supplier_code not in suppliers_by_product[row.product_sku]:
            raise ValueError("Compra de fornecedor não associado ao produto.")
        if not isinstance(row.unit_cost_ordered, Decimal) or row.unit_cost_ordered < 0:
            raise ValueError("Custo de compra deve ser Decimal não negativo.")
        in_bootstrap = earliest <= order.ordered_at <= latest_bootstrap
        in_commercial_window = config.start_date <= order.ordered_at.date() <= config.end_date
        if not (in_bootstrap or in_commercial_window):
            raise ValueError("Data da purchase order fora do horizonte válido.")
    for row in data.goods_receipts:
        order = pos.get(row.order_key)
        if order is None or row.location_code not in {loc.code for loc in master.stock_locations}:
            raise ValueError("Goods receipt referencia compra ou local inexistente.")
        if row.received_at < order.ordered_at:
            raise ValueError("Recebimento anterior à purchase order.")
        if row.received_at <= latest_bootstrap and not earliest <= row.received_at <= latest_bootstrap:
            raise ValueError("Recebimento de bootstrap fora da janela aprovada.")
        if row.received_at > latest_bootstrap and row.received_at.date() < config.start_date:
            raise ValueError("Recebimento fora da janela de bootstrap/comercial.")
    receipt_movement_for_item: dict[str, list] = defaultdict(list)
    for row in data.goods_receipt_items:
        receipt = receipts.get(row.receipt_key)
        order_item = poi.get(row.order_item_key)
        if receipt is None or order_item is None or receipt.order_key != order_item.order_key:
            raise ValueError("Linha de recebimento cruza purchase order.")
        if row.quantity_received < 0 or row.accepted_quantity < 0 or row.rejected_quantity < 0:
            raise ValueError("Quantidades de recebimento não podem ser negativas.")
        if row.accepted_quantity + row.rejected_quantity != row.quantity_received:
            raise ValueError("accepted + rejected diverge de quantity_received.")
        if row.quantity_received > order_item.quantity_ordered:
            raise ValueError("Receipt isolado supera a quantidade pedida.")
        if not isinstance(row.unit_acquisition_cost, Decimal):
            raise ValueError("Custo de aquisição deve ser Decimal.")
        received_by_item[row.order_item_key] += row.quantity_received
        matches = movements_by_receipt_item.get(row.key, ())
        if row.accepted_quantity:
            if len(matches) != 1 or matches[0].quantity_delta != row.accepted_quantity:
                raise ValueError("Entrada aceita sem movimento receipt correspondente.")
            movement = matches[0]
            if movement.product_sku != order_item.product_sku or movement.location_code != receipt.location_code:
                raise ValueError("Movimento receipt diverge do produto/local do recebimento.")
            if movement.movement_type != "receipt" or movement.quantity_delta <= 0 or movement.unit_cost != row.unit_acquisition_cost:
                raise ValueError("Movimento receipt tem direção ou custo inválido.")
            receipt_movement_for_item[row.key].append(movement)
        elif matches:
            raise ValueError("Linha totalmente rejeitada não pode criar estoque vendável.")
    if any(quantity > poi[key].quantity_ordered for key, quantity in received_by_item.items()):
        raise ValueError("Recebimento acumulado supera purchase order item.")
    if not any(0 < row.quantity_received < poi[row.order_item_key].quantity_ordered for row in data.goods_receipt_items):
        raise ValueError("Smoke precisa conter ao menos uma compra parcialmente recebida.")
    if not any(row.rejected_quantity > 0 for row in data.goods_receipt_items):
        raise ValueError("Smoke precisa exercitar quantidade rejeitada em recebimento.")

    items_by_order: dict[str, list] = defaultdict(list)
    for item in data.sales_order_items:
        items_by_order[item.order_key].append(item)
    history_by_order: dict[str, list] = defaultdict(list)
    for event in data.order_status_history:
        if event.order_key not in orders or event.status not in {"draft", "placed", "confirmed", "cancelled", "completed"}:
            raise ValueError("Histórico de status referencia pedido/estado inválido.")
        if event.occurred_at > cutoff or event.occurred_at.tzinfo is None:
            raise ValueError("Status fora do cutoff ou sem fuso horário.")
        history_by_order[event.order_key].append(event)
    discounts_by_order: dict[str, Decimal] = defaultdict(lambda: Decimal("0.00"))
    discounts_by_item: dict[str, Decimal] = defaultdict(lambda: Decimal("0.00"))
    for discount in data.applied_discounts:
        order = orders.get(discount.order_key)
        item = items.get(discount.item_key)
        if order is None or item is None or item.order_key != order.key:
            raise ValueError("Desconto referencia item de outro pedido.")
        if discount.scope not in {"line", "order_allocation"} or not isinstance(discount.amount, Decimal) or discount.amount <= 0:
            raise ValueError("Desconto inválido ou não decimal.")
        discounts_by_order[order.key] += discount.amount
        discounts_by_item[item.key] += discount.amount

    cancellations_by_item: dict[str, list] = defaultdict(list)
    for cancellation in data.sales_order_item_cancellations:
        order = orders.get(cancellation.order_key)
        item = items.get(cancellation.item_key)
        amounts = (cancellation.gross_cancelled_amount, cancellation.discount_cancelled_amount,
                   cancellation.net_cancelled_amount, cancellation.shipping_cancelled_amount)
        if (order is None or item is None or item.order_key != order.key
                or cancellation.cancellation_reason != "stock_timeout"
                or cancellation.cancelled_at.tzinfo is None
                or cancellation.cancelled_at < order.placed_at + timedelta(days=config.generation["max_stock_wait_days"])
                or cancellation.cancelled_at > cutoff
                or cancellation.cancelled_quantity <= 0
                or any(not isinstance(value, Decimal) or value < 0 for value in amounts)
                or cancellation.net_cancelled_amount != cancellation.gross_cancelled_amount - cancellation.discount_cancelled_amount):
            raise ValueError("Cancelamento de item contém referência, motivo, tempo, quantidade ou valores inválidos.")
        if cancellation.gross_cancelled_amount != item.unit_sale_price * cancellation.cancelled_quantity:
            raise ValueError("Valor bruto cancelado diverge do preço e quantidade originais.")
        cancellations_by_item[item.key].append(cancellation)

    gross_by_item: dict[str, Decimal] = {}
    for order in data.sales_orders:
        channel = channels.get(order.channel_code)
        if channel is None or channel.channel_type != order.channel_type:
            raise ValueError("Pedido não corresponde ao canal configurado.")
        if order.channel_type != "physical" and (order.customer_code is None or order.customer_code not in customers):
            raise ValueError("Venda digital sem cliente identificado.")
        if order.customer_code is not None and order.customer_code not in customers:
            raise ValueError("Pedido referencia cliente inexistente.")
        if order.channel_type == "physical":
            if order.store_code not in stores or stores[order.store_code].opened_on > order.placed_at.date():
                raise ValueError("Venda física usa loja inexistente ou ainda fechada.")
        elif order.store_code is not None:
            raise ValueError("Pedido digital não deve carregar loja física de venda.")
        if order.address_key:
            address = addresses.get(order.address_key)
            if address is None or address.customer_code != order.customer_code:
                raise ValueError("Snapshot de endereço pertence a outro cliente.")
        if not config.start_date <= order.placed_at.date() <= config.end_date or order.placed_at > cutoff:
            raise ValueError("Pedido fora da janela comercial.")
        if not items_by_order[order.key]:
            raise ValueError("Pedido sem linhas comerciais.")
        subtotal = Decimal("0.00")
        for item in items_by_order[order.key]:
            if item.product_sku not in products or item.quantity <= 0 or not isinstance(item.unit_sale_price, Decimal):
                raise ValueError("Linha de venda com SKU, quantidade ou preço inválido.")
            candidates = prices.get((item.product_sku, order.channel_code), ())
            product_price = next((row for row in reversed(candidates)
                                  if row.valid_from <= order.placed_at
                                  and (row.valid_to is None or order.placed_at < row.valid_to)), None)
            if product_price is None:
                raise ValueError("Preço fora da vigência na hora da venda.")
            if item.unit_sale_price != product_price.amount:
                raise ValueError("Snapshot de preço da linha diverge da vigência aplicada.")
            gross = (item.unit_sale_price * item.quantity).quantize(Decimal("0.01"))
            gross_by_item[item.key] = gross
            if discounts_by_item[item.key] > gross:
                raise ValueError("Desconto supera o valor elegível da linha.")
            subtotal += gross
        if subtotal != order.subtotal or discounts_by_order[order.key] != order.discount:
            raise ValueError("Subtotal ou alocações de desconto não reconciliam com o cabeçalho.")
        if order.total != order.subtotal - order.discount + order.shipping or order.total < 0:
            raise ValueError("Total do pedido incorreto ou negativo.")
        validate_order_history(history_by_order[order.key], order.placed_at, order.status)

    fulfillments_by_order: dict[str, list] = defaultdict(list)
    fulfilled_by_item: dict[str, int] = defaultdict(int)
    allocated_by_item: dict[str, int] = defaultdict(int)
    reservation_by_item_location: dict[tuple[str, str], int] = defaultdict(int)
    reservations_by_key = {row.key: row for row in data.stock_reservations}
    state_by_reservation: dict[str, list] = defaultdict(list)
    orders_with_fulfillment = {row.order_key for row in data.fulfillments}
    for state in data.stock_state_events:
        if state.occurred_at > cutoff or state.occurred_at.tzinfo is None:
            raise ValueError("Evento de estoque fora do cutoff ou sem fuso horário.")
        if state.reservation_key:
            state_by_reservation[state.reservation_key].append(state)
    for reservation in data.stock_reservations:
        order = orders.get(reservation.order_key)
        item = items.get(reservation.item_key)
        if order is None or item is None or item.order_key != order.key or item.product_sku != reservation.product_sku:
            raise ValueError("Reserva não corresponde ao item vendido.")
        if reservation.quantity <= 0 or reservation.status not in {"active", "released", "expired", "consumed"}:
            raise ValueError("Reserva possui quantidade/status inválido.")
        if reservation.status == "released" and order.status != "cancelled":
            raise ValueError("Reserva liberada sem cancelamento.")
        if order.status == "cancelled" and order.key in orders_with_fulfillment:
            raise ValueError("Pedido cancelado tem fulfillment associado.")
        reservation_by_item_location[(item.key, reservation.location_code)] += reservation.quantity
        states = state_by_reservation[reservation.key]
        if not states or states[0].event_type != "reserve" or (reservation.status == "released" and states[-1].event_type != "release") or (reservation.status == "consumed" and states[-1].event_type != "fulfillment"):
            raise ValueError("Ciclo de vida da reserva não reconcilia com eventos.")

    fulfillment_movement_by_item: dict[str, list] = defaultdict(list)
    for fulfillment in data.fulfillments:
        order = orders.get(fulfillment.order_key)
        if order is None or fulfillment.status != "completed" or fulfillment.fulfillment_type not in {"delivery", "store_pickup"}:
            raise ValueError("Fulfillment referencia pedido ou modalidade inválidos.")
        if fulfillment.fulfillment_type == "store_pickup" and (not fulfillment.pickup_store_code or fulfillment.carrier_code is not None):
            raise ValueError("Retirada exige loja e não pode usar carrier.")
        if fulfillment.fulfillment_type == "delivery" and fulfillment.pickup_store_code is not None:
            raise ValueError("Delivery não deve apontar pickup_store.")
        if fulfillment.planned_at < order.placed_at or (fulfillment.completed_at and fulfillment.completed_at < fulfillment.planned_at):
            raise ValueError("Instantes de fulfillment incoerentes.")
        fulfillments_by_order[order.key].append(fulfillment)
    for item in data.fulfillment_items:
        fulfillment = fulfillments.get(item.fulfillment_key)
        sale_item = items.get(item.sale_item_key)
        order = orders.get(item.order_key)
        if fulfillment is None or sale_item is None or order is None or fulfillment.order_key != order.key or sale_item.order_key != order.key:
            raise ValueError("Fulfillment item cruza pedidos ou referências.")
        if order.status == "cancelled":
            raise ValueError("Pedido cancelado não pode ter fulfillment.")
        if item.quantity_allocated <= 0 or item.fulfilled_quantity < 0 or item.fulfilled_quantity > item.quantity_allocated:
            raise ValueError("Quantidade alocada/atendida inválida.")
        if reservation_by_item_location[(sale_item.key, fulfillment.location_code)] < item.quantity_allocated:
            raise ValueError("Fulfillment excede a reserva do item/local.")
        fulfilled_by_item[sale_item.key] += item.fulfilled_quantity
        allocated_by_item[sale_item.key] += item.quantity_allocated
        if item.fulfilled_quantity:
            matches = movements_by_fulfillment_item.get(item.key, ())
            if len(matches) != 1 or matches[0].quantity_delta != -item.fulfilled_quantity:
                raise ValueError("Saída fulfillment diverge da quantidade atendida.")
            movement = matches[0]
            if movement.movement_type != "fulfillment" or movement.quantity_delta >= 0 or not isinstance(movement.unit_cost, Decimal):
                raise ValueError("Movimento fulfillment exige direção negativa e custo Decimal.")
            if movement.product_sku != sale_item.product_sku or movement.location_code != fulfillment.location_code:
                raise ValueError("Movimento fulfillment diverge de item ou local.")
            fulfillment_movement_by_item[item.key].append(movement)
        if item.fulfilled_quantity != item.quantity_allocated:
            if order.status == "completed":
                raise ValueError("Pedido completed contém linha parcialmente atendida.")
    cancelled_by_item: dict[str, int] = defaultdict(int)
    cancelled_by_order: dict[str, int] = defaultdict(int)
    cancellation_shipping_by_order: dict[str, Decimal] = defaultdict(lambda: Decimal("0.00"))
    for item_key, rows in cancellations_by_item.items():
        item = items[item_key]
        order = orders[item.order_key]
        offset = fulfilled_by_item[item_key]
        original_discount = discounts_by_item[item_key]
        for cancellation in sorted(rows, key=lambda row: (row.cancelled_at, row.key)):
            expected_discount = discount_slice(original_discount, item.quantity, offset, cancellation.cancelled_quantity)
            if cancellation.discount_cancelled_amount != expected_discount:
                raise ValueError("Desconto cancelado diverge do rateio determinístico por unidade.")
            offset += cancellation.cancelled_quantity
            cancelled_by_item[item_key] += cancellation.cancelled_quantity
            cancelled_by_order[order.key] += cancellation.cancelled_quantity
            cancellation_shipping_by_order[order.key] += cancellation.shipping_cancelled_amount
    for item_key, item in items.items():
        fulfilled = fulfilled_by_item[item_key]
        cancelled = cancelled_by_item[item_key]
        if fulfilled + cancelled > item.quantity:
            raise ValueError("Fulfillment e cancelamento acumulados excedem quantidade original.")
        if orders[item.order_key].status == "completed" and fulfilled + cancelled != item.quantity:
            raise ValueError("Pedido completed mantém quantidade pendente em item.")
        if orders[item.order_key].status == "cancelled" and cancelled and (fulfilled or cancelled != item.quantity):
            raise ValueError("Pedido integralmente cancelado tem fulfillment ou saldo não cancelado.")
    for order_key, amount in cancellation_shipping_by_order.items():
        order = orders[order_key]
        fulfilled = sum(fulfilled_by_item[row.key] for row in items_by_order[order_key])
        cancelled = cancelled_by_order[order_key]
        ordered = sum(row.quantity for row in items_by_order[order_key])
        expected_shipping = order.shipping if not fulfilled and cancelled == ordered and order.status == "cancelled" else Decimal("0.00")
        if amount != expected_shipping:
            raise ValueError("Estorno de frete diverge da regra de cancelamento integral/entrega parcial.")
    if any(allocated_by_item[key] > item.quantity for key, item in items.items()):
        raise ValueError("Quantidade alocada em fulfillments supera o item vendido.")
    if not any(count > 1 for count in (len(rows) for rows in fulfillments_by_order.values())):
        raise ValueError("Smoke não exercitou pedido dividido em mais de um fulfillment.")
    if not any(fulfilled_by_item.get(item.key, 0) < item.quantity for item in data.sales_order_items):
        raise ValueError("Smoke não exercitou atendimento parcial/não atendido.")

    # Replay the state ledger to validate locks' intended invariants and weighted average.
    replay: dict[tuple[str, str], StockPosition] = {}
    state_events = sorted(data.stock_state_events, key=lambda row: (row.occurred_at, row.priority, row.key))
    movements_by_key = movements
    for event in state_events:
        key = (event.product_sku, event.location_code)
        position = replay.setdefault(key, StockPosition(*key))
        if event.event_type == "receipt":
            movement = movements_by_key.get(event.movement_key or "")
            if movement is None or movement.movement_type != "receipt" or movement.quantity_delta != event.quantity:
                raise ValueError("Stock event receipt não possui movimento correspondente.")
            if not isinstance(event.unit_cost, Decimal):
                raise ValueError("Receipt cost precisa ser Decimal.")
            position.average_unit_cost = weighted_moving_average(position.on_hand_quantity, position.average_unit_cost, event.quantity, event.unit_cost)
            position.on_hand_quantity += event.quantity
        elif event.event_type == "reserve":
            if position.available_quantity < event.quantity:
                raise ValueError(
                    "Reserva maior que o disponível no instante do evento: "
                    f"state={event.key}, sku={event.product_sku}, location={event.location_code}, "
                    f"at={event.occurred_at.isoformat()}, quantity={event.quantity}, "
                    f"available={position.available_quantity}, on_hand={position.on_hand_quantity}, "
                    f"reserved={position.reserved_quantity}."
                )
            position.reserved_quantity += event.quantity
        elif event.event_type == "release":
            if position.reserved_quantity < event.quantity:
                raise ValueError("Cancelamento libera reserva inexistente.")
            position.reserved_quantity -= event.quantity
        elif event.event_type == "fulfillment":
            movement = movements_by_key.get(event.movement_key or "")
            if movement is None or movement.movement_type != "fulfillment" or movement.quantity_delta != -event.quantity:
                raise ValueError("Stock event fulfillment não possui movimento correspondente.")
            if event.quantity > position.reserved_quantity or event.quantity > position.on_hand_quantity:
                raise ValueError("Saída excede quantidade física/reservada.")
            if movement.unit_cost != position.average_unit_cost:
                raise ValueError("Custo da saída não usa a média vigente no instante.")
            position.on_hand_quantity -= event.quantity
            position.reserved_quantity -= event.quantity
        elif event.event_type == "transfer_out":
            movement = movements_by_key.get(event.movement_key or "")
            if (movement is None or movement.movement_type != "transfer_out"
                    or movement.quantity_delta != -event.quantity or position.available_quantity < event.quantity
                    or movement.unit_cost != position.average_unit_cost):
                raise ValueError("Transferência excede disponibilidade ou custo médio de origem inválido.")
            position.on_hand_quantity -= event.quantity
        elif event.event_type in {"transfer_in", "customer_return"}:
            movement = movements_by_key.get(event.movement_key or "")
            expected_type = event.event_type
            if (movement is None or movement.movement_type != expected_type
                    or movement.quantity_delta != event.quantity or movement.unit_cost != event.unit_cost):
                raise ValueError("Entrada de transferência/retorno sem movimento correspondente.")
            position.average_unit_cost = weighted_moving_average(
                position.on_hand_quantity, position.average_unit_cost, event.quantity, event.unit_cost,
            )
            position.on_hand_quantity += event.quantity
        else:
            raise ValueError("Stock event possui tipo desconhecido.")
        if position.on_hand_quantity < 0 or position.reserved_quantity < 0 or position.reserved_quantity > position.on_hand_quantity:
            raise ValueError("Posição negativa ou reservada acima do físico.")

    for key, position in data.stock_positions.items():
        calculated = replay.get(key)
        if calculated is None:
            if (position.on_hand_quantity, position.reserved_quantity, position.average_unit_cost) != (
                0, 0, Decimal("0.00000000")
            ):
                raise ValueError("stock_positions sem movimento/evento deve permanecer vazia.")
            continue
        if (position.on_hand_quantity, position.reserved_quantity, position.average_unit_cost) != (
            calculated.on_hand_quantity, calculated.reserved_quantity, calculated.average_unit_cost
        ):
            raise ValueError("stock_positions diverge do replay do ledger.")
    if not set(replay).issubset(data.stock_positions):
        raise ValueError("Evento de estoque não possui posição final correspondente.")
    physical_by_position: dict[tuple[str, str], int] = defaultdict(int)
    for movement in data.stock_movements:
        key = (movement.product_sku, movement.location_code)
        physical_by_position[key] += movement.quantity_delta
        if movement.movement_type == "receipt" and movement.quantity_delta <= 0:
            raise ValueError("Movimento receipt deve ser positivo.")
        if movement.movement_type == "fulfillment" and movement.quantity_delta >= 0:
            raise ValueError("Movimento fulfillment deve ser negativo.")
        if movement.movement_type in {"transfer_in", "customer_return"} and movement.quantity_delta <= 0:
            raise ValueError("Movimento de entrada deve ser positivo.")
        if movement.movement_type == "transfer_out" and movement.quantity_delta >= 0:
            raise ValueError("Movimento transfer_out deve ser negativo.")
        if movement.movement_type not in {"receipt", "fulfillment", "transfer_out", "transfer_in", "customer_return"}:
            raise ValueError("Fora de escopo: tipo de movimento inesperado.")
        if not isinstance(movement.unit_cost, Decimal) or movement.unit_cost < 0:
            raise ValueError("Custo de movimento obrigatório deve ser Decimal não negativo.")
        if movement.occurred_at > cutoff:
            raise ValueError("Movimento após cutoff.")
    for key, position in data.stock_positions.items():
        if physical_by_position[key] != position.on_hand_quantity:
            raise ValueError("Saldo físico não concilia com a soma dos movimentos.")
    if any(left.occurred_at > right.occurred_at for left, right in pairwise(data.stock_state_events)):
        raise ValueError("Eventos de estado de estoque não estão cronológicos.")
    if any(left[0] > right[0] for left, right in pairwise(data.event_trace)):
        raise ValueError("Fila de eventos não foi processada em ordem cronológica.")

    expected_realized_cost = sum(
        (Decimal(-movement.quantity_delta) * movement.unit_cost for movement in data.stock_movements if movement.movement_type == "fulfillment"),
        Decimal("0.00"),
    )
    reported = data.summary()["realized_cost"]
    if reported != expected_realized_cost:
        raise ValueError("Custo realizado reportado diverge do ledger.")
