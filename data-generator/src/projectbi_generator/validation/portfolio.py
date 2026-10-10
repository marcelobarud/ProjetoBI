"""Portfolio-only SQL integrity checks and documented distribution bands."""

from __future__ import annotations

from collections import defaultdict
from decimal import Decimal

from psycopg import sql

from projectbi_generator.database import OPERATIONAL_TABLES
from projectbi_generator.validation.order_history import ORDER_STATUS_TRANSITIONS
from projectbi_generator.validation.sql_diagnostics import run_sql_validation, set_validation_timeout


def _ratio(numerator: int | Decimal, denominator: int | Decimal) -> Decimal:
    if not denominator:
        return Decimal(0)
    return Decimal(numerator) * 100 / Decimal(denominator)


def collect_portfolio_metrics(connection, timezone: str) -> dict:
    metrics: dict = {}
    metrics["orders_by_year"] = dict(run_sql_validation(connection, "portfolio_metric.orders_by_year",
        """SELECT extract(year FROM placed_at AT TIME ZONE %s)::integer, count(*)
             FROM sales.sales_orders GROUP BY 1 ORDER BY 1""", (timezone,), fetch="all"))
    metrics["orders_by_month"] = dict(run_sql_validation(connection, "portfolio_metric.orders_by_month",
        """SELECT to_char(placed_at AT TIME ZONE %s, 'YYYY-MM'), count(*)
             FROM sales.sales_orders GROUP BY 1 ORDER BY 1""", (timezone,), fetch="all"))
    metrics["orders_by_channel"] = dict(run_sql_validation(connection, "portfolio_metric.orders_by_channel",
        """SELECT c.channel_code, count(*) FROM sales.sales_orders o
             JOIN sales.sales_channels c USING (sales_channel_id)
            GROUP BY c.channel_code ORDER BY c.channel_code""", fetch="all"))
    metrics["orders_by_type"] = dict(run_sql_validation(connection, "portfolio_metric.orders_by_type",
        "SELECT channel_type, count(*) FROM sales.sales_orders GROUP BY 1", fetch="all"))
    metrics["orders_by_year_type"] = defaultdict(dict)
    year_types = run_sql_validation(connection, "portfolio_metric.orders_by_year_type",
        """SELECT extract(year FROM placed_at AT TIME ZONE %s)::integer,channel_type,count(*)
             FROM sales.sales_orders GROUP BY 1,2 ORDER BY 1,2""", (timezone,), fetch="all")
    for year,channel_type,count in year_types:
        metrics["orders_by_year_type"][year][channel_type] = count
    metrics["monthly_distribution"] = run_sql_validation(connection, "portfolio_metric.monthly_distribution",
        """SELECT to_char(placed_at AT TIME ZONE %s,'YYYY-MM'),count(*),
                  count(*) FILTER(WHERE discount_amount>0),
                  avg(discount_amount/nullif(subtotal_amount,0)) FILTER(WHERE discount_amount>0)
             FROM sales.sales_orders GROUP BY 1 ORDER BY 1""", (timezone,), fetch="all")
    metrics["store_orders"] = run_sql_validation(connection, "portfolio_metric.store_orders",
        """SELECT coalesce(s.store_code,'unassigned'),count(*) FROM sales.sales_orders o
            LEFT JOIN core.stores s USING(store_id)
            WHERE o.channel_type='physical' GROUP BY 1 ORDER BY 1""", fetch="all")
    metrics["monthly_category_units"] = run_sql_validation(connection, "portfolio_metric.monthly_category_units",
        """SELECT to_char(o.placed_at AT TIME ZONE %s,'YYYY-MM'),c.category_code,sum(i.quantity)
             FROM sales.sales_order_items i JOIN sales.sales_orders o USING(sales_order_id)
             JOIN catalog.products p USING(product_id) JOIN catalog.categories c USING(category_id)
            GROUP BY 1,2 ORDER BY 1,2""", (timezone,), fetch="all")
    metrics["orders_by_status"] = dict(run_sql_validation(connection, "portfolio_metric.orders_by_status",
        "SELECT order_status, count(*) FROM sales.sales_orders GROUP BY 1 ORDER BY 1", fetch="all"))
    metrics["customer_types"] = dict(run_sql_validation(connection, "portfolio_metric.customer_types",
        "SELECT customer_type, count(*) FROM crm.customers GROUP BY 1 ORDER BY 1", fetch="all"))
    metrics["anonymous_physical"] = run_sql_validation(connection, "portfolio_metric.anonymous_physical",
        """SELECT count(*) FILTER (WHERE customer_id IS NULL), count(*)
             FROM sales.sales_orders WHERE channel_type='physical'""")
    metrics["digital_anonymous"] = run_sql_validation(connection, "portfolio_metric.digital_anonymous",
        "SELECT count(*) FROM sales.sales_orders WHERE channel_type<>'physical' AND customer_id IS NULL")[0]
    recurrence_rows = run_sql_validation(connection, "portfolio_metric.customer_recurrence",
        """WITH frequency AS (
               SELECT c.customer_type, count(*) order_count
                 FROM crm.customers c JOIN sales.sales_orders o USING (customer_id)
                WHERE o.order_status<>'cancelled' GROUP BY c.customer_id,c.customer_type
           )
           SELECT customer_type,
                  count(*) FILTER (WHERE order_count=1),
                  count(*) FILTER (WHERE order_count BETWEEN 2 AND 4),
                  count(*) FILTER (WHERE order_count BETWEEN 5 AND 10),
                  count(*) FILTER (WHERE order_count>=11),
                  avg(order_count)::numeric(12,4), count(*)
             FROM frequency GROUP BY customer_type""", fetch="all")
    metrics["recurrence"] = {row[0]: row[1:] for row in recurrence_rows}
    if metrics["recurrence"]:
        metrics["recurrence_overall"] = tuple(
            sum(values[index] for values in metrics["recurrence"].values())
            for index in (*range(4), 5)
        )
    else:
        metrics["recurrence_overall"] = (0,0,0,0,0)
    ticket_customer_rows = run_sql_validation(connection, "portfolio_metric.ticket_by_customer_type",
        """SELECT coalesce(c.customer_type,'anonymous'), count(*),
                  avg(o.total_amount)::numeric(18,2), sum(o.total_amount)
             FROM sales.sales_orders o LEFT JOIN crm.customers c USING (customer_id)
            WHERE o.order_status='completed' GROUP BY 1 ORDER BY 1""", fetch="all")
    metrics["ticket_by_customer_type"] = {row[0]: row[1:] for row in ticket_customer_rows}
    ticket_channel_rows = run_sql_validation(connection, "portfolio_metric.ticket_by_channel",
        """SELECT channel_type, count(*), avg(total_amount)::numeric(18,2), sum(total_amount)
             FROM sales.sales_orders WHERE order_status='completed'
            GROUP BY channel_type ORDER BY channel_type""", fetch="all")
    metrics["ticket_by_channel"] = {row[0]: row[1:] for row in ticket_channel_rows}
    metrics["discounts"] = run_sql_validation(connection, "portfolio_metric.discounts",
        """SELECT count(*) FILTER (WHERE discount_amount>0), count(*),
                  coalesce(sum(discount_amount),0), coalesce(sum(subtotal_amount),0),
                  avg(discount_amount/nullif(subtotal_amount,0)) FILTER (WHERE discount_amount>0)
             FROM sales.sales_orders""")
    payment_method_rows = run_sql_validation(connection, "portfolio_metric.payment_methods",
        """SELECT m.method_type, count(*) FILTER (WHERE p.status IN ('captured','settled')),
                  count(*) FILTER (WHERE p.status IN ('declined','failed')), count(*)
             FROM payments.payments p JOIN payments.payment_methods m USING (payment_method_id)
            GROUP BY m.method_type ORDER BY m.method_type""", fetch="all")
    metrics["payment_methods"] = {row[0]: row[1:] for row in payment_method_rows}
    metrics["returns"] = run_sql_validation(connection, "portfolio_metric.returns",
        """SELECT count(DISTINCT r.sales_order_id) FILTER (WHERE o.order_status='completed'),
                  count(DISTINCT r.sales_order_id) FILTER (WHERE o.order_status='completed' AND o.channel_type<>'physical'),
                  count(DISTINCT r.sales_order_id) FILTER (WHERE o.order_status='completed' AND o.channel_type='physical'),
                  count(DISTINCT r.sales_order_id) FILTER (WHERE o.order_status='completed' AND c.customer_type='business'),
                  count(*), count(*) FILTER (WHERE ri.stock_destination='sellable'),
                  count(*) FILTER (WHERE ri.stock_destination<>'sellable'),
                  coalesce(sum(ri.quantity_received) FILTER (WHERE ri.stock_destination='sellable'),0)
             FROM after_sales.returns r JOIN sales.sales_orders o USING (sales_order_id)
             LEFT JOIN crm.customers c USING (customer_id)
             LEFT JOIN after_sales.return_items ri USING (return_id)""")
    metrics["returns_completed_orders"] = run_sql_validation(connection, "portfolio_metric.completed_orders",
        "SELECT count(*) FROM sales.sales_orders WHERE order_status='completed'")[0]
    metrics["fulfilled_units"] = run_sql_validation(connection, "portfolio_metric.fulfilled_units",
        """SELECT coalesce(sum(fulfilled_quantity),0)
             FROM logistics.fulfillment_items WHERE fulfilled_quantity>0""")[0]
    metrics["product_concentration"] = run_sql_validation(connection, "portfolio_metric.product_concentration",
        """WITH sku_units AS (
               SELECT i.product_id, sum(i.quantity) units FROM sales.sales_order_items i
                 JOIN sales.sales_orders o USING(sales_order_id) WHERE o.order_status='completed' GROUP BY i.product_id
           ) SELECT coalesce(max(units),0), coalesce(sum(units),0), count(*) FROM sku_units""")
    metrics["financials"] = run_sql_validation(connection, "portfolio_metric.financials",
        """WITH order_finance AS (
               SELECT count(*) FILTER (WHERE order_status='completed') completed_orders,
                      coalesce(sum(subtotal_amount) FILTER (WHERE order_status='completed'),0) gross_order_value,
                      coalesce(sum(discount_amount) FILTER (WHERE order_status='completed'),0) discount_amount,
                      coalesce(sum(subtotal_amount-discount_amount) FILTER (WHERE order_status='completed'),0) net_product_value,
                      coalesce(sum(shipping_amount) FILTER (WHERE order_status='completed'),0) shipping_charged,
                      coalesce(sum(total_amount) FILTER (WHERE order_status='completed'),0) order_total
                 FROM sales.sales_orders
           ), captured AS (
               SELECT coalesce(sum(amount),0) amount FROM payments.payments WHERE status IN ('captured','settled')
           ), refunds AS (
               SELECT coalesce(sum(amount),0) amount FROM payments.refunds WHERE status='completed'
           ), cogs AS (
               SELECT coalesce(sum(abs(quantity_delta)::numeric*unit_cost),0) amount
                 FROM inventory.stock_movements WHERE movement_type='fulfillment'
           )
           SELECT f.*, c.amount, r.amount, g.amount
             FROM order_finance f CROSS JOIN captured c CROSS JOIN refunds r CROSS JOIN cogs g""")
    metrics["margin"] = run_sql_validation(connection, "portfolio_metric.margin",
        """WITH discounts AS (
               SELECT sales_order_id,sales_order_item_id,sum(amount) amount
                 FROM sales.applied_discounts GROUP BY sales_order_id,sales_order_item_id
           ), returned AS (
               SELECT source_fulfillment_item_id,sum(quantity_received) units
                 FROM after_sales.return_items WHERE quantity_received>0 AND source_fulfillment_item_id IS NOT NULL
                GROUP BY source_fulfillment_item_id
           ), fulfillment_history_cost AS (
               SELECT fi.fulfillment_item_id,
                      round(sum(abs(fm.quantity_delta)::numeric*fm.unit_cost)
                        / nullif(sum(abs(fm.quantity_delta)),0),8) historical_unit_cost
                 FROM logistics.fulfillment_items fi
                 JOIN inventory.stock_movements fm ON fm.fulfillment_item_id=fi.fulfillment_item_id
                      AND fm.movement_type='fulfillment'
                GROUP BY fi.fulfillment_item_id
           ), return_movement_cost AS (
               SELECT return_item_id,sum(abs(m.quantity_delta)::numeric*m.unit_cost) cost
                 FROM inventory.stock_movements m
                WHERE m.movement_type='customer_return' AND m.return_item_id IS NOT NULL
                GROUP BY return_item_id
           ), return_cost AS (
               SELECT ri.source_fulfillment_item_id,
                      coalesce(sum(coalesce(rmc.cost,0))
                        FILTER (WHERE ri.stock_destination='sellable'),0) sellable_cogs_reversal,
                      coalesce(sum(ri.quantity_received*fh.historical_unit_cost)
                        FILTER (WHERE ri.stock_destination IN ('quarantine','repair','discard')),0) non_sellable_loss
                 FROM after_sales.return_items ri
                 JOIN fulfillment_history_cost fh ON fh.fulfillment_item_id=ri.source_fulfillment_item_id
                 LEFT JOIN return_movement_cost rmc ON rmc.return_item_id=ri.return_item_id
                WHERE ri.quantity_received>0
                GROUP BY ri.source_fulfillment_item_id
           ), fulfillment_cost AS (
               SELECT fi.fulfillment_item_id,fi.sales_order_id,fi.sales_order_item_id,fi.fulfilled_quantity,
                      coalesce(r.units,0) returned_units,
                      sum(abs(m.quantity_delta)::numeric*m.unit_cost) full_cogs,
                      coalesce(rc.sellable_cogs_reversal,0) sellable_cogs_reversal
                 FROM logistics.fulfillment_items fi
                 JOIN inventory.stock_movements m ON m.fulfillment_item_id=fi.fulfillment_item_id AND m.movement_type='fulfillment'
                 LEFT JOIN returned r ON r.source_fulfillment_item_id=fi.fulfillment_item_id
                 LEFT JOIN return_cost rc ON rc.source_fulfillment_item_id=fi.fulfillment_item_id
                GROUP BY fi.fulfillment_item_id,fi.sales_order_id,fi.sales_order_item_id,fi.fulfilled_quantity,r.units,
                         rc.sellable_cogs_reversal
           ), eligible AS (
               SELECT greatest(f.fulfilled_quantity-f.returned_units,0)::numeric*
                        (i.unit_sale_price-coalesce(d.amount,0)/nullif(i.quantity,0)) revenue,
                      f.full_cogs-f.sellable_cogs_reversal cogs
                 FROM fulfillment_cost f JOIN sales.sales_orders o USING(sales_order_id)
                 JOIN sales.sales_order_items i USING(sales_order_id,sales_order_item_id)
                 LEFT JOIN discounts d ON d.sales_order_id=i.sales_order_id AND d.sales_order_item_id=i.sales_order_item_id
                WHERE o.order_status='completed'
           ) SELECT coalesce(sum(revenue),0),coalesce(sum(cogs),0) FROM eligible""")
    metrics["margin_return_costs"] = run_sql_validation(connection, "portfolio_metric.margin_return_costs",
        """WITH fulfillment_history_cost AS (
               SELECT fi.fulfillment_item_id,
                      round(sum(abs(fm.quantity_delta)::numeric*fm.unit_cost)
                        / nullif(sum(abs(fm.quantity_delta)),0),8) historical_unit_cost
                 FROM logistics.fulfillment_items fi
                 JOIN inventory.stock_movements fm ON fm.fulfillment_item_id=fi.fulfillment_item_id
                      AND fm.movement_type='fulfillment'
                GROUP BY fi.fulfillment_item_id
           ), return_movement_cost AS (
               SELECT return_item_id,sum(abs(m.quantity_delta)::numeric*m.unit_cost) cost
                 FROM inventory.stock_movements m
                WHERE m.movement_type='customer_return' AND m.return_item_id IS NOT NULL
                GROUP BY return_item_id
           )
           SELECT coalesce(sum(coalesce(rmc.cost,0)) FILTER (WHERE ri.stock_destination='sellable'),0) sellable_cogs_reversed,
                  coalesce(sum(ri.quantity_received*fh.historical_unit_cost)
                    FILTER (WHERE ri.stock_destination IN ('quarantine','repair','discard')),0) non_sellable_loss_included
             FROM after_sales.return_items ri
             JOIN fulfillment_history_cost fh ON fh.fulfillment_item_id=ri.source_fulfillment_item_id
             LEFT JOIN return_movement_cost rmc ON rmc.return_item_id=ri.return_item_id
             JOIN logistics.fulfillment_items fi ON fi.fulfillment_item_id=ri.source_fulfillment_item_id
             JOIN sales.sales_orders o ON o.sales_order_id=ri.sales_order_id
            WHERE o.order_status='completed' AND ri.quantity_received>0""")
    metrics["stock_totals"] = run_sql_validation(connection, "portfolio_metric.stock_totals",
        """SELECT coalesce(sum(on_hand_quantity),0),coalesce(sum(reserved_quantity),0),
                  coalesce(sum(available_quantity),0),count(*) FROM inventory.stock_positions""")
    metrics["transfer_totals"] = run_sql_validation(connection, "portfolio_metric.transfer_totals",
        """SELECT (SELECT count(*) FROM inventory.stock_transfers),
                  (SELECT count(*) FROM inventory.stock_transfer_items),
                  count(*) FILTER (WHERE movement_type IN ('transfer_in','transfer_out')),
                  count(DISTINCT stock_transfer_item_id) FILTER (WHERE movement_type IN ('transfer_in','transfer_out'))
             FROM inventory.stock_movements""")
    metrics["table_counts"] = {
        f"{schema}.{table}": run_sql_validation(connection, f"portfolio.table_count.{schema}.{table}",
            sql.SQL("SELECT count(*) FROM {}.{}").format(sql.Identifier(schema), sql.Identifier(table)).as_string(connection))[0]
        for schema, table in OPERATIONAL_TABLES
    }
    metrics["time_ranges"] = {
        row[0]: (row[1], row[2]) for row in run_sql_validation(connection, "portfolio_metric.time_ranges",
            """SELECT entity, min(local_date), max(local_date) FROM (
                 SELECT 'sales orders'::text entity, (placed_at AT TIME ZONE %s)::date local_date FROM sales.sales_orders
                 UNION ALL SELECT 'payments', (attempted_at AT TIME ZONE %s)::date FROM payments.payments
                 UNION ALL SELECT 'stock movements', (occurred_at AT TIME ZONE %s)::date FROM inventory.stock_movements
                 UNION ALL SELECT 'fulfillment events', (occurred_at AT TIME ZONE %s)::date FROM logistics.fulfillment_events
                 UNION ALL SELECT 'returns', (requested_at AT TIME ZONE %s)::date FROM after_sales.returns
                 UNION ALL SELECT 'refunds', (requested_at AT TIME ZONE %s)::date FROM payments.refunds
             ) dates GROUP BY entity ORDER BY entity""",
            (timezone,)*6, fetch="all")
    }
    return metrics


