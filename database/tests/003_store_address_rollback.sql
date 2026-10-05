BEGIN;

DO $store_address_test$
DECLARE
    token TEXT := 'T' || substr(md5(txid_current()::TEXT), 1, 8);
    event_time TIMESTAMPTZ := TIMESTAMPTZ '2026-09-15 12:00:00-03';
    store_id_value BIGINT;
    violated_constraint TEXT;
    violated_column TEXT;
BEGIN
    INSERT INTO core.stores (
        store_code, name, status, postal_code, street, street_number, complement,
        district, city, state_code, country_code, created_at, updated_at
    ) VALUES (
        token || '-valid', 'Loja temporária de validação', 'active', '01001000',
        'Praça da Sé', '1', NULL, 'Sé', 'São Paulo', 'SP', 'BR', event_time, event_time
    ) RETURNING store_id INTO store_id_value;

    IF NOT EXISTS (
        SELECT 1 FROM core.stores
        WHERE store_id = store_id_value AND postal_code = '01001000'
          AND city = 'São Paulo' AND state_code = 'SP' AND country_code = 'BR'
    ) THEN
        RAISE EXCEPTION 'Endereço válido não foi persistido durante o teste.';
    END IF;

    BEGIN
        INSERT INTO core.stores (store_code,name,status,postal_code,street,street_number,district,city,state_code,country_code,created_at,updated_at)
        VALUES (token||'-letters','Teste','active','01A01000','Rua Teste','1','Centro','Brasília','DF','BR',event_time,event_time);
        RAISE EXCEPTION 'CHECK aceitou CEP com letras.';
    EXCEPTION WHEN check_violation THEN
        GET STACKED DIAGNOSTICS violated_constraint = CONSTRAINT_NAME;
        IF violated_constraint <> 'ck_stores_postal_code' THEN RAISE; END IF;
    END;
    BEGIN
        INSERT INTO core.stores (store_code,name,status,postal_code,street,street_number,district,city,state_code,country_code,created_at,updated_at)
        VALUES (token||'-short','Teste','active','1234567','Rua Teste','1','Centro','Brasília','DF','BR',event_time,event_time);
        RAISE EXCEPTION 'CHECK aceitou CEP com quantidade diferente de oito dígitos.';
    EXCEPTION WHEN check_violation THEN
        GET STACKED DIAGNOSTICS violated_constraint = CONSTRAINT_NAME;
        IF violated_constraint <> 'ck_stores_postal_code' THEN RAISE; END IF;
    END;
    BEGIN
        INSERT INTO core.stores (store_code,name,status,postal_code,street,street_number,district,city,state_code,country_code,created_at,updated_at)
        VALUES (token||'-uf','Teste','active','01001000','Rua Teste','1','Centro','Brasília','XX','BR',event_time,event_time);
        RAISE EXCEPTION 'CHECK aceitou UF inválida.';
    EXCEPTION WHEN check_violation THEN
        GET STACKED DIAGNOSTICS violated_constraint = CONSTRAINT_NAME;
        IF violated_constraint <> 'ck_stores_state_code' THEN RAISE; END IF;
    END;
    BEGIN
        INSERT INTO core.stores (store_code,name,status,postal_code,street,street_number,district,city,state_code,country_code,created_at,updated_at)
        VALUES (token||'-country','Teste','active','01001000','Rua Teste','1','Centro','Brasília','DF','AR',event_time,event_time);
        RAISE EXCEPTION 'CHECK aceitou país diferente de BR.';
    EXCEPTION WHEN check_violation THEN
        GET STACKED DIAGNOSTICS violated_constraint = CONSTRAINT_NAME;
        IF violated_constraint <> 'ck_stores_country_code' THEN RAISE; END IF;
    END;

    BEGIN
        INSERT INTO core.stores (store_code,name,status,street,street_number,district,city,state_code,country_code,created_at,updated_at)
        VALUES (token||'-null-postal','Teste','active','Rua Teste','1','Centro','Brasília','DF','BR',event_time,event_time);
        RAISE EXCEPTION 'NOT NULL não rejeitou postal_code nulo.';
    EXCEPTION WHEN not_null_violation THEN
        GET STACKED DIAGNOSTICS violated_column = COLUMN_NAME;
        IF violated_column <> 'postal_code' THEN RAISE; END IF;
    END;
    BEGIN
        INSERT INTO core.stores (store_code,name,status,postal_code,street_number,district,city,state_code,country_code,created_at,updated_at)
        VALUES (token||'-null-street','Teste','active','01001000','1','Centro','Brasília','DF','BR',event_time,event_time);
        RAISE EXCEPTION 'NOT NULL não rejeitou street nulo.';
    EXCEPTION WHEN not_null_violation THEN
        GET STACKED DIAGNOSTICS violated_column = COLUMN_NAME;
        IF violated_column <> 'street' THEN RAISE; END IF;
    END;
    BEGIN
        INSERT INTO core.stores (store_code,name,status,postal_code,street,district,city,state_code,country_code,created_at,updated_at)
        VALUES (token||'-null-number','Teste','active','01001000','Rua Teste','Centro','Brasília','DF','BR',event_time,event_time);
        RAISE EXCEPTION 'NOT NULL não rejeitou street_number nulo.';
    EXCEPTION WHEN not_null_violation THEN
        GET STACKED DIAGNOSTICS violated_column = COLUMN_NAME;
        IF violated_column <> 'street_number' THEN RAISE; END IF;
    END;
    BEGIN
        INSERT INTO core.stores (store_code,name,status,postal_code,street,street_number,city,state_code,country_code,created_at,updated_at)
        VALUES (token||'-null-district','Teste','active','01001000','Rua Teste','1','Brasília','DF','BR',event_time,event_time);
        RAISE EXCEPTION 'NOT NULL não rejeitou district nulo.';
    EXCEPTION WHEN not_null_violation THEN
        GET STACKED DIAGNOSTICS violated_column = COLUMN_NAME;
        IF violated_column <> 'district' THEN RAISE; END IF;
    END;
    BEGIN
        INSERT INTO core.stores (store_code,name,status,postal_code,street,street_number,district,state_code,country_code,created_at,updated_at)
        VALUES (token||'-null-city','Teste','active','01001000','Rua Teste','1','Centro','DF','BR',event_time,event_time);
        RAISE EXCEPTION 'NOT NULL não rejeitou city nulo.';
    EXCEPTION WHEN not_null_violation THEN
        GET STACKED DIAGNOSTICS violated_column = COLUMN_NAME;
        IF violated_column <> 'city' THEN RAISE; END IF;
    END;
    BEGIN
        INSERT INTO core.stores (store_code,name,status,postal_code,street,street_number,district,city,country_code,created_at,updated_at)
        VALUES (token||'-null-state','Teste','active','01001000','Rua Teste','1','Centro','Brasília','BR',event_time,event_time);
        RAISE EXCEPTION 'NOT NULL não rejeitou state_code nulo.';
    EXCEPTION WHEN not_null_violation THEN
        GET STACKED DIAGNOSTICS violated_column = COLUMN_NAME;
        IF violated_column <> 'state_code' THEN RAISE; END IF;
    END;
    BEGIN
        INSERT INTO core.stores (store_code,name,status,postal_code,street,street_number,district,city,state_code,created_at,updated_at)
        VALUES (token||'-null-country','Teste','active','01001000','Rua Teste','1','Centro','Brasília','DF',event_time,event_time);
        RAISE EXCEPTION 'NOT NULL não rejeitou country_code nulo.';
    EXCEPTION WHEN not_null_violation THEN
        GET STACKED DIAGNOSTICS violated_column = COLUMN_NAME;
        IF violated_column <> 'country_code' THEN RAISE; END IF;
    END;

    RAISE NOTICE 'Teste de endereço de loja aprovado: endereço válido, CHECKs e campos obrigatórios.';
END;
$store_address_test$;

ROLLBACK;
