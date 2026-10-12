# Prontidão analítica para Power BI — ProjetoBI

**Escopo:** preparação documental M6. Não cria modelo semântico, medidas DAX, relatório ou conexão Power BI.
**Fonte:** database operacional PostgreSQL 18, migrations 001–003, 9 schemas e 41 tabelas.
**Estado estrutural/documental verificado em 2026-10-09:** inspeção `BEGIN READ ONLY`; 72 FKs; naquele momento, 41 tabelas vazias e zero linhas persistidas. As amostras numéricas históricas abaixo vêm de fixtures sintéticas rollback-only e não descrevem o Portfolio permanente.

**Atualização M5 (2026-10-10):** o Portfolio foi persistido e revalidado em nova conexão read-only; 120.000 pedidos, 41 tabelas e 13 baselines SQL passaram por contagens/reconciliações. Na Fase 4.0, uma nova inspeção somente leitura confirmou 3.894.457 linhas antes e depois do backup. Este documento permanece preparatório: não define modelo semântico, medidas DAX ou relatório. Consulte `../data-generation/portfolio-validation.md` para as métricas do dataset e `phase-4.0-preparation.md` para as decisões de PBIP/TMDL.

## 1. Inventário de entidades e granularidade

| Schema | Entidade | PK | Granularidade operacional | Papel analítico candidato |
|---|---|---|---|---|
| core | stores | store_id | Uma unidade física | Dimensão de loja/local comercial |
| core | employees | employee_id | Um funcionário | Dimensão de funcionário, quando necessária |
| core | employee_roles | employee_role_id | Uma função | Dimensão de função |
| core | employee_assignments | employee_assignment_id | Um vínculo de funcionário/função/local por vigência | Ponte temporal; pode multiplicar fatos se a vigência não for respeitada |
| crm | customers | customer_id | Uma identidade de cliente PF/PJ identificada | Dimensão de cliente; pedido anônimo tem customer_id nulo |
| crm | individual_profiles | customer_id | Um perfil PF por cliente | Extensão 1:0..1 do cliente |
| crm | business_profiles | customer_id | Um perfil PJ por cliente | Extensão 1:0..1 do cliente |
| crm | customer_contacts | customer_contact_id | Um contato de cliente | Entidade descritiva; não juntar sem agregação se a medida for por cliente |
| crm | customer_addresses | customer_address_id | Um endereço cadastrado | Entidade descritiva; endereço da venda também possui snapshot no pedido |
| catalog | categories | category_id | Uma categoria, com pai opcional | Dimensão hierárquica de produto |
| catalog | brands | brand_id | Uma marca | Dimensão de produto |
| catalog | products | product_id | Um SKU | Dimensão de produto; `specifications` é JSONB opcional |
| catalog | product_suppliers | product_supplier_id | Uma associação produto-fornecedor | Ponte; preferência é temporal/operacional atual |
| catalog | product_prices | product_price_id | Um preço de SKU/canal e período de vigência | Histórico de preço; usar canal e intervalo temporal ao consultar |
| sales | sales_channels | sales_channel_id | Um canal | Dimensão de canal |
| sales | sales_orders | sales_order_id | Um pedido | Fato de pedidos no cabeçalho |
| sales | sales_order_items | sales_order_item_id | Uma linha comercial de pedido/SKU | Fato de itens vendidos |
| sales | order_status_history | order_status_history_id | Uma mudança/evento de estado do pedido | Fato de eventos de estado; não equivale a um pedido por linha |
| sales | applied_discounts | applied_discount_id | Uma alocação de desconto a item | Fato de desconto; agregar ao item antes de unir a outras linhas filhas |
| sales | sales_order_item_cancellations | sales_order_item_cancellation_id | Uma parcela cancelada de um item | Fato de cancelamento; a quantidade original do item permanece preservada |
| procurement | suppliers | supplier_id | Um fornecedor | Dimensão de fornecedor |
| procurement | purchase_orders | purchase_order_id | Um pedido de compra | Fato de compras no cabeçalho |
| procurement | purchase_order_items | purchase_order_item_id | Uma linha de pedido de compra/SKU | Fato de compras em nível de item |
| procurement | goods_receipts | goods_receipt_id | Um recebimento de compra/local | Fato de recebimento no cabeçalho |
| procurement | goods_receipt_items | goods_receipt_item_id | Uma linha recebida/rejeitada de compra/SKU | Fato de recebimentos |
| inventory | stock_locations | stock_location_id | Um local de estoque | Dimensão de local |
| inventory | stock_positions | stock_position_id | Uma posição corrente de SKU/local | Snapshot corrente de estoque; não é histórico diário |
| inventory | stock_movements | stock_movement_id | Um evento de movimento de estoque | Fato de ledger; grão canônico de mudanças físicas e custos |
| inventory | stock_reservations | stock_reservation_id | Uma reserva de item/local e seu ciclo de estado | Fato de reservas; estado/status precisa ser interpretado |
| inventory | stock_transfers | stock_transfer_id | Uma transferência entre locais | Cabeçalho de transferência |
| inventory | stock_transfer_items | stock_transfer_item_id | Uma linha de transferência/SKU | Fato de transferência em nível de item |
| payments | payment_methods | payment_method_id | Uma forma de pagamento | Dimensão de forma de pagamento |
| payments | payments | payment_id | Uma tentativa/captura associada a um pedido | Fato financeiro de pagamentos; retries e divisão são múltiplas linhas |
| payments | payment_installments | payment_installment_id | Uma parcela de um pagamento | Fato de vencimento/liquidação, filho do pagamento |
| payments | refunds | refund_id | Um estorno associado a pagamento e, conforme origem, devolução ou cancelamento | Fato de estorno; pode haver vários por pedido/pagamento |
| logistics | carriers | carrier_id | Uma transportadora | Dimensão de transportadora |
| logistics | fulfillments | fulfillment_id | Uma remessa/retirada do pedido | Cabeçalho de atendimento |
| logistics | fulfillment_items | fulfillment_item_id | Uma alocação atendida de item em fulfillment | Fato de atendimento; pode dividir um item em múltiplos fulfillments |
| logistics | fulfillment_events | fulfillment_event_id | Um evento logístico de fulfillment | Fato de eventos logísticos |
| after_sales | returns | return_id | Uma solicitação de devolução do pedido | Cabeçalho de devolução |
| after_sales | return_items | return_item_id | Uma linha devolvida de item e fulfillment de origem | Fato de devolução/recebimento |

