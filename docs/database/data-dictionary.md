# Dicionário de dados proposto

**Fase 2A.1 — proposta física consolidada, pronta para revisão final.** Os tipos são PostgreSQL 18. “Não”/“Sim” indicam nulabilidade proposta; identidade e colunas calculadas são indicadas nas observações. Não há script executável neste documento.

## Convenções

- Todas as PKs técnicas usam BIGINT GENERATED ALWAYS AS IDENTITY, exceto customer_id nas tabelas de perfil, que é PK/FK sem identidade.
- Códigos internos e referências externas são atributos distintos dos IDs técnicos. Timestamps administrativos comuns são created_at TIMESTAMPTZ NOT NULL e updated_at TIMESTAMPTZ NOT NULL, mantidos pela aplicação.
- Não há defaults implícitos definidos pelo banco além da geração das identidades e da coluna calculada explicitamente indicada; valores iniciais e timestamps são fornecidos pela aplicação.
- Valores monetários BRL: NUMERIC(19,2); custos unitários: NUMERIC(20,8); quantidades inteiras: BIGINT. Não usar ponto flutuante para dinheiro.
- Domínios de status, tipo e estado são limitados por CHECK, detalhados em constraints-and-indexes.md.

## core

### core.stores

| Coluna | Tipo | Nulável | Finalidade |
|---|---|---|---|
| store_id | BIGINT GENERATED ALWAYS AS IDENTITY | Não | PK técnica. |
| store_code | VARCHAR(30) | Não | Código interno único. |
| name | VARCHAR(160) | Não | Nome da loja. |
| status | VARCHAR(20) | Não | Estado operacional. |
| opened_on | DATE | Sim | Data civil de abertura. |
| closed_on | DATE | Sim | Data civil de encerramento. |
| phone | VARCHAR(30) | Sim | Telefone de contato. |
| email | VARCHAR(254) | Sim | E-mail de contato. |
| created_at | TIMESTAMPTZ | Não | Criação. |
| updated_at | TIMESTAMPTZ | Não | Última atualização. |
| notes | TEXT | Sim | Observações administrativas. |

### core.employees

| Coluna | Tipo | Nulável | Finalidade |
|---|---|---|---|
| employee_id | BIGINT GENERATED ALWAYS AS IDENTITY | Não | PK técnica. |
| employee_code | VARCHAR(30) | Não | Código interno único. |
| first_name | VARCHAR(100) | Não | Nome. |
| last_name | VARCHAR(120) | Não | Sobrenome. |
| email | VARCHAR(254) | Sim | E-mail de trabalho. |
| phone | VARCHAR(30) | Sim | Telefone. |
| hired_on | DATE | Não | Data civil de admissão. |
| terminated_on | DATE | Sim | Data civil de desligamento. |
| status | VARCHAR(20) | Não | Estado cadastral. |
| created_at | TIMESTAMPTZ | Não | Criação. |
| updated_at | TIMESTAMPTZ | Não | Última atualização. |

### core.employee_roles

| Coluna | Tipo | Nulável | Finalidade |
|---|---|---|---|
| employee_role_id | BIGINT GENERATED ALWAYS AS IDENTITY | Não | PK técnica. |
| role_code | VARCHAR(30) | Não | Código único da função. |
| name | VARCHAR(100) | Não | Nome da função. |
| is_active | BOOLEAN | Não | Disponibilidade para novos vínculos. |
| created_at | TIMESTAMPTZ | Não | Criação. |
| updated_at | TIMESTAMPTZ | Não | Última atualização. |

### core.employee_assignments

| Coluna | Tipo | Nulável | Finalidade |
|---|---|---|---|
| employee_assignment_id | BIGINT GENERATED ALWAYS AS IDENTITY | Não | PK técnica. |
| employee_id | BIGINT | Não | FK para employees. |
| employee_role_id | BIGINT | Não | FK para employee_roles. |
| store_id | BIGINT | Sim | FK para stores; nulo para função central/remota. |
| valid_from | DATE | Não | Início civil da vigência. |
| valid_to | DATE | Sim | Fim civil inclusivo; nulo enquanto vigente. |
| created_at | TIMESTAMPTZ | Não | Criação do vínculo. |
| notes | TEXT | Sim | Observações. |

## crm

### crm.customers

| Coluna | Tipo | Nulável | Finalidade |
|---|---|---|---|
| customer_id | BIGINT GENERATED ALWAYS AS IDENTITY | Não | PK técnica. |
| customer_code | VARCHAR(30) | Não | Código interno único. |
| customer_type | VARCHAR(12) | Não | individual ou business. |
| display_name | VARCHAR(180) | Não | Nome de exibição. |
| status | VARCHAR(20) | Não | Estado cadastral. |
| created_at | TIMESTAMPTZ | Não | Criação. |
| updated_at | TIMESTAMPTZ | Não | Última atualização. |
| notes | TEXT | Sim | Observações administrativas. |

