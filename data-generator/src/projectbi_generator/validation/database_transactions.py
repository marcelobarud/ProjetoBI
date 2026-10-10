"""SQL-backed checks for the 13 transaction tables inside the rollback smoke."""

from __future__ import annotations

from collections import defaultdict, deque
from datetime import datetime, time
from decimal import Decimal, ROUND_HALF_UP, getcontext
from time import perf_counter

from psycopg import Connection, sql

from projectbi_generator.config import GeneratorConfig
from projectbi_generator.generators.transactions import weighted_moving_average
from projectbi_generator.models.transactions import TransactionData
from projectbi_generator.validation.sql_diagnostics import run_sql_validation, set_validation_timeout
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
    "sales_order_item_cancellations": ("sales", "sales_order_item_cancellations"),
    "fulfillments": ("logistics", "fulfillments"),
    "fulfillment_items": ("logistics", "fulfillment_items"),
    "payments": ("payments", "payments"),
    "payment_installments": ("payments", "payment_installments"),
    "refunds": ("payments", "refunds"),
    "fulfillment_events": ("logistics", "fulfillment_events"),
    "stock_transfers": ("inventory", "stock_transfers"),
    "stock_transfer_items": ("inventory", "stock_transfer_items"),
    "returns": ("after_sales", "returns"),
    "return_items": ("after_sales", "return_items"),
}
PHASE3C_TABLES = {
    "purchase_orders", "purchase_order_items", "goods_receipts", "goods_receipt_items",
    "stock_positions", "stock_movements", "stock_reservations", "sales_orders",
    "sales_order_items", "order_status_history", "applied_discounts", "sales_order_item_cancellations", "fulfillments",
    "fulfillment_items",
}