As PKs e FKs técnicas entre entidades são as definidas pelas migrations e pelo dicionário de dados. Datas analíticas são dimensões candidatas a construir durante a futura modelagem; não existem dimensões de calendário físicas nesta fonte operacional.

## 2. Fatos e dimensões candidatos

| Fato candidato | Grão | Dimensões/relacionamentos úteis | Medidas candidatas e limite |
|---|---|---|---|
| Pedidos | Uma linha de `sales_orders` | Data do pedido, canal, cliente opcional, loja, vendedor | Contagem de pedidos; `subtotal_amount`, `discount_amount`, frete e `total_amount`. O estado no cabeçalho é o estado corrente/final da linha, não um evento histórico. |
| Itens comerciais | Uma linha de `sales_order_items` | Pedido, produto/SKU, categoria, canal e data via pedido | Quantidade vendida, preço, valor bruto e desconto rateado. Não somar um valor de pedido repetido em cada item. |
| Fulfillment/COGS | Uma linha de `inventory.stock_movements` do tipo `fulfillment`, vinculada ao `fulfillment_item_id` | Data do movimento, SKU, local, pedido/item e fulfillment | Unidades expedidas e custo histórico `ABS(quantity_delta) * unit_cost`. Este ledger, e não `sales_order_items`, é a fonte de custo realizado. Um item pode ter movimentos com custos distintos. |
| Pagamentos | Uma linha de `payments.payments` | Pedido, forma de pagamento e data da tentativa/captura | Tentativas e valores capturados/liquidados por status. Não equivalem a receita comercial. |
| Parcelas | Uma linha de `payment_installments` | Pagamento, forma de pagamento via pagamento, vencimento/liquidação | Valor e status da parcela; não somar junto com o pagamento para medir caixa sem escolher um grão. |
| Refunds | Uma linha de `payments.refunds` | Pedido, pagamento, data do processamento e origem (return ou cancelamento) | Valor de refunds concluídos. Refund pode ser dividido entre pagamentos e não deve ser multiplicado por itens/returns. |
| Devoluções | Uma linha de `after_sales.return_items` | Pedido/item, fulfillment de origem, data de recebimento e destino | Quantidades solicitadas/aprovadas/recebidas; custo de retorno e perda segundo a regra financeira abaixo. Cabeçalho e itens têm grãos diferentes. |
| Posição de estoque | Uma linha de `inventory.stock_positions` por SKU/local | Produto/categoria e local | Saldo físico, reservado, disponível e valor ao custo médio corrente. É somente posição atual; não reconstrói saldos históricos por data. |
| Movimentos de estoque | Uma linha de `inventory.stock_movements` | SKU, local, tipo e data; referência opcional a recebimento, fulfillment, retorno ou transferência | Quantidade delta e custo unitário no evento. Para o saldo histórico, acumular eventos até a data e respeitar a ordenação causal documentada. |
| Compras e recebimentos | Cabeçalho e itens em fatos separados | Fornecedor, produto, local, funcionário e datas | Quantidade/custo pedido e aceito; recebimentos parciais/rejeitados exigem separar linha de pedido da linha recebida. |

