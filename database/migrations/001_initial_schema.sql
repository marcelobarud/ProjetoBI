-- ProjetoBI Fase 2B - PostgreSQL 18. Gerado a partir da proposta aprovada.
-- Aplicar integralmente dentro de transação. Sem dados, triggers, procedures ou defaults temporais.
BEGIN;
CREATE SCHEMA core;
CREATE SCHEMA crm;
CREATE SCHEMA catalog;
CREATE SCHEMA inventory;
CREATE SCHEMA payments;
CREATE SCHEMA logistics;
CREATE SCHEMA after_sales;
CREATE SCHEMA sales;
CREATE SCHEMA procurement;

CREATE TABLE core.stores (
    store_id BIGINT GENERATED ALWAYS AS IDENTITY NOT NULL,
    store_code VARCHAR(30) NOT NULL,
    name VARCHAR(160) NOT NULL,
    status VARCHAR(20) NOT NULL,
    opened_on DATE,
    closed_on DATE,
    phone VARCHAR(30),
    email VARCHAR(254),
    created_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL,
    notes TEXT,
    CONSTRAINT pk_stores PRIMARY KEY (store_id)
);

CREATE TABLE core.employees (
    employee_id BIGINT GENERATED ALWAYS AS IDENTITY NOT NULL,
    employee_code VARCHAR(30) NOT NULL,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(120) NOT NULL,
    email VARCHAR(254),
    phone VARCHAR(30),
    hired_on DATE NOT NULL,
    terminated_on DATE,
    status VARCHAR(20) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL,
    CONSTRAINT pk_employees PRIMARY KEY (employee_id)
);

CREATE TABLE core.employee_roles (
    employee_role_id BIGINT GENERATED ALWAYS AS IDENTITY NOT NULL,
    role_code VARCHAR(30) NOT NULL,
    name VARCHAR(100) NOT NULL,
    is_active BOOLEAN NOT NULL,
    created_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL,
    CONSTRAINT pk_employee_roles PRIMARY KEY (employee_role_id)
);

CREATE TABLE core.employee_assignments (
    employee_assignment_id BIGINT GENERATED ALWAYS AS IDENTITY NOT NULL,
    employee_id BIGINT NOT NULL,
    employee_role_id BIGINT NOT NULL,
    store_id BIGINT,
    valid_from DATE NOT NULL,
    valid_to DATE,
    created_at TIMESTAMPTZ NOT NULL,
    notes TEXT,
    CONSTRAINT pk_employee_assignments PRIMARY KEY (employee_assignment_id)
);

CREATE TABLE crm.customers (
    customer_id BIGINT GENERATED ALWAYS AS IDENTITY NOT NULL,
    customer_code VARCHAR(30) NOT NULL,
    customer_type VARCHAR(12) NOT NULL,
    display_name VARCHAR(180) NOT NULL,
    status VARCHAR(20) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL,
    notes TEXT,
    CONSTRAINT pk_customers PRIMARY KEY (customer_id)
);

CREATE TABLE crm.individual_profiles (
    customer_id BIGINT NOT NULL,
    cpf VARCHAR(11),
    birth_date DATE,
    created_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL,
    CONSTRAINT pk_individual_profiles PRIMARY KEY (customer_id)
);

CREATE TABLE crm.business_profiles (
    customer_id BIGINT NOT NULL,
    legal_name VARCHAR(200) NOT NULL,
    trade_name VARCHAR(200),
    cnpj VARCHAR(14),
    state_registration VARCHAR(30),
    created_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL,
    CONSTRAINT pk_business_profiles PRIMARY KEY (customer_id)
);

CREATE TABLE crm.customer_contacts (
    customer_contact_id BIGINT GENERATED ALWAYS AS IDENTITY NOT NULL,
    customer_id BIGINT NOT NULL,
    contact_type VARCHAR(20) NOT NULL,
    contact_value VARCHAR(254) NOT NULL,
    is_primary BOOLEAN NOT NULL,
    is_active BOOLEAN NOT NULL,
    created_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL,
    CONSTRAINT pk_customer_contacts PRIMARY KEY (customer_contact_id)
);

CREATE TABLE crm.customer_addresses (
    customer_address_id BIGINT GENERATED ALWAYS AS IDENTITY NOT NULL,
    customer_id BIGINT NOT NULL,
    address_label VARCHAR(50),
    recipient_name VARCHAR(180),
    postal_code VARCHAR(8) NOT NULL,
    street VARCHAR(180) NOT NULL,
    street_number VARCHAR(30) NOT NULL,
    complement VARCHAR(100),
    district VARCHAR(100) NOT NULL,
    city VARCHAR(120) NOT NULL,
    state_code CHAR(2) NOT NULL,
    country_code CHAR(2) NOT NULL,
    is_default BOOLEAN NOT NULL,
    is_active BOOLEAN NOT NULL,
    created_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL,
    CONSTRAINT pk_customer_addresses PRIMARY KEY (customer_address_id)
);

CREATE TABLE catalog.categories (
    category_id BIGINT GENERATED ALWAYS AS IDENTITY NOT NULL,
    parent_category_id BIGINT,
    category_code VARCHAR(40) NOT NULL,
    name VARCHAR(120) NOT NULL,
    is_active BOOLEAN NOT NULL,
    created_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL,
    CONSTRAINT pk_categories PRIMARY KEY (category_id)
);

CREATE TABLE catalog.brands (
    brand_id BIGINT GENERATED ALWAYS AS IDENTITY NOT NULL,
    brand_code VARCHAR(40) NOT NULL,
    name VARCHAR(120) NOT NULL,
    is_active BOOLEAN NOT NULL,
    created_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL,
    CONSTRAINT pk_brands PRIMARY KEY (brand_id)
);

CREATE TABLE catalog.products (
    product_id BIGINT GENERATED ALWAYS AS IDENTITY NOT NULL,
    sku VARCHAR(60) NOT NULL,
    category_id BIGINT NOT NULL,
    brand_id BIGINT,
    name VARCHAR(180) NOT NULL,
    description TEXT,
    specifications JSONB,
    unit_of_measure VARCHAR(12) NOT NULL,
    status VARCHAR(20) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL,
    CONSTRAINT pk_products PRIMARY KEY (product_id)
);

CREATE TABLE catalog.product_suppliers (
    product_supplier_id BIGINT GENERATED ALWAYS AS IDENTITY NOT NULL,
    product_id BIGINT NOT NULL,
    supplier_id BIGINT NOT NULL,
    supplier_product_code VARCHAR(80),
    is_preferred BOOLEAN NOT NULL,
    is_active BOOLEAN NOT NULL,
    created_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL,
    CONSTRAINT pk_product_suppliers PRIMARY KEY (product_supplier_id)
);

CREATE TABLE catalog.product_prices (
    product_price_id BIGINT GENERATED ALWAYS AS IDENTITY NOT NULL,
    product_id BIGINT NOT NULL,
    sales_channel_id BIGINT NOT NULL,
    amount NUMERIC(19,2) NOT NULL,
    valid_from TIMESTAMPTZ NOT NULL,
    valid_to TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL,
    created_by_employee_id BIGINT,
    CONSTRAINT pk_product_prices PRIMARY KEY (product_price_id)
);

CREATE TABLE inventory.stock_locations (
    stock_location_id BIGINT GENERATED ALWAYS AS IDENTITY NOT NULL,
    store_id BIGINT,
    location_code VARCHAR(40) NOT NULL,
    name VARCHAR(120) NOT NULL,
    location_type VARCHAR(20) NOT NULL,
    status VARCHAR(20) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL,
    CONSTRAINT pk_stock_locations PRIMARY KEY (stock_location_id)
);

CREATE TABLE inventory.stock_positions (
    stock_position_id BIGINT GENERATED ALWAYS AS IDENTITY NOT NULL,
    product_id BIGINT NOT NULL,
    stock_location_id BIGINT NOT NULL,
    on_hand_quantity BIGINT NOT NULL,
    reserved_quantity BIGINT NOT NULL,
    available_quantity BIGINT GENERATED ALWAYS AS (on_hand_quantity - reserved_quantity) STORED NOT NULL,
    average_unit_cost NUMERIC(20,8) NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL,
    CONSTRAINT pk_stock_positions PRIMARY KEY (stock_position_id)
);