### crm.individual_profiles

| Coluna | Tipo | Nulável | Finalidade |
|---|---|---|---|
| customer_id | BIGINT | Não | PK/FK para customers, sem identidade própria. |
| cpf | VARCHAR(11) | Sim | CPF somente dígitos, único quando informado. |
| birth_date | DATE | Sim | Data civil de nascimento. |
| created_at | TIMESTAMPTZ | Não | Criação do perfil. |
| updated_at | TIMESTAMPTZ | Não | Última atualização. |

### crm.business_profiles

| Coluna | Tipo | Nulável | Finalidade |
|---|---|---|---|
| customer_id | BIGINT | Não | PK/FK para customers, sem identidade própria. |
| legal_name | VARCHAR(200) | Não | Razão social informada. |
| trade_name | VARCHAR(200) | Sim | Nome fantasia. |
| cnpj | VARCHAR(14) | Sim | CNPJ somente dígitos, único quando informado. |
| state_registration | VARCHAR(30) | Sim | Inscrição estadual informada. |
| created_at | TIMESTAMPTZ | Não | Criação do perfil. |
| updated_at | TIMESTAMPTZ | Não | Última atualização. |

### crm.customer_contacts

| Coluna | Tipo | Nulável | Finalidade |
|---|---|---|---|
| customer_contact_id | BIGINT GENERATED ALWAYS AS IDENTITY | Não | PK técnica. |
| customer_id | BIGINT | Não | FK para customers. |
| contact_type | VARCHAR(20) | Não | Tipo limitado por domínio. |
| contact_value | VARCHAR(254) | Não | Valor informado. |
| is_primary | BOOLEAN | Não | Contato preferencial. |
| is_active | BOOLEAN | Não | Estado atual. |
| created_at | TIMESTAMPTZ | Não | Criação. |
| updated_at | TIMESTAMPTZ | Não | Última atualização. |

### crm.customer_addresses

| Coluna | Tipo | Nulável | Finalidade |
|---|---|---|---|
| customer_address_id | BIGINT GENERATED ALWAYS AS IDENTITY | Não | PK técnica. |
| customer_id | BIGINT | Não | FK para customers. |
| address_label | VARCHAR(50) | Sim | Rótulo residencial/comercial. |
| recipient_name | VARCHAR(180) | Sim | Destinatário usual. |
| postal_code | VARCHAR(8) | Não | CEP somente dígitos. |
| street | VARCHAR(180) | Não | Logradouro. |
| street_number | VARCHAR(30) | Não | Número ou indicação aceita para endereço sem número. |
| complement | VARCHAR(100) | Sim | Complemento. |
| district | VARCHAR(100) | Não | Bairro/distrito. |
| city | VARCHAR(120) | Não | Município informado. |
| state_code | CHAR(2) | Não | UF brasileira. |
| country_code | CHAR(2) | Não | País; operação proposta brasileira. |
| is_default | BOOLEAN | Não | Endereço preferencial. |
| is_active | BOOLEAN | Não | Disponibilidade cadastral. |
| created_at | TIMESTAMPTZ | Não | Criação. |
| updated_at | TIMESTAMPTZ | Não | Última atualização. |

## catalog

### catalog.categories

| Coluna | Tipo | Nulável | Finalidade |
|---|---|---|---|
| category_id | BIGINT GENERATED ALWAYS AS IDENTITY | Não | PK técnica. |
| parent_category_id | BIGINT | Sim | FK autorreferente para categoria-pai. |
| category_code | VARCHAR(40) | Não | Código único. |
| name | VARCHAR(120) | Não | Nome. |
| is_active | BOOLEAN | Não | Disponibilidade. |
| created_at | TIMESTAMPTZ | Não | Criação. |
| updated_at | TIMESTAMPTZ | Não | Última atualização. |

### catalog.brands

| Coluna | Tipo | Nulável | Finalidade |
|---|---|---|---|
| brand_id | BIGINT GENERATED ALWAYS AS IDENTITY | Não | PK técnica. |
| brand_code | VARCHAR(40) | Não | Código único. |
| name | VARCHAR(120) | Não | Marca. |
| is_active | BOOLEAN | Não | Disponibilidade. |
| created_at | TIMESTAMPTZ | Não | Criação. |
| updated_at | TIMESTAMPTZ | Não | Última atualização. |

### catalog.products

