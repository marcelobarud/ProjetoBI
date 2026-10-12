# Fase 4.5B — Fundação do modelo financeiro e de devoluções

**Status: PASS — modelo financeiro/devoluções carregado, reconciliado e reaberto no Power BI Desktop.**
**Checkpoint de entrada:** `cd308d0`; regularização isolada em `74ca3be`.
**Projeto:** `powerbi/ProjetoBI.pbip`

## Escopo e regularização do TMDL

A fase prepara o modelo para receita analítica após devoluções, custos de fulfillment, reversão sellable, perda non-sellable e COGS ajustado. Não cria medidas financeiras DAX definitivas nem relatórios.

O commit `74ca3be` aceitou a serialização nativa do Desktop em `_Medidas.tmdl`. A diferença contra `cd308d0` contém somente as oito expressões DAX simples normalizadas para a linha da declaração. A verificação anterior de equivalência confirmou 28 expressões, nomes, descrições, formatos, sete pastas e lineage tags sem mudança funcional. O commit contém apenas esse arquivo. As alterações locais de Desktop preexistentes em PBIR/TMDL continuam preservadas fora do commit.

## Inspeção de fontes e seleção mínima

A matriz foi construída a partir das migrations 001–003, catálogo PostgreSQL 18.6, chaves reais, `readiness.md`/contratos M6, regras de transação e baselines 01, 09, 10 e 11. Os 13 arquivos de baseline foram inventariados; baselines 01/09/11 foram executados em transação somente leitura. A tabela `stock_positions` do baseline 10 é snapshot de custo médio atual e não serve ao custo histórico de fulfillment, portanto não foi selecionada.

| Entidade | Grão, chave e dependências | Linhas | Indicadores e riscos | Decisão |
|---|---|---:|---|---|
| `logistics.fulfillments` | Um cabeçalho por `fulfillment_id`; contém pedido, estado, local e horários. | 176.716 | O contrato usa o instante do movimento de estoque e a chave de fulfillment já carregada na linha filha. Importá-la não acrescenta dado necessário ao baseline e adicionaria outro ramo 1:N. | Não importada. |
| `logistics.fulfillment_items` | Uma linha por `fulfillment_item_id`; FK composta para fulfillment e item comercial. | 237.742 | Liga movimento a pedido/item/fulfillment. Pode ter múltiplos movimentos de custo por linha; preservar grão do movimento e não juntar a outras filhas cruas. | Usada como dependência projetada em `FatoCustoFulfillment`, não como tabela semântica autônoma. |
| `inventory.stock_movements` | Um evento por `stock_movement_id`; FKs para fulfillment item ou item de devolução. | 429.462 total; 237.742 `fulfillment`; 2.851 `customer_return` | Fonte canônica do COGS histórico e do custo efetivamente reintegrado. `unit_cost NUMERIC(20,8)`. Outros tipos de movimento ficam fora da fato de custo de fulfillment. | Selecionada: eventos `fulfillment` formam `FatoCustoFulfillment`; custos `customer_return` são agregados por `return_item_id` na fato de devoluções. |
| `after_sales.returns` | Um cabeçalho por `return_id`; FK para pedido e dependência 1:N de itens. | 7.129 | Status, motivo e instante de solicitação. Join pelo par de chaves de pedido/devolução é N:1 a partir de cada item. | Usada na projeção de `FatoDevolucoes`, sem carga separada. |
| `after_sales.return_items` | Um item por `return_item_id`; FKs para cabeçalho, item comercial e fulfillment de origem. | 7.129 | Quantidades solicitadas/aprovadas/recebidas, condição e destino. Grão adequado para classificação sellable/non-sellable. | Selecionada como grão de `FatoDevolucoes`. |
| `sales.applied_discounts` | Uma alocação por `applied_discount_id`; FK composta para item comercial. | 94.045 | Baseline 11 calcula desconto por item; join cru multiplicaria itens/devoluções. | Selecionada apenas dentro de uma pré-agregação única por `(sales_order_id, sales_order_item_id)` para projetar `FatoItensPedido` e `FatoDevolucoes`. Não é fato separada. |

`payments.refunds` permanece fora: o valor de refund é um evento financeiro independente e não integra os indicadores desta fundação. Não se subtrai refund da receita. `inventory.stock_positions` também fica fora porque representa o custo médio atual, não o ledger histórico.

## Fatos e relações