CREATE TABLE inventory.stock_movements (
    stock_movement_id BIGINT GENERATED ALWAYS AS IDENTITY NOT NULL,
    product_id BIGINT NOT NULL,
    stock_location_id BIGINT NOT NULL,
    movement_type VARCHAR(24) NOT NULL,
    quantity_delta BIGINT NOT NULL,
    unit_cost NUMERIC(20,8),
    goods_receipt_item_id BIGINT,
    fulfillment_item_id BIGINT,
    return_item_id BIGINT,
    stock_transfer_item_id BIGINT,
    adjustment_employee_id BIGINT,
    reason_code VARCHAR(30),
    occurred_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ NOT NULL,
    notes TEXT,
    CONSTRAINT pk_stock_movements PRIMARY KEY (stock_movement_id)
);

CREATE TABLE inventory.stock_reservations (
    stock_reservation_id BIGINT GENERATED ALWAYS AS IDENTITY NOT NULL,
    sales_order_id BIGINT NOT NULL,
    sales_order_item_id BIGINT NOT NULL,
    product_id BIGINT NOT NULL,
    stock_location_id BIGINT NOT NULL,
    quantity BIGINT NOT NULL,
    status VARCHAR(20) NOT NULL,
    reserved_at TIMESTAMPTZ NOT NULL,
    expires_at TIMESTAMPTZ,
    released_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL,
    CONSTRAINT pk_stock_reservations PRIMARY KEY (stock_reservation_id)
);

CREATE TABLE inventory.stock_transfers (
    stock_transfer_id BIGINT GENERATED ALWAYS AS IDENTITY NOT NULL,
    transfer_number VARCHAR(40) NOT NULL,
    source_stock_location_id BIGINT NOT NULL,
    destination_stock_location_id BIGINT NOT NULL,
    requested_by_employee_id BIGINT,
    received_by_employee_id BIGINT,
    status VARCHAR(20) NOT NULL,
    requested_at TIMESTAMPTZ NOT NULL,
    dispatched_at TIMESTAMPTZ,
    received_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL,
    notes TEXT,
    CONSTRAINT pk_stock_transfers PRIMARY KEY (stock_transfer_id)
);

CREATE TABLE inventory.stock_transfer_items (
    stock_transfer_item_id BIGINT GENERATED ALWAYS AS IDENTITY NOT NULL,
    stock_transfer_id BIGINT NOT NULL,
    product_id BIGINT NOT NULL,
    line_number INTEGER NOT NULL,
    quantity_planned BIGINT NOT NULL,
    quantity_dispatched BIGINT,
    quantity_received BIGINT,
    created_at TIMESTAMPTZ NOT NULL,
    CONSTRAINT pk_stock_transfer_items PRIMARY KEY (stock_transfer_item_id)
);

CREATE TABLE payments.payment_methods (
    payment_method_id BIGINT GENERATED ALWAYS AS IDENTITY NOT NULL,
    method_code VARCHAR(30) NOT NULL,
    name VARCHAR(100) NOT NULL,
    method_type VARCHAR(24) NOT NULL,
    is_installment_capable BOOLEAN NOT NULL,
    is_active BOOLEAN NOT NULL,
    created_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL,
    CONSTRAINT pk_payment_methods PRIMARY KEY (payment_method_id)
);

CREATE TABLE payments.payments (
    payment_id BIGINT GENERATED ALWAYS AS IDENTITY NOT NULL,
    sales_order_id BIGINT NOT NULL,
    payment_method_id BIGINT NOT NULL,
    payment_reference VARCHAR(120),
    status VARCHAR(20) NOT NULL,
    amount NUMERIC(19,2) NOT NULL,
    currency_code CHAR(3) NOT NULL,
    attempted_at TIMESTAMPTZ NOT NULL,
    authorized_at TIMESTAMPTZ,
    settled_at TIMESTAMPTZ,
    external_reference VARCHAR(120),
    created_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL,
    CONSTRAINT pk_payments PRIMARY KEY (payment_id)
);

CREATE TABLE payments.payment_installments (
    payment_installment_id BIGINT GENERATED ALWAYS AS IDENTITY NOT NULL,
    payment_id BIGINT NOT NULL,
    installment_number INTEGER NOT NULL,
    due_on DATE,
    amount NUMERIC(19,2) NOT NULL,
    status VARCHAR(20) NOT NULL,
    paid_at TIMESTAMPTZ,
    external_reference VARCHAR(120),
    created_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL,
    CONSTRAINT pk_payment_installments PRIMARY KEY (payment_installment_id)
);

CREATE TABLE payments.refunds (
    refund_id BIGINT GENERATED ALWAYS AS IDENTITY NOT NULL,
    sales_order_id BIGINT NOT NULL,
    payment_id BIGINT NOT NULL,
    return_id BIGINT,
    status VARCHAR(20) NOT NULL,
    amount NUMERIC(19,2) NOT NULL,
    reason_code VARCHAR(30),
    requested_at TIMESTAMPTZ NOT NULL,
    processed_at TIMESTAMPTZ,
    external_reference VARCHAR(120),
    created_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL,
    CONSTRAINT pk_refunds PRIMARY KEY (refund_id)
);

CREATE TABLE logistics.carriers (
    carrier_id BIGINT GENERATED ALWAYS AS IDENTITY NOT NULL,
    carrier_code VARCHAR(30) NOT NULL,
    name VARCHAR(160) NOT NULL,
    tax_identifier VARCHAR(14),
    is_active BOOLEAN NOT NULL,
    created_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL,
    CONSTRAINT pk_carriers PRIMARY KEY (carrier_id)
);

CREATE TABLE logistics.fulfillments (
    fulfillment_id BIGINT GENERATED ALWAYS AS IDENTITY NOT NULL,
    sales_order_id BIGINT NOT NULL,
    fulfillment_number VARCHAR(40) NOT NULL,
    fulfillment_type VARCHAR(20) NOT NULL,
    status VARCHAR(24) NOT NULL,
    stock_location_id BIGINT,
    pickup_store_id BIGINT,
    carrier_id BIGINT,
    tracking_number VARCHAR(100),
    planned_at TIMESTAMPTZ,
    dispatched_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL,
    CONSTRAINT pk_fulfillments PRIMARY KEY (fulfillment_id)
);

CREATE TABLE logistics.fulfillment_items (
    fulfillment_item_id BIGINT GENERATED ALWAYS AS IDENTITY NOT NULL,
    sales_order_id BIGINT NOT NULL,
    fulfillment_id BIGINT NOT NULL,
    sales_order_item_id BIGINT NOT NULL,
    quantity_allocated BIGINT NOT NULL,
    fulfilled_quantity BIGINT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL,
    CONSTRAINT pk_fulfillment_items PRIMARY KEY (fulfillment_item_id)
);

CREATE TABLE logistics.fulfillment_events (
    fulfillment_event_id BIGINT GENERATED ALWAYS AS IDENTITY NOT NULL,
    fulfillment_id BIGINT NOT NULL,
    event_type VARCHAR(30) NOT NULL,
    occurred_at TIMESTAMPTZ NOT NULL,
    recorded_by_employee_id BIGINT,
    description VARCHAR(240),
    external_reference VARCHAR(120),
    created_at TIMESTAMPTZ NOT NULL,
    CONSTRAINT pk_fulfillment_events PRIMARY KEY (fulfillment_event_id)
);

CREATE TABLE after_sales.returns (
    return_id BIGINT GENERATED ALWAYS AS IDENTITY NOT NULL,
    sales_order_id BIGINT NOT NULL,
    return_number VARCHAR(40) NOT NULL,
    status VARCHAR(24) NOT NULL,
    reason_code VARCHAR(30) NOT NULL,
    requested_by_employee_id BIGINT,
    approved_by_employee_id BIGINT,
    requested_at TIMESTAMPTZ NOT NULL,
    decided_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL,
    notes TEXT,
    CONSTRAINT pk_returns PRIMARY KEY (return_id)
);

CREATE TABLE after_sales.return_items (
    return_item_id BIGINT GENERATED ALWAYS AS IDENTITY NOT NULL,
    sales_order_id BIGINT NOT NULL,
    return_id BIGINT NOT NULL,
    sales_order_item_id BIGINT NOT NULL,
    source_fulfillment_item_id BIGINT,
    quantity_requested BIGINT NOT NULL,
    quantity_approved BIGINT NOT NULL,
    quantity_received BIGINT NOT NULL,
    item_condition VARCHAR(20),
    stock_destination VARCHAR(20),
    received_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL,
    notes TEXT,
    CONSTRAINT pk_return_items PRIMARY KEY (return_item_id)
);

