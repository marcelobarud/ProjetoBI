DO $preflight$
DECLARE
    actual_schemas BIGINT;
    actual_tables BIGINT;
    row_total BIGINT := 0;
    relation RECORD;
    pk_count BIGINT;
    fk_count BIGINT;
    check_count BIGINT;
    unique_count BIGINT;
    index_total BIGINT;
BEGIN
    IF current_database() <> 'projeto_bi' OR current_setting('server_version') NOT LIKE '18.%' THEN
        RAISE EXCEPTION 'Preflight exige projeto_bi em PostgreSQL 18.x.';
    END IF;
    SELECT count(*) INTO actual_schemas FROM pg_namespace
     WHERE nspname !~ '^pg_' AND nspname NOT IN ('information_schema','public');
    IF actual_schemas <> 9 THEN RAISE EXCEPTION 'Preflight encontrou % schemas operacionais; esperado 9.', actual_schemas; END IF;
    SELECT count(*) INTO actual_tables FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace
     WHERE c.relkind IN ('r','p') AND n.nspname IN ('core','crm','catalog','sales','procurement','inventory','payments','logistics','after_sales');
    IF actual_tables <> 40 OR to_regclass('sales.sales_order_item_cancellations') IS NOT NULL THEN
        RAISE EXCEPTION 'Schema não está no estado exato anterior à migration 003; nenhuma alteração foi aplicada.';
    END IF;
    SELECT count(*) INTO index_total FROM pg_indexes
     WHERE schemaname IN ('core','crm','catalog','sales','procurement','inventory','payments','logistics','after_sales');
    IF index_total <> 149 THEN RAISE EXCEPTION 'Preflight encontrou % índices; esperado 149.', index_total; END IF;
    SELECT
        count(*) FILTER (WHERE contype='p'), count(*) FILTER (WHERE contype='f'),
        count(*) FILTER (WHERE contype='c'), count(*) FILTER (WHERE contype='u')
      INTO pk_count, fk_count, check_count, unique_count
      FROM pg_constraint c JOIN pg_class t ON t.oid=c.conrelid JOIN pg_namespace n ON n.oid=t.relnamespace
     WHERE n.nspname IN ('core','crm','catalog','sales','procurement','inventory','payments','logistics','after_sales');
    IF pk_count <> 40 OR fk_count <> 70 OR check_count <> 78 OR unique_count <> 37 THEN
        RAISE EXCEPTION 'Preflight encontrou contagens FK/CHECK/UNIQUE divergentes.';
    END IF;
    FOR relation IN SELECT schemaname, tablename FROM pg_tables
                     WHERE schemaname IN ('core','crm','catalog','sales','procurement','inventory','payments','logistics','after_sales')
    LOOP
        EXECUTE format('SELECT count(*) FROM %I.%I', relation.schemaname, relation.tablename) INTO row_total;
        IF row_total <> 0 THEN
            RAISE EXCEPTION 'Preflight encontrou dados em %.%; migration bloqueada.', relation.schemaname, relation.tablename;
        END IF;
    END LOOP;
    RAISE NOTICE 'Preflight 003 aprovado: estrutura anterior exata e 40 tabelas vazias.';
END;
$preflight$;