Dimensões candidatas principais: data (com papéis separados por cada timestamp), canal, produto, categoria, marca, cliente com atributo PF/PJ, loja, local de estoque, forma de pagamento, fornecedor, transportadora e funcionário. Essas são hipóteses de trabalho para modelagem futura, não uma aprovação de esquema estrela, chaves substitutas, relações ou filtros.

Cardinalidades a respeitar no desenho das relações: canal→pedidos e preços 1:N; cliente→pedidos/contatos/endereços 1:N e cliente→perfil PF/PJ 1:0..1; categoria→produtos 1:N e categoria-pai→subcategorias 1:N; produto→itens comerciais, preços, associações de fornecedor, compras e posições/movimentos 1:N; pedido→itens, histórico, fulfillment, pagamentos, refunds, devoluções e cancelamentos 1:N; item comercial→descontos, cancelamentos, fulfillments e returns 1:N; fulfillment→itens e eventos 1:N; pagamento→parcelas e refunds 1:N; return→return items 1:N; pedido de compra→itens e recebimentos 1:N, e item de compra→linhas recebidas 1:N; local→posições/movimentos 1:N. As FKs técnicas e suas composições permanecem no modelo operacional; tabelas de ponte, como produto-fornecedor, materializam relações N:N entre entidades de negócio.

## 3. Contratos de métrica e regra de margem

- **Pedidos:** contar `sales_order_id` em `sales_orders`; usar `order_status` conforme o corte declarado. Eventos em `order_status_history` são mudanças, não novas vendas.
- **Valor comercial no cabeçalho:** `subtotal_amount`, `discount_amount`, `shipping_amount` e `total_amount` são valores do pedido. Usar medidas de cabeçalho sem junção crua 1:N; para análise por produto/categoria, usar itens e seus descontos alocados.
- **Receita líquida analítica de produto para margem:** no gate Portfolio, valor comercial líquido por unidade atendida e ainda não recebida em devolução, abatendo o desconto alocado ao item. Esse número tem escopo distinto de `total_amount`, valor que inclui frete, pagamento ou captura.
- **COGS original:** soma de `ABS(quantity_delta) * unit_cost` dos movimentos `fulfillment`. Preservar os movimentos originais; não editar nem apagar ledger para representar devoluções.
- **Reversão vendável:** subtrair do COGS analítico apenas o custo gravado nos movimentos `customer_return` correspondentes às unidades recebidas como `sellable` e efetivamente reintegradas.
- **Perda não vendável:** unidades recebidas em `quarantine`, `repair` ou `discard` multiplicadas pelo custo histórico ponderado dos movimentos de fulfillment de origem. Mostrar como componente identificado do COGS que permanece reconhecido; não subtrair de novo.
- **Identidade de conciliação:** `COGS analítico = COGS original de fulfillment − reversão sellable`. A perda non-sellable é subconjunto do COGS analítico e não é termo adicional nessa subtração. Cada `return_item_id` deve contribuir uma única vez.
- **Caixa:** pagamentos capturados/liquidados e refunds concluídos são fluxos financeiros; não rotular como vendas sem definição adicional.
- **Estoque:** valor de `stock_positions` é saldo atual vezes custo médio móvel atual. Valorização histórica requer replay temporal do ledger e sua regra de custo; não usar snapshot atual para períodos passados.

## 4. Relações ambíguas, fanout e precauções