| Coluna | Tipo | Nulável | Finalidade |
|---|---|---|---|
| product_id | BIGINT GENERATED ALWAYS AS IDENTITY | Não | PK técnica do SKU. |
| sku | VARCHAR(60) | Não | Identificador único do SKU vendável. |
| category_id | BIGINT | Não | FK para categories. |
| brand_id | BIGINT | Sim | FK para brands. |
| name | VARCHAR(180) | Não | Nome comercial. |
| description | TEXT | Sim | Descrição operacional. |
| specifications | JSONB | Sim | Objeto opcional com especificações técnicas variáveis do SKU; chaves snake_case; coerência por categoria validada pelo gerador; sem schema rígido ou GIN inicial. |
| unit_of_measure | VARCHAR(12) | Não | Unidade comercial/de estoque. |
| status | VARCHAR(20) | Não | Estado de comercialização. |
| created_at | TIMESTAMPTZ | Não | Criação. |
| updated_at | TIMESTAMPTZ | Não | Última atualização. |

### catalog.product_suppliers

| Coluna | Tipo | Nulável | Finalidade |
|---|---|---|---|
| product_supplier_id | BIGINT GENERATED ALWAYS AS IDENTITY | Não | PK técnica. |
| product_id | BIGINT | Não | FK para products. |
| supplier_id | BIGINT | Não | FK para procurement.suppliers. |
| supplier_product_code | VARCHAR(80) | Sim | Referência do produto no fornecedor. |
| is_preferred | BOOLEAN | Não | Preferência atual de compra. |
| is_active | BOOLEAN | Não | Estado da associação. |
| created_at | TIMESTAMPTZ | Não | Criação. |
| updated_at | TIMESTAMPTZ | Não | Última atualização. |

### catalog.product_prices

| Coluna | Tipo | Nulável | Finalidade |
|---|---|---|---|
| product_price_id | BIGINT GENERATED ALWAYS AS IDENTITY | Não | PK técnica. |
| product_id | BIGINT | Não | FK para products. |
| sales_channel_id | BIGINT | Não | FK para sales.sales_channels. |
| amount | NUMERIC(19,2) | Não | Preço comercial BRL. |
| valid_from | TIMESTAMPTZ | Não | Início da vigência. |
| valid_to | TIMESTAMPTZ | Sim | Fim exclusivo; nulo enquanto vigente. |
| created_at | TIMESTAMPTZ | Não | Registro da versão de preço. |
| created_by_employee_id | BIGINT | Sim | Funcionário que registrou a alteração. |

## inventory

### inventory.stock_locations

| Coluna | Tipo | Nulável | Finalidade |
|---|---|---|---|
| stock_location_id | BIGINT GENERATED ALWAYS AS IDENTITY | Não | PK técnica. |
| store_id | BIGINT | Sim | FK para core.stores; nulo para centro independente. |
| location_code | VARCHAR(40) | Não | Código único do local. |
| name | VARCHAR(120) | Não | Nome operacional. |
| location_type | VARCHAR(20) | Não | Tipo de local, limitado por domínio. |
| status | VARCHAR(20) | Não | Estado operacional. |
| created_at | TIMESTAMPTZ | Não | Criação. |
| updated_at | TIMESTAMPTZ | Não | Última atualização. |

### inventory.stock_positions

| Coluna | Tipo | Nulável | Finalidade |
|---|---|---|---|
| stock_position_id | BIGINT GENERATED ALWAYS AS IDENTITY | Não | PK técnica. |
| product_id | BIGINT | Não | FK para catalog.products. |
| stock_location_id | BIGINT | Não | FK para stock_locations. |
| on_hand_quantity | BIGINT | Não | Saldo físico persistido. |
| reserved_quantity | BIGINT | Não | Quantidade comprometida por reservas ativas. |
| available_quantity | BIGINT GENERATED ALWAYS AS (on_hand_quantity - reserved_quantity) STORED | Não | Calculada como físico menos reservado. |
| average_unit_cost | NUMERIC(20,8) | Não | Custo médio móvel unitário persistido. |
| updated_at | TIMESTAMPTZ | Não | Última atualização transacional da posição. |

### inventory.stock_movements

