# Constraints e índices propostos

**Fase 2A.1 — proposta física consolidada.** Esta especificação não é migration nem SQL executável. Os nomes seguem os prefixos documentados em relational-model.md. FKs usam comportamento restritivo padrão (NO ACTION/RESTRICT); não há exclusão em cascata para histórico. Cadastros referenciados devem ser inativados.

## Convenções e validação pelo banco

- PK: pk_<table>; FK: fk_<table>_<target>; UNIQUE: uq_<table>_<meaning>; CHECK: ck_<table>_<meaning>; índice: idx_<table>_<columns>.
- Identidade BIGINT em todas as PKs técnicas, salvo customer_id como PK/FK nos perfis PF/PJ.
- FK não cria índice automaticamente no PostgreSQL. Índices para buscas transacionais e joins frequentes são listados abaixo; índices de unicidade são os próprios índices únicos.
- Colunas administrativas padrão NOT NULL (created_at, updated_at) têm seus valores fornecidos pela aplicação. Atualização de updated_at também cabe à aplicação.
- Domínios CHECK abaixo são vocabulários propostos, sujeitos à aprovação. CHECKs não consultam outras tabelas nem validam agregados.

## Constraints por tabela

A notação “PK” identifica a chave primária; as FKs indicam colunas → destino; “UNIQUE” e “CHECK” descrevem integridade local. Nulabilidade detalhada coluna a coluna está no dicionário.

### core

| Tabela | PK e FKs | UNIQUE / CHECK propostos |
|---|---|---|
| stores | PK(store_id) | UNIQUE(store_code); status ∈ {active, inactive, closed}; closed_on ≥ opened_on quando ambos preenchidos. |
| employees | PK(employee_id) | UNIQUE(employee_code); status ∈ {active, inactive, terminated}; terminated_on ≥ hired_on. |
| employee_roles | PK(employee_role_id) | UNIQUE(role_code); UNIQUE(name). |
| employee_assignments | PK(employee_assignment_id); employee_id → employees; employee_role_id → employee_roles; store_id opcional → stores | valid_to nulo ou ≥ valid_from. |

### crm

| Tabela | PK e FKs | UNIQUE / CHECK propostos |
|---|---|---|
| customers | PK(customer_id) | UNIQUE(customer_code); customer_type ∈ {individual, business}; status ∈ {active, inactive}. |
| individual_profiles | PK(customer_id); customer_id → customers | CPF nulo ou 11 dígitos; UNIQUE(cpf) parcial quando não nulo. |
| business_profiles | PK(customer_id); customer_id → customers | legal_name obrigatório; CNPJ nulo ou 14 dígitos; UNIQUE(cnpj) parcial quando não nulo. |
| customer_contacts | PK(customer_contact_id); customer_id → customers | contact_type ∈ {email, phone, other}; índice único parcial de contato primário ativo por cliente (a definir como no máximo um contato primário geral). |
| customer_addresses | PK(customer_address_id); customer_id → customers | postal_code com 8 dígitos; UF em sigla brasileira; país BR nesta operação; no máximo um endereço padrão ativo por cliente. |

A regra que vincula customer_type a exatamente um perfil PF/PJ depende de consistência entre tabelas e será verificada transacionalmente pela aplicação/gerador. Não se propõe trigger. Como perfil é opcional na estrutura, a regra mínima também requer validação de que cliente ativo não esteja sem perfil.

### catalog