1. `sales_orders` → itens, pagamentos, refunds, fulfillments, eventos, returns, status history e cancelamentos são relações 1:N. Juntar duas ou mais tabelas filhas cruas multiplica linhas e infla valores. Agregar cada fato ao grão do relatório antes do join.
2. `sales_order_items` → `applied_discounts`, `fulfillment_items`, cancelamentos e `return_items` são relações 1:N ou 1:0..N. Fazer pré-agregação ao grão de item com a chave composta de pedido e item antes de comparar medidas.
3. `fulfillment_items` → `stock_movements` pode gerar mais de uma linha de custo por item atendido. Calcular COGS no grão do movimento e agregar depois; não assumir custo único na linha comercial.
4. `return_items` → `source_fulfillment_item_id` dá atribuição de origem para custo; o refund tem sua própria ligação a pagamento e ao cabeçalho de return ou cancelamento. Não associar refund a cada item sem regra e rateio explícitos.
5. `payments` → parcelas e refunds são relações diferentes. Captura, parcelas pagas e refunds não são medidas intercambiáveis nem devem ser somadas juntas.
6. `product_prices` exige correspondência de produto, canal e intervalo `[valid_from, valid_to)`; junção só por SKU pode encontrar preços múltiplos.
7. Produto/categoria/marca e cliente são cadastros correntes, não dimensões com histórico completo de alterações; uma análise “como conhecido na data” não pode ser presumida.
8. `employee_assignments` é temporal e pode ter vários períodos/funções. Uma venda não deve ser atribuída a toda lotação atual ou histórica do funcionário.
9. `sales_orders` contém snapshot de endereço de entrega; `customer_addresses` representa cadastro, que pode mudar. Para atributos de endereço na venda, priorizar os snapshots do pedido.
10. Transferências criam `transfer_out` e `transfer_in` em datas/locais diferentes. Contar cada movimento como venda, compra ou consumo final duplica a transferência interna.
11. `stock_positions` e `stock_movements` são snapshot e ledger, respectivamente. Não somar os dois como se fossem movimentos independentes.

## 5. Política temporal

- `TIMESTAMPTZ` é instante absoluto. Para datas civis e agrupamento comercial, converter explicitamente com `AT TIME ZONE 'America/Sao_Paulo'` antes de extrair dia, mês ou ano.
- O horizonte aprovado do Portfolio vai de 2023-01-01 a 2026-09-30; há bootstrap de estoque em nov–dez/2022, que não deve ser tratado como venda comercial.
- 2026 é parcial até 30 de setembro. Comparação YoY/YTD deve comparar **2025-01-01 a 2025-09-30** com **2026-01-01 a 2026-09-30** na mesma timezone, e deve rotular o intervalo parcial. Não comparar 2026 YTD a 2025 completo.
- `placed_at` é o marco temporal para coortes de pedido/venda; fulfillment, eventos logísticos, recebimentos, movimentos de estoque, recebimentos de devolução e processamento de refund respondem a perguntas de evento distintas. Não trocar a data sem declarar a métrica.
- A versão deste projeto não tem atualizações pós-cutoff no conjunto aprovado; “YTD” é uma janela fixa deste dataset, não um filtro móvel até a data de hoje.

## 6. Consultas de referência e amostra verificável

Consultas prontas e somente leitura:

- [`01_order_grain.sql`](../../database/queries/powerbi_readiness/01_order_grain.sql): pedido por linha, com fatos filhos pré-agregados.
- [`02_margin_by_channel_category.sql`](../../database/queries/powerbi_readiness/02_margin_by_channel_category.sql): margem por canal/categoria, com ledger de fulfillment e devoluções separados antes do join.
- [`03_sales_yoy_ytd.sql`](../../database/queries/powerbi_readiness/03_sales_yoy_ytd.sql): comparação parcial de 2025 e 2026 até setembro em data local.
- [`04_current_inventory_snapshot.sql`](../../database/queries/powerbi_readiness/04_current_inventory_snapshot.sql): posição corrente sem pretensão de histórico.
- A implementação das 13 consultas de baseline e da reconciliação pós-carga está em [`baselines.py`](../../data-generator/src/projectbi_generator/validation/baselines.py); os arquivos de baseline são materializados/executados no marco M5 após autorização e carga.

