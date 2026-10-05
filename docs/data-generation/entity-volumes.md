# Volumes por entidade — Fase 3A

Contagens são aproximadas e referem-se ao profile inteiro. `smoke` deve validar o fluxo end-to-end em centenas de pedidos; `portfolio` é a base analítica principal; `large` dobra principalmente transações e aumenta moderadamente master data. Eventos e filhos são derivados, não objetivos independentes. A implementação pode variar dentro de aproximadamente ±15% para entidades transacionais e manter exatamente os vínculos e regras.

Abreviações: `S` = smoke; `P` = portfolio; `L` = large. FKs e ordem estão em [dependency-order.md](dependency-order.md).

| Tabela | Função | Dependências principais | S | P | L | Regra derivadora |
|---|---|---|---:|---:|---:|---|
| `core.stores` | Unidades físicas | — | 2 | 10 | 10 | Profile; lojas com datas e escalas variadas. |
| `core.employees` | Equipe operacional | — | 12 | 90 | 120 | 80–100 em P; L cresce pouco. |
| `core.employee_roles` | Funções | — | 5 | 7 | 7 | Catálogo pequeno (6–8 em P). |
| `core.employee_assignments` | Lotação/função por período | employees, roles, stores | 16 | 115 | 155 | 1–2 períodos por funcionário; centrais podem não ter store. |
| `crm.customers` | Identidades PF/PJ | — | 20 | 45.000 | 90.000 | Cadastros identificados distintos; anonimato fica no pedido físico. |
| `crm.individual_profiles` | Extensão PF | customers | 18 | 40.500 | 81.000 | 88–92% dos customers identificados. |
| `crm.business_profiles` | Extensão PJ | customers | 2 | 4.500 | 9.000 | Complemento de PF; proporção restante. |
| `crm.customer_contacts` | Contatos de cliente | customers | 24 | 60.000 | 120.000 | Média ~1,3 por cliente; alguns sem segundo contato. |
| `crm.customer_addresses` | Endereços estruturados | customers | 24 | 52.000 | 104.000 | Média ~1,15; usados conforme canal/entrega. |
| `catalog.categories` | Árvore de categorias | — | 15 | 42 | 50 | Hierarquia acíclica de 35–50 nós em P. |
| `catalog.brands` | Marcas fictícias | — | 12 | 65 | 75 | Catálogo mestre (50–80 em P). |
| `catalog.products` | SKUs | categories, brands | 30 | 1.000 | 1.500 | SKU por faixa/família e ciclo de vida. |
| `catalog.product_suppliers` | Abastecedores por SKU | products, suppliers | 36 | 1.600 | 2.500 | 1–3 por SKU; máximo de 1 preferencial ativo. |
| `catalog.product_prices` | Vigências de preço/canal | products, sales_channels, employees? | 120 | 14.000 | 22.000 | Média de 3–4 períodos por SKU/canal habilitado. |
| `inventory.stock_locations` | Lojas/centros de estoque | stores? | 4 | 14 | 14 | 10 lojas + 2 centros + 0–3 locais de operação aprovados. |
| `inventory.stock_positions` | Saldos SKU/local | products, stock_locations | 90 | 10.000 | 15.000 | Apenas combinações ativas com posição necessária; não produto × local cartesiano. |
| `inventory.stock_movements` | Ledger de estoque/custo | products, locations, receipt/fulfillment/return/transfer | 350 | 330.000 | 680.000 | Soma de recebimentos aceitos, saídas atendidas, retornos, transferências e poucos ajustes. |
| `inventory.stock_reservations` | Compromissos pré-saída | orders/items, products, locations | 420 | 170.000 | 350.000 | Apenas pedidos com reserva; uma linha por item/local/período operacional. |
| `inventory.stock_transfers` | Cabeçalhos de transferência | locations, employees? | 8 | 1.800 | 3.600 | Evento raro motivado por rebalanceamento/reposição. |
| `inventory.stock_transfer_items` | SKUs transferidos | transfers, products | 16 | 4.000 | 8.000 | 1–3 itens por transferência; gera pares de movimentos. |
| `payments.payment_methods` | Formas de pagamento | — | 4 | 5 | 5 | Métodos de referência estáveis. |
| `payments.payments` | Tentativas/operações | orders, payment_methods | 330 | 132.000 | 265.000 | Pedidos × tentativas/split; inclui poucos declinados. |
| `payments.payment_installments` | Parcelas | payments | 95 | 85.000 | 170.000 | Apenas pagamentos parceláveis; quantia concilia ao pagamento. |
| `payments.refunds` | Reembolsos | orders, payments, returns? | 2 | 7.000 | 14.000 | Derivado das devoluções/decisões; pode haver mais de um por retorno. |
| `logistics.carriers` | Transportadoras fictícias | — | 3 | 12 | 15 | Cadastro pequeno; retirada não exige carrier. |
| `logistics.fulfillments` | Unidades de entrega/retirada | orders, locations?, stores?, carriers? | 280 | 124.000 | 250.000 | Pedidos atendidos; pequeno acréscimo por split. |
| `logistics.fulfillment_items` | Alocação atendida por linha | fulfillments, order_items | 650 | 275.000 | 560.000 | Deriva das quantidades vendidas; splits acrescentam linhas. |
| `logistics.fulfillment_events` | Eventos logísticos | fulfillments, employees? | 620 | 310.000 | 625.000 | 2–3 eventos por fulfillment, com sequência por modalidade. |
| `after_sales.returns` | Solicitações de devolução | orders, employees? | 16 | 8.000 | 16.000 | ~4–8% dos pedidos concluídos, com variação canal/categoria. |
| `after_sales.return_items` | Linhas/devoluções físicas | returns, order_items, fulfillment_items | 20 | 12.000 | 24.000 | Itens e quantidades elegíveis; podem agregar vários itens por solicitação. |
| `sales.sales_channels` | Canais de origem | — | 4 | 4 | 4 | Físico, e-commerce, dois marketplaces genéricos. |
| `sales.sales_orders` | Pedidos | channels, customers?, stores?, employees?, addresses? | 300 | 120.000 | 240.000 | Perfil/cutoff/seasonality; pedidos físicos permitem cliente nulo. |
| `sales.sales_order_items` | Itens vendidos | orders, products | 630 | 264.000 | 528.000 | Pedidos × média 2,0–2,3 linhas, distribuição long-tail. |
| `sales.order_status_history` | Histórico de status | orders, employees? | 900 | 330.000 | 660.000 | 2–3 eventos por pedido, proporcional ao ciclo real. |
| `sales.applied_discounts` | Descontos alocados | orders/items | 120 | 55.000 | 110.000 | 30–45% pedidos com desconto; rateio pode criar linhas por item. |
| `procurement.suppliers` | Fornecedores fictícios | — | 8 | 45 | 50 | Catálogo mestre de 40–50 fornecedores. |
| `procurement.purchase_orders` | Compras | suppliers, employees? | 35 | 16.000 | 27.000 | Demanda/reposição, estoque mínimo e lead time; inclui bootstrap. |
| `procurement.purchase_order_items` | Linhas de compra | purchase_orders, products | 100 | 48.000 | 81.000 | Média 3 produtos/ordem, ponderada por reposição. |
| `procurement.goods_receipts` | Eventos de recebimento | purchase_orders, locations, employees? | 40 | 18.000 | 30.000 | 1–1,2 por compra; parciais minoritários. |
| `procurement.goods_receipt_items` | Linhas recebidas | receipts, purchase_order_items | 110 | 55.000 | 93.000 | Linhas efetivamente conferidas; aceites/rejeições conciliam. |

`?` indica FK opcional. Contagens de sub-tabelas PF/PJ devem reconciliar com `crm.customers`; valores NULL em `customer_id` de pedido não criam linha em customer. Linhas de fulfillment e movimento precisam derivar de quantidades efetivamente atendidas, nunca só da intenção do pedido.

## Leitura da projeção total

No portfolio, cabeçalhos de venda (~120k), itens (~264k), movimentos (~330k), pagamentos/parcelas, eventos de fulfillment e detalhe de compras/devoluções elevam o conjunto total a aproximadamente **2,0–2,8 milhões de linhas**. Smoke fica tipicamente abaixo de 15 mil linhas; large na ordem de **4–5,5 milhões**. A engine deve produzir em streaming/batches para manter baixo uso de memória.
