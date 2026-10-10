-- Posição corrente, não uma fotografia histórica. Não somar snapshots de datas distintas.
SELECT l.stock_location_id,
       l.location_code,
       l.name AS location_name,
       p.product_id,
       pr.sku,
       pr.name AS product_name,
       c.category_code,
       p.on_hand_quantity,
       p.reserved_quantity,
       p.available_quantity,
       p.average_unit_cost,
       p.on_hand_quantity * p.average_unit_cost AS on_hand_value_at_average_cost,
       p.updated_at AS position_updated_at
  FROM inventory.stock_positions p
  JOIN inventory.stock_locations l USING (stock_location_id)
  JOIN catalog.products pr USING (product_id)
  JOIN catalog.categories c USING (category_id)
 ORDER BY l.location_code, pr.sku;
