-- Comparação anual parcial: 01/jan–30/set de 2025 contra o mesmo período de 2026.
-- Datas civis usam America/Sao_Paulo; YTD compara a mesma janela de calendário.
WITH order_scope AS (
    SELECT sales_order_id,
           (placed_at AT TIME ZONE 'America/Sao_Paulo')::date AS local_date,
           extract(year FROM placed_at AT TIME ZONE 'America/Sao_Paulo')::integer AS sales_year,
           order_status,
           subtotal_amount,
           discount_amount,
           shipping_amount,
           total_amount
      FROM sales.sales_orders
     WHERE (placed_at AT TIME ZONE 'America/Sao_Paulo')::date
           BETWEEN DATE '2025-01-01' AND DATE '2025-09-30'
        OR (placed_at AT TIME ZONE 'America/Sao_Paulo')::date
           BETWEEN DATE '2026-01-01' AND DATE '2026-09-30'
)
SELECT sales_year,
       count(*) AS all_orders,
       count(*) FILTER (WHERE order_status = 'completed') AS completed_orders,
       sum(subtotal_amount) FILTER (WHERE order_status = 'completed') AS gross_product_value,
       sum(discount_amount) FILTER (WHERE order_status = 'completed') AS discounts,
       sum(subtotal_amount - discount_amount) FILTER (WHERE order_status = 'completed') AS net_product_value,
       sum(shipping_amount) FILTER (WHERE order_status = 'completed') AS shipping_charged,
       sum(total_amount) FILTER (WHERE order_status = 'completed') AS completed_order_total
  FROM order_scope
 GROUP BY sales_year
 ORDER BY sales_year;
