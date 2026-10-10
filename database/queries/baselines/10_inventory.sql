SELECT l.location_code,l.name,c.category_code,
       count(*) positions,sum(p.on_hand_quantity) on_hand,
       sum(p.reserved_quantity) reserved,sum(p.available_quantity) available,
       sum(p.on_hand_quantity*p.average_unit_cost) inventory_value_at_average_cost
  FROM inventory.stock_positions p JOIN inventory.stock_locations l USING(stock_location_id)
  JOIN catalog.products pr USING(product_id) JOIN catalog.categories c USING(category_id)
 GROUP BY 1,2,3 ORDER BY 1,3;
