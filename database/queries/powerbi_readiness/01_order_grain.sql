-- Um resultado por pedido. Cada tabela filha é agregada à chave de pedido
-- antes dos joins, evitando multiplicação de valores entre itens, pagamentos e devoluções.
WITH item_discounts AS (
    SELECT sales_order_id, sales_order_item_id, sum(amount) AS allocated_discount
      FROM sales.applied_discounts
     GROUP BY sales_order_id, sales_order_item_id
), items_by_order AS (
    SELECT i.sales_order_id,
           count(*) AS item_lines,
           sum(i.quantity) AS ordered_units,
           sum(i.quantity * i.unit_sale_price) AS item_gross_value,
           sum(coalesce(d.allocated_discount, 0)) AS item_allocated_discount
      FROM sales.sales_order_items i
      LEFT JOIN item_discounts d
        ON d.sales_order_id = i.sales_order_id
       AND d.sales_order_item_id = i.sales_order_item_id
     GROUP BY i.sales_order_id
), payments_by_order AS (
    SELECT sales_order_id,
           count(*) AS payment_attempts,
           sum(amount) FILTER (WHERE status IN ('captured', 'settled')) AS captured_or_settled_amount
      FROM payments.payments
     GROUP BY sales_order_id
), refunds_by_order AS (
    SELECT sales_order_id,
           count(*) FILTER (WHERE status = 'completed') AS completed_refunds,
           sum(amount) FILTER (WHERE status = 'completed') AS completed_refund_amount
      FROM payments.refunds
     GROUP BY sales_order_id
), returns_by_order AS (
    SELECT r.sales_order_id,
           count(DISTINCT r.return_id) AS return_count,
           sum(ri.quantity_received) AS units_received
      FROM after_sales.returns r
      LEFT JOIN after_sales.return_items ri USING (sales_order_id, return_id)
     GROUP BY r.sales_order_id
)
SELECT o.sales_order_id,
       o.order_number,
       o.placed_at,
       (o.placed_at AT TIME ZONE 'America/Sao_Paulo')::date AS local_order_date,
       o.order_status,
       o.channel_type,
       ch.channel_code,
       c.customer_type,
       o.currency_code,
       o.subtotal_amount,
       o.discount_amount,
       o.shipping_amount,
       o.total_amount,
       coalesce(i.item_lines, 0) AS item_lines,
       coalesce(i.ordered_units, 0) AS ordered_units,
       coalesce(i.item_gross_value, 0) AS item_gross_value,
       coalesce(i.item_allocated_discount, 0) AS item_allocated_discount,
       coalesce(p.payment_attempts, 0) AS payment_attempts,
       coalesce(p.captured_or_settled_amount, 0) AS captured_or_settled_amount,
       coalesce(r.completed_refunds, 0) AS completed_refunds,
       coalesce(r.completed_refund_amount, 0) AS completed_refund_amount,
       coalesce(rt.return_count, 0) AS return_count,
       coalesce(rt.units_received, 0) AS units_received
  FROM sales.sales_orders o
  JOIN sales.sales_channels ch USING (sales_channel_id)
  LEFT JOIN crm.customers c USING (customer_id)
  LEFT JOIN items_by_order i USING (sales_order_id)
  LEFT JOIN payments_by_order p USING (sales_order_id)
  LEFT JOIN refunds_by_order r USING (sales_order_id)
  LEFT JOIN returns_by_order rt USING (sales_order_id)
 ORDER BY o.placed_at, o.sales_order_id;
