"""In-memory invariants for the phase-3D financial and reverse-logistics flows."""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime, time
from decimal import Decimal

from projectbi_generator.config import GeneratorConfig
from projectbi_generator.generators.transactions import weighted_moving_average
from projectbi_generator.models.entities import MasterData
from projectbi_generator.models.transactions import TransactionData

SUCCESS = {"captured", "settled"}


def validate_completed_data(data: TransactionData, master: MasterData, config: GeneratorConfig) -> dict[str, Decimal | int]:
    cutoff = datetime.combine(config.end_date, time(23, 59, 59), tzinfo=config.timezone)
    orders = {row.key: row for row in data.sales_orders}
    items = {row.key: row for row in data.sales_order_items}
    fulfillments = {row.key: row for row in data.fulfillments}
    fulfillment_items = {row.key: row for row in data.fulfillment_items}
    methods = {row.code: row for row in master.payment_methods}
    customers = {row.code: row for row in master.customers}
    payments = {row.key: row for row in data.payments}
    returns = {row.key: row for row in data.returns}
    payment_by_order: dict[str, list] = defaultdict(list)
    installments_by_payment: dict[str, list] = defaultdict(list)
    refunds_by_payment: dict[str, list] = defaultdict(list)
    return_quantity: dict[str, int] = defaultdict(int)
    _unique("payments", [row.key for row in data.payments])
    _unique("payment references", [row.reference for row in data.payments])
    _unique("installments", [row.key for row in data.payment_installments])
    _unique("transfer numbers", [row.number for row in data.stock_transfers])
    _unique("transfer items", [row.key for row in data.stock_transfer_items])
    _unique("return numbers", [row.number for row in data.returns])
    _unique("return items", [row.key for row in data.return_items])
    _unique("refunds", [row.key for row in data.refunds])

    for payment in data.payments:
        order = orders.get(payment.order_key)
        method = methods.get(payment.method_code)
        if order is None or method is None or not method.is_active or not isinstance(payment.amount, Decimal) or payment.amount <= 0:
            raise ValueError("Pagamento referencia pedido/meio inválido ou valor não decimal positivo.")
        if payment.status not in {"pending", "authorized", "captured", "settled", "declined", "cancelled", "failed"}:
            raise ValueError("Status de pagamento não permitido pelo schema.")
        if payment.attempted_at > cutoff or payment.attempted_at < order.placed_at:
            raise ValueError("Tentativa de pagamento fora do intervalo/cutoff do pedido.")
        if payment.status in {"declined", "failed", "cancelled"}:
            if payment.authorized_at is not None or payment.settled_at is not None:
                raise ValueError("Pagamento recusado/falho/cancelado não pode conter autorização/liquidação.")
        elif payment.status in SUCCESS:
            if payment.authorized_at is None or payment.settled_at is None or not payment.attempted_at <= payment.authorized_at <= payment.settled_at <= cutoff:
                raise ValueError("Pagamento bem-sucedido tem cronologia inválida.")
        if method.method_type == "cash" and order.channel_type != "physical":
            raise ValueError("Dinheiro foi usado fora de venda física.")
        if method.method_type == "bank_transfer" and (not order.customer_code or customers[order.customer_code].customer_type != "business"):
            raise ValueError("Transferência bancária deve estar associada a cliente PJ.")
        payment_by_order[order.key].append(payment)

    captured_total = Decimal("0.00")
    for order in data.sales_orders:
        operations = payment_by_order[order.key]
        captured = sum((row.amount for row in operations if row.status in SUCCESS), Decimal("0.00"))
        captured_total += captured
        if order.status == "cancelled":
            if captured != 0 or not any(row.status == "cancelled" for row in operations):
                raise ValueError("Pedido cancelado não possui cancelamento financeiro coerente.")
        elif captured != order.total:
            raise ValueError("Operações capturadas não conciliam exatamente com o total do pedido.")
    if not any(row.status == "declined" for row in data.payments) or not any(row.status == "failed" for row in data.payments):
        raise ValueError("Smoke deve exercitar tentativas declined e failed.")
    for payment in data.payments:
        if payment.status in {"declined", "failed"}:
            if not any(row.order_key == payment.order_key and row.status in SUCCESS and row.attempted_at > payment.attempted_at for row in data.payments):
                raise ValueError("Tentativa recusada/falha sem retry posterior bem-sucedido.")
    split_orders = sum(sum(row.status in SUCCESS for row in payment_by_order[order.key]) > 1 for order in data.sales_orders)
    if split_orders == 0:
        raise ValueError("Smoke não contém split payment.")

    for row in data.payment_installments:
        payment = payments.get(row.payment_key)
        if payment is None or payment.status not in SUCCESS or not methods[payment.method_code].is_installment_capable:
            raise ValueError("Parcela associada a pagamento não parcelável ou sem sucesso.")
        if row.status not in {"pending", "paid", "overdue", "cancelled", "failed"} or row.amount <= 0:
            raise ValueError("Parcela tem estado ou valor inválido.")
        if row.paid_at and (row.paid_at.date() != row.due_on or row.paid_at > cutoff):
            raise ValueError("Pagamento de parcela está fora do vencimento/cutoff.")
        installments_by_payment[payment.key].append(row)
    installment_counts = set()
    for payment in data.payments:
        installments = installments_by_payment[payment.key]
        if installments:
            installments.sort(key=lambda row: row.number)
            if [row.number for row in installments] != list(range(1, len(installments) + 1)):
                raise ValueError("Numeração de parcelas não é sequencial.")
            if sum((row.amount for row in installments), Decimal("0.00")) != payment.amount:
                raise ValueError("Parcelas não conciliam exatamente com o pagamento.")
            if not methods[payment.method_code].is_installment_capable:
                raise ValueError("Meio sem parcelamento recebeu parcelas.")
            installment_counts.add(len(installments))
    if not any(count == 1 for count in installment_counts) or not any(2 <= count <= 4 for count in installment_counts) or not any(count >= 5 for count in installment_counts):
        raise ValueError("Smoke deve conter pagamentos em 1, 2–4 e pelo menos 5 parcelas.")
    if any(methods[payment.method_code].method_type in {"cash", "instant"} and installments_by_payment[payment.key] for payment in data.payments):
        raise ValueError("Dinheiro e pagamento instantâneo não podem ser parcelados.")

    event_by_fulfillment: dict[str, list] = defaultdict(list)
    allowed_events = {"prepared", "dispatched", "delivery_attempt", "delivered", "pickup_ready", "picked_up", "exception", "cancelled"}
    for event in data.fulfillment_events:
        if event.fulfillment_key not in fulfillments or event.event_type not in allowed_events or event.occurred_at > cutoff:
            raise ValueError("Evento logístico referencia remessa inválida ou excede cutoff.")
        event_by_fulfillment[event.fulfillment_key].append(event)
    for fulfillment in data.fulfillments:
        events = sorted(event_by_fulfillment[fulfillment.key], key=lambda row: (row.occurred_at, row.event_type))
        types = [row.event_type for row in events]
        if fulfillment.status == "cancelled" and ({"delivered", "picked_up"} & set(types)):
            raise ValueError("Fulfillment cancelado recebeu evento de conclusão posterior.")
        if fulfillment.status != "completed":
            continue
        if not types or types[0] != "prepared":
            raise ValueError("Fulfillment completo não começa com prepared.")
        if fulfillment.fulfillment_type == "delivery":
            if "dispatched" not in types or "delivered" not in types or types.index("dispatched") > types.index("delivered"):
                raise ValueError("Sequência delivery sem dispatched antes de delivered.")
            if events[types.index("dispatched")].occurred_at >= events[types.index("delivered")].occurred_at:
                raise ValueError("Entrega ocorreu antes do despacho.")
        elif fulfillment.fulfillment_type == "store_pickup":
            if "pickup_ready" not in types or "picked_up" not in types or types.index("pickup_ready") > types.index("picked_up"):
                raise ValueError("Sequência pickup sem pickup_ready antes de picked_up.")
            if events[types.index("pickup_ready")].occurred_at >= events[types.index("picked_up")].occurred_at:
                raise ValueError("Retirada ocorreu antes de pickup_ready.")

    movement_by_transfer: dict[str, list] = defaultdict(list)
    movement_by_return: dict[str, list] = defaultdict(list)
    for movement in data.stock_movements:
        if movement.movement_type in {"transfer_in", "transfer_out"}:
            if movement.transfer_item_key is None:
                raise ValueError("Movimento de transferência sem item de origem.")
            movement_by_transfer[movement.transfer_item_key].append(movement)
        if movement.movement_type == "customer_return":
            if movement.return_item_key is None:
                raise ValueError("Movimento customer_return sem return_item.")
            movement_by_return[movement.return_item_key].append(movement)
    transfer_state_events = {row.transfer_item_key: [] for row in data.stock_state_events if row.transfer_item_key}
    for event in data.stock_state_events:
        if event.transfer_item_key:
            transfer_state_events[event.transfer_item_key].append(event)
    for transfer in data.stock_transfers:
        if transfer.status not in {"draft", "in_transit", "completed", "cancelled"}:
            raise ValueError("Status de transferência não permitido pelo schema.")
        if transfer.source_location_code == transfer.destination_location_code or transfer.received_at > cutoff or not transfer.requested_at <= transfer.dispatched_at <= transfer.received_at:
            raise ValueError("Origem/destino ou cronologia da transferência inválida.")
        rows = [row for row in data.stock_transfer_items if row.transfer_key == transfer.key]
        if not rows:
            raise ValueError("Transferência sem itens.")
        for row in rows:
            if row.quantity_planned <= 0 or row.quantity_dispatched != row.quantity_planned or row.quantity_received != row.quantity_dispatched:
                raise ValueError("Quantidades planejada/enviada/recebida da transferência divergem.")
            paired = movement_by_transfer[row.key]
            out = [move for move in paired if move.movement_type == "transfer_out"]
            incoming = [move for move in paired if move.movement_type == "transfer_in"]
            if len(out) != 1 or len(incoming) != 1:
                raise ValueError("Transfer item sem par transfer_out/transfer_in único.")
            if (out[0].quantity_delta != -row.quantity_dispatched or incoming[0].quantity_delta != row.quantity_received
                    or out[0].unit_cost != incoming[0].unit_cost or out[0].occurred_at >= incoming[0].occurred_at):
                raise ValueError("Movimentos de transferência não conciliam quantidade/custo/tempo.")
            if out[0].location_code != transfer.source_location_code or incoming[0].location_code != transfer.destination_location_code:
                raise ValueError("Transferência foi lançada nos locais incorretos.")

    fulfillment_stock: dict[str, list] = defaultdict(list)
    for move in data.stock_movements:
        if move.movement_type == "fulfillment" and move.fulfillment_item_key:
            fulfillment_stock[move.fulfillment_item_key].append(move)
    for row in data.return_items:
        ret = returns.get(row.return_key)
        order_item = items.get(row.sale_item_key)
        source = fulfillment_items.get(row.source_fulfillment_item_key)
        if ret is None or order_item is None or source is None or source.order_key != row.order_key or source.sale_item_key != row.sale_item_key or ret.order_key != row.order_key:
            raise ValueError("Return item aponta para fulfillment/pedido/item diferente.")
        if source.fulfilled_quantity <= 0 or row.quantity_requested <= 0 or not 0 <= row.quantity_approved <= row.quantity_requested or not 0 <= row.quantity_received <= row.quantity_approved:
            raise ValueError("Quantidade solicitada/aprovada/recebida da devolução inválida.")
        return_quantity[source.key] += row.quantity_received
        if return_quantity[source.key] > source.fulfilled_quantity:
            raise ValueError("Devoluções acumuladas excedem a saída física de origem.")
        if row.quantity_received:
            if row.received_at is None or row.received_at > cutoff or not row.item_condition or not row.stock_destination or not ret.decided_at or row.received_at < ret.decided_at:
                raise ValueError("Recebimento da devolução sem estado/tempo obrigatório.")
            if row.stock_destination not in {"sellable", "quarantine", "repair", "discard"} or row.item_condition not in {"unopened", "good", "damaged", "defective", "unknown"}:
                raise ValueError("Condição/destino de devolução não permitido.")
            return_moves = movement_by_return[row.key]
            if row.stock_destination == "sellable":
                if len(return_moves) != 1:
                    raise ValueError("Retorno sellable não gerou exatamente um movimento de entrada.")
                sources = fulfillment_stock[source.key]
                if not sources:
                    raise ValueError("Retorno sellable sem custo histórico de fulfillment.")
                historical = sum((Decimal(abs(move.quantity_delta))*move.unit_cost for move in sources), Decimal("0")) / sum(abs(move.quantity_delta) for move in sources)
                if return_moves[0].unit_cost != historical.quantize(Decimal("0.00000001")):
                    raise ValueError("Custo customer_return não é a média histórica da saída original.")
                if return_moves[0].quantity_delta != row.quantity_received:
                    raise ValueError("Quantidade customer_return difere da devolução recebida.")
            elif return_moves:
                raise ValueError("Retorno não vendável aumentou estoque sellable.")
        elif movement_by_return[row.key]:
            raise ValueError("Devolução sem recebimento físico gerou movimento.")

    allowed_return_status = {"requested", "approved", "rejected", "partially_received", "received", "closed", "cancelled"}
    for ret in data.returns:
        if ret.order_key not in orders or ret.status not in allowed_return_status or ret.reason_code not in {"defective", "damaged", "incorrect_item", "buyer_remorse", "other"}:
            raise ValueError("Cabeçalho de devolução contém referência/status/motivo inválido.")
        if ret.requested_at > cutoff or ret.requested_at < orders[ret.order_key].placed_at or (ret.decided_at and (ret.decided_at < ret.requested_at or ret.decided_at > cutoff)):
            raise ValueError("Cronologia do cabeçalho de devolução inválida.")
        if ret.status == "rejected" and any(row.return_key == ret.key and row.quantity_approved for row in data.return_items):
            raise ValueError("Devolução rejeitada mantém quantidade aprovada.")

    for refund in data.refunds:
        payment = payments.get(refund.payment_key)
        ret = returns.get(refund.return_key) if refund.return_key else None
        if payment is None or payment.status not in SUCCESS or payment.order_key != refund.order_key or refund.order_key not in orders:
            raise ValueError("Refund não referencia pagamento capturado do mesmo pedido.")
        if ret and ret.order_key != refund.order_key:
            raise ValueError("Refund referencia devolução de outro pedido.")
        if refund.status not in {"requested", "processing", "completed", "rejected", "cancelled"} or refund.amount <= 0:
            raise ValueError("Status/valor de refund inválido.")
        if refund.requested_at > cutoff or refund.requested_at < payment.settled_at or (refund.processed_at and (refund.processed_at < refund.requested_at or refund.processed_at > cutoff)):
            raise ValueError("Cronologia de refund inválida.")
        refunds_by_payment[payment.key].append(refund)
    for payment_key, rows in refunds_by_payment.items():
        payment = payments[payment_key]
        completed = sum((row.amount for row in rows if row.status == "completed"), Decimal("0.00"))
        if completed > payment.amount:
            raise ValueError("Refund acumulado excede valor capturado do pagamento.")
    if any(sum((row.amount for row in rows if row.status == "completed"), Decimal("0.00")) > sum((payment.amount for payment in payment_by_order[order_key] if payment.status in SUCCESS), Decimal("0.00")) for order_key, rows in _refunds_by_order(data).items()):
        raise ValueError("Refund acumulado excede captura total do pedido.")

    # Replay all receipt, fulfillment, transfer and sellable-return events with Decimal cost.
    balances: dict[tuple[str, str], int] = defaultdict(int)
    reserved: dict[tuple[str, str], int] = defaultdict(int)
    averages: dict[tuple[str, str], Decimal] = defaultdict(lambda: Decimal("0.00000000"))
    movements = {row.key: row for row in data.stock_movements}
    for event in sorted(data.stock_state_events, key=lambda row: (row.occurred_at, row.priority, row.key)):
        key = (event.product_sku, event.location_code)
        if event.event_type == "receipt":
            averages[key] = weighted_moving_average(balances[key], averages[key], event.quantity, event.unit_cost)
            balances[key] += event.quantity
        elif event.event_type == "reserve":
            if balances[key] - reserved[key] < event.quantity:
                raise ValueError("Reserva maior que estoque disponível.")
            reserved[key] += event.quantity
        elif event.event_type == "release":
            reserved[key] -= event.quantity
        elif event.event_type == "fulfillment":
            if reserved[key] < event.quantity or balances[key] < event.quantity or event.unit_cost != averages[key]:
                raise ValueError("Saída fulfillment diverge da reserva, saldo ou custo médio.")
            balances[key] -= event.quantity
            reserved[key] -= event.quantity
        elif event.event_type == "transfer_out":
            if balances[key] - reserved[key] < event.quantity or event.unit_cost != averages[key]:
                raise ValueError("Transferência excede disponível ou não usa custo de origem.")
            balances[key] -= event.quantity
        elif event.event_type in {"transfer_in", "customer_return"}:
            if event.unit_cost is None:
                raise ValueError("Entrada de transferência/retorno sem custo.")
            averages[key] = weighted_moving_average(balances[key], averages[key], event.quantity, event.unit_cost)
            balances[key] += event.quantity
        else:
            raise ValueError("Evento de estoque não permitido na Fase 3D.")
    positions = {(row.product_sku, row.location_code): row for row in data.stock_positions.values()}
    if set(positions) != set(balances):
        raise ValueError("Stock positions não cobre exatamente o conjunto de eventos físicos.")
    for key, position in positions.items():
        if position.on_hand_quantity != balances[key] or position.reserved_quantity != reserved[key] or position.available_quantity != balances[key] - reserved[key] or position.average_unit_cost != averages[key]:
            raise ValueError("Stock position/average cost diverge do ledger cronológico.")
    active = defaultdict(int)
    for reservation in data.stock_reservations:
        if reservation.status == "active":
            active[(reservation.product_sku, reservation.location_code)] += reservation.quantity
    if any(active[key] != reserved[key] for key in set(active) | set(reserved)):
        raise ValueError("Saldo reservado diverge das reservas ainda ativas.")
    if sum(balances.values()) != sum(row.accepted_quantity for row in data.goods_receipt_items) - sum(row.fulfilled_quantity for row in data.fulfillment_items) + sum(row.quantity_received for row in data.return_items if row.stock_destination == "sellable"):
        raise ValueError("Reconciliação global de estoque físico falhou.")
    if sum((Decimal(-row.quantity_delta) * row.unit_cost for row in data.stock_movements if row.movement_type == "fulfillment"), Decimal("0.00")) != data.summary()["realized_cost"]:
        raise ValueError("Custo realizado não reconcilia com saídas fulfillment.")

    return {
        "orders": len(data.sales_orders), "payments": len(data.payments),
        "declined_attempts": sum(row.status in {"declined", "failed"} for row in data.payments),
        "installments": len(data.payment_installments), "fulfillment_events": len(data.fulfillment_events),
        "transfers": len(data.stock_transfers), "returns": len(data.returns),
        "return_items": len(data.return_items), "refunds": len(data.refunds),
        "captured_amount": captured_total, "refund_amount": data.summary()["refund_amount"],
        "net_financial_amount": captured_total - data.summary()["refund_amount"],
    }


def _unique(label: str, values: list[str]) -> None:
    if len(values) != len(set(values)):
        raise ValueError(f"Chave lógica duplicada em {label}.")


def _refunds_by_order(data: TransactionData) -> dict[str, list]:
    result: dict[str, list] = defaultdict(list)
    for row in data.refunds:
        result[row.order_key].append(row)
    return result