| Coluna | Tipo | Nulável | Finalidade |
|---|---|---|---|
| stock_movement_id | BIGINT GENERATED ALWAYS AS IDENTITY | Não | PK técnica. |
| product_id | BIGINT | Não | FK para products. |
| stock_location_id | BIGINT | Não | FK para stock_locations. |
| movement_type | VARCHAR(24) | Não | Tipo/direção do movimento. |
| quantity_delta | BIGINT | Não | Variação assinada da quantidade física. |
| unit_cost | NUMERIC(20,8) | Sim | Custo unitário aplicado ao movimento; obrigatório em recebimento, saída fulfillment, retorno físico e transferências; saídas fulfillment registram a média vigente e retornos vendáveis usam custo histórico alocado. |
| goods_receipt_item_id | BIGINT | Sim | Origem opcional: item de recebimento. |
| fulfillment_item_id | BIGINT | Sim | Origem opcional: item atendido. |
| return_item_id | BIGINT | Sim | Origem opcional: item de devolução. |
| stock_transfer_item_id | BIGINT | Sim | Origem opcional: item transferido. |
| adjustment_employee_id | BIGINT | Sim | Responsável por ajuste manual. |
| reason_code | VARCHAR(30) | Sim | Motivo limitado por domínio para ajuste. |
| occurred_at | TIMESTAMPTZ | Não | Instante do movimento efetivo. |
| created_at | TIMESTAMPTZ | Não | Instante de registro. |
| notes | TEXT | Sim | Observações. |

### inventory.stock_reservations

| Coluna | Tipo | Nulável | Finalidade |
|---|---|---|---|
| stock_reservation_id | BIGINT GENERATED ALWAYS AS IDENTITY | Não | PK técnica. |
| sales_order_id | BIGINT | Não | FK composta para item do pedido. |
| sales_order_item_id | BIGINT | Não | Item reservado. |
| product_id | BIGINT | Não | SKU associado, consistente com a linha do pedido. |
| stock_location_id | BIGINT | Não | Local reservado. |
| quantity | BIGINT | Não | Quantidade comprometida. |
| status | VARCHAR(20) | Não | active, released, expired ou consumed. |
| reserved_at | TIMESTAMPTZ | Não | Instante da reserva. |
| expires_at | TIMESTAMPTZ | Sim | Expiração opcional. |
| released_at | TIMESTAMPTZ | Sim | Instante de liberação/consumo. |
| created_at | TIMESTAMPTZ | Não | Criação. |

### inventory.stock_transfers

| Coluna | Tipo | Nulável | Finalidade |
|---|---|---|---|
| stock_transfer_id | BIGINT GENERATED ALWAYS AS IDENTITY | Não | PK técnica. |
| transfer_number | VARCHAR(40) | Não | Número único. |
| source_stock_location_id | BIGINT | Não | Local de origem. |
| destination_stock_location_id | BIGINT | Não | Local de destino diferente da origem. |
| requested_by_employee_id | BIGINT | Sim | Funcionário solicitante. |
| received_by_employee_id | BIGINT | Sim | Funcionário que confirma recebimento. |
| status | VARCHAR(20) | Não | Estado do ciclo da transferência. |
| requested_at | TIMESTAMPTZ | Não | Instante de solicitação. |
| dispatched_at | TIMESTAMPTZ | Sim | Instante de saída. |
| received_at | TIMESTAMPTZ | Sim | Instante de conclusão no destino. |
| created_at | TIMESTAMPTZ | Não | Criação. |
| updated_at | TIMESTAMPTZ | Não | Última atualização. |
| notes | TEXT | Sim | Observações e diferenças. |

### inventory.stock_transfer_items

| Coluna | Tipo | Nulável | Finalidade |
|---|---|---|---|
| stock_transfer_item_id | BIGINT GENERATED ALWAYS AS IDENTITY | Não | PK técnica. |
| stock_transfer_id | BIGINT | Não | FK para stock_transfers. |
| product_id | BIGINT | Não | FK para products. |
| line_number | INTEGER | Não | Sequência única por transferência. |
| quantity_planned | BIGINT | Não | Quantidade planejada. |
| quantity_dispatched | BIGINT | Sim | Quantidade expedida. |
| quantity_received | BIGINT | Sim | Quantidade recebida. |
| created_at | TIMESTAMPTZ | Não | Criação da linha. |

## payments

### payments.payment_methods

| Coluna | Tipo | Nulável | Finalidade |
|---|---|---|---|
| payment_method_id | BIGINT GENERATED ALWAYS AS IDENTITY | Não | PK técnica. |
| method_code | VARCHAR(30) | Não | Código único. |
| name | VARCHAR(100) | Não | Nome do meio. |
| method_type | VARCHAR(24) | Não | Tipo operacional do meio de pagamento. |
| is_installment_capable | BOOLEAN | Não | Indica se pode parcelar. |
| is_active | BOOLEAN | Não | Disponibilidade para novas operações. |
| created_at | TIMESTAMPTZ | Não | Criação. |
| updated_at | TIMESTAMPTZ | Não | Última atualização. |

### payments.payments