| Tabela | PK e FKs | UNIQUE / CHECK propostos |
|---|---|---|
| categories | PK(category_id); parent_category_id opcional → categories | UNIQUE(category_code); parent_category_id <> category_id. Não permitir ciclos exige validação na aplicação. |
| brands | PK(brand_id) | UNIQUE(brand_code); UNIQUE(name). |
| products | PK(product_id); category_id → categories; brand_id opcional → brands | UNIQUE(sku); status ∈ {active, inactive, discontinued}; unit_of_measure dentro do conjunto aprovado; specifications nulo ou JSONB object. Coerência interna/por categoria cabe ao gerador; sem schema rígido ou índice GIN inicial. |
| product_suppliers | PK(product_supplier_id); product_id → products; supplier_id → procurement.suppliers | UNIQUE(product_id, supplier_id); no máximo um fornecedor preferido ativo por produto via índice único parcial. |
| product_prices | PK(product_price_id); product_id → products; sales_channel_id → sales.sales_channels; created_by_employee_id opcional → core.employees | amount ≥ 0; valid_to nulo ou > valid_from. Períodos de um mesmo SKU/canal não se sobrepõem (validação transacional). |

### sales

| Tabela | PK e FKs | UNIQUE / CHECK propostos |
|---|---|---|
| sales_channels | PK(sales_channel_id) | UNIQUE(channel_code); UNIQUE(sales_channel_id, channel_type) para FK composta do pedido; channel_type ∈ {physical, ecommerce, marketplace}. |
| sales_orders | PK(sales_order_id); (sales_channel_id, channel_type) → sales_channels; customer_id opcional → customers; store_id opcional → core.stores; salesperson_employee_id opcional → employees; customer_address_id opcional → customer_addresses | UNIQUE(order_number); CHECK cliente nulo somente se channel_type=physical; order_status ∈ {draft, placed, confirmed, cancelled, completed}; currency_code = BRL; valores monetários ≥ 0; total conciliado com subtotal, desconto e frete pela aplicação. |
| sales_order_items | PK(sales_order_item_id); sales_order_id → sales_orders; product_id → products | UNIQUE(sales_order_id, line_number); UNIQUE(sales_order_id, sales_order_item_id) para FKs compostas; quantity > 0; unit_sale_price ≥ 0. Custo realizado não é armazenado na linha de pedido. |
| order_status_history | PK(order_status_history_id); sales_order_id → sales_orders; changed_by_employee_id opcional → employees | status ∈ {draft, placed, confirmed, cancelled, completed}; eventos imutáveis por convenção; sequência/estado corrente atualizados na mesma transação. |
| applied_discounts | PK(applied_discount_id); (sales_order_id, sales_order_item_id) → sales_order_items | discount_scope ∈ {line, order_allocation}; amount > 0; desconto da linha não pode exceder seu valor elegível; soma das alocações de cabeçalho = desconto do pedido; valor líquido de cada linha ≥ 0 (validação transacional). |

A constraint composta do pedido assegura que channel_type armazenado corresponda ao canal; o CHECK da tabela permite customer_id nulo somente no tipo físico. Não se propõe regra adicional de loja obrigatória no canal físico nesta etapa.

### procurement

| Tabela | PK e FKs | UNIQUE / CHECK propostos |
|---|---|---|
| suppliers | PK(supplier_id) | UNIQUE(supplier_code); UNIQUE(tax_identifier) parcial; status ∈ {active, inactive}. |
| purchase_orders | PK(purchase_order_id); supplier_id → suppliers; responsible_employee_id opcional → core.employees | UNIQUE(purchase_order_number); status ∈ {draft, submitted, partially_received, received, cancelled}; currency_code = BRL; expected_on não anterior a ordered_at convertido para data, regra de aplicação. |
| purchase_order_items | PK(purchase_order_item_id); purchase_order_id → purchase_orders; product_id → catalog.products | UNIQUE(purchase_order_id, line_number); UNIQUE(purchase_order_id, purchase_order_item_id); quantity_ordered > 0; unit_cost_ordered ≥ 0. |
| goods_receipts | PK(goods_receipt_id); (purchase_order_id) → purchase_orders; stock_location_id → inventory.stock_locations; checked_by_employee_id opcional → core.employees | UNIQUE(receipt_number); UNIQUE(purchase_order_id, goods_receipt_id); status ∈ {in_progress, accepted, completed, cancelled}. |
| goods_receipt_items | PK(goods_receipt_item_id); (purchase_order_id, goods_receipt_id) → goods_receipts; (purchase_order_id, purchase_order_item_id) → purchase_order_items | UNIQUE(goods_receipt_id, purchase_order_item_id); quantidades recebida/aceita/rejeitada ≥ 0; accepted + rejected = received; custo ≥ 0. |

