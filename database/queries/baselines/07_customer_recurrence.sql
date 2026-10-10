WITH frequency AS (
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
  FROM bands ORDER BY customer_type,recurrence_band;
