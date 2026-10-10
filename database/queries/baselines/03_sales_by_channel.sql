SELECT o.channel_type, c.channel_code, o.order_status,
       count(*) orders, count(DISTINCT o.customer_id) identified_customers,
       count(*) FILTER(WHERE o.customer_id IS NULL) anonymous_orders,
       sum(o.subtotal_amount) gross_product_value, sum(o.discount_amount) discount_amount,
       sum(o.subtotal_amount-o.discount_amount) net_product_value,
       sum(o.shipping_amount) shipping_charged, sum(o.total_amount) order_total,
       avg(o.total_amount) average_ticket
  FROM sales.sales_orders o JOIN sales.sales_channels c USING(sales_channel_id)
 GROUP BY 1,2,3 ORDER BY 1,2,3;