O recebimento acumulado por item não pode superar quantidade comprada, exceto se política futura permitir tolerância. Validar na aplicação/gerador com bloqueio da linha de compra. Somente linhas aceitas confirmadas originam movimento de estoque.

### inventory

| Tabela | PK e FKs | UNIQUE / CHECK propostos |
|---|---|---|
| stock_locations | PK(stock_location_id); store_id opcional → core.stores | UNIQUE(location_code); location_type ∈ {store, warehouse, digital, other}; status ∈ {active, inactive}. |
| stock_positions | PK(stock_position_id); product_id → catalog.products; stock_location_id → stock_locations | UNIQUE(product_id, stock_location_id); on_hand_quantity ≥ 0; reserved_quantity ≥ 0 e ≤ on_hand_quantity; available_quantity = on_hand_quantity - reserved_quantity; average_unit_cost ≥ 0. |
| stock_movements | PK(stock_movement_id); product_id → catalog.products; stock_location_id → stock_locations; goods_receipt_item_id opcional → procurement.goods_receipt_items; fulfillment_item_id opcional → logistics.fulfillment_items; return_item_id opcional → after_sales.return_items; stock_transfer_item_id opcional → stock_transfer_items; adjustment_employee_id opcional → core.employees | movement_type ∈ {receipt, fulfillment, customer_return, transfer_in, transfer_out, adjustment_in, adjustment_out}; quantity_delta <> 0; receipt/customer_return/transfer_in/adjustment_in positivos e fulfillment/transfer_out/adjustment_out negativos; CHECK exige somente a FK de origem aplicável (nenhuma para ajuste); unit_cost ≥ 0 e obrigatório em receipt, fulfillment, customer_return, transfer_in e transfer_out; saída fulfillment usa a média vigente no instante. |
| stock_reservations | PK(stock_reservation_id); (sales_order_id, sales_order_item_id) → sales_order_items; product_id → products; stock_location_id → stock_locations | quantity > 0; status ∈ {active, released, expired, consumed}; expires_at nulo ou ≥ reserved_at. Produto deve ser o mesmo da linha do pedido; validação transacional. |
| stock_transfers | PK(stock_transfer_id); source_stock_location_id e destination_stock_location_id → stock_locations; funcionários solicitante/recebedor opcionais → employees | UNIQUE(transfer_number); origem <> destino; status ∈ {draft, in_transit, completed, cancelled}; instantes em ordem coerente. |
| stock_transfer_items | PK(stock_transfer_item_id); stock_transfer_id → stock_transfers; product_id → products | UNIQUE(stock_transfer_id, line_number); quantity_planned > 0; quantidades enviadas/recebidas não negativas; recebida ≤ expedida, salvo divergência formalmente registrada. |

A reconciliação física entre ledger e posição e o pareamento de dois movimentos de transferência são invariantes transacionais da aplicação/gerador. Movimentos são append-only por convenção operacional; correção usa movimento compensatório, não edição histórica.

### payments

| Tabela | PK e FKs | UNIQUE / CHECK propostos |
|---|---|---|
| payment_methods | PK(payment_method_id) | UNIQUE(method_code); method_type ∈ {card, cash, instant, bank_transfer, other}. |
| payments | PK(payment_id); sales_order_id → sales_orders; payment_method_id → payment_methods | UNIQUE(sales_order_id, payment_id) para FK de reembolso; status ∈ {pending, authorized, captured, settled, declined, cancelled, failed}; currency_code = BRL; amount > 0; valores recebidos dependem do estado financeiro, não do pedido. |
| payment_installments | PK(payment_installment_id); payment_id → payments | UNIQUE(payment_id, installment_number); installment_number > 0; amount > 0; status ∈ {pending, paid, overdue, cancelled, failed}. |
| refunds | PK(refund_id); (sales_order_id, payment_id) → payments; (sales_order_id, return_id) → after_sales.returns opcional | status ∈ {requested, processing, completed, rejected, cancelled}; amount > 0; referência composta impede cruzar pedidos. |