- `FatoCustoFulfillment`: **uma linha por movimento de estoque do tipo `fulfillment`**, chave `stock_movement_id`, 237.742 linhas na origem atual. Preserva IDs de movimento, fulfillment, fulfillment item, pedido/item, produto, local, quantidade, instante operacional e status do pedido. Os atributos dimensionais de cliente, loja e canal vêm do pedido de origem.
- `FatoDevolucoes`: **uma linha por `return_item_id`**, 7.129 linhas. Preserva chaves de devolução/pedido/item/fulfillment, quantidades, status do cabeçalho, razão, condição, destino, datas locais de solicitação/recebimento, chave dimensional de produto/pedido e valores financeiros atribuídos pelo contrato.
- `FatoItensPedido` permanece no grão original de `sales_order_item_id` e com as mesmas 241.637 linhas. Recebe apenas `item_discount_amount`, projetado após pré-agregar descontos pela chave composta do item. O campo é necessário para calcular receita líquida atribuída a produto/categoria segundo o baseline 11; não altera as 28 medidas existentes.
- As tabelas semânticas passam de 8 para 10, incluindo `_Medidas`. As relações passam de 9 para 21: 12 novas relações dimensão→fato, filtro unidirecional; nenhuma relação fato-fato, muitos-para-muitos ou bidirecional.
- Em ambas as novas fatos, a data operacional é a relação ativa com `DimCalendario`: `movement_date` para custo e `return_received_date` para recebimento. A relação por `order_date` fica inativa para uso explícito em métricas de coorte. Datas são projetadas em `America/Sao_Paulo`; instantes originais são preservados em texto UTC ISO, além do timestamp local. Um recebimento não é reclassificado como ocorrido na data do pedido.
- Todas as dimensões compartilhadas são usadas quando semanticamente válidas: calendário, produto, cliente, loja e canal. Loja representa a loja do pedido; `stock_location_id` conserva o local físico como rastreabilidade, sem confundi-lo com loja comercial.

As consultas `FatoCustoFulfillment` e `FatoDevolucoes` são fatos finais carregados. Não há consultas staging carregadas. Agregações SQL internas de descontos, custo histórico por fulfillment item e movimentos customer_return por return item reduzem cada ramo filho a uma chave antes dos joins.

## Privilégios PostgreSQL

A role `projetobi_pbi_ro` recebeu somente `USAGE` em `logistics`, `inventory` e `after_sales`; e `SELECT` explícito em `logistics.fulfillment_items`, `inventory.stock_movements`, `after_sales.returns`, `after_sales.return_items` e `sales.applied_discounts`. O schema `sales` já possuía `USAGE`. Nenhum privilégio foi concedido em `logistics.fulfillments` ou em outras tabelas.

A própria role autenticou em `projeto_bi`, retornou `transaction_read_only=on`, leu as cinco tabelas e teve `INSERT`, `UPDATE`, `DELETE`, `TRUNCATE` negados. A configuração `default_transaction_read_only=on` foi conferida no catálogo da role. Não houve alteração de dados, estrutura, migrations ou outras roles.

## Precisão monetária

O `unit_cost` real é `NUMERIC(20,8)`, conforme migration e catálogo. Power Query não converte custo de oito casas em `Currency.Type` nem em `number` binário. Os custos são projetados em PostgreSQL como inteiros `BIGINT` escalados por `10^8`:

- `unit_cost_x1e8`: custo unitário histórico em unidades de `R$ 0,00000001`.
- `fulfillment_cogs_x1e8`: `ABS(quantity_delta) * unit_cost * 10^8`, calculado e convertido no PostgreSQL.
- `return_movement_cost_x1e8`, `sellable_cogs_reversal_x1e8` e `non_sellable_loss_x1e8`: projeções análogas; custo non-sellable usa a média histórica por fulfillment item arredondada a oito casas conforme contrato.
- `returned_commercial_value_x1e8`: valor comercial atribuído às unidades recebidas, derivado do preço unitário menos o desconto pré-agregado por item e rateado pela quantidade original, com arredondamento na oitava casa para uma coluna inteira exata.

O maior custo estendido por movimento observado, escalado, foi `2.694.438.685.680`; a soma escalada do COGS canônico foi `72.598.154.099.143.845`. Ambos cabem em `Int64`. A consulta DAX temporária no Desktop retornou exatamente a soma inteira `72.598.154.099.143.845`, que ultrapassa `2^53`, sem perda. Após somar os custos analíticos em inteiros e dividir por `10^8`, o mecanismo DAX retornou `717.455.650,25964522` para o COGS ajustado, ante `717.455.650,25964524` exatos no PostgreSQL: diferença de `R$ 0,00000002`. O arredondamento para centavos permaneceu `R$ 717.455.650,26`. A representação binária intermediária foi medida; a agregação Whole Number é exata e a apresentação monetária em centavos coincide com o contrato.