CREATE TABLE sales.sales_channels (
    sales_channel_id BIGINT GENERATED ALWAYS AS IDENTITY NOT NULL,
    channel_code VARCHAR(30) NOT NULL,
    name VARCHAR(100) NOT NULL,
    channel_type VARCHAR(20) NOT NULL,
    is_active BOOLEAN NOT NULL,
    created_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL,
    CONSTRAINT pk_sales_channels PRIMARY KEY (sales_channel_id)
);

CREATE TABLE sales.sales_orders (
    sales_order_id BIGINT GENERATED ALWAYS AS IDENTITY NOT NULL,
    order_number VARCHAR(40) NOT NULL,
    sales_channel_id BIGINT NOT NULL,
    channel_type VARCHAR(20) NOT NULL,
    customer_id BIGINT,
    store_id BIGINT,
    salesperson_employee_id BIGINT,
    customer_address_id BIGINT,
    order_status VARCHAR(24) NOT NULL,
    placed_at TIMESTAMPTZ NOT NULL,
    currency_code CHAR(3) NOT NULL,
    subtotal_amount NUMERIC(19,2) NOT NULL,
    discount_amount NUMERIC(19,2) NOT NULL,
    shipping_amount NUMERIC(19,2) NOT NULL,
    total_amount NUMERIC(19,2) NOT NULL,
    recipient_name VARCHAR(180),
    postal_code_snapshot VARCHAR(8),
    street_snapshot VARCHAR(180),
    street_number_snapshot VARCHAR(30),
    complement_snapshot VARCHAR(100),
    district_snapshot VARCHAR(100),
    city_snapshot VARCHAR(120),
    state_code_snapshot CHAR(2),
    country_code_snapshot CHAR(2),
    external_reference VARCHAR(120),
    created_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL,
    notes TEXT,
    CONSTRAINT pk_sales_orders PRIMARY KEY (sales_order_id)
);

CREATE TABLE sales.sales_order_items (
    sales_order_item_id BIGINT GENERATED ALWAYS AS IDENTITY NOT NULL,
    sales_order_id BIGINT NOT NULL,
    line_number INTEGER NOT NULL,
    product_id BIGINT NOT NULL,
    sku_snapshot VARCHAR(60) NOT NULL,
    product_name_snapshot VARCHAR(180) NOT NULL,
    quantity BIGINT NOT NULL,
    unit_sale_price NUMERIC(19,2) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL,
    CONSTRAINT pk_sales_order_items PRIMARY KEY (sales_order_item_id)
);

CREATE TABLE sales.order_status_history (
    order_status_history_id BIGINT GENERATED ALWAYS AS IDENTITY NOT NULL,
    sales_order_id BIGINT NOT NULL,
    status VARCHAR(24) NOT NULL,
    occurred_at TIMESTAMPTZ NOT NULL,
    changed_by_employee_id BIGINT,
    reason VARCHAR(240),
    created_at TIMESTAMPTZ NOT NULL,
    CONSTRAINT pk_order_status_history PRIMARY KEY (order_status_history_id)
);

CREATE TABLE sales.applied_discounts (
    applied_discount_id BIGINT GENERATED ALWAYS AS IDENTITY NOT NULL,
    sales_order_id BIGINT NOT NULL,
    sales_order_item_id BIGINT NOT NULL,
    discount_scope VARCHAR(16) NOT NULL,
    discount_code VARCHAR(60),
    campaign_reference VARCHAR(120),
    description VARCHAR(180),
    amount NUMERIC(19,2) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL,
    CONSTRAINT pk_applied_discounts PRIMARY KEY (applied_discount_id)
);

CREATE TABLE procurement.suppliers (
    supplier_id BIGINT GENERATED ALWAYS AS IDENTITY NOT NULL,
    supplier_code VARCHAR(30) NOT NULL,
    legal_name VARCHAR(200) NOT NULL,
    trade_name VARCHAR(180),
    tax_identifier VARCHAR(14),
    email VARCHAR(254),
    phone VARCHAR(30),
    status VARCHAR(20) NOT NULL,
    external_reference VARCHAR(120),
    created_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL,
    notes TEXT,
    CONSTRAINT pk_suppliers PRIMARY KEY (supplier_id)
);

CREATE TABLE procurement.purchase_orders (
    purchase_order_id BIGINT GENERATED ALWAYS AS IDENTITY NOT NULL,
    purchase_order_number VARCHAR(40) NOT NULL,
    supplier_id BIGINT NOT NULL,
    responsible_employee_id BIGINT,
    status VARCHAR(24) NOT NULL,
    ordered_at TIMESTAMPTZ NOT NULL,
    expected_on DATE,
    currency_code CHAR(3) NOT NULL,
    external_reference VARCHAR(120),
    created_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL,
    notes TEXT,
    CONSTRAINT pk_purchase_orders PRIMARY KEY (purchase_order_id)
);

CREATE TABLE procurement.purchase_order_items (
    purchase_order_item_id BIGINT GENERATED ALWAYS AS IDENTITY NOT NULL,
    purchase_order_id BIGINT NOT NULL,
    line_number INTEGER NOT NULL,
    product_id BIGINT NOT NULL,
    quantity_ordered BIGINT NOT NULL,
    unit_cost_ordered NUMERIC(20,8) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL,
    CONSTRAINT pk_purchase_order_items PRIMARY KEY (purchase_order_item_id)
);

CREATE TABLE procurement.goods_receipts (
    goods_receipt_id BIGINT GENERATED ALWAYS AS IDENTITY NOT NULL,
    purchase_order_id BIGINT NOT NULL,
    stock_location_id BIGINT NOT NULL,
    checked_by_employee_id BIGINT,
    receipt_number VARCHAR(40) NOT NULL,
    status VARCHAR(20) NOT NULL,
    received_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ NOT NULL,
    notes TEXT,
    CONSTRAINT pk_goods_receipts PRIMARY KEY (goods_receipt_id)
);

CREATE TABLE procurement.goods_receipt_items (
    goods_receipt_item_id BIGINT GENERATED ALWAYS AS IDENTITY NOT NULL,
    purchase_order_id BIGINT NOT NULL,
    goods_receipt_id BIGINT NOT NULL,
    purchase_order_item_id BIGINT NOT NULL,
    quantity_received BIGINT NOT NULL,
    accepted_quantity BIGINT NOT NULL,
    rejected_quantity BIGINT NOT NULL,
    unit_acquisition_cost NUMERIC(20,8) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL,
    CONSTRAINT pk_goods_receipt_items PRIMARY KEY (goods_receipt_item_id)
);

-- Constraints locais e relacionamentos são adicionados depois da criação de todas as tabelas.

-- Integridade local e chaves alternativas conforme constraints-and-indexes.md.
ALTER TABLE core.stores ADD CONSTRAINT uq_stores_store_code UNIQUE (store_code);
ALTER TABLE core.stores ADD CONSTRAINT ck_stores_status CHECK (status IN ('active', 'inactive', 'closed'));
ALTER TABLE core.stores ADD CONSTRAINT ck_stores_closed_on CHECK (closed_on IS NULL OR opened_on IS NULL OR closed_on >= opened_on);
ALTER TABLE core.employees ADD CONSTRAINT uq_employees_employee_code UNIQUE (employee_code);
ALTER TABLE core.employees ADD CONSTRAINT ck_employees_status CHECK (status IN ('active', 'inactive', 'terminated'));
ALTER TABLE core.employees ADD CONSTRAINT ck_employees_terminated_on CHECK (terminated_on IS NULL OR terminated_on >= hired_on);
ALTER TABLE core.employee_roles ADD CONSTRAINT uq_employee_roles_role_code UNIQUE (role_code);
ALTER TABLE core.employee_roles ADD CONSTRAINT uq_employee_roles_name UNIQUE (name);
ALTER TABLE core.employee_assignments ADD CONSTRAINT ck_employee_assignments_valid_dates CHECK (valid_to IS NULL OR valid_to >= valid_from);