def validate_loaded_transactions(
    connection: Connection,
    config: GeneratorConfig,
    master,
    data: TransactionData,
    validate_phase3c: bool = True,
    include_check_results: bool = False,
) -> dict[str, int | Decimal] | tuple[dict[str, int | Decimal], dict[str, int]]:
    """Validate relational SQL invariants and recompute cost from the persisted ledger."""
    set_validation_timeout(connection)
    if validate_phase3c:
        validate_transactional_data(data, master, config)
    counts: dict[str, int] = {}
    tables = TRANSACTION_TABLES.items() if not validate_phase3c else (
        (key, pair) for key, pair in TRANSACTION_TABLES.items() if key in PHASE3C_TABLES
    )
    for key, (schema, table) in tables:
        count = run_sql_validation(
            connection,
            f"table_count.{schema}.{table}",
            sql.SQL("SELECT count(*) FROM {}.{}").format(sql.Identifier(schema), sql.Identifier(table)).as_string(connection),
        )[0]
        aliases = {"applied_discounts": "discounts", "stock_reservations": "reservations"}
        expected_count = data.counts().get(aliases.get(key, key), len(getattr(data, key, ())))
        if count != expected_count:
            raise RuntimeError(f"Contagem de integração divergente em {schema}.{table}.")
        counts[key] = count

    cutoff = datetime.combine(config.end_date, time(23, 59, 59), tzinfo=config.timezone)
    base_checks = (
        ("procurement.receipt_quantity_cap", """SELECT count(*) FROM (
             SELECT poi.purchase_order_item_id FROM procurement.purchase_order_items poi
               LEFT JOIN procurement.goods_receipt_items gri USING (purchase_order_item_id)
              GROUP BY poi.purchase_order_item_id, poi.quantity_ordered
             HAVING coalesce(sum(gri.quantity_received),0) > poi.quantity_ordered) q""", ()),
        ("procurement.receipt_acceptance_balance", "SELECT count(*) FROM procurement.goods_receipt_items WHERE accepted_quantity + rejected_quantity <> quantity_received", ()),
        ("inventory.stock_position_bounds", "SELECT count(*) FROM inventory.stock_positions WHERE on_hand_quantity < 0 OR reserved_quantity < 0 OR reserved_quantity > on_hand_quantity OR available_quantity <> on_hand_quantity-reserved_quantity", ()),
        ("inventory.stock_ledger_balance", """SELECT count(*) FROM (
             SELECT coalesce(p.product_id,m.product_id) product_id, coalesce(p.stock_location_id,m.stock_location_id) location_id,
                    coalesce(p.on_hand_quantity,0) on_hand, coalesce(sum(m.quantity_delta),0) ledger
               FROM inventory.stock_positions p FULL JOIN inventory.stock_movements m
                 ON p.product_id=m.product_id AND p.stock_location_id=m.stock_location_id
              GROUP BY p.product_id,p.stock_location_id,p.on_hand_quantity,m.product_id,m.stock_location_id
             HAVING coalesce(p.on_hand_quantity,0) <> coalesce(sum(m.quantity_delta),0)) q""", ()),
        ("logistics.fulfillment_quantity_cap", """SELECT count(*) FROM (
             SELECT oi.sales_order_item_id, oi.quantity, coalesce(sum(fi.fulfilled_quantity),0) fulfilled
               FROM sales.sales_order_items oi LEFT JOIN logistics.fulfillment_items fi USING (sales_order_item_id)
              GROUP BY oi.sales_order_item_id,oi.quantity HAVING coalesce(sum(fi.fulfilled_quantity),0)>oi.quantity) q""", ()),
        ("sales.item_resolution_cache", """SELECT count(*) FROM sales.sales_order_items oi
             LEFT JOIN (SELECT sales_order_id,sales_order_item_id,sum(fulfilled_quantity) quantity
                          FROM logistics.fulfillment_items GROUP BY sales_order_id,sales_order_item_id) f
               USING (sales_order_id,sales_order_item_id)
             LEFT JOIN (SELECT sales_order_id,sales_order_item_id,sum(cancelled_quantity) quantity
                          FROM sales.sales_order_item_cancellations GROUP BY sales_order_id,sales_order_item_id) c
               USING (sales_order_id,sales_order_item_id)
            WHERE oi.fulfilled_quantity<>coalesce(f.quantity,0)
               OR oi.cancelled_quantity<>coalesce(c.quantity,0)
               OR oi.fulfilled_quantity+oi.cancelled_quantity>oi.quantity""", ()),
        ("inventory.reservation_product_match", """SELECT count(*) FROM inventory.stock_reservations r
             JOIN sales.sales_order_items i ON i.sales_order_id=r.sales_order_id AND i.sales_order_item_id=r.sales_order_item_id
            WHERE r.product_id <> i.product_id""", ()),
        ("inventory.movement_direction_source_cost", """SELECT count(*) FROM inventory.stock_movements
            WHERE (movement_type='receipt' AND (quantity_delta<=0 OR goods_receipt_item_id IS NULL OR unit_cost IS NULL))
               OR (movement_type='fulfillment' AND (quantity_delta>=0 OR fulfillment_item_id IS NULL OR unit_cost IS NULL))
               OR (movement_type='customer_return' AND (quantity_delta<=0 OR return_item_id IS NULL OR unit_cost IS NULL))
               OR (movement_type='transfer_out' AND (quantity_delta>=0 OR stock_transfer_item_id IS NULL OR unit_cost IS NULL))
               OR (movement_type='transfer_in' AND (quantity_delta<=0 OR stock_transfer_item_id IS NULL OR unit_cost IS NULL))""", ()),
        ("sales.order_total_reconciliation", "SELECT count(*) FROM sales.sales_orders o WHERE o.total_amount <> o.subtotal_amount-o.discount_amount+o.shipping_amount", ()),
        ("sales.discount_amount_cap", """SELECT count(*) FROM (
             SELECT i.sales_order_item_id, i.quantity*i.unit_sale_price gross, coalesce(sum(d.amount),0) discounts
               FROM sales.sales_order_items i LEFT JOIN sales.applied_discounts d USING (sales_order_id,sales_order_item_id)
              GROUP BY i.sales_order_item_id,i.quantity,i.unit_sale_price
             HAVING coalesce(sum(d.amount),0)>i.quantity*i.unit_sale_price) q""", ()),
        ("sales.channel_customer_compatibility", """SELECT count(*) FROM sales.sales_orders o JOIN sales.sales_channels c USING (sales_channel_id)
            WHERE o.channel_type<>c.channel_type OR (o.channel_type<>'physical' AND o.customer_id IS NULL)""", ()),
        ("catalog.price_validity", """SELECT count(*) FROM sales.sales_order_items i JOIN sales.sales_orders o USING (sales_order_id)
            WHERE NOT EXISTS (SELECT 1 FROM catalog.product_prices p
                 WHERE p.product_id=i.product_id AND p.sales_channel_id=o.sales_channel_id
                   AND p.valid_from<=o.placed_at AND (p.valid_to IS NULL OR o.placed_at<p.valid_to)
                   AND p.amount=i.unit_sale_price)""", ()),
        ("sales.latest_status_history", """SELECT count(*) FROM sales.sales_orders o
            WHERE o.order_status <> (SELECT h.status FROM sales.order_status_history h WHERE h.sales_order_id=o.sales_order_id
                                     ORDER BY h.occurred_at DESC,h.order_status_history_id DESC LIMIT 1)""", ()),
        ("procurement.receipt_chronology", """SELECT count(*) FROM procurement.goods_receipts gr
            JOIN procurement.purchase_orders po USING (purchase_order_id) WHERE gr.received_at < po.ordered_at""", ()),
        ("inventory.movement_cutoff", "SELECT count(*) FROM inventory.stock_movements WHERE occurred_at > %s", (cutoff,)),
        ("sales.order_cutoff", "SELECT count(*) FROM sales.sales_orders WHERE placed_at > %s", (cutoff,)),
    )
    base_results = {
        name: run_sql_validation(connection, name, statement, params, expect_zero=True)[0]
        for name, statement, params in base_checks
    }
    failed_base = [name for name, count in base_results.items() if count]
    if failed_base:
        raise RuntimeError("Invariantes SQL falharam: " + ", ".join(failed_base))
    check_results = dict(base_results)

    extended_checks = (
        ("payments.capture_order_reconciliation", """WITH captures AS (
             SELECT sales_order_id,sum(amount) captured FROM payments.payments
              WHERE status IN ('captured','settled') GROUP BY sales_order_id
          ), refunds AS (
             SELECT sales_order_id,sum(amount) refunded FROM payments.refunds
              WHERE status='completed' GROUP BY sales_order_id
          ), item_totals AS (
             SELECT sales_order_id,sum(quantity) ordered,sum(fulfilled_quantity) fulfilled,sum(cancelled_quantity) cancelled
               FROM sales.sales_order_items GROUP BY sales_order_id
          ), fulfillment_orders AS (
             SELECT DISTINCT sales_order_id FROM logistics.fulfillments
          )
          SELECT count(*) FROM sales.sales_orders o
          LEFT JOIN captures c USING (sales_order_id)
          LEFT JOIN refunds r USING (sales_order_id)
          LEFT JOIN item_totals i USING (sales_order_id)
          LEFT JOIN fulfillment_orders f USING (sales_order_id)
          WHERE (o.order_status<>'cancelled' AND coalesce(c.captured,0)<>o.total_amount)
             OR (o.order_status='cancelled' AND coalesce(c.captured,0)=0 AND coalesce(r.refunded,0)<>0)
             OR (o.order_status='cancelled' AND coalesce(c.captured,0)>0 AND (
                  c.captured<>o.total_amount OR coalesce(r.refunded,0)<>c.captured OR f.sales_order_id IS NOT NULL
                  OR coalesce(i.fulfilled,0)<>0 OR coalesce(i.cancelled,0)<>coalesce(i.ordered,0)))""", ()),
        ("payments.declined_timestamps", "SELECT count(*) FROM payments.payments WHERE status IN ('declined','failed','cancelled') AND (authorized_at IS NOT NULL OR settled_at IS NOT NULL)", ()),
        ("payments.installment_total_reconciliation", """SELECT count(*) FROM (
             SELECT p.payment_id,p.amount,coalesce(sum(i.amount),0) installments
               FROM payments.payments p LEFT JOIN payments.payment_installments i USING (payment_id)
              GROUP BY p.payment_id,p.amount
              HAVING count(i.payment_installment_id)>0 AND coalesce(sum(i.amount),0)<>p.amount) q""", ()),
        ("payments.installment_method_eligibility", """SELECT count(*) FROM payments.payment_installments i JOIN payments.payments p USING (payment_id)
             JOIN payments.payment_methods m USING (payment_method_id)
            WHERE m.is_installment_capable IS FALSE OR m.method_type IN ('cash','instant')""", ()),
        ("payments.refund_cap", """SELECT count(*) FROM (
             SELECT payment_id,sum(amount) refunded FROM payments.refunds WHERE status='completed' GROUP BY payment_id
          ) r JOIN payments.payments p USING (payment_id)
          WHERE p.status NOT IN ('captured','settled') OR r.refunded>p.amount""", ()),
        ("sales.item_quantity_balance", """SELECT count(*) FROM (
             SELECT oi.sales_order_id,oi.sales_order_item_id,oi.quantity,oi.fulfilled_quantity,oi.cancelled_quantity,
                    oi.quantity-oi.fulfilled_quantity-oi.cancelled_quantity outstanding
               FROM sales.sales_order_items oi
          ) q WHERE fulfilled_quantity<0 OR cancelled_quantity<0 OR outstanding<0
               OR quantity<>fulfilled_quantity+cancelled_quantity+outstanding""", ()),
        ("sales.completed_order_resolved", """SELECT count(*) FROM sales.sales_orders o
             WHERE o.order_status='completed' AND (
               EXISTS (SELECT 1 FROM sales.sales_order_items i WHERE i.sales_order_id=o.sales_order_id
                        AND i.quantity<>i.fulfilled_quantity+i.cancelled_quantity)
               OR EXISTS (SELECT 1 FROM logistics.fulfillments f WHERE f.sales_order_id=o.sales_order_id AND f.status NOT IN ('completed','cancelled'))
               OR EXISTS (SELECT 1 FROM inventory.stock_reservations r WHERE r.sales_order_id=o.sales_order_id AND r.status='active')
               OR EXISTS (SELECT 1 FROM payments.refunds r WHERE r.sales_order_id=o.sales_order_id AND r.reason_code='stock_timeout' AND r.status<>'completed'))""", ()),
        ("sales.cancelled_order_integrity", """SELECT count(*) FROM sales.sales_orders o
             WHERE o.order_status='cancelled' AND EXISTS (
                 SELECT 1 FROM sales.sales_order_item_cancellations c WHERE c.sales_order_id=o.sales_order_id
             ) AND (EXISTS (SELECT 1 FROM logistics.fulfillments f WHERE f.sales_order_id=o.sales_order_id)
               OR (SELECT coalesce(sum(i.quantity),0) FROM sales.sales_order_items i WHERE i.sales_order_id=o.sales_order_id)
                  <>(SELECT coalesce(sum(c.cancelled_quantity),0) FROM sales.sales_order_item_cancellations c WHERE c.sales_order_id=o.sales_order_id))""", ()),
        ("sales.cancellation_amount_reconciliation", """SELECT count(*) FROM (
             SELECT c.sales_order_item_cancellation_id,c.cancelled_quantity*i.unit_sale_price gross,
                    c.gross_cancelled_amount,c.discount_cancelled_amount,c.net_cancelled_amount,
                    coalesce(sum(d.amount),0) original_discount
               FROM sales.sales_order_item_cancellations c
               JOIN sales.sales_order_items i USING (sales_order_id,sales_order_item_id)
               LEFT JOIN sales.applied_discounts d USING (sales_order_id,sales_order_item_id)
              GROUP BY c.sales_order_item_cancellation_id,c.cancelled_quantity,i.unit_sale_price,c.gross_cancelled_amount,
                       c.discount_cancelled_amount,c.net_cancelled_amount
          ) q WHERE gross<>gross_cancelled_amount OR discount_cancelled_amount>original_discount
                 OR net_cancelled_amount<>gross_cancelled_amount-discount_cancelled_amount""", ()),
        ("sales.cancellation_discount_allocation", """WITH cancellation_offsets AS (
             SELECT c.sales_order_item_cancellation_id,c.cancelled_quantity,c.discount_cancelled_amount,
                    i.quantity,i.fulfilled_quantity,
                    coalesce(sum(d.amount),0) original_discount,
                    coalesce(sum(c.cancelled_quantity) OVER (
                        PARTITION BY c.sales_order_id,c.sales_order_item_id
                        ORDER BY c.cancelled_at,c.sales_order_item_cancellation_id
                        ROWS BETWEEN UNBOUNDED PRECEDING AND 1 PRECEDING),0) prior_cancelled
               FROM sales.sales_order_item_cancellations c
               JOIN sales.sales_order_items i USING (sales_order_id,sales_order_item_id)
               LEFT JOIN sales.applied_discounts d USING (sales_order_id,sales_order_item_id)
              GROUP BY c.sales_order_item_cancellation_id,c.cancelled_quantity,c.discount_cancelled_amount,
                       i.quantity,i.fulfilled_quantity,c.cancelled_at,c.sales_order_id,c.sales_order_item_id
          ), cents AS (
             SELECT *,round(original_discount*100)::bigint total_cents,
                    fulfilled_quantity+prior_cancelled item_offset
               FROM cancellation_offsets
          )
          SELECT count(*) FROM cents
           WHERE discount_cancelled_amount <>
                 ((cancelled_quantity*(total_cents/quantity)
                   + greatest(0,least(item_offset+cancelled_quantity,total_cents%%quantity)-item_offset))::numeric/100)""", ()),
        ("payments.cancellation_refund_origin", """SELECT count(*) FROM payments.refunds r
             LEFT JOIN sales.sales_order_item_cancellations c
               ON c.sales_order_id=r.sales_order_id
              AND c.sales_order_item_cancellation_id=r.sales_order_item_cancellation_id
            WHERE (r.reason_code='stock_timeout' AND (c.sales_order_item_cancellation_id IS NULL OR r.return_id IS NOT NULL OR r.status<>'completed'))
               OR (r.sales_order_item_cancellation_id IS NOT NULL AND (c.sales_order_item_cancellation_id IS NULL OR r.reason_code<>'stock_timeout'))""", ()),
        ("payments.cancellation_refund_reconciliation", """SELECT count(*) FROM sales.sales_order_item_cancellations c
             LEFT JOIN (SELECT sales_order_id,sales_order_item_cancellation_id,
                               sum(amount) FILTER (WHERE status='completed') refunded
                          FROM payments.refunds GROUP BY sales_order_id,sales_order_item_cancellation_id) r
               USING (sales_order_id,sales_order_item_cancellation_id)
            WHERE coalesce(r.refunded,0)<>c.net_cancelled_amount+c.shipping_cancelled_amount""", ()),
        ("sales.cancellation_freight_policy", """SELECT count(*) FROM sales.sales_orders o
             WHERE (SELECT coalesce(sum(c.shipping_cancelled_amount),0) FROM sales.sales_order_item_cancellations c
                     WHERE c.sales_order_id=o.sales_order_id)
               <> CASE WHEN o.order_status='cancelled'
                         AND (SELECT coalesce(sum(i.fulfilled_quantity),0) FROM sales.sales_order_items i WHERE i.sales_order_id=o.sales_order_id)=0
                         AND (SELECT coalesce(sum(i.cancelled_quantity),0) FROM sales.sales_order_items i WHERE i.sales_order_id=o.sales_order_id)
                             =(SELECT coalesce(sum(i.quantity),0) FROM sales.sales_order_items i WHERE i.sales_order_id=o.sales_order_id)
                       THEN o.shipping_amount ELSE 0 END""", ()),
        ("sales.cancellation_chronology", """SELECT count(*) FROM sales.sales_order_item_cancellations c
             JOIN sales.sales_orders o USING (sales_order_id)
            WHERE c.cancelled_at<o.placed_at + make_interval(days => %s) OR c.cancelled_at>o.placed_at + make_interval(days => %s)
               OR c.cancellation_reason<>'stock_timeout'""", (config.generation.get('max_stock_wait_days', 14), config.generation.get('max_stock_wait_days', 14))),
        ("inventory.transfer_movement_pair", """SELECT count(*) FROM (
             SELECT stock_transfer_item_id,
                    count(*) FILTER (WHERE movement_type='transfer_out') outs,
                    count(*) FILTER (WHERE movement_type='transfer_in') ins,
                    sum(quantity_delta) qty,min(unit_cost) min_cost,max(unit_cost) max_cost,
                    count(DISTINCT stock_location_id) locations
               FROM inventory.stock_movements WHERE movement_type IN ('transfer_out','transfer_in')
              GROUP BY stock_transfer_item_id
              HAVING count(*) FILTER (WHERE movement_type='transfer_out')<>1
                 OR count(*) FILTER (WHERE movement_type='transfer_in')<>1
                 OR sum(quantity_delta)<>0 OR min(unit_cost)<>max(unit_cost) OR count(DISTINCT stock_location_id)<>2) q""", ()),
        ("returns.fulfillment_source_quantity", """SELECT count(*) FROM after_sales.return_items ri
             JOIN logistics.fulfillment_items fi ON fi.fulfillment_item_id=ri.source_fulfillment_item_id
            WHERE fi.sales_order_id<>ri.sales_order_id OR fi.sales_order_item_id<>ri.sales_order_item_id
               OR ri.quantity_received>fi.fulfilled_quantity""", ()),
        ("returns.cumulative_fulfilled_quantity", """SELECT count(*) FROM (
             SELECT source_fulfillment_item_id,sum(quantity_received) returned
               FROM after_sales.return_items WHERE source_fulfillment_item_id IS NOT NULL GROUP BY source_fulfillment_item_id
          ) r JOIN logistics.fulfillment_items fi ON fi.fulfillment_item_id=r.source_fulfillment_item_id
            WHERE r.returned>fi.fulfilled_quantity""", ()),
        ("returns.inventory_destination", """SELECT count(*) FROM after_sales.return_items ri
             LEFT JOIN inventory.stock_movements m ON m.return_item_id=ri.return_item_id AND m.movement_type='customer_return'
            WHERE (ri.stock_destination='sellable' AND ri.quantity_received>0 AND (m.stock_movement_id IS NULL OR m.quantity_delta<>ri.quantity_received))
               OR (ri.stock_destination<>'sellable' AND m.stock_movement_id IS NOT NULL)""", ()),
        ("logistics.event_cutoff_state", """SELECT count(*) FROM logistics.fulfillment_events e JOIN logistics.fulfillments f USING (fulfillment_id)
            WHERE e.occurred_at > %s OR (f.status='cancelled' AND e.event_type IN ('delivered','picked_up'))""", (cutoff,)),
        ("payments.refund_relation_time", """SELECT count(*) FROM payments.refunds r JOIN payments.payments p USING (payment_id)
            WHERE r.sales_order_id<>p.sales_order_id OR r.requested_at<p.settled_at OR r.processed_at<r.requested_at""", ()),
    )
    extended_results = {
        name: run_sql_validation(connection, name, statement, params, expect_zero=True)[0]
        for name, statement, params in extended_checks
    }
    failed_extended = [name for name, count in extended_results.items() if count]
    if failed_extended:
        raise RuntimeError("Invariantes SQL Fase 3D falharam: " + ", ".join(failed_extended))
    check_results.update(extended_results)

    reservation_mismatch = run_sql_validation(connection, "inventory.active_reservation_balance", """
        SELECT count(*) FROM inventory.stock_positions p
         WHERE p.reserved_quantity<>(SELECT coalesce(sum(r.quantity),0) FROM inventory.stock_reservations r
                                     WHERE r.product_id=p.product_id AND r.stock_location_id=p.stock_location_id AND r.status='active')
    """, expect_zero=True)[0]
    if reservation_mismatch:
        raise RuntimeError("reserved_quantity diverge das reservas ativas.")
    check_results["inventory.active_reservation_balance"] = reservation_mismatch

    # PostgreSQL identity order is also INSERT order. The causal sink inserts every
    # ledger row while consuming the corresponding stock-state event, so the
    # replay uses occurred_at + identity as its total order. Include all source
    # foreign-key references for a useful first-divergence report.
    ledger = run_sql_validation(connection, "inventory.stock_movement_ledger_read", """
        SELECT m.stock_movement_id, m.product_id, p.sku, m.stock_location_id,
               l.location_code, m.movement_type, m.occurred_at,
               m.quantity_delta, m.unit_cost,
               CASE m.movement_type
                 WHEN 'receipt' THEN 'goods_receipt='||gr.receipt_number||'; purchase_line='||poi.line_number
                 WHEN 'fulfillment' THEN 'fulfillment='||f.fulfillment_number||'; sale_line='||soi.line_number
                 WHEN 'transfer_out' THEN 'transfer='||st.transfer_number||'; line='||sti.line_number
                 WHEN 'transfer_in' THEN 'transfer='||st.transfer_number||'; line='||sti.line_number
                 WHEN 'customer_return' THEN 'return='||r.return_number||'; return_item_id='||ri.return_item_id
                 ELSE 'unmapped'
               END AS source_reference
          FROM inventory.stock_movements m
          JOIN catalog.products p USING (product_id)
          JOIN inventory.stock_locations l USING (stock_location_id)
          LEFT JOIN procurement.goods_receipt_items gri USING (goods_receipt_item_id)
          LEFT JOIN procurement.goods_receipts gr USING (goods_receipt_id)
          LEFT JOIN procurement.purchase_order_items poi USING (purchase_order_item_id)
          LEFT JOIN logistics.fulfillment_items fi USING (fulfillment_item_id)
          LEFT JOIN logistics.fulfillments f USING (fulfillment_id)
          LEFT JOIN sales.sales_order_items soi USING (sales_order_item_id)
          LEFT JOIN inventory.stock_transfer_items sti USING (stock_transfer_item_id)
          LEFT JOIN inventory.stock_transfers st USING (stock_transfer_id)
          LEFT JOIN after_sales.return_items ri USING (return_item_id)
          LEFT JOIN after_sales.returns r USING (return_id)
         ORDER BY m.occurred_at, m.stock_movement_id
    """, fetch="all")
    balances: dict[tuple[int, int], int] = defaultdict(int)
    averages: dict[tuple[int, int], Decimal] = defaultdict(lambda: Decimal("0.00000000"))
    history: dict[tuple[int, int], deque[tuple]] = defaultdict(lambda: deque(maxlen=5))

    def transition(row: tuple, qty_before: int, avg_before: Decimal) -> tuple[int, Decimal]:
        kind, delta, unit_cost = row[5], row[7], row[8]
        if kind in {"receipt", "transfer_in", "customer_return"}:
            avg_after = weighted_moving_average(qty_before, avg_before, delta, unit_cost)
            return qty_before + delta, avg_after
        return qty_before + delta, avg_before

    def describe(row: tuple, qty_before: int, avg_before: Decimal) -> str:
        qty_after, avg_after = transition(row, qty_before, avg_before)
        return (
            f"movement_id={row[0]} source={row[9]} type={row[5]} at={row[6].isoformat()} "
            f"delta={row[7]} recorded_unit_cost={row[8]} qty_before={qty_before} "
            f"average_before={avg_before} qty_after={qty_after} average_after_expected={avg_after}"
        )

    replay_started = perf_counter()
    print("[validation] inventory.moving_average_replay START", flush=True)
    for index, row in enumerate(ledger):
        movement_id, product_id, sku, location_id, location_code, kind, occurred_at, delta, unit_cost, source = row
        key = (product_id, location_id)
        qty_before, avg_before = balances[key], averages[key]
        qty_after, avg_after = transition(row, qty_before, avg_before)
        if kind in {"fulfillment", "transfer_out"} and unit_cost != avg_before:
            related = history[key]
            before = list(related)[-5:]
            window = [describe(item[0], item[1], item[2]) for item in before]
            window.append(describe(row, qty_before, avg_before))
            look_qty, look_avg = qty_after, avg_after
            found = 0
            for later_index in range(index + 1, len(ledger)):
                later = ledger[later_index]
                if (later[1], later[3]) != key:
                    continue
                window.append(describe(later, look_qty, look_avg))
                look_qty, look_avg = transition(later, look_qty, look_avg)
                found += 1
                if found == 5:
                    break
            difference = unit_cost - avg_before
            raise RuntimeError(
                "FIRST DIVERGENCE in persisted moving-average replay: "
                f"movement_id={movement_id}; logical_movement_key=not persisted; "
                f"product_id={product_id}; SKU={sku}; stock_location_id={location_id}; location={location_code}; "
                f"movement_type={kind}; occurred_at={occurred_at.isoformat()}; quantity_delta={delta}; "
                f"recorded_unit_cost={unit_cost}; expected_unit_cost={avg_before}; difference={difference}; "
                f"quantity_before={qty_before}; average_before={avg_before}; quantity_after={qty_after}; "
                f"average_after_expected={avg_after}; source_reference={source}; "
                f"decimal_precision={getcontext().prec}; cost_rounding={ROUND_HALF_UP}; "
                "ledger_window=[" + " | ".join(window) + "]"
            )
        balances[key], averages[key] = qty_after, avg_after
        history[key].append((row, qty_before, avg_before))
    print(f"[validation] inventory.moving_average_replay PASS {perf_counter()-replay_started:.2f}s rows={len(ledger)}", flush=True)
    check_results["inventory.moving_average_replay"] = 0
    persisted_positions = run_sql_validation(
        connection,
        "inventory.stock_position_replay_compare_input",
        "SELECT product_id,stock_location_id,on_hand_quantity,reserved_quantity,available_quantity,average_unit_cost FROM inventory.stock_positions",
        fetch="all",
    )
    for product_id, location_id, on_hand, reserved, available, average in persisted_positions:
        key = (product_id, location_id)
        if on_hand != balances[key] or average != averages[key] or available != on_hand - reserved:
            product_row = next(item for item in ledger if item[1] == product_id and item[3] == location_id)
            raise RuntimeError(
                "FIRST POSITION DIVERGENCE: "
                f"product_id={product_id}; SKU={product_row[2]}; "
                f"stock_location_id={location_id}; location={product_row[4]}; "
                f"persisted_on_hand={on_hand}; replay_on_hand={balances[key]}; "
                f"persisted_average_unit_cost={average}; replay_average_unit_cost={averages[key]}; "
                f"reserved={reserved}; available={available}; "
                "ledger_tail=[" + " | ".join(describe(item[0], item[1], item[2]) for item in list(history[key])[-6:]) + "]"
            )

    ledger_cost = run_sql_validation(
        connection,
        "inventory.realized_fulfillment_cost",
        """SELECT coalesce(sum(abs(quantity_delta)::numeric*unit_cost),0)
             FROM inventory.stock_movements WHERE movement_type='fulfillment'""",
    )[0]
    expected_cost = data.summary()["realized_cost"]
    if ledger_cost != expected_cost:
        raise RuntimeError("Custo realizado SQL diverge do agregado reportado pelo gerador.")
    counts["realized_cost"] = ledger_cost
    check_results["inventory.realized_fulfillment_cost"] = 0
    return (counts, check_results) if include_check_results else counts
