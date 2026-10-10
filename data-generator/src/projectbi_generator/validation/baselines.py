"""Versioned operational SQL baselines for the committed portfolio dataset."""

from __future__ import annotations

from pathlib import Path

from projectbi_generator.database import OPERATIONAL_TABLES


def _control_totals_sql() -> str:
    rows = [f"SELECT '{schema}.{table}' AS table_name, count(*)::bigint AS row_count FROM {schema}.{table}"
            for schema, table in OPERATIONAL_TABLES]
    return "\nUNION ALL\n".join(rows) + "\nORDER BY table_name"


BASELINE_QUERIES: dict[str, str] = {
    "00_control_totals.sql": _control_totals_sql(),
    "01_sales_overview.sql": """WITH item_discounts AS (
    SELECT sales_order_id, sales_order_item_id, sum(amount) amount
      FROM sales.applied_discounts GROUP BY sales_order_id, sales_order_item_id
), order_items AS (
    SELECT i.sales_order_id, sum(i.quantity) units,
           sum(i.quantity*i.unit_sale_price) gross_product_value,
           sum(coalesce(d.amount,0)) allocated_discount
      FROM sales.sales_order_items i LEFT JOIN item_discounts d
        ON d.sales_order_id=i.sales_order_id AND d.sales_order_item_id=i.sales_order_item_id
     GROUP BY i.sales_order_id
)
SELECT count(*) FILTER (WHERE o.order_status='completed') completed_orders,
       count(DISTINCT i.sales_order_id) FILTER (WHERE o.order_status='completed') orders_with_items,
       coalesce(sum(i.units) FILTER (WHERE o.order_status='completed'),0) units_sold,
       coalesce(sum(i.gross_product_value) FILTER (WHERE o.order_status='completed'),0) gross_product_value,
       coalesce(sum(i.allocated_discount) FILTER (WHERE o.order_status='completed'),0) discount_amount,
       coalesce(sum(i.gross_product_value-i.allocated_discount) FILTER (WHERE o.order_status='completed'),0) net_product_value,
       coalesce(sum(o.shipping_amount) FILTER (WHERE o.order_status='completed'),0) shipping_charged,
       coalesce(sum(o.total_amount) FILTER (WHERE o.order_status='completed'),0) completed_order_total,
       coalesce(avg(o.total_amount) FILTER (WHERE o.order_status='completed'),0) average_completed_ticket
  FROM sales.sales_orders o LEFT JOIN order_items i USING(sales_order_id)""",
    "02_sales_monthly.sql": """WITH item_totals AS (
    SELECT sales_order_id, sum(quantity) units, sum(quantity*unit_sale_price) gross
      FROM sales.sales_order_items GROUP BY sales_order_id
)
SELECT to_char(o.placed_at AT TIME ZONE 'America/Sao_Paulo','YYYY-MM') year_month,
       o.order_status, o.channel_type, count(*) orders,
       coalesce(sum(i.units),0) units,
       sum(o.subtotal_amount) gross_order_product_value,
       sum(o.discount_amount) discount_amount,
       sum(o.subtotal_amount-o.discount_amount) net_product_value,
       sum(o.shipping_amount) shipping_charged,
       sum(o.total_amount) order_total
  FROM sales.sales_orders o LEFT JOIN item_totals i USING(sales_order_id)
 GROUP BY 1,2,3 ORDER BY 1,2,3""",
    "03_sales_by_channel.sql": """SELECT o.channel_type, c.channel_code, o.order_status,
       count(*) orders, count(DISTINCT o.customer_id) identified_customers,
       count(*) FILTER(WHERE o.customer_id IS NULL) anonymous_orders,
       sum(o.subtotal_amount) gross_product_value, sum(o.discount_amount) discount_amount,
       sum(o.subtotal_amount-o.discount_amount) net_product_value,
       sum(o.shipping_amount) shipping_charged, sum(o.total_amount) order_total,
       avg(o.total_amount) average_ticket
  FROM sales.sales_orders o JOIN sales.sales_channels c USING(sales_channel_id)
 GROUP BY 1,2,3 ORDER BY 1,2,3""",
    "04_sales_by_store.sql": """SELECT s.store_code,s.name,o.order_status,count(*) orders,
       sum(o.subtotal_amount) gross_product_value,sum(o.discount_amount) discount_amount,
       sum(o.subtotal_amount-o.discount_amount) net_product_value,
       sum(o.shipping_amount) shipping_charged,sum(o.total_amount) order_total,
       avg(o.total_amount) average_ticket
  FROM sales.sales_orders o JOIN core.stores s USING(store_id)
 WHERE o.channel_type='physical'
 GROUP BY 1,2,3 ORDER BY 1,3""",
    "05_sales_by_category.sql": """WITH item_discounts AS (
    SELECT sales_order_id,sales_order_item_id,sum(amount) amount
      FROM sales.applied_discounts GROUP BY sales_order_id,sales_order_item_id
)
SELECT c.category_code,c.name,o.order_status,count(DISTINCT o.sales_order_id) orders,
       count(*) order_items,sum(i.quantity) units,
       sum(i.quantity*i.unit_sale_price) gross_product_value,
       sum(coalesce(d.amount,0)) discount_amount,
       sum(i.quantity*i.unit_sale_price-coalesce(d.amount,0)) net_product_value
  FROM sales.sales_order_items i JOIN sales.sales_orders o USING(sales_order_id)
  JOIN catalog.products p USING(product_id) JOIN catalog.categories c USING(category_id)
  LEFT JOIN item_discounts d ON d.sales_order_id=i.sales_order_id AND d.sales_order_item_id=i.sales_order_item_id
 GROUP BY 1,2,3 ORDER BY 1,3""",
    "06_product_performance.sql": """WITH item_discounts AS (
    SELECT sales_order_id,sales_order_item_id,sum(amount) amount
      FROM sales.applied_discounts GROUP BY sales_order_id,sales_order_item_id
)
SELECT p.sku,p.name,c.category_code,o.order_status,count(DISTINCT o.sales_order_id) orders,
       count(*) order_items,sum(i.quantity) units,
       sum(i.quantity*i.unit_sale_price) gross_product_value,
       sum(coalesce(d.amount,0)) discount_amount,
       sum(i.quantity*i.unit_sale_price-coalesce(d.amount,0)) net_product_value
  FROM sales.sales_order_items i JOIN sales.sales_orders o USING(sales_order_id)
  JOIN catalog.products p USING(product_id) JOIN catalog.categories c USING(category_id)
  LEFT JOIN item_discounts d ON d.sales_order_id=i.sales_order_id AND d.sales_order_item_id=i.sales_order_item_id
 GROUP BY 1,2,3,4 ORDER BY units DESC,p.sku,o.order_status""",
    "07_customer_recurrence.sql": """WITH frequency AS (
    SELECT c.customer_id,c.customer_type,count(*) FILTER(WHERE o.order_status<>'cancelled') order_count,
           count(*) FILTER(WHERE o.order_status='completed') completed_orders,
           sum(o.total_amount) FILTER(WHERE o.order_status='completed') completed_order_value
      FROM crm.customers c LEFT JOIN sales.sales_orders o USING(customer_id)
     GROUP BY c.customer_id,c.customer_type
), bands AS (
    SELECT customer_type,CASE WHEN order_count=1 THEN '1'
         WHEN order_count BETWEEN 2 AND 4 THEN '2-4'
         WHEN order_count BETWEEN 5 AND 10 THEN '5-10' ELSE '11+' END recurrence_band,
         count(*) customers
      FROM frequency WHERE order_count>0 GROUP BY 1,2
)
SELECT customer_type,recurrence_band,customers,
       100.0*customers/sum(customers) OVER(PARTITION BY customer_type) customer_percent
  FROM bands ORDER BY customer_type,recurrence_band""",
    "08_payments_and_refunds.sql": """SELECT 'payment' record_type,m.method_type method_or_status,p.status,
       count(*) records,sum(p.amount) amount
  FROM payments.payments p JOIN payments.payment_methods m USING(payment_method_id)
 GROUP BY 1,2,3
UNION ALL
SELECT 'refund','refund',r.status,count(*),sum(r.amount)
  FROM payments.refunds r GROUP BY r.status
ORDER BY 1,2,3""",
    "09_returns.sql": """WITH return_items AS (
    SELECT return_id,min(stock_destination) FILTER(WHERE stock_destination IS NOT NULL) stock_destination,
           count(*) return_items,sum(quantity_requested) units_requested,
           sum(quantity_approved) units_approved,sum(quantity_received) units_received
      FROM after_sales.return_items GROUP BY return_id
), return_refunds AS (
    SELECT return_id,count(*) refund_rows,sum(amount) amount
      FROM payments.refunds WHERE status='completed' AND return_id IS NOT NULL GROUP BY return_id
), per_return AS (
    SELECT r.return_id,r.sales_order_id,r.status,ri.stock_destination,
           coalesce(ri.return_items,0) return_items,coalesce(ri.units_requested,0) units_requested,
           coalesce(ri.units_approved,0) units_approved,coalesce(ri.units_received,0) units_received,
           coalesce(rf.refund_rows,0) refund_rows,coalesce(rf.amount,0) refund_amount
      FROM after_sales.returns r LEFT JOIN return_items ri USING(return_id)
      LEFT JOIN return_refunds rf USING(return_id)
)
SELECT o.channel_type,coalesce(c.customer_type,'anonymous') customer_type,r.status return_status,
       r.stock_destination,count(*) returns,sum(r.return_items) return_items,
       sum(r.units_requested) units_requested,sum(r.units_approved) units_approved,
       sum(r.units_received) units_received,sum(r.refund_rows) refund_rows,sum(r.refund_amount) refund_amount
  FROM per_return r JOIN sales.sales_orders o USING(sales_order_id)
  LEFT JOIN crm.customers c USING(customer_id)
 GROUP BY 1,2,3,4 ORDER BY 1,2,3,4""",
    "10_inventory.sql": """SELECT l.location_code,l.name,c.category_code,
       count(*) positions,sum(p.on_hand_quantity) on_hand,
       sum(p.reserved_quantity) reserved,sum(p.available_quantity) available,
       sum(p.on_hand_quantity*p.average_unit_cost) inventory_value_at_average_cost
  FROM inventory.stock_positions p JOIN inventory.stock_locations l USING(stock_location_id)
  JOIN catalog.products pr USING(product_id) JOIN catalog.categories c USING(category_id)
 GROUP BY 1,2,3 ORDER BY 1,3""",
    "11_cost_and_margin.sql": """WITH item_discount AS (
    SELECT sales_order_id,sales_order_item_id,sum(amount) amount
      FROM sales.applied_discounts GROUP BY sales_order_id,sales_order_item_id
), return_units AS (
    SELECT source_fulfillment_item_id,sum(quantity_received) units
      FROM after_sales.return_items WHERE quantity_received>0 AND source_fulfillment_item_id IS NOT NULL
     GROUP BY source_fulfillment_item_id
), fulfillment_history_cost AS (
    SELECT fi.fulfillment_item_id,
           round(sum(abs(fm.quantity_delta)::numeric*fm.unit_cost)
             / nullif(sum(abs(fm.quantity_delta)),0),8) historical_unit_cost
      FROM logistics.fulfillment_items fi
      JOIN inventory.stock_movements fm ON fm.fulfillment_item_id=fi.fulfillment_item_id AND fm.movement_type='fulfillment'
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
), sales_cost AS (
    SELECT fi.fulfillment_item_id,fi.sales_order_id,fi.sales_order_item_id,
           fi.fulfilled_quantity,coalesce(ru.units,0) returned_units,
           sum(abs(m.quantity_delta)::numeric*m.unit_cost) full_cogs,
           coalesce(rc.sellable_cogs_reversal,0) sellable_cogs_reversal,
           coalesce(rc.non_sellable_loss,0) non_sellable_loss
      FROM logistics.fulfillment_items fi
      JOIN inventory.stock_movements m ON m.fulfillment_item_id=fi.fulfillment_item_id AND m.movement_type='fulfillment'
      LEFT JOIN return_units ru ON ru.source_fulfillment_item_id=fi.fulfillment_item_id
      LEFT JOIN return_cost rc ON rc.source_fulfillment_item_id=fi.fulfillment_item_id
     GROUP BY fi.fulfillment_item_id,fi.sales_order_id,fi.sales_order_item_id,fi.fulfilled_quantity,ru.units,
              rc.sellable_cogs_reversal,rc.non_sellable_loss
), item_margin AS (
    SELECT sc.sales_order_id,sc.sales_order_item_id,o.channel_type,c.category_code,
           CASE WHEN o.order_status='completed' THEN greatest(sc.fulfilled_quantity-sc.returned_units,0) ELSE 0 END net_units,
           CASE WHEN o.order_status='completed' THEN greatest(sc.fulfilled_quantity-sc.returned_units,0) ELSE 0 END::numeric *
               (i.unit_sale_price-coalesce(d.amount,0)/nullif(i.quantity,0)) net_commercial_revenue,
           sc.full_cogs,
           CASE WHEN o.order_status='completed' THEN sc.full_cogs ELSE 0 END completed_fulfillment_cogs,
           CASE WHEN o.order_status='completed' THEN sc.sellable_cogs_reversal ELSE 0 END sellable_cogs_reversal,
           CASE WHEN o.order_status='completed' THEN sc.non_sellable_loss ELSE 0 END non_sellable_loss,
           CASE WHEN o.order_status='completed' THEN sc.full_cogs-sc.sellable_cogs_reversal ELSE 0 END net_margin_cogs
      FROM sales_cost sc JOIN sales.sales_orders o USING(sales_order_id)
      JOIN sales.sales_order_items i USING(sales_order_id,sales_order_item_id)
      JOIN catalog.products p USING(product_id) JOIN catalog.categories c USING(category_id)
      LEFT JOIN item_discount d ON d.sales_order_id=i.sales_order_id AND d.sales_order_item_id=i.sales_order_item_id
)
SELECT channel_type,category_code,sum(net_units) fulfilled_units,
       sum(net_commercial_revenue) net_product_commercial_revenue,
       sum(full_cogs) canonical_fulfillment_cogs,sum(completed_fulfillment_cogs) completed_fulfillment_cogs,
       sum(sellable_cogs_reversal) sellable_cogs_reversed,sum(non_sellable_loss) non_sellable_return_loss,
       sum(net_margin_cogs) net_margin_cogs,
       sum(net_commercial_revenue)-sum(net_margin_cogs) gross_profit,
       (sum(net_commercial_revenue)-sum(net_margin_cogs))/nullif(sum(net_commercial_revenue),0) gross_margin_rate
  FROM item_margin GROUP BY channel_type,category_code ORDER BY channel_type,category_code""",
    "12_yoy_ytd.sql": """WITH scope AS (
    SELECT sales_order_id,(placed_at AT TIME ZONE 'America/Sao_Paulo')::date local_date,
           extract(year FROM placed_at AT TIME ZONE 'America/Sao_Paulo')::integer sales_year,
           order_status,subtotal_amount,discount_amount,shipping_amount,total_amount
      FROM sales.sales_orders
     WHERE (placed_at AT TIME ZONE 'America/Sao_Paulo')::date BETWEEN DATE '2025-01-01' AND DATE '2025-09-30'
        OR (placed_at AT TIME ZONE 'America/Sao_Paulo')::date BETWEEN DATE '2026-01-01' AND DATE '2026-09-30'
), item_units AS (
    SELECT i.sales_order_id,sum(i.quantity) units FROM sales.sales_order_items i GROUP BY i.sales_order_id
), payment_cash AS (
    SELECT p.sales_order_id,sum(p.amount) FILTER(WHERE p.status IN ('captured','settled')) captured
      FROM payments.payments p GROUP BY p.sales_order_id
), refunds AS (
    SELECT r.sales_order_id,sum(r.amount) FILTER(WHERE r.status='completed') refunded
      FROM payments.refunds r GROUP BY r.sales_order_id
), order_cogs AS (
    SELECT fi.sales_order_id,sum(abs(m.quantity_delta)::numeric*m.unit_cost) cogs
      FROM logistics.fulfillment_items fi JOIN inventory.stock_movements m
        ON m.fulfillment_item_id=fi.fulfillment_item_id AND m.movement_type='fulfillment'
     GROUP BY fi.sales_order_id
)
SELECT s.sales_year,count(*) orders,
       count(*) FILTER(WHERE s.order_status='completed') completed_orders,
       coalesce(sum(i.units) FILTER(WHERE s.order_status='completed'),0) units_sold,
       coalesce(sum(s.subtotal_amount) FILTER(WHERE s.order_status='completed'),0) gross_product_value,
       coalesce(sum(s.discount_amount) FILTER(WHERE s.order_status='completed'),0) discount_amount,
       coalesce(sum(s.subtotal_amount-s.discount_amount) FILTER(WHERE s.order_status='completed'),0) net_product_value,
       coalesce(sum(s.shipping_amount) FILTER(WHERE s.order_status='completed'),0) shipping_charged,
       coalesce(sum(s.total_amount) FILTER(WHERE s.order_status='completed'),0) order_total,sum(coalesce(p.captured,0)) captured_amount,
       coalesce(sum(coalesce(r.refunded,0)),0) refund_amount,
       sum(coalesce(p.captured,0))-sum(coalesce(r.refunded,0)) net_captured_amount,
       sum(coalesce(c.cogs,0)) realized_cogs,
       sum(s.subtotal_amount-s.discount_amount) FILTER(WHERE s.order_status='completed')-sum(coalesce(c.cogs,0)) gross_profit
  FROM scope s LEFT JOIN item_units i USING(sales_order_id)
  LEFT JOIN payment_cash p USING(sales_order_id) LEFT JOIN refunds r USING(sales_order_id)
  LEFT JOIN order_cogs c USING(sales_order_id)
 GROUP BY s.sales_year ORDER BY s.sales_year""",
}