ALTER TABLE crm.customers ADD CONSTRAINT uq_customers_customer_code UNIQUE (customer_code);
ALTER TABLE crm.customers ADD CONSTRAINT ck_customers_customer_type CHECK (customer_type IN ('individual', 'business'));
ALTER TABLE crm.customers ADD CONSTRAINT ck_customers_status CHECK (status IN ('active', 'inactive'));
ALTER TABLE crm.individual_profiles ADD CONSTRAINT ck_individual_profiles_cpf_digits CHECK (cpf IS NULL OR cpf ~ '^[0-9]{11}$');
CREATE UNIQUE INDEX uq_individual_profiles_cpf ON crm.individual_profiles (cpf) WHERE cpf IS NOT NULL;
ALTER TABLE crm.business_profiles ADD CONSTRAINT ck_business_profiles_cnpj_digits CHECK (cnpj IS NULL OR cnpj ~ '^[0-9]{14}$');
CREATE UNIQUE INDEX uq_business_profiles_cnpj ON crm.business_profiles (cnpj) WHERE cnpj IS NOT NULL;
ALTER TABLE crm.customer_contacts ADD CONSTRAINT ck_customer_contacts_type CHECK (contact_type IN ('email', 'phone', 'other'));
CREATE UNIQUE INDEX uq_customer_contacts_primary_active ON crm.customer_contacts (customer_id) WHERE is_primary AND is_active;
ALTER TABLE crm.customer_addresses ADD CONSTRAINT ck_customer_addresses_postal_code CHECK (postal_code ~ '^[0-9]{8}$');
ALTER TABLE crm.customer_addresses ADD CONSTRAINT ck_customer_addresses_state CHECK (state_code IN ('AC','AL','AP','AM','BA','CE','DF','ES','GO','MA','MT','MS','MG','PA','PB','PR','PE','PI','RJ','RN','RS','RO','RR','SC','SP','SE','TO'));
ALTER TABLE crm.customer_addresses ADD CONSTRAINT ck_customer_addresses_country CHECK (country_code = 'BR');
CREATE UNIQUE INDEX uq_customer_addresses_default_active ON crm.customer_addresses (customer_id) WHERE is_default AND is_active;

ALTER TABLE catalog.categories ADD CONSTRAINT uq_categories_category_code UNIQUE (category_code);
ALTER TABLE catalog.categories ADD CONSTRAINT ck_categories_not_own_parent CHECK (parent_category_id IS NULL OR parent_category_id <> category_id);
ALTER TABLE catalog.brands ADD CONSTRAINT uq_brands_brand_code UNIQUE (brand_code);
ALTER TABLE catalog.brands ADD CONSTRAINT uq_brands_name UNIQUE (name);
ALTER TABLE catalog.products ADD CONSTRAINT uq_products_sku UNIQUE (sku);
ALTER TABLE catalog.products ADD CONSTRAINT ck_products_status CHECK (status IN ('active', 'inactive', 'discontinued'));
ALTER TABLE catalog.products ADD CONSTRAINT ck_products_specifications_object CHECK (specifications IS NULL OR jsonb_typeof(specifications) = 'object');
-- unit_of_measure permanece sem CHECK de domínio nesta versão; valores permitidos não foram especificados.
ALTER TABLE catalog.product_suppliers ADD CONSTRAINT uq_product_suppliers_product_supplier UNIQUE (product_id, supplier_id);
CREATE UNIQUE INDEX uq_product_suppliers_preferred_active ON catalog.product_suppliers (product_id) WHERE is_preferred AND is_active;
ALTER TABLE catalog.product_prices ADD CONSTRAINT ck_product_prices_amount CHECK (amount >= 0);
ALTER TABLE catalog.product_prices ADD CONSTRAINT ck_product_prices_valid_range CHECK (valid_to IS NULL OR valid_to > valid_from);

ALTER TABLE sales.sales_channels ADD CONSTRAINT uq_sales_channels_channel_code UNIQUE (channel_code);
ALTER TABLE sales.sales_channels ADD CONSTRAINT uq_sales_channels_id_type UNIQUE (sales_channel_id, channel_type);
ALTER TABLE sales.sales_channels ADD CONSTRAINT ck_sales_channels_type CHECK (channel_type IN ('physical', 'ecommerce', 'marketplace'));
ALTER TABLE sales.sales_orders ADD CONSTRAINT uq_sales_orders_order_number UNIQUE (order_number);
ALTER TABLE sales.sales_orders ADD CONSTRAINT ck_sales_orders_status CHECK (order_status IN ('draft', 'placed', 'confirmed', 'cancelled', 'completed'));
ALTER TABLE sales.sales_orders ADD CONSTRAINT ck_sales_orders_currency CHECK (currency_code = 'BRL');
ALTER TABLE sales.sales_orders ADD CONSTRAINT ck_sales_orders_customer_by_channel CHECK (customer_id IS NOT NULL OR channel_type = 'physical');
ALTER TABLE sales.sales_orders ADD CONSTRAINT ck_sales_orders_amounts CHECK (subtotal_amount >= 0 AND discount_amount >= 0 AND shipping_amount >= 0 AND total_amount >= 0);
ALTER TABLE sales.sales_order_items ADD CONSTRAINT uq_sales_order_items_order_line UNIQUE (sales_order_id, line_number);
ALTER TABLE sales.sales_order_items ADD CONSTRAINT uq_sales_order_items_order_id UNIQUE (sales_order_id, sales_order_item_id);
ALTER TABLE sales.sales_order_items ADD CONSTRAINT ck_sales_order_items_quantity CHECK (quantity > 0);
ALTER TABLE sales.sales_order_items ADD CONSTRAINT ck_sales_order_items_sale_price CHECK (unit_sale_price >= 0);
ALTER TABLE sales.order_status_history ADD CONSTRAINT ck_order_status_history_status CHECK (status IN ('draft', 'placed', 'confirmed', 'cancelled', 'completed'));
ALTER TABLE sales.applied_discounts ADD CONSTRAINT ck_applied_discounts_scope CHECK (discount_scope IN ('line', 'order_allocation'));
ALTER TABLE sales.applied_discounts ADD CONSTRAINT ck_applied_discounts_amount CHECK (amount > 0);

ALTER TABLE procurement.suppliers ADD CONSTRAINT uq_suppliers_supplier_code UNIQUE (supplier_code);
ALTER TABLE procurement.suppliers ADD CONSTRAINT ck_suppliers_status CHECK (status IN ('active', 'inactive'));
CREATE UNIQUE INDEX uq_suppliers_tax_identifier ON procurement.suppliers (tax_identifier) WHERE tax_identifier IS NOT NULL;
ALTER TABLE procurement.purchase_orders ADD CONSTRAINT uq_purchase_orders_number UNIQUE (purchase_order_number);
ALTER TABLE procurement.purchase_orders ADD CONSTRAINT ck_purchase_orders_status CHECK (status IN ('draft', 'submitted', 'partially_received', 'received', 'cancelled'));
ALTER TABLE procurement.purchase_orders ADD CONSTRAINT ck_purchase_orders_currency CHECK (currency_code = 'BRL');
ALTER TABLE procurement.purchase_order_items ADD CONSTRAINT uq_purchase_order_items_order_line UNIQUE (purchase_order_id, line_number);
ALTER TABLE procurement.purchase_order_items ADD CONSTRAINT uq_purchase_order_items_order_id UNIQUE (purchase_order_id, purchase_order_item_id);
ALTER TABLE procurement.purchase_order_items ADD CONSTRAINT ck_purchase_order_items_quantity CHECK (quantity_ordered > 0);
ALTER TABLE procurement.purchase_order_items ADD CONSTRAINT ck_purchase_order_items_cost CHECK (unit_cost_ordered >= 0);
ALTER TABLE procurement.goods_receipts ADD CONSTRAINT uq_goods_receipts_receipt_number UNIQUE (receipt_number);
ALTER TABLE procurement.goods_receipts ADD CONSTRAINT uq_goods_receipts_order_id UNIQUE (purchase_order_id, goods_receipt_id);
ALTER TABLE procurement.goods_receipts ADD CONSTRAINT ck_goods_receipts_status CHECK (status IN ('in_progress', 'accepted', 'completed', 'cancelled'));
ALTER TABLE procurement.goods_receipt_items ADD CONSTRAINT uq_goods_receipt_items_receipt_item UNIQUE (goods_receipt_id, purchase_order_item_id);
ALTER TABLE procurement.goods_receipt_items ADD CONSTRAINT ck_goods_receipt_items_quantities CHECK (quantity_received >= 0 AND accepted_quantity >= 0 AND rejected_quantity >= 0 AND accepted_quantity + rejected_quantity = quantity_received);
ALTER TABLE procurement.goods_receipt_items ADD CONSTRAINT ck_goods_receipt_items_cost CHECK (unit_acquisition_cost >= 0);

