WITH item_totals AS (
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
 GROUP BY 1,2,3 ORDER BY 1,2,3;
