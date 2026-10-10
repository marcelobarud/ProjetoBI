WITH item_discounts AS (
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
  FROM sales.sales_orders o LEFT JOIN order_items i USING(sales_order_id);