ALTER TABLE inventory.stock_locations ADD CONSTRAINT uq_stock_locations_location_code UNIQUE (location_code);
ALTER TABLE inventory.stock_locations ADD CONSTRAINT ck_stock_locations_type CHECK (location_type IN ('store', 'warehouse', 'digital', 'other'));
ALTER TABLE inventory.stock_locations ADD CONSTRAINT ck_stock_locations_status CHECK (status IN ('active', 'inactive'));
ALTER TABLE inventory.stock_positions ADD CONSTRAINT uq_stock_positions_product_location UNIQUE (product_id, stock_location_id);
ALTER TABLE inventory.stock_positions ADD CONSTRAINT ck_stock_positions_quantities CHECK (on_hand_quantity >= 0 AND reserved_quantity >= 0 AND reserved_quantity <= on_hand_quantity);
ALTER TABLE inventory.stock_positions ADD CONSTRAINT ck_stock_positions_average_cost CHECK (average_unit_cost >= 0);
ALTER TABLE inventory.stock_movements ADD CONSTRAINT ck_stock_movements_type CHECK (movement_type IN ('receipt', 'fulfillment', 'customer_return', 'transfer_in', 'transfer_out', 'adjustment_in', 'adjustment_out'));
ALTER TABLE inventory.stock_movements ADD CONSTRAINT ck_stock_movements_nonzero CHECK (quantity_delta <> 0);
ALTER TABLE inventory.stock_movements ADD CONSTRAINT ck_stock_movements_direction CHECK ((movement_type IN ('receipt', 'customer_return', 'transfer_in', 'adjustment_in') AND quantity_delta > 0) OR (movement_type IN ('fulfillment', 'transfer_out', 'adjustment_out') AND quantity_delta < 0));
ALTER TABLE inventory.stock_movements ADD CONSTRAINT ck_stock_movements_cost CHECK (unit_cost IS NULL OR unit_cost >= 0);
ALTER TABLE inventory.stock_movements ADD CONSTRAINT ck_stock_movements_required_cost CHECK (movement_type NOT IN ('receipt', 'fulfillment', 'customer_return', 'transfer_in', 'transfer_out') OR unit_cost IS NOT NULL);
ALTER TABLE inventory.stock_movements ADD CONSTRAINT ck_stock_movements_adjustment_reason CHECK (movement_type NOT IN ('adjustment_in', 'adjustment_out') OR (reason_code IS NOT NULL AND reason_code IN ('count_correction', 'damage', 'loss', 'found', 'other')));
ALTER TABLE inventory.stock_movements ADD CONSTRAINT ck_stock_movements_source CHECK (
    (movement_type = 'receipt' AND goods_receipt_item_id IS NOT NULL AND fulfillment_item_id IS NULL AND return_item_id IS NULL AND stock_transfer_item_id IS NULL)
 OR (movement_type = 'fulfillment' AND goods_receipt_item_id IS NULL AND fulfillment_item_id IS NOT NULL AND return_item_id IS NULL AND stock_transfer_item_id IS NULL)
 OR (movement_type = 'customer_return' AND goods_receipt_item_id IS NULL AND fulfillment_item_id IS NULL AND return_item_id IS NOT NULL AND stock_transfer_item_id IS NULL)
 OR (movement_type IN ('transfer_in', 'transfer_out') AND goods_receipt_item_id IS NULL AND fulfillment_item_id IS NULL AND return_item_id IS NULL AND stock_transfer_item_id IS NOT NULL)
 OR (movement_type IN ('adjustment_in', 'adjustment_out') AND goods_receipt_item_id IS NULL AND fulfillment_item_id IS NULL AND return_item_id IS NULL AND stock_transfer_item_id IS NULL AND adjustment_employee_id IS NOT NULL)
);
ALTER TABLE inventory.stock_reservations ADD CONSTRAINT ck_stock_reservations_quantity CHECK (quantity > 0);
ALTER TABLE inventory.stock_reservations ADD CONSTRAINT ck_stock_reservations_status CHECK (status IN ('active', 'released', 'expired', 'consumed'));
ALTER TABLE inventory.stock_reservations ADD CONSTRAINT ck_stock_reservations_expiry CHECK (expires_at IS NULL OR expires_at >= reserved_at);
ALTER TABLE inventory.stock_transfers ADD CONSTRAINT uq_stock_transfers_number UNIQUE (transfer_number);
ALTER TABLE inventory.stock_transfers ADD CONSTRAINT ck_stock_transfers_distinct_locations CHECK (source_stock_location_id <> destination_stock_location_id);
ALTER TABLE inventory.stock_transfers ADD CONSTRAINT ck_stock_transfers_status CHECK (status IN ('draft', 'in_transit', 'completed', 'cancelled'));
ALTER TABLE inventory.stock_transfers ADD CONSTRAINT ck_stock_transfers_times CHECK ((dispatched_at IS NULL OR dispatched_at >= requested_at) AND (received_at IS NULL OR (dispatched_at IS NOT NULL AND received_at >= dispatched_at)));
ALTER TABLE inventory.stock_transfer_items ADD CONSTRAINT uq_stock_transfer_items_line UNIQUE (stock_transfer_id, line_number);
ALTER TABLE inventory.stock_transfer_items ADD CONSTRAINT ck_stock_transfer_items_quantities CHECK (quantity_planned > 0 AND (quantity_dispatched IS NULL OR quantity_dispatched >= 0) AND (quantity_received IS NULL OR quantity_received >= 0) AND (quantity_received IS NULL OR (quantity_dispatched IS NOT NULL AND quantity_received <= quantity_dispatched)));

ALTER TABLE payments.payment_methods ADD CONSTRAINT uq_payment_methods_code UNIQUE (method_code);
ALTER TABLE payments.payment_methods ADD CONSTRAINT ck_payment_methods_type CHECK (method_type IN ('card', 'cash', 'instant', 'bank_transfer', 'other'));
ALTER TABLE payments.payments ADD CONSTRAINT uq_payments_order_id UNIQUE (sales_order_id, payment_id);
ALTER TABLE payments.payments ADD CONSTRAINT ck_payments_status CHECK (status IN ('pending', 'authorized', 'captured', 'settled', 'declined', 'cancelled', 'failed'));
ALTER TABLE payments.payments ADD CONSTRAINT ck_payments_currency CHECK (currency_code = 'BRL');
ALTER TABLE payments.payments ADD CONSTRAINT ck_payments_amount CHECK (amount > 0);
ALTER TABLE payments.payment_installments ADD CONSTRAINT uq_payment_installments_number UNIQUE (payment_id, installment_number);
ALTER TABLE payments.payment_installments ADD CONSTRAINT ck_payment_installments_number CHECK (installment_number > 0);
ALTER TABLE payments.payment_installments ADD CONSTRAINT ck_payment_installments_amount CHECK (amount > 0);
ALTER TABLE payments.payment_installments ADD CONSTRAINT ck_payment_installments_status CHECK (status IN ('pending', 'paid', 'overdue', 'cancelled', 'failed'));
ALTER TABLE payments.refunds ADD CONSTRAINT ck_refunds_status CHECK (status IN ('requested', 'processing', 'completed', 'rejected', 'cancelled'));
ALTER TABLE payments.refunds ADD CONSTRAINT ck_refunds_amount CHECK (amount > 0);
ALTER TABLE payments.refunds ADD CONSTRAINT ck_refunds_reason CHECK (reason_code IS NULL OR reason_code IN ('customer_request', 'return', 'duplicate_charge', 'other'));

