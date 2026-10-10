WITH return_items AS (
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
 GROUP BY 1,2,3,4 ORDER BY 1,2,3,4;