def create_baseline_files(project_root: Path) -> Path:
    target = project_root / "database" / "queries" / "baselines"
    target.mkdir(parents=True, exist_ok=True)
    for filename, statement in BASELINE_QUERIES.items():
        (target / filename).write_text(statement.rstrip() + ";\n", encoding="utf-8")
    return target


def execute_baseline_files(connection, directory: Path) -> dict[str, list[tuple]]:
    """Run each reviewed, single-statement baseline and return bounded aggregate rows."""
    results: dict[str, list[tuple]] = {}
    for filename in sorted(BASELINE_QUERIES):
        path = directory / filename
        statement = path.read_text(encoding="utf-8").strip().rstrip(";")
        cursor = connection.execute(statement)
        rows = cursor.fetchall()
        if not rows:
            raise RuntimeError(f"Baseline SQL sem resultado: {filename}")
        results[filename] = rows
    counts = results["00_control_totals.sql"]
    if len(counts) != len(OPERATIONAL_TABLES):
        raise RuntimeError("Baseline de controle não retornou todas as tabelas operacionais aprovadas.")
    return results


def validate_baseline_results(results: dict[str, list[tuple]], portfolio_metrics: dict) -> dict[str, str]:
    """Reconcile baseline control, commercial totals, and canonical fulfillment COGS."""
    control = {name: count for name, count in results["00_control_totals.sql"]}
    if control != portfolio_metrics["table_counts"]:
        raise RuntimeError("Baseline de controle diverge das contagens lidas após COMMIT.")
    totals = results["01_sales_overview.sql"][0]
    finance = portfolio_metrics["financials"]
    # The baseline intentionally reports completed commercial orders only.
    if (totals[0],totals[3],totals[4],totals[5],totals[6],totals[7]) != (
        finance[0],finance[1],finance[2],finance[3],finance[4],finance[5]
    ):
        raise RuntimeError("Baseline comercial diverge dos totais independentes do relatório Portfolio.")
    payments = results["08_payments_and_refunds.sql"]
    baseline_captured = sum((row[4] for row in payments if row[0]=="payment" and row[2] in {"captured","settled"}), start=0)
    baseline_refunds = sum((row[4] for row in payments if row[0]=="refund" and row[2]=="completed"), start=0)
    if baseline_captured != finance[6] or baseline_refunds != finance[7]:
        raise RuntimeError("Baseline financeiro diverge das métricas SQL independentes.")
    cost_rows = results["11_cost_and_margin.sql"]
    baseline_cogs = sum((row[4] for row in cost_rows), start=0)
    if baseline_cogs != finance[8]:
        raise RuntimeError("Baseline COGS diverge do ledger canônico stock_movements/fulfillment.")
    completed_canonical_cogs = sum((row[5] for row in cost_rows), start=0)
    if completed_canonical_cogs != portfolio_metrics["margin"][1] + portfolio_metrics["margin_return_costs"][0]:
        raise RuntimeError("COGS completed do baseline diverge da reversão sellable e do COGS analítico.")
    baseline_margin_cogs = sum((row[8] for row in cost_rows), start=0)
    if baseline_margin_cogs != portfolio_metrics["margin"][1]:
        raise RuntimeError("Baseline COGS analítico diverge da margem operacional ajustada por devoluções sellable.")
    baseline_non_sellable_loss = sum((row[7] for row in cost_rows), start=0)
    if baseline_non_sellable_loss != portfolio_metrics["margin_return_costs"][1]:
        raise RuntimeError("Baseline de perda non-sellable diverge do custo histórico ponderado das linhas fulfillment de origem.")
    ytd_years = {row[0] for row in results["12_yoy_ytd.sql"]}
    if ytd_years != {2025, 2026}:
        raise RuntimeError("Baseline YTD não contém exatamente Jan–Set 2025 e Jan–Set 2026.")
    return {
        "00_control_totals.sql": "41 table counts reconcile",
        "01_sales_overview.sql": "completed orders, gross value, and discounts reconcile",
        "08_payments_and_refunds.sql": "captured payments and completed refunds reconcile",
        "11_cost_and_margin.sql": "canonical fulfillment COGS, adjusted margin COGS, and non-sellable return loss reconcile",
        "12_yoy_ytd.sql": "2025 and 2026 Jan-Sep available",
    }