| Coluna | Tipo | Nulável | Finalidade |
|---|---|---|---|
| payment_id | BIGINT GENERATED ALWAYS AS IDENTITY | Não | PK técnica. |
| sales_order_id | BIGINT | Não | FK para sales_orders. |
| payment_method_id | BIGINT | Não | FK para payment_methods. |
| payment_reference | VARCHAR(120) | Sim | Referência do gateway/adquirente. |
| status | VARCHAR(20) | Não | Estado financeiro independente do pedido. |
| amount | NUMERIC(19,2) | Não | Valor tentado/operado. |
| currency_code | CHAR(3) | Não | Moeda da operação. |
| attempted_at | TIMESTAMPTZ | Não | Instante da tentativa. |
| authorized_at | TIMESTAMPTZ | Sim | Instante de autorização. |
| settled_at | TIMESTAMPTZ | Sim | Instante de liquidação, quando aplicável. |
| external_reference | VARCHAR(120) | Sim | Referência externa idempotente. |
| created_at | TIMESTAMPTZ | Não | Criação. |
| updated_at | TIMESTAMPTZ | Não | Última atualização. |

### payments.payment_installments

| Coluna | Tipo | Nulável | Finalidade |
|---|---|---|---|
| payment_installment_id | BIGINT GENERATED ALWAYS AS IDENTITY | Não | PK técnica. |
| payment_id | BIGINT | Não | FK para payments. |
| installment_number | INTEGER | Não | Número sequencial da parcela. |
| due_on | DATE | Sim | Vencimento civil. |
| amount | NUMERIC(19,2) | Não | Valor da parcela. |
| status | VARCHAR(20) | Não | Situação individual. |
| paid_at | TIMESTAMPTZ | Sim | Instante de pagamento. |
| external_reference | VARCHAR(120) | Sim | Referência externa da parcela. |
| created_at | TIMESTAMPTZ | Não | Criação. |
| updated_at | TIMESTAMPTZ | Não | Última atualização. |

### payments.refunds

| Coluna | Tipo | Nulável | Finalidade |
|---|---|---|---|
| refund_id | BIGINT GENERATED ALWAYS AS IDENTITY | Não | PK técnica. |
| sales_order_id | BIGINT | Não | Chave para validar mesmo pedido. |
| payment_id | BIGINT | Não | FK composta para pagamento/pedido. |
| return_id | BIGINT | Sim | FK composta para devolução/pedido; nulo para estorno sem devolução. |
| status | VARCHAR(20) | Não | Estado próprio do reembolso. |
| amount | NUMERIC(19,2) | Não | Valor solicitado/estornado. |
| reason_code | VARCHAR(30) | Sim | Motivo limitado por domínio. |
| requested_at | TIMESTAMPTZ | Não | Instante de solicitação. |
| processed_at | TIMESTAMPTZ | Sim | Instante de processamento. |
| external_reference | VARCHAR(120) | Sim | Referência do processador. |
| created_at | TIMESTAMPTZ | Não | Criação. |
| updated_at | TIMESTAMPTZ | Não | Última atualização. |

## logistics

### logistics.carriers

| Coluna | Tipo | Nulável | Finalidade |
|---|---|---|---|
| carrier_id | BIGINT GENERATED ALWAYS AS IDENTITY | Não | PK técnica. |
| carrier_code | VARCHAR(30) | Não | Código único. |
| name | VARCHAR(160) | Não | Transportadora/prestador. |
| tax_identifier | VARCHAR(14) | Sim | Identificador fiscal informado. |
| is_active | BOOLEAN | Não | Disponibilidade. |
| created_at | TIMESTAMPTZ | Não | Criação. |
| updated_at | TIMESTAMPTZ | Não | Última atualização. |

### logistics.fulfillments

| Coluna | Tipo | Nulável | Finalidade |
|---|---|---|---|
| fulfillment_id | BIGINT GENERATED ALWAYS AS IDENTITY | Não | PK técnica. |
| sales_order_id | BIGINT | Não | FK para sales_orders. |
| fulfillment_number | VARCHAR(40) | Não | Número único. |
| fulfillment_type | VARCHAR(20) | Não | delivery ou store_pickup. |
| status | VARCHAR(24) | Não | Estado de execução independente do pedido. |
| stock_location_id | BIGINT | Sim | Local de origem operacional. |
| pickup_store_id | BIGINT | Sim | Loja de retirada. |
| carrier_id | BIGINT | Sim | Transportadora, nula em retirada/entrega própria. |
| tracking_number | VARCHAR(100) | Sim | Código de rastreio. |
| planned_at | TIMESTAMPTZ | Sim | Instante previsto. |
| dispatched_at | TIMESTAMPTZ | Sim | Instante de despacho. |
| completed_at | TIMESTAMPTZ | Sim | Instante de entrega/retirada concluída. |
| created_at | TIMESTAMPTZ | Não | Criação. |
| updated_at | TIMESTAMPTZ | Não | Última atualização. |