def validate_portfolio_critical(connection, config) -> dict:
    """Run critical cross-table invariants not covered by PostgreSQL local FKs."""
    set_validation_timeout(connection)
    cutoff = config.end_date
    allowed_transitions = " OR ".join(
        f"(previous_status='{previous}' AND status='{current}')"
        for previous, following in ORDER_STATUS_TRANSITIONS.items()
        for current in sorted(following)
    )
    checks = (
        ("portfolio.customer_profile_exclusivity", """SELECT count(*) FROM crm.customers c LEFT JOIN crm.individual_profiles i USING(customer_id)
              LEFT JOIN crm.business_profiles b USING(customer_id)
            WHERE (i.customer_id IS NOT NULL)::int + (b.customer_id IS NOT NULL)::int <> 1
               OR (c.customer_type='individual')<>(i.customer_id IS NOT NULL)
               OR (c.customer_type='business')<>(b.customer_id IS NOT NULL)""", ()),
        ("portfolio.order_item_discount_reconciliation", """SELECT count(*) FROM sales.sales_orders o
             LEFT JOIN (SELECT sales_order_id,sum(quantity*unit_sale_price) gross FROM sales.sales_order_items GROUP BY sales_order_id) i USING(sales_order_id)
             LEFT JOIN (SELECT sales_order_id,sum(amount) allocated FROM sales.applied_discounts GROUP BY sales_order_id) d USING(sales_order_id)
            WHERE o.subtotal_amount<>coalesce(i.gross,0) OR o.discount_amount<>coalesce(d.allocated,0)
               OR o.subtotal_amount-o.discount_amount<0""", ()),
        ("portfolio.sales_updated_at_chronology", "SELECT count(*) FROM sales.sales_orders o WHERE o.updated_at<o.placed_at", ()),
        ("portfolio.sales_status_history_chronology", """SELECT count(*) FROM sales.order_status_history h
             JOIN sales.sales_orders o USING (sales_order_id)
            WHERE (h.status='draft' AND h.occurred_at>=o.placed_at)
               OR (h.status<>'draft' AND h.occurred_at<o.placed_at)""", ()),
        ("portfolio.sales_status_history_placed_marker", """SELECT count(*) FROM sales.sales_orders o
             WHERE (SELECT count(*) FROM sales.order_status_history h
                     WHERE h.sales_order_id=o.sales_order_id AND h.status='draft')<>1
                OR (SELECT count(*) FROM sales.order_status_history h
                     WHERE h.sales_order_id=o.sales_order_id AND h.status='placed' AND h.occurred_at=o.placed_at)<>1
                OR EXISTS (SELECT 1 FROM sales.order_status_history h
                     WHERE h.sales_order_id=o.sales_order_id AND h.status='placed' AND h.occurred_at<>o.placed_at)""", ()),
        ("portfolio.sales_status_history_ordering", """WITH ordered AS (
              SELECT occurred_at,lag(occurred_at) OVER (PARTITION BY sales_order_id ORDER BY order_status_history_id) previous_at
                FROM sales.order_status_history
          ) SELECT count(*) FROM ordered WHERE previous_at>occurred_at""", ()),
        ("portfolio.sales_status_history_transitions", f"""WITH ordered AS (
              SELECT status,lag(status) OVER (PARTITION BY sales_order_id ORDER BY occurred_at,order_status_history_id) previous_status
                FROM sales.order_status_history
          ) SELECT count(*) FROM ordered WHERE previous_status IS NOT NULL AND NOT ({allowed_transitions})""", ()),
        ("portfolio.terminal_order_reservations", """SELECT count(*) FROM sales.sales_orders o
             WHERE o.order_status IN ('cancelled','completed') AND EXISTS (
               SELECT 1 FROM inventory.stock_reservations r WHERE r.sales_order_id=o.sales_order_id AND r.status='active')""", ()),
        ("portfolio.refund_eligibility_by_return", """SELECT count(*) FROM (
              WITH item_discount AS (
                SELECT sales_order_id,sales_order_item_id,sum(amount) amount FROM sales.applied_discounts GROUP BY sales_order_id,sales_order_item_id
              ), eligible AS (
                SELECT ri.return_id,sum(ri.quantity_approved*round(oi.unit_sale_price-coalesce(d.amount,0)/nullif(oi.quantity,0),2)) amount
                  FROM after_sales.return_items ri JOIN sales.sales_order_items oi
                    ON oi.sales_order_id=ri.sales_order_id AND oi.sales_order_item_id=ri.sales_order_item_id
                  LEFT JOIN item_discount d ON d.sales_order_id=oi.sales_order_id AND d.sales_order_item_id=oi.sales_order_item_id
                 GROUP BY ri.return_id
              ), refunded AS (
                SELECT return_id,sum(amount) amount FROM payments.refunds WHERE status='completed' AND return_id IS NOT NULL GROUP BY return_id
              ) SELECT e.return_id FROM eligible e JOIN refunded r USING(return_id) WHERE r.amount>e.amount) q""", ()),
        ("portfolio.historical_return_cost", """SELECT count(*) FROM after_sales.return_items ri
             JOIN inventory.stock_movements rm ON rm.return_item_id=ri.return_item_id AND rm.movement_type='customer_return'
             JOIN LATERAL (SELECT sum(abs(m.quantity_delta)::numeric*m.unit_cost)/nullif(sum(abs(m.quantity_delta)),0) unit_cost
                 FROM inventory.stock_movements m WHERE m.fulfillment_item_id=ri.source_fulfillment_item_id AND m.movement_type='fulfillment') source_cost ON true
            WHERE ri.stock_destination='sellable' AND rm.unit_cost<>source_cost.unit_cost""", ()),
        ("portfolio.sales_cutoff", "SELECT count(*) FROM sales.sales_orders o WHERE o.placed_at AT TIME ZONE %s >= (%s::date + 1)::timestamp", (config.timezone.key, cutoff)),
        ("portfolio.stock_bootstrap_commercial_cutoff", """SELECT count(*) FROM inventory.stock_movements m
             WHERE ((m.occurred_at AT TIME ZONE %s)::date < %s::date
                    AND (m.movement_type<>'receipt' OR (m.occurred_at AT TIME ZONE %s)::date < %s::date))
                OR (m.occurred_at AT TIME ZONE %s)::date > %s::date""",
         (config.timezone.key, config.start_date, config.timezone.key, config.bootstrap_start_date, config.timezone.key, cutoff)),
        ("portfolio.cost_columns_numeric_20_8", """SELECT 3-count(*) FROM information_schema.columns
             WHERE (table_schema,table_name,column_name) IN
               (('procurement','goods_receipt_items','unit_acquisition_cost'),('inventory','stock_positions','average_unit_cost'),('inventory','stock_movements','unit_cost'))
               AND data_type='numeric' AND numeric_precision=20 AND numeric_scale=8""", ()),
        ("portfolio.stock_available_generated_column", """SELECT 1-count(*) FROM information_schema.columns
             WHERE table_schema='inventory' AND table_name='stock_positions' AND column_name='available_quantity' AND is_generated='ALWAYS'""", ()),
        ("portfolio.fulfillment_event_chronology", """SELECT count(*) FROM (
              SELECT f.fulfillment_id,
                     min(e.occurred_at) FILTER(WHERE e.event_type='prepared') prepared_at,
                     min(e.occurred_at) FILTER(WHERE e.event_type='dispatched') dispatched_at,
                     min(e.occurred_at) FILTER(WHERE e.event_type='delivered') delivered_at,
                     min(e.occurred_at) FILTER(WHERE e.event_type='pickup_ready') pickup_ready_at,
                     min(e.occurred_at) FILTER(WHERE e.event_type='picked_up') picked_up_at
                FROM logistics.fulfillments f JOIN logistics.fulfillment_events e USING(fulfillment_id) GROUP BY f.fulfillment_id
          ) q WHERE (delivered_at IS NOT NULL AND (dispatched_at IS NULL OR delivered_at<dispatched_at))
                 OR (dispatched_at IS NOT NULL AND prepared_at IS NOT NULL AND dispatched_at<prepared_at)
                 OR (picked_up_at IS NOT NULL AND (pickup_ready_at IS NULL OR picked_up_at<pickup_ready_at))
                 OR (pickup_ready_at IS NOT NULL AND prepared_at IS NOT NULL AND pickup_ready_at<prepared_at)""", ()),
        ("portfolio.transfer_endpoints_quantities_cost", """SELECT count(*) FROM (
              SELECT i.stock_transfer_item_id,t.source_stock_location_id,t.destination_stock_location_id,i.quantity_dispatched,i.quantity_received,
                     count(*) FILTER(WHERE m.movement_type='transfer_out') out_count,count(*) FILTER(WHERE m.movement_type='transfer_in') in_count,
                     max(m.stock_location_id) FILTER(WHERE m.movement_type='transfer_out') out_location,
                     max(m.stock_location_id) FILTER(WHERE m.movement_type='transfer_in') in_location,
                     sum(abs(m.quantity_delta)) FILTER(WHERE m.movement_type='transfer_out') out_quantity,
                     sum(m.quantity_delta) FILTER(WHERE m.movement_type='transfer_in') in_quantity,
                     min(m.unit_cost) FILTER(WHERE m.movement_type IN ('transfer_out','transfer_in')) min_cost,
                     max(m.unit_cost) FILTER(WHERE m.movement_type IN ('transfer_out','transfer_in')) max_cost
                FROM inventory.stock_transfer_items i JOIN inventory.stock_transfers t USING(stock_transfer_id)
                LEFT JOIN inventory.stock_movements m USING(stock_transfer_item_id)
               GROUP BY i.stock_transfer_item_id,t.source_stock_location_id,t.destination_stock_location_id,i.quantity_dispatched,i.quantity_received
          ) q WHERE out_count<>1 OR in_count<>1 OR out_location<>source_stock_location_id OR in_location<>destination_stock_location_id
                 OR out_quantity<>quantity_dispatched OR in_quantity<>quantity_received OR min_cost<>max_cost""", ()),
        ("portfolio.commercial_event_cutoff", """SELECT count(*) FROM (
              SELECT occurred_at FROM sales.order_status_history UNION ALL SELECT placed_at FROM sales.sales_orders
              UNION ALL SELECT attempted_at FROM payments.payments UNION ALL SELECT authorized_at FROM payments.payments WHERE authorized_at IS NOT NULL
              UNION ALL SELECT settled_at FROM payments.payments WHERE settled_at IS NOT NULL
              UNION ALL SELECT planned_at FROM logistics.fulfillments WHERE planned_at IS NOT NULL
              UNION ALL SELECT dispatched_at FROM logistics.fulfillments WHERE dispatched_at IS NOT NULL
              UNION ALL SELECT completed_at FROM logistics.fulfillments WHERE completed_at IS NOT NULL
              UNION ALL SELECT occurred_at FROM logistics.fulfillment_events UNION ALL SELECT requested_at FROM inventory.stock_transfers
              UNION ALL SELECT dispatched_at FROM inventory.stock_transfers WHERE dispatched_at IS NOT NULL
              UNION ALL SELECT received_at FROM inventory.stock_transfers WHERE received_at IS NOT NULL
              UNION ALL SELECT reserved_at FROM inventory.stock_reservations
              UNION ALL SELECT released_at FROM inventory.stock_reservations WHERE released_at IS NOT NULL
              UNION ALL SELECT requested_at FROM after_sales.returns UNION ALL SELECT decided_at FROM after_sales.returns WHERE decided_at IS NOT NULL
              UNION ALL SELECT received_at FROM after_sales.return_items WHERE received_at IS NOT NULL
              UNION ALL SELECT requested_at FROM payments.refunds UNION ALL SELECT processed_at FROM payments.refunds WHERE processed_at IS NOT NULL
              UNION ALL SELECT occurred_at FROM inventory.stock_movements
          ) events WHERE (occurred_at AT TIME ZONE %s)::date>%s::date""", (config.timezone.key, cutoff)),
    )
    results = {name: run_sql_validation(connection, name, statement, params, expect_zero=True)[0]
               for name, statement, params in checks}
    failed = {name: count for name, count in results.items() if count}
    if failed:
        raise RuntimeError("CRITICAL Portfolio validation failed: " + ", ".join(f"{key}={value}" for key,value in failed.items()))
    return results