Soma de parcelas igual ao valor contratado e soma dos reembolsos concluídos limitada ao valor liquidado/reembolsável dependem de validação transacional e regras do meio de pagamento.

### logistics

| Tabela | PK e FKs | UNIQUE / CHECK propostos |
|---|---|---|
| carriers | PK(carrier_id) | UNIQUE(carrier_code); tax_identifier único parcial; estado ativo/inativo. |
| fulfillments | PK(fulfillment_id); sales_order_id → sales_orders; stock_location_id opcional → stock_locations; pickup_store_id opcional → stores; carrier_id opcional → carriers | UNIQUE(sales_order_id, fulfillment_number); UNIQUE(sales_order_id, fulfillment_id); fulfillment_type ∈ {delivery, store_pickup}; status ∈ {pending, preparing, dispatched, completed, failed, cancelled}; store_pickup exige pickup_store_id e carrier_id nulo; delivery exige pickup_store_id nulo e permite carrier_id nulo para entrega própria. |
| fulfillment_items | PK(fulfillment_item_id); (sales_order_id, fulfillment_id) → fulfillments; (sales_order_id, sales_order_item_id) → sales_order_items | UNIQUE(fulfillment_id, sales_order_item_id); UNIQUE(sales_order_id, sales_order_item_id, fulfillment_item_id) para FK de devolução; quantity_allocated > 0; fulfilled_quantity ≥ 0 e ≤ alocada. |
| fulfillment_events | PK(fulfillment_event_id); fulfillment_id → fulfillments; recorded_by_employee_id opcional → employees | event_type ∈ {prepared, dispatched, delivery_attempt, delivered, pickup_ready, picked_up, exception, cancelled}; eventos append-only; occurred_at não nulo. |

Total atendido entre fulfillments não pode exceder a quantidade do item vendido e deve respeitar reservas/saídas. Aplicação valida e serializa a linha do item.

### after_sales

| Tabela | PK e FKs | UNIQUE / CHECK propostos |
|---|---|---|
| returns | PK(return_id); sales_order_id → sales_orders; requested_by_employee_id e approved_by_employee_id opcionais → employees | UNIQUE(sales_order_id, return_number); UNIQUE(sales_order_id, return_id); status ∈ {requested, approved, rejected, partially_received, received, closed, cancelled}; reason_code limitado a conjunto curto aprovado. |
| return_items | PK(return_item_id); (sales_order_id, return_id) → returns; (sales_order_id, sales_order_item_id) → sales_order_items; (sales_order_id, sales_order_item_id, source_fulfillment_item_id) opcional → logistics.fulfillment_items | UNIQUE(return_id, source_fulfillment_item_id) quando a origem não é nula; requested > 0; approved entre 0 e solicitado; received entre 0 e aprovado; item_condition ∈ {unopened, good, damaged, defective, unknown}; stock_destination ∈ {sellable, quarantine, repair, discard}; origem deve ter sido efetivamente atendida antes de recebimento físico; estado físico informado quando quantity_received > 0. |

Quantidade aceita/acumulada em múltiplas devoluções ≤ quantidade efetivamente atendida da origem física indicada é validada transacionalmente, com bloqueio do item atendido. Recebimento físico, retorno ao estoque vendável e reembolso são operações separadas.

## Índices essenciais

Além dos índices de PK/UNIQUE acima, criar somente os seguintes grupos de apoio:

| Índice (nome lógico) | Colunas / condição | Motivo |
|---|---|---|
| idx_employee_assignments_employee_dates | employee_id, valid_from DESC | Histórico e vigência de lotação. |
| idx_customer_contacts_customer_active | customer_id, is_active | Contatos ativos. |
| idx_customer_addresses_customer_active | customer_id, is_active | Endereços do cliente. |
| idx_categories_parent | parent_category_id | Navegação hierárquica. |
| idx_products_category_status | category_id, status | Busca de catálogo por categoria. |
| idx_product_prices_product_channel_from | product_id, sales_channel_id, valid_from DESC | Seleção de preço vigente. |
| idx_sales_orders_customer_placed | customer_id, placed_at DESC | Histórico do cliente. |
| idx_sales_orders_channel_placed | sales_channel_id, placed_at DESC | Consulta temporal por canal. |
| idx_sales_orders_status_placed | order_status, placed_at DESC | Filas/monitoramento operacional. |
| idx_sales_order_items_product_order | product_id, sales_order_id | Histórico do SKU. |
| idx_order_status_history_order_time | sales_order_id, occurred_at DESC | Linha do tempo do pedido. |
| idx_purchase_orders_supplier_date | supplier_id, ordered_at DESC | Histórico de compras. |
| idx_goods_receipts_purchase_time | purchase_order_id, received_at DESC | Recebimentos parciais. |
| idx_stock_movements_product_location_time | product_id, stock_location_id, occurred_at DESC | Ledger e reconciliação. |
| idx_stock_movements_source_refs | cada source FK não nula em índice parcial | Idempotência e busca da origem de movimento. |
| idx_stock_movements_fulfillment_item | fulfillment_item_id, occurred_at | Custo realizado por item atendido e pedido. |
| idx_stock_reservations_item_status | sales_order_item_id, status | Reservas ativas por linha. |
| idx_stock_transfers_status_requested | status, requested_at DESC | Fila de transferências. |
| idx_payments_order_attempt | sales_order_id, attempted_at DESC | Tentativas independentes por pedido. |
| idx_payment_installments_payment_status | payment_id, status | Acompanhamento de parcelas. |
| idx_refunds_payment_status | payment_id, status | Reconciliação de reembolsos. |
| idx_fulfillments_order_status | sales_order_id, status | Atendimentos parciais do pedido. |
| idx_fulfillment_events_fulfillment_time | fulfillment_id, occurred_at DESC | Linha do tempo logística. |
| idx_fulfillment_items_order_item | sales_order_id, sales_order_item_id, fulfillment_id | Percurso da linha comercial até saídas físicas e custos. |
| idx_returns_order_requested | sales_order_id, requested_at DESC | Histórico de devolução. |
| idx_return_items_order_item | sales_order_item_id, sales_order_id | Limites acumulados por item vendido. |
| idx_return_items_source_fulfillment | source_fulfillment_item_id | Rastrear origem física e custo da unidade devolvida. |

Índices parciais únicos adicionais: CPF/CNPJ e tax_identifier quando preenchidos; endereço/contact primário ativo por cliente; fornecedor preferencial ativo por produto; referências externas idempotentes quando a origem garantir unicidade. Não adicionar GIN a specifications nesta versão; avaliar somente se consultas operacionais reais por chaves internas justificarem. Evitar índices redundantes com PK/UNIQUE, baixa seletividade sem carga comprovada e todas as colunas indiscriminadamente.

Os códigos de motivo são propostas curtas a revisar: returns.reason_code ∈ {defective, damaged, incorrect_item, buyer_remorse, other}; refunds.reason_code ∈ {customer_request, return, duplicate_charge, other}; stock_movements.reason_code para ajuste ∈ {count_correction, damage, loss, found, other}. Não há regra fiscal implícita nesses vocabulários.

### Cobertura adicional de FKs