### logistics.fulfillment_items

| Coluna | Tipo | Nulável | Finalidade |
|---|---|---|---|
| fulfillment_item_id | BIGINT GENERATED ALWAYS AS IDENTITY | Não | PK técnica. |
| sales_order_id | BIGINT | Não | Chave para consistência pedido/item. |
| fulfillment_id | BIGINT | Não | FK composta para remessa/pedido. |
| sales_order_item_id | BIGINT | Não | FK composta para item/pedido. |
| quantity_allocated | BIGINT | Não | Quantidade destinada à remessa. |
| fulfilled_quantity | BIGINT | Não | Quantidade efetivamente entregue/retirada. |
| created_at | TIMESTAMPTZ | Não | Criação. |
| updated_at | TIMESTAMPTZ | Não | Atualização de atendimento. |

### logistics.fulfillment_events

| Coluna | Tipo | Nulável | Finalidade |
|---|---|---|---|
| fulfillment_event_id | BIGINT GENERATED ALWAYS AS IDENTITY | Não | PK técnica. |
| fulfillment_id | BIGINT | Não | FK para fulfillments. |
| event_type | VARCHAR(30) | Não | Evento logístico limitado por domínio. |
| occurred_at | TIMESTAMPTZ | Não | Instante real do evento. |
| recorded_by_employee_id | BIGINT | Sim | Funcionário registrador. |
| description | VARCHAR(240) | Sim | Detalhe operacional. |
| external_reference | VARCHAR(120) | Sim | Referência da transportadora/gateway. |
| created_at | TIMESTAMPTZ | Não | Instante de registro. |

## after_sales

### after_sales.returns

| Coluna | Tipo | Nulável | Finalidade |
|---|---|---|---|
| return_id | BIGINT GENERATED ALWAYS AS IDENTITY | Não | PK técnica. |
| sales_order_id | BIGINT | Não | FK para sales_orders. |
| return_number | VARCHAR(40) | Não | Número único. |
| status | VARCHAR(24) | Não | Estado administrativo da devolução. |
| reason_code | VARCHAR(30) | Não | Motivo limitado por domínio. |
| requested_by_employee_id | BIGINT | Sim | Funcionário que registrou solicitação. |
| approved_by_employee_id | BIGINT | Sim | Funcionário aprovador. |
| requested_at | TIMESTAMPTZ | Não | Instante de solicitação. |
| decided_at | TIMESTAMPTZ | Sim | Instante de decisão. |
| created_at | TIMESTAMPTZ | Não | Criação. |
| updated_at | TIMESTAMPTZ | Não | Última atualização. |
| notes | TEXT | Sim | Observações. |

### after_sales.return_items

| Coluna | Tipo | Nulável | Finalidade |
|---|---|---|---|
| return_item_id | BIGINT GENERATED ALWAYS AS IDENTITY | Não | PK técnica. |
| sales_order_id | BIGINT | Não | Chave para consistência devolução/item. |
| return_id | BIGINT | Não | FK composta para returns/sales_order. |
| sales_order_item_id | BIGINT | Não | FK composta para item/pedido. |
| source_fulfillment_item_id | BIGINT | Sim | FK composta para fulfillment item do mesmo pedido e item vendido; exigido antes de confirmar recebimento físico/devolução vendável. |
| quantity_requested | BIGINT | Não | Quantidade solicitada. |
| quantity_approved | BIGINT | Não | Quantidade aprovada. |
| quantity_received | BIGINT | Não | Quantidade fisicamente recebida. |
| item_condition | VARCHAR(20) | Sim | Condição observada no recebimento. |
| stock_destination | VARCHAR(20) | Sim | Vendável, quarentena, reparo ou descarte. |
| received_at | TIMESTAMPTZ | Sim | Instante de recebimento físico. |
| created_at | TIMESTAMPTZ | Não | Criação. |
| notes | TEXT | Sim | Observações. |

## sales

### sales.sales_channels

| Coluna | Tipo | Nulável | Finalidade |
|---|---|---|---|
| sales_channel_id | BIGINT GENERATED ALWAYS AS IDENTITY | Não | PK técnica. |
| channel_code | VARCHAR(30) | Não | Código único do canal. |
| name | VARCHAR(100) | Não | Nome operacional. |
| channel_type | VARCHAR(20) | Não | physical, ecommerce ou marketplace. |
| is_active | BOOLEAN | Não | Disponibilidade para novas vendas. |
| created_at | TIMESTAMPTZ | Não | Criação. |
| updated_at | TIMESTAMPTZ | Não | Última atualização. |

