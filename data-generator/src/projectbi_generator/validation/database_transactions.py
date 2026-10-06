"""SQL-backed checks for the 13 transaction tables inside the rollback smoke."""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime, time
from decimal import Decimal

from psycopg import Connection, sql

from projectbi_generator.config import GeneratorConfig
from projectbi_generator.models.transactions import TransactionData
from projectbi_generator.validation.transactions import validate_transactional_data

TRANSACTION_TABLES = {
    "purchase_orders": ("procurement", "purchase_orders"),
    "purchase_order_items": ("procurement", "purchase_order_items"),
    "goods_receipts": ("procurement", "goods_receipts"),
    "goods_receipt_items": ("procurement", "goods_receipt_items"),
    "stock_positions": ("inventory", "stock_positions"),
    "stock_movements": ("inventory", "stock_movements"),
    "stock_reservations": ("inventory", "stock_reservations"),
    "sales_orders": ("sales", "sales_orders"),
    "sales_order_items": ("sales", "sales_order_items"),
    "order_status_history": ("sales", "order_status_history"),
    "applied_discounts": ("sales", "applied_discounts"),
    "fulfillments": ("logistics", "fulfillments"),
    "fulfillment_items": ("logistics", "fulfillment_items"),
}


def validate_loaded_transactions(connection: Connection, config: GeneratorConfig, master, data: TransactionData) -> dict[str, int | Decimal]:
    """Validate relational SQL invariants and recompute cost from the persisted ledger."""
    validate_transactional_data(data, master, config)
    counts: dict[str, int] = {}
    for key, (schema, table) in TRANSACTION_TABLES.items():
        count = connection.execute(sql.SQL("SELECT count(*) FROM {}.{}").format(sql.Identifier(schema), sql.Identifier(table))).fetchone()[0]
        aliases = {"applied_discounts": "discounts", "stock_reservations": "reservations"}
        expected_count = data.counts().get(aliases.get(key, key), len(getattr(data, key, ())))
        if count != expected_count:
            raise RuntimeError(f"Contagem de integração divergente em {schema}.{table}.")
        counts[key] = count

    violations = connection.execute("""
        SELECT
          (SELECT count(*) FROM (
             SELECT poi.purchase_order_item_id
               FROM procurement.purchase_order_items poi
               LEFT JOIN procurement.goods_receipt_items gri USING (purchase_order_item_id)
              GROUP BY poi.purchase_order_item_id, poi.quantity_ordered
             HAVING coalesce(sum(gri.quantity_received),0) > poi.quantity_ordered
          ) q),
          (SELECT count(*) FROM procurement.goods_receipt_items WHERE accepted_quantity + rejected_quantity <> quantity_received),
          (SELECT count(*) FROM inventory.stock_positions WHERE on_hand_quantity < 0 OR reserved_quantity < 0 OR reserved_quantity > on_hand_quantity OR available_quantity <> on_hand_quantity-reserved_quantity),
          (SELECT count(*) FROM (
             SELECT coalesce(p.product_id,m.product_id) product_id, coalesce(p.stock_location_id,m.stock_location_id) location_id,
                    coalesce(p.on_hand_quantity,0) on_hand, coalesce(sum(m.quantity_delta),0) ledger
               FROM inventory.stock_positions p FULL JOIN inventory.stock_movements m
                 ON p.product_id=m.product_id AND p.stock_location_id=m.stock_location_id
              GROUP BY p.product_id,p.stock_location_id,p.on_hand_quantity,m.product_id,m.stock_location_id
             HAVING coalesce(p.on_hand_quantity,0) <> coalesce(sum(m.quantity_delta),0)
          ) q),
          (SELECT count(*) FROM (
             SELECT oi.sales_order_item_id, oi.quantity, coalesce(sum(fi.fulfilled_quantity),0) fulfilled
               FROM sales.sales_order_items oi LEFT JOIN logistics.fulfillment_items fi USING (sales_order_item_id)
              GROUP BY oi.sales_order_item_id,oi.quantity HAVING coalesce(sum(fi.fulfilled_quantity),0)>oi.quantity
          ) q),
          (SELECT count(*) FROM inventory.stock_reservations r
             JOIN sales.sales_order_items i ON i.sales_order_id=r.sales_order_id AND i.sales_order_item_id=r.sales_order_item_id
            WHERE r.product_id <> i.product_id),
          (SELECT count(*) FROM inventory.stock_movements
            WHERE (movement_type='receipt' AND (quantity_delta<=0 OR goods_receipt_item_id IS NULL OR unit_cost IS NULL))
               OR (movement_type='fulfillment' AND (quantity_delta>=0 OR fulfillment_item_id IS NULL OR unit_cost IS NULL))),
          (SELECT count(*) FROM sales.sales_orders o
            WHERE o.total_amount <> o.subtotal_amount-o.discount_amount+o.shipping_amount),
          (SELECT count(*) FROM (
             SELECT i.sales_order_item_id, i.quantity*i.unit_sale_price gross, coalesce(sum(d.amount),0) discounts
               FROM sales.sales_order_items i LEFT JOIN sales.applied_discounts d USING (sales_order_id,sales_order_item_id)
              GROUP BY i.sales_order_item_id,i.quantity,i.unit_sale_price
             HAVING coalesce(sum(d.amount),0)>i.quantity*i.unit_sale_price
          ) q),
          (SELECT count(*) FROM sales.sales_orders o JOIN sales.sales_channels c USING (sales_channel_id)
            WHERE o.channel_type<>c.channel_type OR (o.channel_type<>'physical' AND o.customer_id IS NULL)),
          (SELECT count(*) FROM sales.sales_order_items i JOIN sales.sales_orders o USING (sales_order_id)
            WHERE NOT EXISTS (SELECT 1 FROM catalog.product_prices p
                 WHERE p.product_id=i.product_id AND p.sales_channel_id=o.sales_channel_id
                   AND p.valid_from<=o.placed_at AND (p.valid_to IS NULL OR o.placed_at<p.valid_to)
                   AND p.amount=i.unit_sale_price)),
          (SELECT count(*) FROM sales.sales_orders o
            WHERE o.order_status <> (SELECT h.status FROM sales.order_status_history h WHERE h.sales_order_id=o.sales_order_id ORDER BY h.occurred_at DESC,h.order_status_history_id DESC LIMIT 1)),
          (SELECT count(*) FROM procurement.goods_receipts WHERE received_at < (SELECT ordered_at FROM procurement.purchase_orders WHERE purchase_order_id=goods_receipts.purchase_order_id)),
          (SELECT count(*) FROM inventory.stock_movements WHERE occurred_at > %s),
          (SELECT count(*) FROM sales.sales_orders WHERE placed_at > %s)
    """, (datetime.combine(config.end_date, time(23, 59, 59), tzinfo=config.timezone),
          datetime.combine(config.end_date, time(23, 59, 59), tzinfo=config.timezone))).fetchone()
    if any(violations):
        labels = ("receipt accumulation", "accepted/rejected", "position bounds", "ledger balance", "fulfillment quantity",
                  "reservation product", "movement direction/source/cost", "order totals", "discount eligibility",
                  "channel/customer", "price validity", "status history", "receipt chronology", "movement cutoff", "order cutoff")
        failed = [label for label, count in zip(labels, violations) if count]
        raise RuntimeError("Invariantes SQL falharam: " + ", ".join(failed))

    # Replay persisted receipt/fulfillment movements with Decimal and NUMERIC(20,8) rounding.
    balances: dict[tuple[int, int], int] = defaultdict(int)
    averages: dict[tuple[int, int], Decimal] = defaultdict(lambda: Decimal("0.00000000"))
    for product_id, location_id, kind, delta, unit_cost in connection.execute(
        """SELECT product_id,stock_location_id,movement_type,quantity_delta,unit_cost
             FROM inventory.stock_movements ORDER BY occurred_at,stock_movement_id"""
    ).fetchall():
        key = (product_id, location_id)
        if kind == "receipt":
            qty = delta
            if balances[key] == 0:
                averages[key] = unit_cost.quantize(Decimal("0.00000001"))
            else:
                averages[key] = ((Decimal(balances[key])*averages[key]+Decimal(qty)*unit_cost)/Decimal(balances[key]+qty)).quantize(Decimal("0.00000001"))
            balances[key] += qty
        elif kind == "fulfillment":
            if unit_cost != averages[key]:
                raise RuntimeError("Custo de fulfillment no banco difere da média móvel reconstruída.")
            balances[key] += delta
    persisted_positions = connection.execute(
        "SELECT product_id,stock_location_id,on_hand_quantity,reserved_quantity,available_quantity,average_unit_cost FROM inventory.stock_positions"
    ).fetchall()
    for product_id, location_id, on_hand, reserved, available, average in persisted_positions:
        key = (product_id, location_id)
        if on_hand != balances[key] or average != averages[key] or available != on_hand - reserved:
            raise RuntimeError("stock_positions diverge da reconstrução cronológica do ledger.")

    ledger_cost = connection.execute(
        """SELECT coalesce(sum(abs(quantity_delta)::numeric*unit_cost),0)
             FROM inventory.stock_movements WHERE movement_type='fulfillment'"""
    ).fetchone()[0]
    expected_cost = data.summary()["realized_cost"]
    if ledger_cost != expected_cost:
        raise RuntimeError("Custo realizado SQL diverge do agregado reportado pelo gerador.")
    counts["realized_cost"] = ledger_cost
    return counts