ALTER TABLE logistics.carriers ADD CONSTRAINT uq_carriers_code UNIQUE (carrier_code);
CREATE UNIQUE INDEX uq_carriers_tax_identifier ON logistics.carriers (tax_identifier) WHERE tax_identifier IS NOT NULL;
ALTER TABLE logistics.fulfillments ADD CONSTRAINT uq_fulfillments_order_number UNIQUE (sales_order_id, fulfillment_number);
ALTER TABLE logistics.fulfillments ADD CONSTRAINT uq_fulfillments_order_id UNIQUE (sales_order_id, fulfillment_id);
ALTER TABLE logistics.fulfillments ADD CONSTRAINT ck_fulfillments_type CHECK (fulfillment_type IN ('delivery', 'store_pickup'));
ALTER TABLE logistics.fulfillments ADD CONSTRAINT ck_fulfillments_status CHECK (status IN ('pending', 'preparing', 'dispatched', 'completed', 'failed', 'cancelled'));
ALTER TABLE logistics.fulfillments ADD CONSTRAINT ck_fulfillments_mode CHECK ((fulfillment_type = 'store_pickup' AND pickup_store_id IS NOT NULL AND carrier_id IS NULL) OR (fulfillment_type = 'delivery' AND pickup_store_id IS NULL));
ALTER TABLE logistics.fulfillment_items ADD CONSTRAINT uq_fulfillment_items_fulfillment_item UNIQUE (fulfillment_id, sales_order_item_id);
ALTER TABLE logistics.fulfillment_items ADD CONSTRAINT uq_fulfillment_items_order_item_id UNIQUE (sales_order_id, sales_order_item_id, fulfillment_item_id);
ALTER TABLE logistics.fulfillment_items ADD CONSTRAINT ck_fulfillment_items_quantities CHECK (quantity_allocated > 0 AND fulfilled_quantity >= 0 AND fulfilled_quantity <= quantity_allocated);
ALTER TABLE logistics.fulfillment_events ADD CONSTRAINT ck_fulfillment_events_type CHECK (event_type IN ('prepared', 'dispatched', 'delivery_attempt', 'delivered', 'pickup_ready', 'picked_up', 'exception', 'cancelled'));

ALTER TABLE after_sales.returns ADD CONSTRAINT uq_returns_order_number UNIQUE (sales_order_id, return_number);
ALTER TABLE after_sales.returns ADD CONSTRAINT uq_returns_order_id UNIQUE (sales_order_id, return_id);
ALTER TABLE after_sales.returns ADD CONSTRAINT ck_returns_status CHECK (status IN ('requested', 'approved', 'rejected', 'partially_received', 'received', 'closed', 'cancelled'));
ALTER TABLE after_sales.returns ADD CONSTRAINT ck_returns_reason CHECK (reason_code IN ('defective', 'damaged', 'incorrect_item', 'buyer_remorse', 'other'));
ALTER TABLE after_sales.return_items ADD CONSTRAINT uq_return_items_return_source UNIQUE (return_id, source_fulfillment_item_id);
ALTER TABLE after_sales.return_items ADD CONSTRAINT ck_return_items_quantities CHECK (quantity_requested > 0 AND quantity_approved >= 0 AND quantity_approved <= quantity_requested AND quantity_received >= 0 AND quantity_received <= quantity_approved);
ALTER TABLE after_sales.return_items ADD CONSTRAINT ck_return_items_condition CHECK (item_condition IS NULL OR item_condition IN ('unopened', 'good', 'damaged', 'defective', 'unknown'));
ALTER TABLE after_sales.return_items ADD CONSTRAINT ck_return_items_destination CHECK (stock_destination IS NULL OR stock_destination IN ('sellable', 'quarantine', 'repair', 'discard'));
ALTER TABLE after_sales.return_items ADD CONSTRAINT ck_return_items_received_state CHECK (quantity_received = 0 OR (item_condition IS NOT NULL AND stock_destination IS NOT NULL AND received_at IS NOT NULL AND source_fulfillment_item_id IS NOT NULL));