Além dos grupos acima, criar índices simples nas FKs opcionais ou nas FKs que não estejam cobertas pela primeira coluna de um índice/UNIQUE já listado: employee_assignments(employee_role_id) e employee_assignments(store_id); categories(parent_category_id); products(category_id) e products(brand_id); product_suppliers(supplier_id); product_prices(sales_channel_id) e product_prices(created_by_employee_id); sales_orders(customer_id), sales_orders(store_id), sales_orders(salesperson_employee_id) e sales_orders(customer_address_id); order_status_history(changed_by_employee_id); applied_discounts(sales_order_item_id); purchase_orders(responsible_employee_id); purchase_order_items(product_id); goods_receipts(stock_location_id) e goods_receipts(checked_by_employee_id); goods_receipt_items(purchase_order_item_id); stock_locations(store_id); stock_movements(adjustment_employee_id) e cada FK de origem já indicada; stock_reservations(product_id) e stock_reservations(stock_location_id); stock_transfers(source_stock_location_id), stock_transfers(destination_stock_location_id), stock_transfers(requested_by_employee_id) e stock_transfers(received_by_employee_id); stock_transfer_items(product_id); payments(payment_method_id); refunds(return_id); fulfillments(stock_location_id), fulfillments(pickup_store_id) e fulfillments(carrier_id); fulfillment_items(sales_order_item_id); fulfillment_events(recorded_by_employee_id); returns(requested_by_employee_id) e returns(approved_by_employee_id); return_items(sales_order_item_id). As FKs de customer_contacts/customer_addresses para customer_id e payment_installments para payment_id já têm índices de apoio listados. Cada item corresponde a índice cujo nome segue idx_<table>_<fk_column>; onde houver baixa seletividade, confirmar necessidade com volume/consulta antes de implementar.

## Regras que exigem aplicação/gerador/transação

1. Clientes ativos identificados têm exatamente um perfil correspondente a customer_type; venda digital tem customer_id; endereço cadastrado, se usado, pertence ao mesmo cliente do pedido. A aplicação/gerador valida perfil e snapshots.
2. Validar não sobreposição de vigências de preço e, quando aplicável, lotações incompatíveis.
3. Validar subtotais/totais, soma das alocações de desconto contra desconto do pedido e líquido não negativo por linha; algoritmo e arredondamento de rateio são de implementação.
4. Validar recebimentos acumulados contra compra e conciliar a linha recebida com o pedido de compra.
5. Validar produto e local da reserva/movimento contra suas origens e serializar reservas dentro da disponibilidade.
6. Atualizar posição, reservas e movimentos na mesma transação; bloquear/serializar a posição por produto/local ao mudar quantidade, reserva ou custo médio; reconciliar posição e ledger.
7. Movimento de saída fulfillment usa o average_unit_cost do local no instante, e guarda unit_cost. Custo realizado por atendimento é soma de ABS(quantity_delta) × unit_cost dos movimentos ligados ao fulfillment_item.
8. Não superar quantidade comprada/atendida; devolução acumulada não excede quantidade efetivamente atendida/vendida; a origem física pertence ao mesmo pedido/item e já foi atendida.
9. Reentrada vendável referencia as saídas originais e usa custo histórico alocado; quarentena, reparo ou descarte não aumenta estoque disponível. Transferência replica custo unitário da saída na entrada do destino.
10. Limitar reembolsos ao valor elegível, conciliar parcelas ao pagamento e manter moeda BRL em venda/compra/pagamento.
11. Inserir eventos históricos e atualizar estado atual juntos. Timestamps vêm explicitamente da camada de gravação; não há default de horário atual generalizado.
12. Atualizar posição+custo médio segundo a entrada ponderada aprovada, sem recalcular a média na saída. Definir detalhes de arredondamento, custo elegível, alocação de custo de retorno e mecanismo concreto de locking na Fase 2B/camada operacional.

## Exclusão e preservação histórica

As FKs não usam ON DELETE CASCADE. Cadastros transacionais referenciados não devem ser apagados; inativar. Remoção de rascunhos sem histórico pode ser avaliada futuramente em política explícita, fora desta proposta. A revisão humana final antecede a implementação da Fase 2B.
