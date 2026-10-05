DO $validate$
DECLARE
    actual_count BIGINT;
    expected_count BIGINT;
    missing_names TEXT;
    unexpected_names TEXT;
BEGIN
    IF current_database() <> 'projeto_bi' THEN
        RAISE EXCEPTION 'Database incorreta: esperado projeto_bi, atual %', current_database();
    END IF;

    WITH expected(schema_name) AS (VALUES
        ('core'), ('crm'), ('catalog'), ('sales'), ('procurement'),
        ('inventory'), ('payments'), ('logistics'), ('after_sales')
    ), actual AS (
        SELECT nspname AS schema_name
        FROM pg_namespace
        WHERE nspname NOT LIKE 'pg\_%' ESCAPE '\'
          AND nspname NOT IN ('information_schema', 'public')
    )
    SELECT
        (SELECT count(*) FROM expected),
        (SELECT count(*) FROM actual),
        (SELECT string_agg(schema_name, ', ') FROM (SELECT schema_name FROM expected EXCEPT SELECT schema_name FROM actual) x),
        (SELECT string_agg(schema_name, ', ') FROM (SELECT schema_name FROM actual EXCEPT SELECT schema_name FROM expected) x)
    INTO expected_count, actual_count, missing_names, unexpected_names;
    IF actual_count <> expected_count OR missing_names IS NOT NULL OR unexpected_names IS NOT NULL THEN
        RAISE EXCEPTION 'Schemas divergentes: esperado %, encontrado %, ausentes [%], inesperados [%]', expected_count, actual_count, missing_names, unexpected_names;
    END IF;

    WITH expected(schema_name, table_name) AS (VALUES
        ('core','stores'), ('core','employees'), ('core','employee_roles'), ('core','employee_assignments'),
        ('crm','customers'), ('crm','individual_profiles'), ('crm','business_profiles'), ('crm','customer_contacts'), ('crm','customer_addresses'),
        ('catalog','categories'), ('catalog','brands'), ('catalog','products'), ('catalog','product_suppliers'), ('catalog','product_prices'),
        ('sales','sales_channels'), ('sales','sales_orders'), ('sales','sales_order_items'), ('sales','order_status_history'), ('sales','applied_discounts'),
        ('procurement','suppliers'), ('procurement','purchase_orders'), ('procurement','purchase_order_items'), ('procurement','goods_receipts'), ('procurement','goods_receipt_items'),
        ('inventory','stock_locations'), ('inventory','stock_positions'), ('inventory','stock_movements'), ('inventory','stock_reservations'), ('inventory','stock_transfers'), ('inventory','stock_transfer_items'),
        ('payments','payment_methods'), ('payments','payments'), ('payments','payment_installments'), ('payments','refunds'),
        ('logistics','carriers'), ('logistics','fulfillments'), ('logistics','fulfillment_items'), ('logistics','fulfillment_events'),
        ('after_sales','returns'), ('after_sales','return_items')
    ), actual AS (
        SELECT n.nspname AS schema_name, c.relname AS table_name
        FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace
        WHERE c.relkind IN ('r','p')
          AND n.nspname IN ('core','crm','catalog','sales','procurement','inventory','payments','logistics','after_sales')
    )
    SELECT
        (SELECT count(*) FROM expected),
        (SELECT count(*) FROM actual),
        (SELECT string_agg(schema_name || '.' || table_name, ', ') FROM (SELECT schema_name, table_name FROM expected EXCEPT SELECT schema_name, table_name FROM actual) x),
        (SELECT string_agg(schema_name || '.' || table_name, ', ') FROM (SELECT schema_name, table_name FROM actual EXCEPT SELECT schema_name, table_name FROM expected) x)
    INTO expected_count, actual_count, missing_names, unexpected_names;
    IF expected_count <> 40 OR actual_count <> expected_count OR missing_names IS NOT NULL OR unexpected_names IS NOT NULL THEN
        RAISE EXCEPTION 'Tabelas divergentes: esperado %, encontrado %, ausentes [%], inesperadas [%]', expected_count, actual_count, missing_names, unexpected_names;
    END IF;

    IF EXISTS (
        SELECT 1 FROM (VALUES
            ('core',4), ('crm',5), ('catalog',5), ('sales',5), ('procurement',5),
            ('inventory',6), ('payments',4), ('logistics',4), ('after_sales',2)
        ) AS e(schema_name, expected_tables)
        LEFT JOIN pg_class c ON c.relnamespace = to_regnamespace(e.schema_name) AND c.relkind IN ('r','p')
        GROUP BY e.schema_name, e.expected_tables
        HAVING count(c.oid) <> e.expected_tables
    ) THEN
        RAISE EXCEPTION 'Quantidade de tabelas por schema diverge do dicionário.';
    END IF;

    SELECT count(*) INTO actual_count
    FROM pg_constraint c
    JOIN pg_class t ON t.oid = c.conrelid
    JOIN pg_namespace n ON n.oid = t.relnamespace
    WHERE n.nspname IN ('core','crm','catalog','sales','procurement','inventory','payments','logistics','after_sales')
      AND c.contype = 'p';
    IF actual_count <> 40 THEN RAISE EXCEPTION 'Esperadas 40 PKs, encontradas %.', actual_count; END IF;

    SELECT count(*) INTO actual_count
    FROM pg_constraint c
    JOIN pg_class t ON t.oid = c.conrelid
    JOIN pg_namespace n ON n.oid = t.relnamespace
    WHERE n.nspname IN ('core','crm','catalog','sales','procurement','inventory','payments','logistics','after_sales')
      AND c.contype = 'f';
    IF actual_count <> 70 THEN RAISE EXCEPTION 'Esperadas 70 FKs, encontradas %.', actual_count; END IF;

    SELECT count(*) INTO actual_count
    FROM pg_constraint c
    JOIN pg_class t ON t.oid = c.conrelid
    JOIN pg_namespace n ON n.oid = t.relnamespace
    WHERE n.nspname IN ('core','crm','catalog','sales','procurement','inventory','payments','logistics','after_sales')
      AND c.contype = 'c';
    IF actual_count <> 75 THEN RAISE EXCEPTION 'Esperados 75 CHECKs, encontrados %.', actual_count; END IF;

    SELECT count(*) INTO actual_count
    FROM pg_constraint c
    JOIN pg_class t ON t.oid = c.conrelid
    JOIN pg_namespace n ON n.oid = t.relnamespace
    WHERE n.nspname IN ('core','crm','catalog','sales','procurement','inventory','payments','logistics','after_sales')
      AND c.contype = 'u';
    IF actual_count <> 37 THEN RAISE EXCEPTION 'Esperadas 37 constraints UNIQUE, encontradas %.', actual_count; END IF;

    IF (SELECT count(*) FROM pg_indexes WHERE schemaname IN ('core','crm','catalog','sales','procurement','inventory','payments','logistics','after_sales')) <> 148 THEN
        RAISE EXCEPTION 'Esperados 148 índices físicos (PK, UNIQUE e índices declarados).';
    END IF;

    IF (SELECT count(*) FROM information_schema.columns
        WHERE table_schema IN ('core','crm','catalog','sales','procurement','inventory','payments','logistics','after_sales')
          AND column_name = 'available_quantity' AND table_name = 'stock_positions'
          AND data_type = 'bigint' AND is_generated = 'ALWAYS') <> 1 THEN
        RAISE EXCEPTION 'stock_positions.available_quantity não é BIGINT GENERATED STORED.';
    END IF;
    IF (SELECT count(*) FROM information_schema.columns WHERE table_schema='catalog' AND table_name='products' AND column_name='specifications' AND udt_name='jsonb' AND is_nullable='YES') <> 1
       OR NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname='ck_products_specifications_object') THEN
        RAISE EXCEPTION 'catalog.products.specifications deve ser JSONB nullable.';
    END IF;
    IF (SELECT count(*) FROM information_schema.columns WHERE table_schema='after_sales' AND table_name='return_items' AND column_name='source_fulfillment_item_id' AND data_type='bigint') <> 1 THEN
        RAISE EXCEPTION 'return_items.source_fulfillment_item_id está ausente ou tem tipo incorreto.';
    END IF;
    IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema IN ('sales','inventory') AND column_name='unit_cost_snapshot') THEN
        RAISE EXCEPTION 'unit_cost_snapshot não deve existir.';
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname='ck_sales_orders_currency' AND pg_get_constraintdef(oid) LIKE '%BRL%')
       OR NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname='ck_purchase_orders_currency' AND pg_get_constraintdef(oid) LIKE '%BRL%')
       OR NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname='ck_payments_currency' AND pg_get_constraintdef(oid) LIKE '%BRL%') THEN
        RAISE EXCEPTION 'CHECK de BRL não encontrado em vendas, compras e pagamentos.';
    END IF;

    IF (SELECT count(*) FROM pg_constraint WHERE conname IN (
        'fk_sales_orders_sales_channel_type', 'fk_applied_discounts_order_items',
        'fk_goods_receipt_items_receipts', 'fk_goods_receipt_items_purchase_items',
        'fk_stock_reservations_order_items', 'fk_refunds_payments', 'fk_refunds_returns',
        'fk_fulfillment_items_fulfillments', 'fk_fulfillment_items_order_items',
        'fk_return_items_returns', 'fk_return_items_order_items', 'fk_return_items_source_fulfillments'
    )) <> 12 THEN
        RAISE EXCEPTION 'FKs compostas críticas estão ausentes.';
    END IF;

    IF (SELECT count(*) FROM pg_indexes WHERE indexname IN (
        'idx_stock_movements_product_location_time', 'idx_stock_movements_fulfillment_item',
        'idx_fulfillment_items_order_item', 'idx_return_items_source_fulfillment',
        'idx_sales_orders_customer_placed', 'idx_goods_receipts_purchase_time',
        'idx_product_prices_product_channel_from', 'idx_returns_order_requested'
    )) <> 8 THEN
        RAISE EXCEPTION 'Índices essenciais de consulta/rastreabilidade estão ausentes.';
    END IF;

    RAISE NOTICE 'Validação estrutural aprovada: database projeto_bi, 9 schemas, 40 tabelas, PK/FK/CHECK/UNIQUE e índices conferidos.';
END;
$validate$;
