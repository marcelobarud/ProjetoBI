# Diagrama entidade-relacionamento proposto

**Fase 2B — visão do modelo físico aprovado.** Os diagramas mostram cardinalidades e FKs principais, sem listar todas as colunas. O modelo permanece operacional e normalizado; não há dimensões ou fatos analíticos. Algumas tabelas aparecem em mais de um diagrama para tornar os vínculos entre domínios legíveis.

Para manter os identificadores Mermaid legíveis, nomes de entidade usam o schema e a tabela unidos por sublinhado; por exemplo, sales_order_status_history representa sales.order_status_history.

## Visão geral

~~~mermaid
flowchart LR
  core[core — organização]
  crm[crm — clientes]
  catalog[catalog — SKU e preços]
  sales[sales — canais e pedidos]
  procurement[procurement — compras]
  inventory[inventory — estoque]
  payments[payments — operações financeiras]
  logistics[logistics — atendimento]
  after_sales[after_sales — devoluções]

  core --> sales
  core --> procurement
  core --> inventory
  crm --> sales
  catalog --> sales
  catalog --> procurement
  catalog --> inventory
  sales --> payments
  sales --> logistics
  sales --> after_sales
  inventory --> logistics
  inventory --> after_sales
  payments --> after_sales
~~~

## Organização, clientes e catálogo