Consultas DAX temporárias, não persistidas como medidas, calcularam receita após devoluções em `R$ 922.588.975,445`, lucro bruto em `R$ 205.133.325,185355` e margem em `22,2345302886815%`; os valores arredondados são `R$ 922.588.975,45`, `R$ 205.133.325,19` e `22,23%`, respectivamente. A perda non-sellable continua incluída no COGS ajustado e não foi subtraída novamente. Nenhuma medida financeira definitiva foi criada.

## Reconciliações SQL somente leitura

As projeções executadas pela role Power BI preservaram chaves e contagens:

| Validação | Resultado |
|---|---:|
| Itens comerciais projetados / chave única | 241.637 / 241.637 |
| Movimentos de fulfillment projetados / chave única | 237.742 / 237.742 |
| Itens de devolução projetados / chave única | 7.129 / 7.129 |
| Órfãos de produto/canal/cliente/loja entre chaves não nulas | 0 |
| Quantidade recebida | 7.128 (uma solicitação sem recebimento tem quantidade 0) |
| Receita de produto concluído antes de devoluções | R$ 949.319.764,19 |
| Valor comercial atribuído aos itens recebidos | R$ 26.730.788,745 |
| Receita após devoluções | R$ 922.588.975,445 |
| COGS de fulfillment — todos os pedidos | R$ 725.981.540,99143845 |
| COGS de fulfillment — pedidos concluídos | R$ 725.466.564,62350805 |
| Reversão sellable | R$ 8.010.914,36386281 |
| COGS analítico ajustado | R$ 717.455.650,25964524 |
| Perda non-sellable, componente já incluído no COGS ajustado | R$ 12.296.704,23413595 |
| Lucro bruto analítico de referência (ainda sem medida DAX) | R$ 205.133.325,18535476 |
| Margem de referência | 22,23% |

As identidades conferidas: `949.319.764,19 − 26.730.788,745 = 922.588.975,445`; `725.466.564,62350805 − 8.010.914,36386281 = 717.455.650,25964524`; e `922.588.975,445 − 717.455.650,25964524 = 205.133.325,18535476`. A perda non-sellable não é deduzida uma segunda vez.

Os baselines executados `01_sales_overview.sql`, `09_returns.sql` e `11_cost_and_margin.sql` fecharam com suas referências. O baseline 09 também evidencia que refund é independente; seus valores não foram carregados nesta fase. O baseline 10 descreve saldo de estoque atual e não é usado para custo histórico.

## Estado de validação e limitações

**Power BI Desktop:** a primeira atualização revelou `We cannot convert a value of type List to type Text` nas duas consultas novas. A causa foi uma lista extra na expressão `Table.TransformColumnTypes`; a estrutura foi corrigida para uma lista de pares coluna/tipo. O refresh seguinte concluiu sem erro. O projeto foi salvo, fechado e reaberto sem erro.

**Validação no mecanismo após refresh e reabertura:** 10 tabelas e 21 relações; 19 relações ativas e duas inativas para os papéis de data do pedido; todas 21 muitas-para-uma e unidirecionais; nenhum relacionamento fato-fato. O grão de `FatoCustoFulfillment` foi 237.742 linhas/chaves únicas e o de `FatoDevolucoes` 7.129 linhas/chaves únicas. As 28 medidas permaneceram em `_Medidas`, distribuídas nas sete Display Folders. A anotação do modelo mantém `__PBI_TimeIntelligenceEnabled = 0`.

Os gates comerciais repetidos após reabertura passaram: 120.000 pedidos; 241.637 itens; 116.305 concluídos; receita antes de devoluções `R$ 949.319.764,19`; YTD 2026 `R$ 234.603.762,77`; YTD 2025 `R$ 209.080.826,98`; crescimento YTD YoY `12,2072100816979%` (12,2072% apresentado). Os inteiros escalados de COGS, reversão sellable, perdas non-sellable e valor comercial de devoluções coincidiram com SQL.

Consultas temporárias por dimensões confirmaram contexto por ano/calendário, canal, produto, categoria, cliente e loja; a classificação por `stock_destination` separou `sellable`, `quarantine`, `repair` e `discard`. Comparações SQL × DAX para canal `CH-PHYSICAL`, categoria `CAT-NOTEBOOK` e ano operacional 2026 coincidiram exatamente em contagens e valores escalados. Chaves dimensionais nulas aparecem no membro em branco; uma solicitação de devolução sem recebimento permanece sem data operacional. Não foram encontrados órfãos para as chaves não nulas.

Escopo futuro: aprovar e implementar medidas DAX financeiras em `_Medidas`. Nenhuma página analítica ou dashboard foi criada nesta fase; não avançar automaticamente para a próxima fase.
