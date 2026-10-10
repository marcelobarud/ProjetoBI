WITH item_discount AS (
    SELECT sales_order_id,sales_order_item_id,sum(amount) amount
      FROM sales.applied_discounts GROUP BY sales_order_id,sales_order_item_id
), return_units AS (
    SELECT source_fulfillment_item_id,sum(quantity_received) units
      FROM after_sales.return_items WHERE quantity_received>0 AND source_fulfillment_item_id IS NOT NULL
     GROUP BY source_fulfillment_item_id
), fulfillment_history_cost AS (
    SELECT fi.fulfillment_item_id,
           round(sum(abs(fm.quantity_delta)::numeric*fm.unit_cost)
             / nullif(sum(abs(fm.quantity_delta)),0),8) historical_unit_cost
      FROM logistics.fulfillment_items fi
      JOIN inventory.stock_movements fm ON fm.fulfillment_item_id=fi.fulfillment_item_id AND fm.movement_type='fulfillment'
     GROUP BY fi.fulfillment_item_id
), return_movement_cost AS (
    SELECT return_item_id,sum(abs(m.quantity_delta)::numeric*m.unit_cost) cost
      FROM inventory.stock_movements m
     WHERE m.movement_type='customer_return' AND m.return_item_id IS NOT NULL
     GROUP BY return_item_id
), return_cost AS (
    SELECT ri.source_fulfillment_item_id,
           coalesce(sum(coalesce(rmc.cost,0))
             FILTER (WHERE ri.stock_destination='sellable'),0) sellable_cogs_reversal,
           coalesce(sum(ri.quantity_received*fh.historical_unit_cost)
             FILTER (WHERE ri.stock_destination IN ('quarantine','repair','discard')),0) non_sellable_loss
      FROM after_sales.return_items ri
      JOIN fulfillment_history_cost fh ON fh.fulfillment_item_id=ri.source_fulfillment_item_id
      LEFT JOIN return_movement_cost rmc ON rmc.return_item_id=ri.return_item_id
     WHERE ri.quantity_received>0
     GROUP BY ri.source_fulfillment_item_id
), sales_cost AS (
    SELECT fi.fulfillment_item_id,fi.sales_order_id,fi.sales_order_item_id,
           fi.fulfilled_quantity,coalesce(ru.units,0) returned_units,
           sum(abs(m.quantity_delta)::numeric*m.unit_cost) full_cogs,
           coalesce(rc.sellable_cogs_reversal,0) sellable_cogs_reversal,
           coalesce(rc.non_sellable_loss,0) non_sellable_loss
      FROM logistics.fulfillment_items fi
      JOIN inventory.stock_movements m ON m.fulfillment_item_id=fi.fulfillment_item_id AND m.movement_type='fulfillment'
      LEFT JOIN return_units ru ON ru.source_fulfillment_item_id=fi.fulfillment_item_id
      LEFT JOIN return_cost rc ON rc.source_fulfillment_item_id=fi.fulfillment_item_id
     GROUP BY fi.fulfillment_item_id,fi.sales_order_id,fi.sales_order_item_id,fi.fulfilled_quantity,ru.units,
              rc.sellable_cogs_reversal,rc.non_sellable_loss
), item_margin AS (
    SELECT sc.sales_order_id,sc.sales_order_item_id,o.channel_type,c.category_code,
           CASE WHEN o.order_status='completed' THEN greatest(sc.fulfilled_quantity-sc.returned_units,0) ELSE 0 END net_units,
           CASE WHEN o.order_status='completed' THEN greatest(sc.fulfilled_quantity-sc.returned_units,0) ELSE 0 END::numeric *
               (i.unit_sale_price-coalesce(d.amount,0)/nullif(i.quantity,0)) net_commercial_revenue,
           sc.full_cogs,
           CASE WHEN o.order_status='completed' THEN sc.full_cogs ELSE 0 END completed_fulfillment_cogs,
           CASE WHEN o.order_status='completed' THEN sc.sellable_cogs_reversal ELSE 0 END sellable_cogs_reversal,
           CASE WHEN o.order_status='completed' THEN sc.non_sellable_loss ELSE 0 END non_sellable_loss,
           CASE WHEN o.order_status='completed' THEN sc.full_cogs-sc.sellable_cogs_reversal ELSE 0 END net_margin_cogs
      FROM sales_cost sc JOIN sales.sales_orders o USING(sales_order_id)
      JOIN sales.sales_order_items i USING(sales_order_id,sales_order_item_id)
      JOIN catalog.products p USING(product_id) JOIN catalog.categories c USING(category_id)
      LEFT JOIN item_discount d ON d.sales_order_id=i.sales_order_id AND d.sales_order_item_id=i.sales_order_item_id
)
SELECT channel_type,category_code,sum(net_units) fulfilled_units,
       sum(net_commercial_revenue) net_product_commercial_revenue,
       sum(full_cogs) canonical_fulfillment_cogs,sum(completed_fulfillment_cogs) completed_fulfillment_cogs,
       sum(sellable_cogs_reversal) sellable_cogs_reversed,sum(non_sellable_loss) non_sellable_return_loss,
       sum(net_margin_cogs) net_margin_cogs,
       sum(net_commercial_revenue)-sum(net_margin_cogs) gross_profit,
       (sum(net_commercial_revenue)-sum(net_margin_cogs))/nullif(sum(net_commercial_revenue),0) gross_margin_rate
  FROM item_margin GROUP BY channel_type,category_code ORDER BY channel_type,category_code;
