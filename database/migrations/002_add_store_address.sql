-- ProjetoBI Fase 2B.2: endereço operacional estruturado para lojas.
-- Aplicar somente após a migration 001 e confirmar que core.stores está vazia.
BEGIN;

ALTER TABLE core.stores
    ADD COLUMN postal_code VARCHAR(8) NOT NULL,
    ADD COLUMN street VARCHAR(180) NOT NULL,
    ADD COLUMN street_number VARCHAR(30) NOT NULL,
    ADD COLUMN complement VARCHAR(100),
    ADD COLUMN district VARCHAR(100) NOT NULL,
    ADD COLUMN city VARCHAR(120) NOT NULL,
    ADD COLUMN state_code CHAR(2) NOT NULL,
    ADD COLUMN country_code CHAR(2) NOT NULL;

ALTER TABLE core.stores ADD CONSTRAINT ck_stores_postal_code
    CHECK (postal_code ~ '^[0-9]{8}$');
ALTER TABLE core.stores ADD CONSTRAINT ck_stores_state_code
    CHECK (state_code IN (
        'AC','AL','AP','AM','BA','CE','DF','ES','GO','MA','MT','MS','MG',
        'PA','PB','PR','PE','PI','RJ','RN','RS','RO','RR','SC','SP','SE','TO'
    ));
ALTER TABLE core.stores ADD CONSTRAINT ck_stores_country_code
    CHECK (country_code = 'BR');

CREATE INDEX idx_stores_state_city ON core.stores (state_code, city);

COMMIT;
