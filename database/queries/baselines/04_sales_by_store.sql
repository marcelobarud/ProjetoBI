SELECT s.store_code,s.name,o.order_status,count(*) orders,
       sum(o.subtotal_amount) gross_product_value,sum(o.discount_amount) discount_amount,
       sum(o.subtotal_amount-o.discount_amount) net_product_value,
       sum(o.shipping_amount) shipping_charged,sum(o.total_amount) order_total,
       avg(o.total_amount) average_ticket
  FROM sales.sales_orders o JOIN core.stores s USING(store_id)
 WHERE o.channel_type='physical'
 GROUP BY 1,2,3 ORDER BY 1,3;
