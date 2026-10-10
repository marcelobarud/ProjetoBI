-- COGS can vary across fulfillment movements for one sales item. Returns are
-- aggregated to the order-item grain before joining to sales facts.
WITH item_discounts AS (
    SELECT sales_order_id, sales_order_item_id, sum(amount) AS discount_amount
      FROM sales.applied_discounts
     GROUP BY sales_order_id, sales_order_item_id
), fulfillment_quantity AS (
    SELECT sales_order_id, sales_order_item_id, sum(fulfilled_quantity) AS fulfilled_units
      FROM logistics.fulfillment_items
     GROUP BY sales_order_id, sales_order_item_id
), fulfillment_cost AS (
    SELECT fi.sales_order_id,
           fi.sales_order_item_id,
           sum(abs(m.quantity_delta)::numeric * m.unit_cost) AS original_fulfillment_cogs
      FROM logistics.fulfillment_items fi
      JOIN inventory.stock_movements m
        ON m.fulfillment_item_id = fi.fulfillment_item_id
       AND m.movement_type = 'fulfillment'
     GROUP BY fi.sales_order_id, fi.sales_order_item_id
), fulfillment_history AS (
    SELECT fi.fulfillment_item_id,
           sum(abs(m.quantity_delta)::numeric * m.unit_cost)
             / nullif(sum(abs(m.quantity_delta)), 0) AS weighted_historical_unit_cost
      FROM logistics.fulfillment_items fi
      JOIN inventory.stock_movements m
        ON m.fulfillment_item_id = fi.fulfillment_item_id
       AND m.movement_type = 'fulfillment'
     GROUP BY fi.fulfillment_item_id
), return_movement_cost AS (
    SELECT return_item_id,
           sum(abs(quantity_delta)::numeric * unit_cost) AS sellable_reversal
      FROM inventory.stock_movements
     WHERE movement_type = 'customer_return'
       AND return_item_id IS NOT NULL
     GROUP BY return_item_id
), returns_by_order_item AS (
    SELECT ri.sales_order_id,
           ri.sales_order_item_id,
           sum(ri.quantity_received) AS received_units,
           sum(coalesce(rmc.sellable_reversal, 0)) FILTER (
               WHERE ri.stock_destination = 'sellable'
           ) AS sellable_cogs_reversed,
           sum(ri.quantity_received * fh.weighted_historical_unit_cost) FILTER (
               WHERE ri.stock_destination IN ('quarantine', 'repair', 'discard')
           ) AS non_sellable_return_loss
      FROM after_sales.return_items ri
      JOIN fulfillment_history fh
        ON fh.fulfillment_item_id = ri.source_fulfillment_item_id
      LEFT JOIN return_movement_cost rmc USING (return_item_id)
     WHERE ri.quantity_received > 0
     GROUP BY ri.sales_order_id, ri.sales_order_item_id
), item_margin AS (
    SELECT o.channel_type,
           c.category_code,
           greatest(coalesce(fq.fulfilled_units, 0) - coalesce(rt.received_units, 0), 0) AS net_units,
           greatest(coalesce(fq.fulfilled_units, 0) - coalesce(rt.received_units, 0), 0)::numeric
             * (i.unit_sale_price - coalesce(d.discount_amount, 0) / nullif(i.quantity, 0)) AS net_product_revenue,
           coalesce(fc.original_fulfillment_cogs, 0) AS original_fulfillment_cogs,
           coalesce(rt.sellable_cogs_reversed, 0) AS sellable_cogs_reversed,
           coalesce(rt.non_sellable_return_loss, 0) AS non_sellable_return_loss
      FROM sales.sales_order_items i
      JOIN sales.sales_orders o USING (sales_order_id)
      JOIN catalog.products p USING (product_id)
      JOIN catalog.categories c USING (category_id)
      LEFT JOIN item_discounts d
        ON d.sales_order_id = i.sales_order_id
       AND d.sales_order_item_id = i.sales_order_item_id
      LEFT JOIN fulfillment_quantity fq
        ON fq.sales_order_id = i.sales_order_id
       AND fq.sales_order_item_id = i.sales_order_item_id
      LEFT JOIN fulfillment_cost fc
        ON fc.sales_order_id = i.sales_order_id
       AND fc.sales_order_item_id = i.sales_order_item_id
      LEFT JOIN returns_by_order_item rt
        ON rt.sales_order_id = i.sales_order_id
       AND rt.sales_order_item_id = i.sales_order_item_id
     WHERE o.order_status = 'completed'
)
SELECT channel_type,
       category_code,
       sum(net_units) AS net_units,
       sum(net_product_revenue) AS net_product_revenue,
       sum(original_fulfillment_cogs) AS original_fulfillment_cogs,
       sum(sellable_cogs_reversed) AS sellable_cogs_reversed,
       sum(original_fulfillment_cogs - sellable_cogs_reversed) AS analytical_cogs,
       sum(non_sellable_return_loss) AS non_sellable_return_loss,
       sum(net_product_revenue - (original_fulfillment_cogs - sellable_cogs_reversed)) AS gross_profit,
       (sum(net_product_revenue) - sum(original_fulfillment_cogs - sellable_cogs_reversed))
         / nullif(sum(net_product_revenue), 0) AS gross_margin_rate
  FROM item_margin
 GROUP BY channel_type, category_code
 ORDER BY channel_type, category_code;
