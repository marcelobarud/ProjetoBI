BEGIN;

DO $smoke$
DECLARE
    token TEXT := 'smoke-' || txid_current()::TEXT;
    event_time TIMESTAMPTZ := TIMESTAMPTZ '2026-01-15 12:00:00+00';
    customer_id_value BIGINT;
    physical_channel_id BIGINT;
    ecommerce_channel_id BIGINT;
    physical_order_id BIGINT;
    ecommerce_order_id BIGINT;
    second_order_id BIGINT;
    sales_item_id BIGINT;
    second_sales_item_id BIGINT;
    fulfillment_id_value BIGINT;
    second_fulfillment_id BIGINT;
    fulfillment_item_id_value BIGINT;
    second_fulfillment_item_id BIGINT;
    category_id_value BIGINT;
    product_id_value BIGINT;
    stock_location_id_value BIGINT;
    position_id_value BIGINT;
BEGIN
    INSERT INTO crm.customers (customer_code, customer_type, display_name, status, created_at, updated_at)
    VALUES (token, 'individual', 'Smoke Test', 'active', event_time, event_time)
    RETURNING customer_id INTO customer_id_value;

    INSERT INTO sales.sales_channels (channel_code, name, channel_type, is_active, created_at, updated_at)
    VALUES (token || '-physical', 'Smoke Physical', 'physical', TRUE, event_time, event_time)
    RETURNING sales_channel_id INTO physical_channel_id;
    INSERT INTO sales.sales_channels (channel_code, name, channel_type, is_active, created_at, updated_at)
    VALUES (token || '-ecommerce', 'Smoke Ecommerce', 'ecommerce', TRUE, event_time, event_time)
    RETURNING sales_channel_id INTO ecommerce_channel_id;

    -- Pedido físico anônimo válido.
    INSERT INTO sales.sales_orders (order_number, sales_channel_id, channel_type, order_status, placed_at, currency_code,
        subtotal_amount, discount_amount, shipping_amount, total_amount, created_at, updated_at)
    VALUES (token || '-order-physical', physical_channel_id, 'physical', 'placed', event_time, 'BRL', 10, 0, 0, 10, event_time, event_time)
    RETURNING sales_order_id INTO physical_order_id;

    -- Pedido ecommerce sem cliente precisa falhar.
    BEGIN
        INSERT INTO sales.sales_orders (order_number, sales_channel_id, channel_type, order_status, placed_at, currency_code,
            subtotal_amount, discount_amount, shipping_amount, total_amount, created_at, updated_at)
        VALUES (token || '-order-no-customer', ecommerce_channel_id, 'ecommerce', 'placed', event_time, 'BRL', 10, 0, 0, 10, event_time, event_time);
        RAISE EXCEPTION 'CHECK aceitou pedido ecommerce sem cliente.';
    EXCEPTION WHEN check_violation THEN
        NULL;
    END;

    INSERT INTO sales.sales_orders (order_number, sales_channel_id, channel_type, customer_id, order_status, placed_at, currency_code,
        subtotal_amount, discount_amount, shipping_amount, total_amount, created_at, updated_at)
    VALUES (token || '-order-ecommerce', ecommerce_channel_id, 'ecommerce', customer_id_value, 'placed', event_time, 'BRL', 20, 0, 0, 20, event_time, event_time)
    RETURNING sales_order_id INTO ecommerce_order_id;
    INSERT INTO sales.sales_orders (order_number, sales_channel_id, channel_type, order_status, placed_at, currency_code,
        subtotal_amount, discount_amount, shipping_amount, total_amount, created_at, updated_at)
    VALUES (token || '-order-second', physical_channel_id, 'physical', 'placed', event_time, 'BRL', 20, 0, 0, 20, event_time, event_time)
    RETURNING sales_order_id INTO second_order_id;

    -- Moeda diferente de BRL e valor monetário negativo precisam falhar.
    BEGIN
        INSERT INTO sales.sales_orders (order_number, sales_channel_id, channel_type, order_status, placed_at, currency_code,
            subtotal_amount, discount_amount, shipping_amount, total_amount, created_at, updated_at)
        VALUES (token || '-order-usd', physical_channel_id, 'physical', 'placed', event_time, 'USD', 10, 0, 0, 10, event_time, event_time);
        RAISE EXCEPTION 'CHECK aceitou moeda diferente de BRL.';
    EXCEPTION WHEN check_violation THEN NULL;
    END;
    BEGIN
        INSERT INTO sales.sales_orders (order_number, sales_channel_id, channel_type, order_status, placed_at, currency_code,
            subtotal_amount, discount_amount, shipping_amount, total_amount, created_at, updated_at)
        VALUES (token || '-order-negative', physical_channel_id, 'physical', 'placed', event_time, 'BRL', -1, 0, 0, 0, event_time, event_time);
        RAISE EXCEPTION 'CHECK aceitou valor monetário negativo.';
    EXCEPTION WHEN check_violation THEN NULL;
    END;

    INSERT INTO catalog.categories (category_code, name, is_active, created_at, updated_at)
    VALUES (token, 'Smoke Category', TRUE, event_time, event_time)
    RETURNING category_id INTO category_id_value;
    INSERT INTO catalog.products (sku, category_id, name, specifications, unit_of_measure, status, created_at, updated_at)
    VALUES (token, category_id_value, 'Smoke Product', '{"memory_gb": 16}'::JSONB, 'UN', 'active', event_time, event_time)
    RETURNING product_id INTO product_id_value;
    BEGIN
        INSERT INTO catalog.products (sku, category_id, name, specifications, unit_of_measure, status, created_at, updated_at)
        VALUES (token || '-array', category_id_value, 'Invalid JSON Shape', '[1,2]'::JSONB, 'UN', 'active', event_time, event_time);
        RAISE EXCEPTION 'CHECK aceitou array em specifications.';
    EXCEPTION WHEN check_violation THEN NULL;
    END;

    INSERT INTO inventory.stock_locations (location_code, name, location_type, status, created_at, updated_at)
    VALUES (token, 'Smoke Location', 'warehouse', 'active', event_time, event_time)
    RETURNING stock_location_id INTO stock_location_id_value;

    INSERT INTO sales.sales_order_items (sales_order_id, line_number, product_id, sku_snapshot, product_name_snapshot, quantity, unit_sale_price, created_at)
    VALUES (ecommerce_order_id, 1, product_id_value, token, 'Smoke Product', 1, 20, event_time)
    RETURNING sales_order_item_id INTO sales_item_id;
    INSERT INTO sales.sales_order_items (sales_order_id, line_number, product_id, sku_snapshot, product_name_snapshot, quantity, unit_sale_price, created_at)
    VALUES (second_order_id, 1, product_id_value, token, 'Smoke Product', 1, 20, event_time)
    RETURNING sales_order_item_id INTO second_sales_item_id;

    INSERT INTO logistics.fulfillments (sales_order_id, fulfillment_number, fulfillment_type, status, created_at, updated_at)
    VALUES (ecommerce_order_id, token || '-fulfillment-a', 'delivery', 'pending', event_time, event_time)
    RETURNING fulfillment_id INTO fulfillment_id_value;
    INSERT INTO logistics.fulfillments (sales_order_id, fulfillment_number, fulfillment_type, status, created_at, updated_at)
    VALUES (second_order_id, token || '-fulfillment-b', 'delivery', 'pending', event_time, event_time)
    RETURNING fulfillment_id INTO second_fulfillment_id;
    INSERT INTO logistics.fulfillment_items (sales_order_id, fulfillment_id, sales_order_item_id, quantity_allocated, fulfilled_quantity, created_at, updated_at)
    VALUES (ecommerce_order_id, fulfillment_id_value, sales_item_id, 1, 1, event_time, event_time)
    RETURNING fulfillment_item_id INTO fulfillment_item_id_value;
    INSERT INTO logistics.fulfillment_items (sales_order_id, fulfillment_id, sales_order_item_id, quantity_allocated, fulfilled_quantity, created_at, updated_at)
    VALUES (second_order_id, second_fulfillment_id, second_sales_item_id, 1, 1, event_time, event_time)
    RETURNING fulfillment_item_id INTO second_fulfillment_item_id;

    INSERT INTO after_sales.returns (sales_order_id, return_number, status, reason_code, requested_at, created_at, updated_at)
    VALUES (ecommerce_order_id, token || '-return', 'requested', 'buyer_remorse', event_time, event_time, event_time);
    -- Recupera a devolução criada nesta transação, cujo número é único por pedido.
    BEGIN
        INSERT INTO after_sales.return_items (sales_order_id, return_id, sales_order_item_id, source_fulfillment_item_id,
            quantity_requested, quantity_approved, quantity_received, created_at)
        SELECT ecommerce_order_id, r.return_id, second_sales_item_id, NULL, 1, 0, 0, event_time
        FROM after_sales.returns r WHERE r.sales_order_id=ecommerce_order_id AND r.return_number=token || '-return';
        RAISE EXCEPTION 'FK composta aceitou item de outro pedido na devolução.';
    EXCEPTION WHEN foreign_key_violation THEN NULL;
    END;
    BEGIN
        INSERT INTO after_sales.return_items (sales_order_id, return_id, sales_order_item_id, source_fulfillment_item_id,
            quantity_requested, quantity_approved, quantity_received, created_at)
        SELECT ecommerce_order_id, r.return_id, sales_item_id, second_fulfillment_item_id, 1, 0, 0, event_time
        FROM after_sales.returns r WHERE r.sales_order_id=ecommerce_order_id AND r.return_number=token || '-return';
        RAISE EXCEPTION 'FK composta aceitou fulfillment de outro pedido/item.';
    EXCEPTION WHEN foreign_key_violation THEN NULL;
    END;

    INSERT INTO inventory.stock_positions (product_id, stock_location_id, on_hand_quantity, reserved_quantity, average_unit_cost, updated_at)
    VALUES (product_id_value, stock_location_id_value, 5, 2, 1.25000000, event_time)
    ON CONFLICT (product_id, stock_location_id) DO NOTHING;
    SELECT available_quantity INTO position_id_value FROM inventory.stock_positions
    WHERE product_id=product_id_value AND stock_location_id=stock_location_id_value;
    IF position_id_value <> 3 THEN
        RAISE EXCEPTION 'available_quantity deveria ser 3, atual %.', position_id_value;
    END IF;
END;
$smoke$;

ROLLBACK;