O schema foi inspecionado separadamente em transação `READ ONLY`. Para testar as consultas com linhas relacionais, as quatro foram executadas dentro da fixture smoke PostgreSQL de 300 pedidos, na mesma transação rollback-only: `01` retornou 300 linhas, `02` 17 grupos canal/categoria, `03` 2 anos e `04` 35 posições; as colunas foram 23, 10, 8 e 13. Os 39 invariantes SQL passaram; `ROLLBACK` e nova conexão confirmaram 41 tabelas e zero linhas. A verificação posterior em nova conexão confirmou novamente 41 tabelas vazias. As contagens verificam que as consultas operam sobre a fixture sintética, mas não substituem a verificação das distribuições do Portfolio persistido; não inferir mix final da fixture smoke.

Amostra financeira verificável da fixture sintética rollback-only de 50.000 pedidos, também conciliada pelos 39 invariantes SQL e pela consulta de margem: receita líquida de produto completed BRL 385.445.464,80; COGS original BRL 302.895.054,13; reversão sellable BRL 3.313.558,21; COGS analítico BRL 299.581.495,92; perda non-sellable incluída BRL 5.076.322,25. É uma evidência de regra e reconciliação, não um baseline de dados persistidos. Na época daquele teste, após rollback e nova conexão, 41 tabelas tinham zero linhas.

## 7. Conexão recomendada e limites

- Usar conexão PostgreSQL explicitamente **read-only** para a exploração BI; não reutilizar as credenciais de escrita do gerador nem armazenar senha em PBIP, M, relatório ou Git.
- A criação de usuário/role ou concessões é uma mudança no banco e não foi executada. Antes da conexão interativa futura, aprovar e provisionar uma credencial separada com somente `CONNECT`, `USAGE` nos schemas necessários e `SELECT` nas tabelas/views aprovadas; sem `CREATE`, `INSERT`, `UPDATE`, `DELETE`, `TRUNCATE` ou privilégios de sequence.
- Em desktop local, armazenar a credencial no gerenciador de credenciais do Power BI/Windows. Para publicação, reavaliar gateway, rede, identidade e política de credenciais; não presumir que a configuração local se transfira.
- A escolha Import vs DirectQuery, atualização, gateway, política de RLS, esquema semântico, dimensões de data, relações bidirecionais e medidas DAX fica para a fase de modelagem aprovada.
- Permanecem decisões da modelagem: relações ativas/inativas e direção de filtro; quais datas serão papéis de calendário; segmentação e anonimato; inclusão de status e cancelamentos em cada KPI; e se receita será medida comercial, caixa liquidado ou líquida de devolução. Este documento registra contratos e opções observáveis, sem escolher definições novas.
- O Portfolio persistido contém fatos sintéticos e distribuições documentadas em `../data-generation/portfolio-validation.md`. Algumas entidades existem estruturalmente, mas não têm linhas neste conjunto: `sales.sales_order_item_cancellations` (0), `inventory.stock_transfers` (0) e `inventory.stock_transfer_items` (0). Os 3.265 pedidos finais `cancelled` tiveram cancelamento anterior a fulfillment; seus 6.557 itens não foram expedidos. O gerador registra esse cancelamento pré-fulfillment no lifecycle/status, enquanto a tabela da migration 003 representa parcelas de itens canceladas por expiração de estoque. Assim, a tabela vazia limita análises de quantidade/valor de cancelamento por linha e refund atribuído a uma parcela da migration 003; não se deve deduzi-las apenas do status do pedido. O profile preserva `supply_transfer_enabled=0` conforme a política homologada e declara até 12 transferências estruturais; o scheduler só materializa transferências quando encontra déficits e excedentes elegíveis e a janela causal cabe antes do cutoff. O relatório persistido não registra qual dessas condições impediu a seleção nesta execução, então a causa exata das tabelas vazias continua não confirmada. Sem transferências registradas, não há amostra de eventos internos `transfer_out`/`transfer_in` para analisar.

**Gate documental M6: PASS para iniciar planejamento da fase de modelagem.** As 41 entidades, fatos/dimensões candidatos, granularidades, chaves, relações, métricas candidatas, riscos de fanout, regra financeira, política temporal, consultas executáveis e orientação read-only estão documentados. A Fase 4.1 criou e reabriu o projeto inicial Power BI Project (PBIP), com TMDL e PBIR, mas sem tabelas carregadas, conexão PostgreSQL ou modelo dimensional. A futura seleção deve ser limitada a entidades necessárias ao grão e às medidas aprovadas, nunca à importação automática das 41 tabelas. O uso da fonte PostgreSQL será exclusivamente read-only, após credencial apropriada. Consulte [`phase-4.1-initial-project.md`](phase-4.1-initial-project.md).