### sales.sales_orders

| Coluna | Tipo | Nulável | Finalidade |
|---|---|---|---|
| sales_order_id | BIGINT GENERATED ALWAYS AS IDENTITY | Não | PK técnica. |
| order_number | VARCHAR(40) | Não | Número de negócio único. |
| sales_channel_id | BIGINT | Não | FK para sales_channels. |
| channel_type | VARCHAR(20) | Não | Cópia protegida do tipo do canal para CHECK de cliente. |
| customer_id | BIGINT | Sim | FK para customers; nulo somente em canal físico. |
| store_id | BIGINT | Sim | Loja relacionada à venda física, se conhecida. |
| salesperson_employee_id | BIGINT | Sim | Funcionário vendedor. |
| customer_address_id | BIGINT | Sim | Endereço cadastral selecionado, quando aplicável. |
| order_status | VARCHAR(24) | Não | Estado comercial atual. |
| placed_at | TIMESTAMPTZ | Não | Instante de realização. |
| currency_code | CHAR(3) | Não | Moeda; proposta BRL. |
| subtotal_amount | NUMERIC(19,2) | Não | Soma comercial antes de descontos/frete. |
| discount_amount | NUMERIC(19,2) | Não | Total de descontos alocados. |
| shipping_amount | NUMERIC(19,2) | Não | Frete cobrado. |
| total_amount | NUMERIC(19,2) | Não | Total snapshot do pedido. |
| recipient_name | VARCHAR(180) | Sim | Snapshot do destinatário. |
| postal_code_snapshot | VARCHAR(8) | Sim | CEP snapshot. |
| street_snapshot | VARCHAR(180) | Sim | Logradouro snapshot. |
| street_number_snapshot | VARCHAR(30) | Sim | Número snapshot. |
| complement_snapshot | VARCHAR(100) | Sim | Complemento snapshot. |
| district_snapshot | VARCHAR(100) | Sim | Bairro snapshot. |
| city_snapshot | VARCHAR(120) | Sim | Município snapshot. |
| state_code_snapshot | CHAR(2) | Sim | UF snapshot. |
| country_code_snapshot | CHAR(2) | Sim | País snapshot. |
| external_reference | VARCHAR(120) | Sim | Referência de marketplace/integração. |
| created_at | TIMESTAMPTZ | Não | Criação do registro. |
| updated_at | TIMESTAMPTZ | Não | Última atualização. |
| notes | TEXT | Sim | Observações operacionais. |

### sales.sales_order_items

| Coluna | Tipo | Nulável | Finalidade |
|---|---|---|---|
| sales_order_item_id | BIGINT GENERATED ALWAYS AS IDENTITY | Não | PK técnica. |
| sales_order_id | BIGINT | Não | FK para sales_orders. |
| line_number | INTEGER | Não | Sequência única no pedido. |
| product_id | BIGINT | Não | FK para products. |
| sku_snapshot | VARCHAR(60) | Não | SKU vendido snapshot. |
| product_name_snapshot | VARCHAR(180) | Não | Nome comercial snapshot. |
| quantity | BIGINT | Não | Quantidade vendida positiva. |
| unit_sale_price | NUMERIC(19,2) | Não | Preço unitário aplicado. |
| created_at | TIMESTAMPTZ | Não | Criação da linha. |

### sales.order_status_history

| Coluna | Tipo | Nulável | Finalidade |
|---|---|---|---|
| order_status_history_id | BIGINT GENERATED ALWAYS AS IDENTITY | Não | PK técnica. |
| sales_order_id | BIGINT | Não | FK para sales_orders. |
| status | VARCHAR(24) | Não | Estado assumido no evento. |
| occurred_at | TIMESTAMPTZ | Não | Instante efetivo da mudança. |
| changed_by_employee_id | BIGINT | Sim | Funcionário que registrou a mudança. |
| reason | VARCHAR(240) | Sim | Motivo resumido. |
| created_at | TIMESTAMPTZ | Não | Instante em que o evento foi registrado. |

### sales.applied_discounts

| Coluna | Tipo | Nulável | Finalidade |
|---|---|---|---|
| applied_discount_id | BIGINT GENERATED ALWAYS AS IDENTITY | Não | PK técnica. |
| sales_order_id | BIGINT | Não | FK composta para pedido/item. |
| sales_order_item_id | BIGINT | Não | Item que recebe a alocação. |
| discount_scope | VARCHAR(16) | Não | line ou order_allocation. |
| discount_code | VARCHAR(60) | Sim | Código promocional snapshot. |
| campaign_reference | VARCHAR(120) | Sim | Identificação externa/campanha snapshot, sem cadastro próprio. |
| description | VARCHAR(180) | Sim | Descrição do desconto aplicado. |
| amount | NUMERIC(19,2) | Não | Valor positivo alocado à linha. |
| created_at | TIMESTAMPTZ | Não | Registro da aplicação. |