~~~mermaid
erDiagram
  core_stores ||--o{ core_employee_assignments : lota
  core_employees ||--o{ core_employee_assignments : exerce
  core_employee_roles ||--o{ core_employee_assignments : classifica
  crm_customers ||--o| crm_individual_profiles : possui
  crm_customers ||--o| crm_business_profiles : possui
  crm_customers ||--o{ crm_customer_contacts : informa
  crm_customers ||--o{ crm_customer_addresses : cadastra
  catalog_categories o|--o{ catalog_categories : organiza
  catalog_categories ||--o{ catalog_products : classifica
  catalog_brands o|--o{ catalog_products : identifica
  catalog_products ||--o{ catalog_product_suppliers : fornecido
  procurement_suppliers ||--o{ catalog_product_suppliers : fornece
  catalog_products ||--o{ catalog_product_prices : precifica
  sales_sales_channels ||--o{ catalog_product_prices : define
  core_employees o|--o{ catalog_product_prices : registra
  core_stores {
    bigint store_id PK
  }
  core_employees {
    bigint employee_id PK
  }
  core_employee_roles {
    bigint employee_role_id PK
  }
  core_employee_assignments {
    bigint employee_assignment_id PK
    bigint employee_id FK
    bigint employee_role_id FK
    bigint store_id FK
  }
  crm_customers {
    bigint customer_id PK
  }
  crm_individual_profiles {
    bigint customer_id PK
  }
  crm_business_profiles {
    bigint customer_id PK
  }
  crm_customer_contacts {
    bigint customer_contact_id PK
    bigint customer_id FK
  }
  crm_customer_addresses {
    bigint customer_address_id PK
    bigint customer_id FK
  }
  catalog_categories {
    bigint category_id PK
    bigint parent_category_id FK
  }
  catalog_brands {
    bigint brand_id PK
  }
  catalog_products {
    bigint product_id PK
    bigint category_id FK
    bigint brand_id FK
    jsonb specifications
  }
  catalog_product_suppliers {
    bigint product_supplier_id PK
    bigint product_id FK
    bigint supplier_id FK
  }
  catalog_product_prices {
    bigint product_price_id PK
    bigint product_id FK
    bigint sales_channel_id FK
  }
  procurement_suppliers {
    bigint supplier_id PK
  }
  sales_sales_channels {
    bigint sales_channel_id PK
  }
~~~

## Compras e estoque

~~~mermaid
erDiagram
  procurement_suppliers ||--o{ procurement_purchase_orders : recebe
  core_employees o|--o{ procurement_purchase_orders : responsabiliza
  procurement_purchase_orders ||--o{ procurement_purchase_order_items : detalha
  catalog_products ||--o{ procurement_purchase_order_items : comprado
  procurement_purchase_orders ||--o{ procurement_goods_receipts : recebido
  inventory_stock_locations ||--o{ procurement_goods_receipts : destino
  procurement_goods_receipts ||--o{ procurement_goods_receipt_items : confere
  procurement_purchase_order_items ||--o{ procurement_goods_receipt_items : atende
  core_stores o|--o{ inventory_stock_locations : abriga
  catalog_products ||--o{ inventory_stock_positions : saldo
  inventory_stock_locations ||--o{ inventory_stock_positions : possui
  catalog_products ||--o{ inventory_stock_movements : movimenta
  inventory_stock_locations ||--o{ inventory_stock_movements : registra
  catalog_products ||--o{ inventory_stock_reservations : reserva
  inventory_stock_locations ||--o{ inventory_stock_reservations : reserva
  sales_sales_order_items ||--o{ inventory_stock_reservations : compromete
  inventory_stock_locations ||--o{ inventory_stock_transfers : origem
  inventory_stock_locations ||--o{ inventory_stock_transfers : destino
  inventory_stock_transfers ||--|{ inventory_stock_transfer_items : detalha
  catalog_products ||--o{ inventory_stock_transfer_items : transfere
  procurement_goods_receipt_items o|--o{ inventory_stock_movements : origem_entrada
  logistics_fulfillment_items o|--o{ inventory_stock_movements : origem_saida
  after_sales_return_items o|--o{ inventory_stock_movements : origem_retorno
  logistics_fulfillment_items o|--o{ after_sales_return_items : origem_fisica
  inventory_stock_transfer_items o|--o{ inventory_stock_movements : origem_transferencia
  procurement_suppliers {
    bigint supplier_id PK
  }
  procurement_purchase_orders {
    bigint purchase_order_id PK
    bigint supplier_id FK
  }
  procurement_purchase_order_items {
    bigint purchase_order_item_id PK
    bigint purchase_order_id FK
    bigint product_id FK
  }
  procurement_goods_receipts {
    bigint goods_receipt_id PK
    bigint purchase_order_id FK
    bigint stock_location_id FK
  }
  procurement_goods_receipt_items {
    bigint goods_receipt_item_id PK
    bigint goods_receipt_id FK
    bigint purchase_order_item_id FK
  }
  inventory_stock_locations {
    bigint stock_location_id PK
    bigint store_id FK
  }
  inventory_stock_positions {
    bigint stock_position_id PK
    bigint product_id FK
    bigint stock_location_id FK
  }
  inventory_stock_movements {
    bigint stock_movement_id PK
    bigint product_id FK
    bigint stock_location_id FK
    bigint fulfillment_item_id FK
    numeric unit_cost
  }
  inventory_stock_reservations {
    bigint stock_reservation_id PK
    bigint sales_order_item_id FK
    bigint stock_location_id FK
  }
  inventory_stock_transfers {
    bigint stock_transfer_id PK
    bigint source_stock_location_id FK
    bigint destination_stock_location_id FK
  }
  inventory_stock_transfer_items {
    bigint stock_transfer_item_id PK
    bigint stock_transfer_id FK
    bigint product_id FK
  }
  catalog_products {
    bigint product_id PK
  }
  core_employees {
    bigint employee_id PK
  }
  core_stores {
    bigint store_id PK
  }
  sales_sales_order_items {
    bigint sales_order_item_id PK
    bigint sales_order_id FK
  }
  logistics_fulfillment_items {
    bigint fulfillment_item_id PK
    bigint sales_order_item_id FK
  }
  after_sales_return_items {
    bigint return_item_id PK
    bigint sales_order_item_id FK
  }
~~~

## Pedidos, pagamentos e devoluções

~~~mermaid
erDiagram
  sales_sales_channels ||--o{ sales_sales_orders : origina
  crm_customers o|--o{ sales_sales_orders : identifica
  core_stores o|--o{ sales_sales_orders : registra
  core_employees o|--o{ sales_sales_orders : vende
  crm_customer_addresses o|--o{ sales_sales_orders : endereco_snapshot
  sales_sales_orders ||--o{ sales_sales_order_items : contem
  catalog_products ||--o{ sales_sales_order_items : vendido
  sales_sales_orders ||--o{ sales_order_status_history : registra
  core_employees o|--o{ sales_order_status_history : altera
  sales_sales_order_items ||--o{ sales_applied_discounts : recebe
  sales_sales_orders ||--o{ payments_payments : cobra
  payments_payment_methods ||--o{ payments_payments : meio
  payments_payments ||--o{ payments_payment_installments : parcela
  payments_payments ||--o{ payments_refunds : reembolsa
  after_sales_returns o|--o{ payments_refunds : associado
  sales_sales_orders ||--o{ after_sales_returns : origina
  after_sales_returns ||--o{ after_sales_return_items : detalha
  sales_sales_order_items ||--o{ after_sales_return_items : devolve
  core_employees o|--o{ after_sales_returns : solicita_aprova
  sales_sales_orders {
    bigint sales_order_id PK
    bigint sales_channel_id FK
    bigint customer_id FK
  }
  sales_sales_order_items {
    bigint sales_order_item_id PK
    bigint sales_order_id FK
    bigint product_id FK
  }
  sales_order_status_history {
    bigint order_status_history_id PK
    bigint sales_order_id FK
  }
  sales_applied_discounts {
    bigint applied_discount_id PK
    bigint sales_order_id FK
    bigint sales_order_item_id FK
  }
  payments_payments {
    bigint payment_id PK
    bigint sales_order_id FK
    bigint payment_method_id FK
  }
  payments_payment_methods {
    bigint payment_method_id PK
  }
  payments_payment_installments {
    bigint payment_installment_id PK
    bigint payment_id FK
  }
  payments_refunds {
    bigint refund_id PK
    bigint payment_id FK
    bigint return_id FK
  }
  after_sales_returns {
    bigint return_id PK
    bigint sales_order_id FK
  }
  after_sales_return_items {
    bigint return_item_id PK
    bigint return_id FK
    bigint sales_order_item_id FK
    bigint source_fulfillment_item_id FK
  }
  sales_sales_channels {
    bigint sales_channel_id PK
  }
  crm_customers {
    bigint customer_id PK
  }
  crm_customer_addresses {
    bigint customer_address_id PK
  }
  core_stores {
    bigint store_id PK
  }
  core_employees {
    bigint employee_id PK
  }
  catalog_products {
    bigint product_id PK
  }
~~~

## Atendimento e logística

~~~mermaid
erDiagram
  sales_sales_orders ||--o{ logistics_fulfillments : atendido_por
  logistics_fulfillments ||--o{ logistics_fulfillment_items : separa
  sales_sales_order_items ||--o{ logistics_fulfillment_items : distribuido
  inventory_stock_locations o|--o{ logistics_fulfillments : origem
  core_stores o|--o{ logistics_fulfillments : retirada
  logistics_carriers o|--o{ logistics_fulfillments : transporta
  logistics_fulfillments ||--o{ logistics_fulfillment_events : acompanha
  core_employees o|--o{ logistics_fulfillment_events : registra
  logistics_fulfillments {
    bigint fulfillment_id PK
    bigint sales_order_id FK
    bigint stock_location_id FK
    bigint pickup_store_id FK
    bigint carrier_id FK
  }
  logistics_fulfillment_items {
    bigint fulfillment_item_id PK
    bigint fulfillment_id FK
    bigint sales_order_item_id FK
  }
  logistics_fulfillment_events {
    bigint fulfillment_event_id PK
    bigint fulfillment_id FK
  }
  logistics_carriers {
    bigint carrier_id PK
  }
  sales_sales_orders {
    bigint sales_order_id PK
  }
  sales_sales_order_items {
    bigint sales_order_item_id PK
    bigint sales_order_id FK
  }
  inventory_stock_locations {
    bigint stock_location_id PK
  }
  core_stores {
    bigint store_id PK
  }
  core_employees {
    bigint employee_id PK
  }
~~~