-- FKs após a criação de todas as tabelas; sem ON DELETE CASCADE.
ALTER TABLE core.employee_assignments ADD CONSTRAINT fk_employee_assignments_employees FOREIGN KEY (employee_id) REFERENCES core.employees (employee_id);
ALTER TABLE core.employee_assignments ADD CONSTRAINT fk_employee_assignments_employee_roles FOREIGN KEY (employee_role_id) REFERENCES core.employee_roles (employee_role_id);
ALTER TABLE core.employee_assignments ADD CONSTRAINT fk_employee_assignments_stores FOREIGN KEY (store_id) REFERENCES core.stores (store_id);
ALTER TABLE crm.individual_profiles ADD CONSTRAINT fk_individual_profiles_customers FOREIGN KEY (customer_id) REFERENCES crm.customers (customer_id);
ALTER TABLE crm.business_profiles ADD CONSTRAINT fk_business_profiles_customers FOREIGN KEY (customer_id) REFERENCES crm.customers (customer_id);
ALTER TABLE crm.customer_contacts ADD CONSTRAINT fk_customer_contacts_customers FOREIGN KEY (customer_id) REFERENCES crm.customers (customer_id);
ALTER TABLE crm.customer_addresses ADD CONSTRAINT fk_customer_addresses_customers FOREIGN KEY (customer_id) REFERENCES crm.customers (customer_id);
ALTER TABLE catalog.categories ADD CONSTRAINT fk_categories_parent FOREIGN KEY (parent_category_id) REFERENCES catalog.categories (category_id);
ALTER TABLE catalog.products ADD CONSTRAINT fk_products_categories FOREIGN KEY (category_id) REFERENCES catalog.categories (category_id);
ALTER TABLE catalog.products ADD CONSTRAINT fk_products_brands FOREIGN KEY (brand_id) REFERENCES catalog.brands (brand_id);
ALTER TABLE catalog.product_suppliers ADD CONSTRAINT fk_product_suppliers_products FOREIGN KEY (product_id) REFERENCES catalog.products (product_id);
ALTER TABLE catalog.product_suppliers ADD CONSTRAINT fk_product_suppliers_suppliers FOREIGN KEY (supplier_id) REFERENCES procurement.suppliers (supplier_id);
ALTER TABLE catalog.product_prices ADD CONSTRAINT fk_product_prices_products FOREIGN KEY (product_id) REFERENCES catalog.products (product_id);
ALTER TABLE catalog.product_prices ADD CONSTRAINT fk_product_prices_sales_channels FOREIGN KEY (sales_channel_id) REFERENCES sales.sales_channels (sales_channel_id);
ALTER TABLE catalog.product_prices ADD CONSTRAINT fk_product_prices_created_by FOREIGN KEY (created_by_employee_id) REFERENCES core.employees (employee_id);
ALTER TABLE sales.sales_orders ADD CONSTRAINT fk_sales_orders_sales_channel_type FOREIGN KEY (sales_channel_id, channel_type) REFERENCES sales.sales_channels (sales_channel_id, channel_type);
ALTER TABLE sales.sales_orders ADD CONSTRAINT fk_sales_orders_customers FOREIGN KEY (customer_id) REFERENCES crm.customers (customer_id);
ALTER TABLE sales.sales_orders ADD CONSTRAINT fk_sales_orders_stores FOREIGN KEY (store_id) REFERENCES core.stores (store_id);
ALTER TABLE sales.sales_orders ADD CONSTRAINT fk_sales_orders_salespersons FOREIGN KEY (salesperson_employee_id) REFERENCES core.employees (employee_id);
ALTER TABLE sales.sales_orders ADD CONSTRAINT fk_sales_orders_customer_addresses FOREIGN KEY (customer_address_id) REFERENCES crm.customer_addresses (customer_address_id);
ALTER TABLE sales.sales_order_items ADD CONSTRAINT fk_sales_order_items_orders FOREIGN KEY (sales_order_id) REFERENCES sales.sales_orders (sales_order_id);
ALTER TABLE sales.sales_order_items ADD CONSTRAINT fk_sales_order_items_products FOREIGN KEY (product_id) REFERENCES catalog.products (product_id);
ALTER TABLE sales.order_status_history ADD CONSTRAINT fk_order_status_history_orders FOREIGN KEY (sales_order_id) REFERENCES sales.sales_orders (sales_order_id);
ALTER TABLE sales.order_status_history ADD CONSTRAINT fk_order_status_history_employees FOREIGN KEY (changed_by_employee_id) REFERENCES core.employees (employee_id);
ALTER TABLE sales.applied_discounts ADD CONSTRAINT fk_applied_discounts_order_items FOREIGN KEY (sales_order_id, sales_order_item_id) REFERENCES sales.sales_order_items (sales_order_id, sales_order_item_id);
ALTER TABLE procurement.purchase_orders ADD CONSTRAINT fk_purchase_orders_suppliers FOREIGN KEY (supplier_id) REFERENCES procurement.suppliers (supplier_id);
ALTER TABLE procurement.purchase_orders ADD CONSTRAINT fk_purchase_orders_responsible FOREIGN KEY (responsible_employee_id) REFERENCES core.employees (employee_id);
ALTER TABLE procurement.purchase_order_items ADD CONSTRAINT fk_purchase_order_items_orders FOREIGN KEY (purchase_order_id) REFERENCES procurement.purchase_orders (purchase_order_id);
ALTER TABLE procurement.purchase_order_items ADD CONSTRAINT fk_purchase_order_items_products FOREIGN KEY (product_id) REFERENCES catalog.products (product_id);
ALTER TABLE procurement.goods_receipts ADD CONSTRAINT fk_goods_receipts_purchase_orders FOREIGN KEY (purchase_order_id) REFERENCES procurement.purchase_orders (purchase_order_id);
ALTER TABLE procurement.goods_receipts ADD CONSTRAINT fk_goods_receipts_stock_locations FOREIGN KEY (stock_location_id) REFERENCES inventory.stock_locations (stock_location_id);
ALTER TABLE procurement.goods_receipts ADD CONSTRAINT fk_goods_receipts_checked_by FOREIGN KEY (checked_by_employee_id) REFERENCES core.employees (employee_id);
ALTER TABLE procurement.goods_receipt_items ADD CONSTRAINT fk_goods_receipt_items_receipts FOREIGN KEY (purchase_order_id, goods_receipt_id) REFERENCES procurement.goods_receipts (purchase_order_id, goods_receipt_id);
ALTER TABLE procurement.goods_receipt_items ADD CONSTRAINT fk_goods_receipt_items_purchase_items FOREIGN KEY (purchase_order_id, purchase_order_item_id) REFERENCES procurement.purchase_order_items (purchase_order_id, purchase_order_item_id);
ALTER TABLE inventory.stock_locations ADD CONSTRAINT fk_stock_locations_stores FOREIGN KEY (store_id) REFERENCES core.stores (store_id);
ALTER TABLE inventory.stock_positions ADD CONSTRAINT fk_stock_positions_products FOREIGN KEY (product_id) REFERENCES catalog.products (product_id);
ALTER TABLE inventory.stock_positions ADD CONSTRAINT fk_stock_positions_locations FOREIGN KEY (stock_location_id) REFERENCES inventory.stock_locations (stock_location_id);
ALTER TABLE inventory.stock_movements ADD CONSTRAINT fk_stock_movements_receipt_items FOREIGN KEY (goods_receipt_item_id) REFERENCES procurement.goods_receipt_items (goods_receipt_item_id);
ALTER TABLE inventory.stock_movements ADD CONSTRAINT fk_stock_movements_fulfillment_items FOREIGN KEY (fulfillment_item_id) REFERENCES logistics.fulfillment_items (fulfillment_item_id);
ALTER TABLE inventory.stock_movements ADD CONSTRAINT fk_stock_movements_return_items FOREIGN KEY (return_item_id) REFERENCES after_sales.return_items (return_item_id);
ALTER TABLE inventory.stock_movements ADD CONSTRAINT fk_stock_movements_transfer_items FOREIGN KEY (stock_transfer_item_id) REFERENCES inventory.stock_transfer_items (stock_transfer_item_id);
ALTER TABLE inventory.stock_movements ADD CONSTRAINT fk_stock_movements_adjustment_employees FOREIGN KEY (adjustment_employee_id) REFERENCES core.employees (employee_id);
ALTER TABLE inventory.stock_reservations ADD CONSTRAINT fk_stock_reservations_order_items FOREIGN KEY (sales_order_id, sales_order_item_id) REFERENCES sales.sales_order_items (sales_order_id, sales_order_item_id);
ALTER TABLE inventory.stock_reservations ADD CONSTRAINT fk_stock_reservations_products FOREIGN KEY (product_id) REFERENCES catalog.products (product_id);
ALTER TABLE inventory.stock_reservations ADD CONSTRAINT fk_stock_reservations_locations FOREIGN KEY (stock_location_id) REFERENCES inventory.stock_locations (stock_location_id);
ALTER TABLE inventory.stock_transfers ADD CONSTRAINT fk_stock_transfers_source_locations FOREIGN KEY (source_stock_location_id) REFERENCES inventory.stock_locations (stock_location_id);
ALTER TABLE inventory.stock_transfers ADD CONSTRAINT fk_stock_transfers_destination_locations FOREIGN KEY (destination_stock_location_id) REFERENCES inventory.stock_locations (stock_location_id);
ALTER TABLE inventory.stock_transfers ADD CONSTRAINT fk_stock_transfers_requested_by FOREIGN KEY (requested_by_employee_id) REFERENCES core.employees (employee_id);
ALTER TABLE inventory.stock_transfers ADD CONSTRAINT fk_stock_transfers_received_by FOREIGN KEY (received_by_employee_id) REFERENCES core.employees (employee_id);
ALTER TABLE inventory.stock_transfer_items ADD CONSTRAINT fk_stock_transfer_items_transfers FOREIGN KEY (stock_transfer_id) REFERENCES inventory.stock_transfers (stock_transfer_id);
ALTER TABLE inventory.stock_transfer_items ADD CONSTRAINT fk_stock_transfer_items_products FOREIGN KEY (product_id) REFERENCES catalog.products (product_id);
ALTER TABLE payments.payments ADD CONSTRAINT fk_payments_sales_orders FOREIGN KEY (sales_order_id) REFERENCES sales.sales_orders (sales_order_id);
ALTER TABLE payments.payments ADD CONSTRAINT fk_payments_payment_methods FOREIGN KEY (payment_method_id) REFERENCES payments.payment_methods (payment_method_id);
ALTER TABLE payments.payment_installments ADD CONSTRAINT fk_payment_installments_payments FOREIGN KEY (payment_id) REFERENCES payments.payments (payment_id);
ALTER TABLE payments.refunds ADD CONSTRAINT fk_refunds_payments FOREIGN KEY (sales_order_id, payment_id) REFERENCES payments.payments (sales_order_id, payment_id);
ALTER TABLE payments.refunds ADD CONSTRAINT fk_refunds_returns FOREIGN KEY (sales_order_id, return_id) REFERENCES after_sales.returns (sales_order_id, return_id);
ALTER TABLE logistics.fulfillments ADD CONSTRAINT fk_fulfillments_sales_orders FOREIGN KEY (sales_order_id) REFERENCES sales.sales_orders (sales_order_id);
ALTER TABLE logistics.fulfillments ADD CONSTRAINT fk_fulfillments_stock_locations FOREIGN KEY (stock_location_id) REFERENCES inventory.stock_locations (stock_location_id);
ALTER TABLE logistics.fulfillments ADD CONSTRAINT fk_fulfillments_pickup_stores FOREIGN KEY (pickup_store_id) REFERENCES core.stores (store_id);
ALTER TABLE logistics.fulfillments ADD CONSTRAINT fk_fulfillments_carriers FOREIGN KEY (carrier_id) REFERENCES logistics.carriers (carrier_id);
ALTER TABLE logistics.fulfillment_items ADD CONSTRAINT fk_fulfillment_items_fulfillments FOREIGN KEY (sales_order_id, fulfillment_id) REFERENCES logistics.fulfillments (sales_order_id, fulfillment_id);
ALTER TABLE logistics.fulfillment_items ADD CONSTRAINT fk_fulfillment_items_order_items FOREIGN KEY (sales_order_id, sales_order_item_id) REFERENCES sales.sales_order_items (sales_order_id, sales_order_item_id);
ALTER TABLE logistics.fulfillment_events ADD CONSTRAINT fk_fulfillment_events_fulfillments FOREIGN KEY (fulfillment_id) REFERENCES logistics.fulfillments (fulfillment_id);
ALTER TABLE logistics.fulfillment_events ADD CONSTRAINT fk_fulfillment_events_employees FOREIGN KEY (recorded_by_employee_id) REFERENCES core.employees (employee_id);
ALTER TABLE after_sales.returns ADD CONSTRAINT fk_returns_sales_orders FOREIGN KEY (sales_order_id) REFERENCES sales.sales_orders (sales_order_id);
ALTER TABLE after_sales.returns ADD CONSTRAINT fk_returns_requested_by FOREIGN KEY (requested_by_employee_id) REFERENCES core.employees (employee_id);
ALTER TABLE after_sales.returns ADD CONSTRAINT fk_returns_approved_by FOREIGN KEY (approved_by_employee_id) REFERENCES core.employees (employee_id);
ALTER TABLE after_sales.return_items ADD CONSTRAINT fk_return_items_returns FOREIGN KEY (sales_order_id, return_id) REFERENCES after_sales.returns (sales_order_id, return_id);
ALTER TABLE after_sales.return_items ADD CONSTRAINT fk_return_items_order_items FOREIGN KEY (sales_order_id, sales_order_item_id) REFERENCES sales.sales_order_items (sales_order_id, sales_order_item_id);
ALTER TABLE after_sales.return_items ADD CONSTRAINT fk_return_items_source_fulfillments FOREIGN KEY (sales_order_id, sales_order_item_id, source_fulfillment_item_id) REFERENCES logistics.fulfillment_items (sales_order_id, sales_order_item_id, fulfillment_item_id);

