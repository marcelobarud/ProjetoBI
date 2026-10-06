"""Transactional row persistence with row locks around every inventory mutation."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from psycopg import Connection

from projectbi_generator.models.entities import MasterData
from projectbi_generator.models.transactions import StockStateEvent, TransactionData


def _lock_position(connection: Connection, product_id: int, location_id: int, at: datetime):
    connection.execute(
        """INSERT INTO inventory.stock_positions
               (product_id, stock_location_id, on_hand_quantity, reserved_quantity, average_unit_cost, updated_at)
           VALUES (%s, %s, 0, 0, 0, %s)
           ON CONFLICT (product_id, stock_location_id) DO NOTHING""",
        (product_id, location_id, at),
    )
    row = connection.execute(
        """SELECT stock_position_id, on_hand_quantity, reserved_quantity, average_unit_cost
             FROM inventory.stock_positions
            WHERE product_id=%s AND stock_location_id=%s
            FOR UPDATE""",
        (product_id, location_id),
    ).fetchone()
    if row is None:
        raise RuntimeError("Não foi possível localizar a posição de estoque bloqueada.")
    return row


def _apply_stock_event(
    connection: Connection,
    event: StockStateEvent,
    ids: dict[str, dict[str, int]],
) -> None:
    product_id = ids["products"][event.product_sku]
    location_id = ids["stock_locations"][event.location_code]
    position_id, on_hand, reserved, average = _lock_position(connection, product_id, location_id, event.occurred_at)
    if event.event_type == "receipt":
        if event.unit_cost is None or event.quantity <= 0:
            raise ValueError("Entrada de receipt requer quantidade e custo válidos.")
        if on_hand == 0:
            new_average = event.unit_cost.quantize(Decimal("0.00000001"))
        else:
            new_average = (
                Decimal(on_hand) * average + Decimal(event.quantity) * event.unit_cost
            ).__truediv__(Decimal(on_hand + event.quantity)).quantize(Decimal("0.00000001"))
        connection.execute(
            """UPDATE inventory.stock_positions
                  SET on_hand_quantity=on_hand_quantity+%s, average_unit_cost=%s, updated_at=%s
                WHERE stock_position_id=%s""",
            (event.quantity, new_average, event.occurred_at, position_id),
        )
    elif event.event_type == "reserve":
        if event.quantity <= 0 or on_hand - reserved < event.quantity:
            raise ValueError("Reserva supera a disponibilidade bloqueada.")
        connection.execute(
            "UPDATE inventory.stock_positions SET reserved_quantity=reserved_quantity+%s, updated_at=%s WHERE stock_position_id=%s",
            (event.quantity, event.occurred_at, position_id),
        )
    elif event.event_type == "release":
        if event.quantity <= 0 or reserved < event.quantity:
            raise ValueError("Liberação supera a reserva bloqueada.")
        connection.execute(
            "UPDATE inventory.stock_positions SET reserved_quantity=reserved_quantity-%s, updated_at=%s WHERE stock_position_id=%s",
            (event.quantity, event.occurred_at, position_id),
        )
        connection.execute(
            "UPDATE inventory.stock_reservations SET status='released', released_at=%s WHERE stock_reservation_id=%s",
            (event.occurred_at, ids["reservations"][event.reservation_key]),
        )
    elif event.event_type == "fulfillment":
        if event.movement_key is None or event.reservation_key is None or event.unit_cost is None:
            raise ValueError("Saída fulfillment requer movimento, reserva e custo.")
        if event.quantity <= 0 or on_hand < event.quantity or reserved < event.quantity:
            raise ValueError("Saída excede estoque/reserva bloqueados.")
        if average != event.unit_cost:
            raise ValueError("Custo do movimento diverge da média móvel bloqueada.")
        movement = next(row for row in ids["movement_values"] if row["key"] == event.movement_key)
        connection.execute(
            """INSERT INTO inventory.stock_movements
                   (product_id, stock_location_id, movement_type, quantity_delta, unit_cost,
                    fulfillment_item_id, occurred_at, created_at)
               VALUES (%s,%s,'fulfillment',%s,%s,%s,%s,%s)""",
            (product_id, location_id, -event.quantity, event.unit_cost,
             ids["fulfillment_items"][movement["fulfillment_item_key"]], event.occurred_at, event.occurred_at),
        )
        connection.execute(
            """UPDATE inventory.stock_positions
                  SET on_hand_quantity=on_hand_quantity-%s, reserved_quantity=reserved_quantity-%s, updated_at=%s
                WHERE stock_position_id=%s""",
            (event.quantity, event.quantity, event.occurred_at, position_id),
        )
        connection.execute(
            "UPDATE inventory.stock_reservations SET status='consumed', released_at=%s WHERE stock_reservation_id=%s",
            (event.occurred_at, ids["reservations"][event.reservation_key]),
        )
        connection.execute(
            """UPDATE logistics.fulfillment_items
                  SET fulfilled_quantity=%s, updated_at=%s WHERE fulfillment_item_id=%s""",
            (event.quantity, event.occurred_at, ids["fulfillment_items"][movement["fulfillment_item_key"]]),
        )
        connection.execute(
            """UPDATE logistics.fulfillments
                  SET status='completed', dispatched_at=%s, completed_at=%s, updated_at=%s
                WHERE fulfillment_id=%s""",
            (event.occurred_at, event.occurred_at, event.occurred_at, ids["fulfillments"][movement["fulfillment_key"]]),
        )
    else:
        raise ValueError(f"Evento de estoque desconhecido: {event.event_type}")


def load_transaction_data(connection: Connection, master: MasterData, data: TransactionData, ids: dict[str, dict[str, int]]) -> dict:
    """Load all 13 tables and replay stock events under SELECT FOR UPDATE in one transaction."""
    po_ids: dict[str, int] = {}
    for row in data.purchase_orders:
        result = connection.execute(
            """INSERT INTO procurement.purchase_orders
                   (purchase_order_number, supplier_id, responsible_employee_id, status, ordered_at,
                    expected_on, currency_code, created_at, updated_at)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s) RETURNING purchase_order_id""",
            (row.number, ids["suppliers"][row.supplier_code], ids["employees"].get(row.responsible_employee_code) if row.responsible_employee_code else None,
             row.status, row.ordered_at, row.expected_on, row.currency_code, row.ordered_at, row.ordered_at),
        ).fetchone()
        po_ids[row.key] = result[0]
    poi_ids: dict[str, int] = {}
    for row in data.purchase_order_items:
        result = connection.execute(
            """INSERT INTO procurement.purchase_order_items
                   (purchase_order_id, line_number, product_id, quantity_ordered, unit_cost_ordered, created_at)
               VALUES (%s,%s,%s,%s,%s,%s) RETURNING purchase_order_item_id""",
            (po_ids[row.order_key], row.line_number, ids["products"][row.product_sku], row.quantity_ordered,
             row.unit_cost_ordered, next(item.ordered_at for item in data.purchase_orders if item.key == row.order_key)),
        ).fetchone()
        poi_ids[row.key] = result[0]
    receipt_ids: dict[str, int] = {}
    for row in data.goods_receipts:
        result = connection.execute(
            """INSERT INTO procurement.goods_receipts
                   (purchase_order_id, stock_location_id, checked_by_employee_id, receipt_number, status, received_at, created_at)
               VALUES (%s,%s,%s,%s,%s,%s,%s) RETURNING goods_receipt_id""",
            (po_ids[row.order_key], ids["stock_locations"][row.location_code],
             ids["employees"].get(row.checked_by_employee_code) if row.checked_by_employee_code else None,
             row.number, row.status, row.received_at, row.received_at),
        ).fetchone()
        receipt_ids[row.key] = result[0]
    receipt_item_ids: dict[str, int] = {}
    for row in data.goods_receipt_items:
        receipt = next(item for item in data.goods_receipts if item.key == row.receipt_key)
        result = connection.execute(
            """INSERT INTO procurement.goods_receipt_items
                   (purchase_order_id, goods_receipt_id, purchase_order_item_id, quantity_received,
                    accepted_quantity, rejected_quantity, unit_acquisition_cost, created_at)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s) RETURNING goods_receipt_item_id""",
            (po_ids[receipt.order_key], receipt_ids[row.receipt_key], poi_ids[row.order_item_key], row.quantity_received,
             row.accepted_quantity, row.rejected_quantity, row.unit_acquisition_cost, receipt.received_at),
        ).fetchone()
        receipt_item_ids[row.key] = result[0]

    order_ids: dict[str, int] = {}
    for row in data.sales_orders:
        snap = row.address_snapshot or (None,) * 9
        result = connection.execute(
            """INSERT INTO sales.sales_orders
                   (order_number, sales_channel_id, channel_type, customer_id, store_id, salesperson_employee_id,
                    customer_address_id, order_status, placed_at, currency_code, subtotal_amount, discount_amount,
                    shipping_amount, total_amount, recipient_name, postal_code_snapshot, street_snapshot,
                    street_number_snapshot, complement_snapshot, district_snapshot, city_snapshot,
                    state_code_snapshot, country_code_snapshot, created_at, updated_at)
               VALUES (%s,%s,%s,%s,%s,%s,%s,'draft',%s,'BRL',%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
               RETURNING sales_order_id""",
            (row.number, ids["sales_channels"][row.channel_code], row.channel_type,
             ids["customers"].get(row.customer_code) if row.customer_code else None,
             ids["stores"].get(row.store_code) if row.store_code else None,
             ids["employees"].get(row.salesperson_code) if row.salesperson_code else None,
             ids["customer_addresses"].get(row.address_key) if row.address_key else None,
             row.placed_at, row.subtotal, row.discount, row.shipping, row.total,
             *snap, row.placed_at, row.placed_at),
        ).fetchone()
        order_ids[row.key] = result[0]
    order_item_ids: dict[str, int] = {}
    for row in data.sales_order_items:
        product = next(item for item in master.products if item.sku == row.product_sku)
        order = next(item for item in data.sales_orders if item.key == row.order_key)
        result = connection.execute(
            """INSERT INTO sales.sales_order_items
                   (sales_order_id, line_number, product_id, sku_snapshot, product_name_snapshot, quantity, unit_sale_price, created_at)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s) RETURNING sales_order_item_id""",
            (order_ids[row.order_key], row.line_number, ids["products"][row.product_sku], row.product_sku,
             product.name, row.quantity, row.unit_sale_price, order.placed_at),
        ).fetchone()
        order_item_ids[row.key] = result[0]
    for row in data.order_status_history:
        connection.execute(
            """INSERT INTO sales.order_status_history
                   (sales_order_id, status, occurred_at, changed_by_employee_id, reason, created_at)
               VALUES (%s,%s,%s,%s,%s,%s)""",
            (order_ids[row.order_key], row.status, row.occurred_at,
             ids["employees"].get(row.changed_by_employee_code) if row.changed_by_employee_code else None,
             row.reason, row.occurred_at),
        )
    for row in data.applied_discounts:
        connection.execute(
            """INSERT INTO sales.applied_discounts
                   (sales_order_id, sales_order_item_id, discount_scope, discount_code, campaign_reference, description, amount, created_at)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s)""",
            (order_ids[row.order_key], order_item_ids[row.item_key], row.scope, row.code, None, row.description, row.amount, row.created_at),
        )

    reservation_ids: dict[str, int] = {}
    for row in data.stock_reservations:
        result = connection.execute(
            """INSERT INTO inventory.stock_reservations
                   (sales_order_id, sales_order_item_id, product_id, stock_location_id, quantity, status,
                    reserved_at, expires_at, released_at, created_at)
               VALUES (%s,%s,%s,%s,%s,'active',%s,NULL,NULL,%s) RETURNING stock_reservation_id""",
            (order_ids[row.order_key], order_item_ids[row.item_key], ids["products"][row.product_sku],
             ids["stock_locations"][row.location_code], row.quantity, row.reserved_at, row.reserved_at),
        ).fetchone()
        reservation_ids[row.key] = result[0]
    fulfillment_ids: dict[str, int] = {}
    for row in data.fulfillments:
        result = connection.execute(
            """INSERT INTO logistics.fulfillments
                   (sales_order_id, fulfillment_number, fulfillment_type, status, stock_location_id,
                    pickup_store_id, carrier_id, planned_at, created_at, updated_at)
               VALUES (%s,%s,%s,'preparing',%s,%s,%s,%s,%s,%s) RETURNING fulfillment_id""",
            (order_ids[row.order_key], row.number, row.fulfillment_type,
             ids["stock_locations"].get(row.location_code) if row.location_code else None,
             ids["stores"].get(row.pickup_store_code) if row.pickup_store_code else None,
             ids["carriers"].get(row.carrier_code) if row.carrier_code else None,
             row.planned_at, row.planned_at, row.planned_at),
        ).fetchone()
        fulfillment_ids[row.key] = result[0]
    fulfillment_item_ids: dict[str, int] = {}
    movement_values: list[dict] = []
    for row in data.fulfillment_items:
        fulfillment = next(item for item in data.fulfillments if item.key == row.fulfillment_key)
        result = connection.execute(
            """INSERT INTO logistics.fulfillment_items
                   (sales_order_id, fulfillment_id, sales_order_item_id, quantity_allocated, fulfilled_quantity, created_at, updated_at)
               VALUES (%s,%s,%s,%s,0,%s,%s) RETURNING fulfillment_item_id""",
            (order_ids[row.order_key], fulfillment_ids[row.fulfillment_key], order_item_ids[row.sale_item_key],
             row.quantity_allocated, fulfillment.planned_at, fulfillment.planned_at),
        ).fetchone()
        fulfillment_item_ids[row.key] = result[0]
        movement_values.append({"key": next((m.key for m in data.stock_movements if m.fulfillment_item_key == row.key), ""),
                                "fulfillment_item_key": row.key, "fulfillment_key": row.fulfillment_key})

    reservation_by_key = reservation_ids
    ids_for_events = {**ids, "reservations": reservation_by_key, "fulfillments": fulfillment_ids,
                      "fulfillment_items": fulfillment_item_ids, "movement_values": movement_values}
    for event in data.stock_state_events:
        if event.event_type == "receipt":
            movement = next(row for row in data.stock_movements if row.key == event.movement_key)
            connection.execute(
                """INSERT INTO inventory.stock_movements
                       (product_id, stock_location_id, movement_type, quantity_delta, unit_cost,
                        goods_receipt_item_id, occurred_at, created_at)
                   VALUES (%s,%s,'receipt',%s,%s,%s,%s,%s)""",
                (ids["products"][event.product_sku], ids["stock_locations"][event.location_code],
                 event.quantity, event.unit_cost, receipt_item_ids[movement.receipt_item_key], event.occurred_at, event.occurred_at),
            )
        _apply_stock_event(connection, event, ids_for_events)
    for row in data.sales_orders:
        connection.execute("UPDATE sales.sales_orders SET order_status=%s, updated_at=%s WHERE sales_order_id=%s",
                           (row.status, row.placed_at, order_ids[row.key]))
    return {
        "purchase_orders": po_ids, "purchase_order_items": poi_ids, "goods_receipts": receipt_ids,
        "goods_receipt_items": receipt_item_ids, "sales_orders": order_ids, "sales_order_items": order_item_ids,
        "reservations": reservation_ids, "fulfillments": fulfillment_ids, "fulfillment_items": fulfillment_item_ids,
    }
