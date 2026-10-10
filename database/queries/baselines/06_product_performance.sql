WITH item_discounts AS (
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
 GROUP BY 1,2,3,4 ORDER BY units DESC,p.sku,o.order_status;