def classify_portfolio_distributions(metrics: dict) -> dict:
    """Classify the approved business bands; warnings do not block COMMIT."""
    checks: list[dict] = []
    failures: list[str] = []
    warnings: list[str] = []

    def band(name: str, value: Decimal, low: Decimal, high: Decimal, *,
             structural: bool = True, tolerance: Decimal = Decimal(0)) -> None:
        if low <= value <= high:
            result = "PASS"
        elif low-tolerance <= value <= high+tolerance:
            result = "WARNING"
            warnings.append(name)
        elif structural:
            result = "FAIL"
            failures.append(name)
        else:
            result = "WARNING"
            warnings.append(name)
        checks.append({"name": name, "value_percent": str(value.quantize(Decimal("0.01"))),
                       "band_percent": [str(low), str(high)], "result": result})

    customer_total = sum(metrics["customer_types"].values())
    band("identified_customers_pf", _ratio(metrics["customer_types"].get("individual", 0), customer_total), Decimal(88), Decimal(92))
    band("identified_customers_pj", _ratio(metrics["customer_types"].get("business", 0), customer_total), Decimal(8), Decimal(12))
    anonymous, physical_total = metrics["anonymous_physical"]
    band("anonymous_physical_orders", _ratio(anonymous, physical_total), Decimal(25), Decimal(35), tolerance=Decimal(2))
    if metrics["digital_anonymous"]:
        checks.append({"name": "digital_anonymous_orders", "value": metrics["digital_anonymous"], "result": "FAIL"})
        failures.append("digital_anonymous_orders")
    else:
        checks.append({"name": "digital_anonymous_orders", "value": 0, "result": "PASS"})

    total_orders = sum(metrics["orders_by_channel"].values())
    by_type = metrics["orders_by_type"]
    band("channel_physical", _ratio(by_type.get("physical", 0), total_orders), Decimal(50), Decimal(55), tolerance=Decimal(2))
    band("channel_ecommerce", _ratio(by_type.get("ecommerce", 0), total_orders), Decimal(25), Decimal(32), tolerance=Decimal(2))
    band("channel_marketplace_combined", _ratio(by_type.get("marketplace", 0), total_orders), Decimal(15), Decimal(22), tolerance=Decimal(2))
    year_bands = {2023:(20000,26000), 2024:(25000,32000), 2025:(32000,40000), 2026:(27000,34000)}
    for year,(low,high) in year_bands.items():
        value = metrics["orders_by_year"].get(year,0)
        if low <= value <= high:
            result = "PASS"
        elif low-2000 <= value <= high+2000:
            result = "WARNING"
            warnings.append(f"orders_{year}")
        else:
            result = "FAIL"
            failures.append(f"orders_{year}")
        checks.append({"name": f"orders_{year}", "value": value, "band": [low,high], "result": result})
    total_result = "PASS" if 110000 <= total_orders <= 130000 else "WARNING" if 105000 <= total_orders <= 135000 else "FAIL"
    if total_result == "WARNING": warnings.append("orders_total")
    if total_result == "FAIL":
        failures.append("orders_total")
    checks.append({"name":"orders_total","value":total_orders,"band":[110000,130000],
                   "result":total_result})

    recurrence_bands = (("one_order",35,50),("two_to_four",30,40),("five_to_ten",10,18),("eleven_plus",2,6))
    overall_buckets = metrics["recurrence_overall"]
    count = overall_buckets[4]
    for ordinal,(name,low,high) in enumerate(recurrence_bands):
        band(f"recurrence_{name}",_ratio(overall_buckets[ordinal],count),Decimal(low),Decimal(high),tolerance=Decimal(3))
    if metrics["recurrence"].get("business") and metrics["recurrence"].get("individual"):
        pj_avg = Decimal(metrics["recurrence"]["business"][4]); pf_avg = Decimal(metrics["recurrence"]["individual"][4])
        status = "PASS" if pj_avg > pf_avg else "WARNING"
        if status == "WARNING": warnings.append("pj_recurrence_higher_than_pf")
        checks.append({"name":"pj_recurrence_higher_than_pf","pf_average":str(pf_avg),"pj_average":str(pj_avg),"result":status})
    if metrics["ticket_by_customer_type"].get("business") and metrics["ticket_by_customer_type"].get("individual"):
        pj_ticket = Decimal(metrics["ticket_by_customer_type"]["business"][1])
        pf_ticket = Decimal(metrics["ticket_by_customer_type"]["individual"][1])
        ticket_ratio = pj_ticket / pf_ticket if pf_ticket else Decimal(0)
        status = "PASS" if Decimal("1.5") <= ticket_ratio <= Decimal("3.0") else "WARNING"
        if status == "WARNING": warnings.append("pj_ticket_ratio_outside_reference")
        checks.append({"name":"pj_to_pf_ticket_ratio","value":str(ticket_ratio.quantize(Decimal("0.01"))),
                       "band":["1.5","3.0"],"result":status})

    completed = metrics["orders_by_status"].get("completed",0)
    cancelled = metrics["orders_by_status"].get("cancelled",0)
    placed = metrics["orders_by_status"].get("placed",0) + metrics["orders_by_status"].get("confirmed",0)
    total_status = sum(metrics["orders_by_status"].values())
    band("completed_orders",_ratio(completed,total_status),Decimal(93),Decimal(97),tolerance=Decimal(1))
    band("cancelled_orders",_ratio(cancelled,total_status),Decimal(2),Decimal(5),tolerance=Decimal(1))
    band("pending_orders",_ratio(placed,total_status),Decimal(0),Decimal(3),tolerance=Decimal(1))
    discounted, order_count, discount_amount, gross, average_discount_rate = metrics["discounts"]
    band("orders_with_discount",_ratio(discounted,order_count),Decimal(30),Decimal(45),tolerance=Decimal(3))
    avg_rate = Decimal(average_discount_rate or 0) * 100
    band("average_discount_on_discounted_orders",avg_rate,Decimal(2),Decimal(12),structural=False)

    method_totals = {key:value[0] for key,value in metrics["payment_methods"].items()}
    captured_payment_count = sum(method_totals.values())
    for method,low,high in (("card",35,50),("instant",30,45),("cash",8,18)):
        band(f"payment_mix_{method}",_ratio(method_totals.get(method,0),captured_payment_count),Decimal(low),Decimal(high),tolerance=Decimal(4))

    return_orders = metrics["returns"][0]
    completed_count = metrics["returns_completed_orders"]
    band("returns_orders_completed_denominator",_ratio(return_orders,completed_count),Decimal(4),Decimal(8),tolerance=Decimal("1.5"))
    margin_revenue, margin_cogs = metrics["margin"]
    if margin_revenue <= 0 or margin_cogs > margin_revenue:
        failures.append("gross_profit_nonpositive")
        checks.append({"name":"operational_gross_profit_positive","revenue":str(margin_revenue),
                       "cogs":str(margin_cogs),"result":"FAIL"})
    else:
        gross_margin_percent = _ratio(margin_revenue-margin_cogs,margin_revenue)
        band("operational_gross_margin",gross_margin_percent,Decimal(8),Decimal(28),tolerance=Decimal(5))
    max_sku, units_total, sku_count = metrics["product_concentration"]
    leader_share = _ratio(max_sku,units_total)
    band("product_leader_units_share",leader_share,Decimal(0),Decimal(2),structural=False)
    physical_orders_total = sum(value for _,value in metrics["store_orders"])
    largest_store = max((value for _,value in metrics["store_orders"]), default=0)
    store_share = _ratio(largest_store,physical_orders_total)
    if store_share > Decimal(16):
        warnings.append("physical_store_share_above_reference")
        status = "WARNING"
    else:
        status = "PASS"
    checks.append({"name":"largest_store_share_of_physical_orders",
                   "value_percent":str(store_share.quantize(Decimal("0.01"))),"result":status})
    if total_orders:
        months = {row[0]:row[1:] for row in metrics["monthly_distribution"]}
        novembers = [int(value[0]) for key,value in months.items() if key.endswith("-11") and key[:4] in {"2023","2024","2025"}]
        other_months = [int(value[0]) for key,value in months.items() if not key.endswith("-11")]
        if novembers and other_months and sum(novembers)/len(novembers) <= sum(other_months)/len(other_months):
            warnings.append("black_friday_november_not_above_other_month_average")
            checks.append({"name":"black_friday_november_peak","result":"WARNING"})
        else:
            checks.append({"name":"black_friday_november_peak","result":"PASS"})
        bf_months = [value for key,value in months.items() if key.endswith("-11") and key[:4] in {"2023","2024","2025"}]
        regular_months = [value for key,value in months.items() if not (key.endswith("-11") and key[:4] in {"2023","2024","2025"})]
        bf_discount = _ratio(sum(int(value[1]) for value in bf_months),sum(int(value[0]) for value in bf_months))
        regular_discount = _ratio(sum(int(value[1]) for value in regular_months),sum(int(value[0]) for value in regular_months))
        status = "PASS" if bf_discount > regular_discount else "WARNING"
        if status == "WARNING": warnings.append("black_friday_discount_incidence_not_higher")
        checks.append({"name":"black_friday_discount_incidence","value_percent":str(bf_discount.quantize(Decimal("0.01"))),
                       "comparison_percent":str(regular_discount.quantize(Decimal("0.01"))),"result":status})
        category_bf = defaultdict(int)
        category_other = defaultdict(int)
        for month,category,units in metrics["monthly_category_units"]:
            target = category_bf if month.endswith("-11") and month[:4] in {"2023","2024","2025"} else category_other
            target[category] += units
        bf_units = sum(category_bf.values())
        other_units = sum(category_other.values())
        mix_variation = (sum(abs(Decimal(category_bf[key])/bf_units-Decimal(category_other[key])/other_units)
                             for key in set(category_bf)|set(category_other))/2
                         if bf_units and other_units else Decimal(0))
        status = "PASS" if mix_variation >= Decimal("0.01") else "WARNING"
        if status == "WARNING": warnings.append("black_friday_category_mix_did_not_shift")
        checks.append({"name":"black_friday_category_mix_shift","total_variation":str(mix_variation.quantize(Decimal("0.0001"))),"result":status})
        december = [int(value[0]) for key,value in months.items() if key.endswith("-12")]
        january = [int(value[0]) for key,value in months.items() if key.endswith("-01")]
        overall_month = sum(int(value[0]) for value in months.values())/max(len(months),1)
        for name, values, is_high in (("december_elevated",december,True),("january_post_peak_lower",january,False)):
            plausibly_seasonal = bool(values) and ((sum(values)/len(values)>overall_month) if is_high else (sum(values)/len(values)<overall_month))
            status = "PASS" if plausibly_seasonal else "WARNING"
            if status == "WARNING": warnings.append(name)
            checks.append({"name":name,"monthly_average":(sum(values)/len(values) if values else None),
                           "overall_month_average":overall_month,"result":status})
        digital_shares = []
        for year,channels in sorted(metrics["orders_by_year_type"].items()):
            digital = channels.get("ecommerce",0)+channels.get("marketplace",0)
            year_total = sum(channels.values())
            digital_shares.append((year,_ratio(digital,year_total)))
        if len(digital_shares)>1 and digital_shares[-1][1] <= digital_shares[0][1]:
            warnings.append("digital_share_did_not_grow_across_horizon")
            checks.append({"name":"digital_share_trend","result":"WARNING","by_year":[(y,str(v)) for y,v in digital_shares]})
        else:
            checks.append({"name":"digital_share_trend","result":"PASS","by_year":[(y,str(v)) for y,v in digital_shares]})
    return {"checks":checks,"critical_fails":0,"distributional_warnings":len(warnings),
            "distributional_fails":len(failures),"warnings":warnings,"fails":failures}
