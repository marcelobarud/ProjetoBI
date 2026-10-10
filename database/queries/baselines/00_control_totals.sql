SELECT 'core.stores' AS table_name, count(*)::bigint AS row_count FROM core.stores
UNION ALL
SELECT 'core.employees' AS table_name, count(*)::bigint AS row_count FROM core.employees
UNION ALL
SELECT 'core.employee_roles' AS table_name, count(*)::bigint AS row_count FROM core.employee_roles
UNION ALL
SELECT 'core.employee_assignments' AS table_name, count(*)::bigint AS row_count FROM core.employee_assignments
UNION ALL
SELECT 'crm.customers' AS table_name, count(*)::bigint AS row_count FROM crm.customers
UNION ALL
SELECT 'crm.individual_profiles' AS table_name, count(*)::bigint AS row_count FROM crm.individual_profiles
UNION ALL
SELECT 'crm.business_profiles' AS table_name, count(*)::bigint AS row_count FROM crm.business_profiles
UNION ALL
SELECT 'crm.customer_contacts' AS table_name, count(*)::bigint AS row_count FROM crm.customer_contacts
UNION ALL
SELECT 'crm.customer_addresses' AS table_name, count(*)::bigint AS row_count FROM crm.customer_addresses
UNION ALL
SELECT 'catalog.categories' AS table_name, count(*)::bigint AS row_count FROM catalog.categories
UNION ALL
SELECT 'catalog.brands' AS table_name, count(*)::bigint AS row_count FROM catalog.brands
UNION ALL
SELECT 'catalog.products' AS table_name, count(*)::bigint AS row_count FROM catalog.products
UNION ALL
SELECT 'catalog.product_suppliers' AS table_name, count(*)::bigint AS row_count FROM catalog.product_suppliers
UNION ALL
SELECT 'catalog.product_prices' AS table_name, count(*)::bigint AS row_count FROM catalog.product_prices
UNION ALL
SELECT 'sales.sales_channels' AS table_name, count(*)::bigint AS row_count FROM sales.sales_channels
UNION ALL
SELECT 'sales.sales_orders' AS table_name, count(*)::bigint AS row_count FROM sales.sales_orders
UNION ALL
SELECT 'sales.sales_order_items' AS table_name, count(*)::bigint AS row_count FROM sales.sales_order_items
UNION ALL
SELECT 'sales.order_status_history' AS table_name, count(*)::bigint AS row_count FROM sales.order_status_history
UNION ALL
SELECT 'sales.applied_discounts' AS table_name, count(*)::bigint AS row_count FROM sales.applied_discounts
UNION ALL
SELECT 'sales.sales_order_item_cancellations' AS table_name, count(*)::bigint AS row_count FROM sales.sales_order_item_cancellations
UNION ALL
SELECT 'procurement.suppliers' AS table_name, count(*)::bigint AS row_count FROM procurement.suppliers
UNION ALL
SELECT 'procurement.purchase_orders' AS table_name, count(*)::bigint AS row_count FROM procurement.purchase_orders
UNION ALL
SELECT 'procurement.purchase_order_items' AS table_name, count(*)::bigint AS row_count FROM procurement.purchase_order_items
UNION ALL
SELECT 'procurement.goods_receipts' AS table_name, count(*)::bigint AS row_count FROM procurement.goods_receipts
UNION ALL
SELECT 'procurement.goods_receipt_items' AS table_name, count(*)::bigint AS row_count FROM procurement.goods_receipt_items
UNION ALL
SELECT 'inventory.stock_locations' AS table_name, count(*)::bigint AS row_count FROM inventory.stock_locations
UNION ALL
SELECT 'inventory.stock_positions' AS table_name, count(*)::bigint AS row_count FROM inventory.stock_positions
UNION ALL
SELECT 'inventory.stock_movements' AS table_name, count(*)::bigint AS row_count FROM inventory.stock_movements
UNION ALL
SELECT 'inventory.stock_reservations' AS table_name, count(*)::bigint AS row_count FROM inventory.stock_reservations
UNION ALL
SELECT 'inventory.stock_transfers' AS table_name, count(*)::bigint AS row_count FROM inventory.stock_transfers
UNION ALL
SELECT 'inventory.stock_transfer_items' AS table_name, count(*)::bigint AS row_count FROM inventory.stock_transfer_items
UNION ALL
SELECT 'payments.payment_methods' AS table_name, count(*)::bigint AS row_count FROM payments.payment_methods
UNION ALL
SELECT 'payments.payments' AS table_name, count(*)::bigint AS row_count FROM payments.payments
UNION ALL
SELECT 'payments.payment_installments' AS table_name, count(*)::bigint AS row_count FROM payments.payment_installments
UNION ALL
SELECT 'payments.refunds' AS table_name, count(*)::bigint AS row_count FROM payments.refunds
UNION ALL
SELECT 'logistics.carriers' AS table_name, count(*)::bigint AS row_count FROM logistics.carriers
UNION ALL
SELECT 'logistics.fulfillments' AS table_name, count(*)::bigint AS row_count FROM logistics.fulfillments
UNION ALL
SELECT 'logistics.fulfillment_items' AS table_name, count(*)::bigint AS row_count FROM logistics.fulfillment_items
UNION ALL
SELECT 'logistics.fulfillment_events' AS table_name, count(*)::bigint AS row_count FROM logistics.fulfillment_events
UNION ALL
SELECT 'after_sales.returns' AS table_name, count(*)::bigint AS row_count FROM after_sales.returns
UNION ALL
SELECT 'after_sales.return_items' AS table_name, count(*)::bigint AS row_count FROM after_sales.return_items
ORDER BY table_name;