-- Índices de consulta e de suporte às FKs não cobertas por PK/UNIQUE.
CREATE INDEX idx_employee_assignments_employee_dates ON core.employee_assignments (employee_id, valid_from DESC);
CREATE INDEX idx_employee_assignments_employee_role ON core.employee_assignments (employee_role_id);
CREATE INDEX idx_employee_assignments_store ON core.employee_assignments (store_id);
CREATE INDEX idx_customer_contacts_customer_active ON crm.customer_contacts (customer_id, is_active);
CREATE INDEX idx_customer_addresses_customer_active ON crm.customer_addresses (customer_id, is_active);
CREATE INDEX idx_categories_parent ON catalog.categories (parent_category_id);
CREATE INDEX idx_products_category_status ON catalog.products (category_id, status);
CREATE INDEX idx_products_brand ON catalog.products (brand_id);
CREATE INDEX idx_product_suppliers_supplier ON catalog.product_suppliers (supplier_id);
CREATE INDEX idx_product_prices_product_channel_from ON catalog.product_prices (product_id, sales_channel_id, valid_from DESC);
CREATE INDEX idx_product_prices_created_by ON catalog.product_prices (created_by_employee_id);
CREATE INDEX idx_product_prices_sales_channel ON catalog.product_prices (sales_channel_id);
CREATE INDEX idx_sales_orders_customer_placed ON sales.sales_orders (customer_id, placed_at DESC);
CREATE INDEX idx_sales_orders_channel_placed ON sales.sales_orders (sales_channel_id, placed_at DESC);
CREATE INDEX idx_sales_orders_status_placed ON sales.sales_orders (order_status, placed_at DESC);
CREATE INDEX idx_sales_orders_store ON sales.sales_orders (store_id);
CREATE INDEX idx_sales_orders_salesperson ON sales.sales_orders (salesperson_employee_id);
CREATE INDEX idx_sales_orders_customer_address ON sales.sales_orders (customer_address_id);
CREATE INDEX idx_sales_order_items_product_order ON sales.sales_order_items (product_id, sales_order_id);
CREATE INDEX idx_order_status_history_order_time ON sales.order_status_history (sales_order_id, occurred_at DESC);
CREATE INDEX idx_order_status_history_changed_by ON sales.order_status_history (changed_by_employee_id);
CREATE INDEX idx_applied_discounts_sales_order_item ON sales.applied_discounts (sales_order_item_id);
CREATE INDEX idx_purchase_orders_supplier_date ON procurement.purchase_orders (supplier_id, ordered_at DESC);
CREATE INDEX idx_purchase_orders_responsible ON procurement.purchase_orders (responsible_employee_id);
CREATE INDEX idx_purchase_order_items_product ON procurement.purchase_order_items (product_id);
CREATE INDEX idx_goods_receipts_purchase_time ON procurement.goods_receipts (purchase_order_id, received_at DESC);
CREATE INDEX idx_goods_receipts_stock_location ON procurement.goods_receipts (stock_location_id);
CREATE INDEX idx_goods_receipts_checked_by ON procurement.goods_receipts (checked_by_employee_id);
CREATE INDEX idx_goods_receipt_items_purchase_item ON procurement.goods_receipt_items (purchase_order_item_id);
CREATE INDEX idx_stock_locations_store ON inventory.stock_locations (store_id);
CREATE INDEX idx_stock_movements_product_location_time ON inventory.stock_movements (product_id, stock_location_id, occurred_at DESC);
CREATE INDEX idx_stock_movements_goods_receipt_item ON inventory.stock_movements (goods_receipt_item_id) WHERE goods_receipt_item_id IS NOT NULL;
CREATE INDEX idx_stock_movements_fulfillment_item ON inventory.stock_movements (fulfillment_item_id, occurred_at) WHERE fulfillment_item_id IS NOT NULL;
CREATE INDEX idx_stock_movements_return_item ON inventory.stock_movements (return_item_id) WHERE return_item_id IS NOT NULL;
CREATE INDEX idx_stock_movements_transfer_item ON inventory.stock_movements (stock_transfer_item_id) WHERE stock_transfer_item_id IS NOT NULL;
CREATE INDEX idx_stock_movements_adjustment_employee ON inventory.stock_movements (adjustment_employee_id);
CREATE INDEX idx_stock_reservations_item_status ON inventory.stock_reservations (sales_order_item_id, status);
CREATE INDEX idx_stock_reservations_order_item ON inventory.stock_reservations (sales_order_id, sales_order_item_id);
CREATE INDEX idx_stock_reservations_product ON inventory.stock_reservations (product_id);
CREATE INDEX idx_stock_reservations_location ON inventory.stock_reservations (stock_location_id);
CREATE INDEX idx_stock_transfers_status_requested ON inventory.stock_transfers (status, requested_at DESC);
CREATE INDEX idx_stock_transfers_source_location ON inventory.stock_transfers (source_stock_location_id);
CREATE INDEX idx_stock_transfers_destination_location ON inventory.stock_transfers (destination_stock_location_id);
CREATE INDEX idx_stock_transfers_requested_by ON inventory.stock_transfers (requested_by_employee_id);
CREATE INDEX idx_stock_transfers_received_by ON inventory.stock_transfers (received_by_employee_id);
CREATE INDEX idx_stock_transfer_items_product ON inventory.stock_transfer_items (product_id);
CREATE INDEX idx_payments_order_attempt ON payments.payments (sales_order_id, attempted_at DESC);
CREATE INDEX idx_payments_payment_method ON payments.payments (payment_method_id);
CREATE INDEX idx_payment_installments_payment_status ON payments.payment_installments (payment_id, status);
CREATE INDEX idx_refunds_payment_status ON payments.refunds (payment_id, status);
CREATE INDEX idx_refunds_return ON payments.refunds (return_id);
CREATE INDEX idx_fulfillments_order_status ON logistics.fulfillments (sales_order_id, status);
CREATE INDEX idx_fulfillments_stock_location ON logistics.fulfillments (stock_location_id);
CREATE INDEX idx_fulfillments_pickup_store ON logistics.fulfillments (pickup_store_id);
CREATE INDEX idx_fulfillments_carrier ON logistics.fulfillments (carrier_id);
CREATE INDEX idx_fulfillment_events_fulfillment_time ON logistics.fulfillment_events (fulfillment_id, occurred_at DESC);
CREATE INDEX idx_fulfillment_events_recorded_by ON logistics.fulfillment_events (recorded_by_employee_id);
CREATE INDEX idx_fulfillment_items_order_item ON logistics.fulfillment_items (sales_order_id, sales_order_item_id, fulfillment_id);
CREATE INDEX idx_fulfillment_items_sales_order_item ON logistics.fulfillment_items (sales_order_item_id);
CREATE INDEX idx_returns_order_requested ON after_sales.returns (sales_order_id, requested_at DESC);
CREATE INDEX idx_returns_requested_by ON after_sales.returns (requested_by_employee_id);
CREATE INDEX idx_returns_approved_by ON after_sales.returns (approved_by_employee_id);
CREATE INDEX idx_return_items_order_item ON after_sales.return_items (sales_order_item_id, sales_order_id);
CREATE INDEX idx_return_items_source_fulfillment ON after_sales.return_items (source_fulfillment_item_id);

COMMIT;
