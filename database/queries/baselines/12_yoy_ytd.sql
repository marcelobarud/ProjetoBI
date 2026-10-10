WITH scope AS (
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
 GROUP BY s.sales_year ORDER BY s.sales_year;