## procurement

### procurement.suppliers

| Coluna | Tipo | Nulável | Finalidade |
|---|---|---|---|
| supplier_id | BIGINT GENERATED ALWAYS AS IDENTITY | Não | PK técnica. |
| supplier_code | VARCHAR(30) | Não | Código interno único. |
| legal_name | VARCHAR(200) | Não | Razão/nome cadastral. |
| trade_name | VARCHAR(180) | Sim | Nome comercial. |
| tax_identifier | VARCHAR(14) | Sim | Identificador fiscal informado, único se preenchido. |
| email | VARCHAR(254) | Sim | E-mail comercial. |
| phone | VARCHAR(30) | Sim | Telefone comercial. |
| status | VARCHAR(20) | Não | Estado cadastral. |
| external_reference | VARCHAR(120) | Sim | Referência em sistema externo. |
| created_at | TIMESTAMPTZ | Não | Criação. |
| updated_at | TIMESTAMPTZ | Não | Última atualização. |
| notes | TEXT | Sim | Observações comerciais. |

### procurement.purchase_orders

| Coluna | Tipo | Nulável | Finalidade |
|---|---|---|---|
| purchase_order_id | BIGINT GENERATED ALWAYS AS IDENTITY | Não | PK técnica. |
| purchase_order_number | VARCHAR(40) | Não | Número único de compra. |
| supplier_id | BIGINT | Não | FK para suppliers. |
| responsible_employee_id | BIGINT | Sim | Funcionário responsável. |
| status | VARCHAR(24) | Não | Estado administrativo da compra. |
| ordered_at | TIMESTAMPTZ | Não | Instante de emissão. |
| expected_on | DATE | Sim | Data civil prevista. |
| currency_code | CHAR(3) | Não | Moeda contratada. |
| external_reference | VARCHAR(120) | Sim | Referência externa. |
| created_at | TIMESTAMPTZ | Não | Criação. |
| updated_at | TIMESTAMPTZ | Não | Última atualização. |
| notes | TEXT | Sim | Observações. |

### procurement.purchase_order_items

| Coluna | Tipo | Nulável | Finalidade |
|---|---|---|---|
| purchase_order_item_id | BIGINT GENERATED ALWAYS AS IDENTITY | Não | PK técnica. |
| purchase_order_id | BIGINT | Não | FK para purchase_orders. |
| line_number | INTEGER | Não | Sequência única na compra. |
| product_id | BIGINT | Não | FK para products. |
| quantity_ordered | BIGINT | Não | Quantidade inteira positiva. |
| unit_cost_ordered | NUMERIC(20,8) | Não | Custo unitário contratado. |
| created_at | TIMESTAMPTZ | Não | Criação da linha. |

### procurement.goods_receipts

| Coluna | Tipo | Nulável | Finalidade |
|---|---|---|---|
| goods_receipt_id | BIGINT GENERATED ALWAYS AS IDENTITY | Não | PK técnica. |
| purchase_order_id | BIGINT | Não | FK para purchase_orders. |
| stock_location_id | BIGINT | Não | Local que recebe os produtos. |
| checked_by_employee_id | BIGINT | Sim | Funcionário conferente. |
| receipt_number | VARCHAR(40) | Não | Número único do recebimento. |
| status | VARCHAR(20) | Não | Situação da conferência. |
| received_at | TIMESTAMPTZ | Não | Instante físico de recebimento. |
| created_at | TIMESTAMPTZ | Não | Registro do evento. |
| notes | TEXT | Sim | Divergências/observações. |

### procurement.goods_receipt_items

| Coluna | Tipo | Nulável | Finalidade |
|---|---|---|---|
| goods_receipt_item_id | BIGINT GENERATED ALWAYS AS IDENTITY | Não | PK técnica. |
| purchase_order_id | BIGINT | Não | Chave para integridade da compra. |
| goods_receipt_id | BIGINT | Não | FK composta para recebimento/compra. |
| purchase_order_item_id | BIGINT | Não | FK composta para linha da compra. |
| quantity_received | BIGINT | Não | Quantidade fisicamente conferida. |
| accepted_quantity | BIGINT | Não | Quantidade aceita para estoque. |
| rejected_quantity | BIGINT | Não | Quantidade rejeitada. |
| unit_acquisition_cost | NUMERIC(20,8) | Não | Custo unitário aplicado à entrada aceita. |
| created_at | TIMESTAMPTZ | Não | Registro da linha. |
