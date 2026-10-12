# Fase 4.6 — auditoria do modelo semântico

**Status: PASS — DASHBOARD READY (modelo semântico validado; ainda não há dashboard).**

**Checkpoint:** a7899e2 — medidas DAX financeiras.
**Power BI Desktop:** 2.158.1177.0 (26.09), processo local em execução no PBIP do projeto.
**Escopo:** inspeção TMDL/PBIR, metadados do mecanismo local, consultas DAX de diagnóstico e reconciliações PostgreSQL somente leitura. Nenhuma alteração de modelo, fonte ou regra de negócio foi feita nesta auditoria.

## 1. Inventário e integridade

O modelo carregado contém dez tabelas: quatro fatos, cinco dimensões compartilhadas e a tabela técnica _Medidas. O número de linhas retornado pelo mecanismo local coincide com as contagens de referência.

| Tabela | Linhas | Grão / finalidade |
|---|---:|---|
| FatoPedidos | 120.000 | Um cabeçalho por pedido |
| FatoItensPedido | 241.637 | Um item comercial por sales_order_item_id; desconto pré-agregado por item |
| FatoCustoFulfillment | 237.742 | Um movimento de estoque de fulfillment por stock_movement_id |
| FatoDevolucoes | 7.129 | Um item de devolução por return_item_id |
| DimProduto | 1.000 | Produto; relação com categoria projetada na dimensão |
| DimCliente | 45.000 | Cliente, incluindo membro em branco para pedidos anônimos |
| DimLoja | 10 | Loja comercial, incluindo membro em branco |
| DimCanal | 4 | Canal de venda |
| DimCalendario | 1.369 | Dias contínuos de 2023-01-01 a 2026-09-30 |
| _Medidas | 1 linha auxiliar em branco | Tabela técnica sem dado de negócio e sem relações |

São 55 medidas visíveis em _Medidas, com descrição, lineage tag única e Display Folder preenchida. Não há erro reportado pelo mecanismo para as medidas, relações ou partições. As dez partições estão em Import. Auto date/time permanece desligado pela anotação __PBI_TimeIntelligenceEnabled = 0; o mecanismo não mostrou tabelas automáticas de data. O registro auxiliar único de _Medidas é resultado da coluna calculada _Apoio em branco, não uma linha comercial.

## 2. Catálogo de medidas

As expressões completas e metadados individuais continuam definidos em powerbi/ProjetoBI.SemanticModel/definition/tables/_Medidas.tmdl. A inspeção confirmou 55 expressões, 55 descrições, 55 lineage tags distintas e os formatos numéricos, monetários e percentuais adequados ao papel descrito. A lista abaixo registra cada medida e sua pasta; os comentários TMDL documentam grão, unidade, filtros e ausência de valor.

| Pasta | Medidas |
|---|---|
| 01 \| Pedidos | Total de Pedidos; Pedidos Concluídos; Pedidos Cancelados; Pedidos Confirmados |
| 02 \| Faturamento | Valor Total dos Pedidos — Todos os Status; Valor Bruto de Produtos — Pedidos Concluídos; Receita Líquida de Produtos — Antes de Devoluções; Frete Cobrado — Pedidos Concluídos; Valor Total — Pedidos Concluídos |
| 03 \| Descontos | Descontos — Pedidos Concluídos |
| 04 \| Ticket Médio | Ticket Médio — Pedidos Concluídos |
| 05 \| Produtos e Itens | Total de Linhas de Itens; Unidades Pedidas; Pedidos Distintos com Itens no Contexto |
| 06 \| Inteligência Temporal | Pedidos no Ano Anterior; Variação Absoluta de Pedidos YoY; Variação Percentual de Pedidos YoY; Pedidos YTD; Receita de Produtos no Ano Anterior — Antes de Devoluções; Variação Absoluta de Receita YoY — Antes de Devoluções; Variação Percentual de Receita YoY — Antes de Devoluções; Receita YTD — Antes de Devoluções; Receita YTD Ano Anterior — Antes de Devoluções; Variação Percentual de Receita YTD YoY — Antes de Devoluções |
| 07 \| Indicadores Percentuais | Taxa de Conclusão; Taxa de Cancelamento; Participação de Pedidos por Status; Participação de Unidades no Contexto de Produto |
| 08 \| Devoluções | Itens de Devolução; Unidades Recebidas em Devolução; Valor Comercial Devolvido — Data do Recebimento; Valor Comercial Devolvido — Data do Pedido |
| 09 \| Custos e COGS | Perda Non-Sellable — Data do Recebimento; Perda Non-Sellable — Data do Pedido; COGS de Fulfillment — Data do Movimento; COGS Original Concluído — Data do Movimento; COGS Original Concluído — Data do Pedido; Reversão COGS Sellable — Data do Recebimento; Reversão COGS Sellable — Data do Pedido; COGS Analítico Ajustado |
| 10 \| Lucro e Margem | Receita de Produtos — Antes de Devoluções (Itens); Receita Analítica Após Devoluções; Lucro Bruto Analítico; Margem Bruta Analítica; Participação do COGS Ajustado na Receita; Percentual de Devoluções Comerciais; Participação da Reversão Sellable no COGS; Participação Non-Sellable no COGS Ajustado |
| 11 \| Análise Financeira Temporal | Receita Analítica YTD; Receita Analítica YTD Ano Anterior; Variação Percentual de Receita Analítica YTD; Variação Absoluta de Receita Analítica YTD; COGS Analítico Ajustado YTD; Lucro Bruto Analítico YTD; Margem Bruta Analítica YTD |

### Dependências e origem

O grafo estático das referências entre medidas foi comparado aos metadados do mecanismo: não há referência inválida ou ciclo. As medidas base se originam de FatoPedidos (contagens, status, valores de cabeçalho), FatoItensPedido (itens, unidades e receita atribuída ao produto) ou FatoCustoFulfillment/FatoDevolucoes (movimentos, custos e devoluções). Medidas temporais, percentuais e de margem dependem dessas bases.

| Cálculo derivado | Dependências-chave |
|---|---|
| Receita líquida de produtos antes de devoluções (cabeçalho) | Valor bruto de produtos concluídos; descontos de pedidos concluídos |
| Receita de produtos antes das devoluções (itens) | FatoPedidos[order_status] e FatoItensPedido; conjunto de pedidos concluídos aplicado por TREATAS |
| Receita analítica após devoluções | Receita por itens; valor comercial devolvido por data do pedido |
| COGS analítico ajustado | COGS original concluído por data do pedido; reversão sellable por data do pedido |
| Lucro e margem brutos | Receita analítica após devoluções; COGS analítico ajustado |
| Medidas YTD financeiras | Medida financeira base correspondente; calendário; para YoY, janela YTD deslocada um ano |
| Percentuais de devolução/COGS/reversão/perda | Numerador financeiro identificado na medida; denominador explicitado na descrição e expressão com DIVIDE |

Os cálculos financeiros usam inteiros x10^8 para custos e valores rateados; somam antes de converter para BRL. Medidas proporcionais usam DIVIDE e retornam BLANK sem denominador. As medidas de cabeçalho que não têm atribuição segura a produto retornam BLANK sob filtro direto de DimProduto. Isso previne que valores de pedido se repitam por item/categoria. A medida financeira por produto usa o grão de item e o desconto pré-agregado homologado. Não se observou cálculo redundante que justifique refatoração. A complexidade localizada em TREATAS e USERELATIONSHIP corresponde à separação necessária entre os grãos e papéis de data; sem evidência de gargalo ou divergência, foi preservada.

## 3. Relacionamentos e filtros

O mecanismo confirmou 21 relacionamentos muitos-para-um, todos unidirecionais, com 19 ativos e dois inativos. Não há relação entre fatos nem filtro bidirecional. O lado um é sempre a dimensão. As relações abaixo preservam o grão das fatos e permitem dimensões conformadas comuns.

| Fato e coluna | Dimensão e coluna | Estado | Uso |
|---|---|---|---|
| FatoPedidos.order_date | DimCalendario.Data | Ativo | Coorte comercial e tempo dos pedidos |
| FatoItensPedido.order_date | DimCalendario.Data | Ativo | Coorte dos itens |
| FatoPedidos.customer_id | DimCliente.customer_id | Ativo | Cliente |
| FatoItensPedido.customer_id | DimCliente.customer_id | Ativo | Cliente |
| FatoPedidos.store_id | DimLoja.store_id | Ativo | Loja comercial |
| FatoItensPedido.store_id | DimLoja.store_id | Ativo | Loja comercial |
| FatoPedidos.sales_channel_id | DimCanal.sales_channel_id | Ativo | Canal |
| FatoItensPedido.sales_channel_id | DimCanal.sales_channel_id | Ativo | Canal |
| FatoItensPedido.product_id | DimProduto.product_id | Ativo | Produto/categoria no grão de item |
| FatoCustoFulfillment.movement_date | DimCalendario.Data | Ativo | Fluxo de custo por data do movimento |
| FatoCustoFulfillment.order_date | DimCalendario.Data | Inativo | Coorte ativada por USERELATIONSHIP |
| FatoCustoFulfillment.product_id | DimProduto.product_id | Ativo | Produto/categoria |
| FatoCustoFulfillment.customer_id | DimCliente.customer_id | Ativo | Cliente |
| FatoCustoFulfillment.store_id | DimLoja.store_id | Ativo | Loja comercial |
| FatoCustoFulfillment.sales_channel_id | DimCanal.sales_channel_id | Ativo | Canal |
| FatoDevolucoes.return_received_date | DimCalendario.Data | Ativo | Fluxo por data de recebimento |
| FatoDevolucoes.order_date | DimCalendario.Data | Inativo | Coorte ativada por USERELATIONSHIP |
| FatoDevolucoes.product_id | DimProduto.product_id | Ativo | Produto/categoria |
| FatoDevolucoes.customer_id | DimCliente.customer_id | Ativo | Cliente |
| FatoDevolucoes.store_id | DimLoja.store_id | Ativo | Loja comercial |
| FatoDevolucoes.sales_channel_id | DimCanal.sales_channel_id | Ativo | Canal |

### Matriz de filtros validada

| Contexto | Evidência e interpretação |
|---|---|
| Calendário × canal | Reconciliação dos quatro anos/canais; filtro percorre dimensão compartilhada às fatos compatíveis. |
| Calendário × produto e categoria | 1.000 produtos reconciliados; as combinações canal × categoria × ano (144 chaves) reconciliaram. Receita financeira respeita o grão de item. |
| Cliente × loja × canal × ano | Consulta combinada retornou um pedido concluído, receita R$ 1.355,02, COGS R$ 1.515,063124 e lucro R$ -160,043124, igual ao SQL. |
| Cabeçalho sob filtro de produto/categoria | Medidas de total/pedidos comerciais que não suportam atribuição retornaram BLANK. Não se distribui o total de cabeçalho em itens. |
| Custos e receita | Custos e devoluções não se relacionam diretamente às fatos de vendas; 144 combinações reconciliaram, sem multiplicação de receita. |
| Devoluções e destinação | 7.129 linhas de item de devolução; 7.128 unidades recebidas; destinos sellable, quarantine, repair e discard reconciliados. Um item sem recebimento permanece sem evento/datado. |
| Membros em branco | 19.318 pedidos concluídos sem cliente e 55.442 sem loja permaneceram nos totais; valores financeiros reconciliaram ao SQL. |
| Subtotais | Testes por produto, categoria/canal/ano, mês, destino e amostra cliente/loja foram conciliados em centavos; membro em branco preservado. |

Não foi encontrado fanout lógico. Uma página deverá usar as medidas adequadas ao assunto: valores de cabeçalho não são métricas de produto; medidas operacionais de custo/devolução não devem ser combinadas silenciosamente com receita de coorte.

## 4. Política temporal

O calendário é contínuo e termina em 2026-09-30, o cutoff comercial aprovado. O Power Query projeta datas locais com America/Sao_Paulo. As três perspectivas permanecem nomeadas e separadas:

- Pedido/coorte: order_date. A margem analítica usa essa perspectiva para receita, COGS concluído, devolução comercial, reversão sellable e perda non-sellable.
- Operação: movement_date para custo de fulfillment e return_received_date para recebimento, reversão ou perda de devolução.
- Comparação: medidas YoY exigem contexto do calendário e deslocam o período com DATEADD; as versões YTD deslocam a janela acumulada equivalente.

As relações order_date dos fatos de custo e devolução são ativadas explicitamente com USERELATIONSHIP, substituindo o vínculo ativo de data operacional no escopo da medida. Nenhuma medida usa TODAY(). Jan–set/2026 foi comparado a jan–set/2025. A documentação da Fase 4.5C registra BLANK em período sem comparação e em data sem evento.

## 5. Reconciliação financeira e comercial

As consultas PostgreSQL deste ciclo foram somente leitura. O alvo foi projeto_bi; a sessão inspecionada permaneceu transaction_read_only=on. A role projetobi_pbi_ro tem LOGIN, sem SUPERUSER/CREATEDB/CREATEROLE/BYPASSRLS, default_transaction_read_only=on, sem CREATE na database/schema e sem grants de escrita nas tabelas auditadas. Não houve DDL, DML, carga nem execução dos baselines com escrita.

| Indicador global | PostgreSQL | DAX local | Resultado |
|---|---:|---:|---|
| Pedidos / concluídos / linhas de itens | 120.000 / 116.305 / 241.637 | Idêntico | PASS |
| Itens de devolução / unidades recebidas | 7.129 / 7.128 | Idêntico | PASS |
| Receita produto antes de devoluções | R$ 949.319.764,19 | R$ 949.319.764,19 | PASS |
| Valor comercial devolvido | R$ 26.730.788,745 | R$ 26.730.788,745 | PASS |
| Receita após devoluções | R$ 922.588.975,445 | R$ 922.588.975,445 | PASS |
| COGS original concluído | R$ 725.466.564,62350805 | R$ 725.466.564,623508 | PASS |
| Reversão sellable | R$ 8.010.914,36386281 | R$ 8.010.914,363863 | PASS |
| COGS ajustado | R$ 717.455.650,25964524 | R$ 717.455.650,259645 | PASS |
| Perda non-sellable, dentro do COGS | R$ 12.296.704,23413595 | R$ 12.296.704,234136 | PASS |
| Lucro bruto analítico | R$ 205.133.325,18535476 | R$ 205.133.325,185355 | PASS |
| Margem bruta | 22,2345302886815% | 22,2345302886815% | PASS |

As identidades financeiras fecham: receita antes menos devolução igual à receita após; COGS concluído menos reversão sellable igual ao COGS ajustado; receita após menos COGS ajustado igual ao lucro; lucro dividido pela receita após igual à margem. O valor non-sellable é informativo e já permanece dentro do COGS ajustado; não se deduz outra vez. Refund de pagamento e frete não são subtraídos/incluídos indevidamente na receita/produto do lucro.

### Precisão e segmentações

Inteiros escalados x10^8 são somados antes da conversão. O maior total escalado observado é 72.598.154.099.143.845, inferior ao limite Int64; também excede 2^53, e os testes inteiros confirmaram a soma esperada. A conversão DAX pode produzir pequena diferença subcentésima binária (documentada previamente como até R$ 0,00000002); os valores conciliam na precisão do contrato e ao centavo. Não houve divergência financeira material ou arredondamento intermediário indevido identificado.

| Corte SQL × DAX | Chaves/grupos | Resultado |
|---|---:|---|
| Produto | 1.000 | Totais por receita, COGS e lucro reconciliam ao centavo; máximas absolutas abaixo de R$ 0,000000001 |
| Canal × categoria × ano | 144 | Todas as chaves e totais reconciliados ao centavo; maior diferença < R$ 0,000000004 |
| Mês comercial | 45 | Reconciliação anterior da Fase 4.5C, ao centavo |
| Destino da devolução | 5 incluindo branco | Soma inteira escalada idêntica; unidades recebidas 7.128 |
| Jan–set por coorte | 2025 e 2026 | Janelas iguais conciliadas; margens 22,9907977484% e 22,9994026697% |
| Cliente/loja/canal/ano | amostra combinada | Receita, custo e lucro coincidiram com SQL |

Os 13 baselines SQL oficiais foram inventariados, permanecem rastreados e sem alteração. Nesta fase, os baselines existentes serviram de contrato/documentação; as consultas de auditoria foram SELECT em sessão somente leitura.

## 6. Desempenho

Foram cronometradas consultas DAX representativas no mecanismo Desktop local, duas execuções de cada consulta. São tempos de parede incluindo transferência local do resultado; não são tempos isolados de execução VertiPaq.

| Consulta | Linhas de saída | Primeira / repetida |
|---|---:|---:|
| Globais | 1 | 50 / 18 ms |
| Ano | 4 | 117 / 56 ms |
| Mês | 45 | 83 / 64 ms |
| Canal × categoria × ano | 144 | 107 / 79 ms |
| Produto | 1.000 | 84 / 77 ms |
| YTD | 4 | 436 / 367 ms |
| Ano operacional | 5 | 9 / 4 ms |

Os tempos não mostram gargalo que justifique alterar medidas homologadas. O YTD foi a consulta mais lenta da amostra, mas permaneceu abaixo de meio segundo na máquina local. Não houve profiling dedicado de memória/VertiPaq nem cronometragem isolada do refresh Power Query; não havia DAX Studio disponível e nenhuma ferramenta foi instalada. Não inventamos consumo de recursos nem atribuímos tempos a uma medida específica.

**Recomendações:** construir visuais com medidas compatíveis com seu grão; manter filtros de página seletivos e evitar matrizes muito detalhadas antes de medir no Desktop; simular os limites da capacidade-alvo e medir refresh/visuais no ambiente de publicação antes do release. O report.json local contém queryLimitOption=None e limites customizados de memória/tempo; a origem dessa mudança não está determinada e a intenção deve ser revista antes de publicação. A documentação Microsoft explica que o Desktop local não aplica naturalmente os limites da capacidade publicada e permite simulação: [Definir limites de consulta no Power BI Desktop](https://learn.microsoft.com/en-us/power-bi/create-reports/desktop-set-visual-query-limits).

## 7. Segurança, riscos e limitações

| Prioridade | Achado | Impacto / ação |
|---|---|---|
| Média, antes de publicar | report.json acrescenta queryLimitOption=None e limites customizados de memória/tempo, sem autoria/objetivo comprovado. | Revisar no Desktop a configuração de simulação para a capacidade de destino antes do release. Nenhuma mudança foi feita nesta fase. |
| Baixa | DAX usa representação de ponto flutuante depois da soma inteira x10^8. | Diferenças subcentésimas conhecidas; centavos homologados coincidem. Documentar se um consumidor futuro exigir precisão subcentésima. |
| Baixa, operacional | Uma solicitação de devolução sem recebimento e membros dimensionais em branco são legítimos. | Preservar tratamento de BLANK/membro em branco em visuais e interpretar contagem de linhas versus unidades recebidas corretamente. |
| Limitação de medição | Sem profiling VertiPaq/memória ou duração isolada de refresh. | Medir visuais e refresh no Desktop/capacidade de destino ao construir o dashboard. |

O PBIP foi reaberto sem erro e a atualização completa já havia sido confirmada pelo usuário na Fase 4.5C. Nesta auditoria, o modelo local foi consultado sem novo refresh. Nenhuma credencial está nos arquivos rastreados; caches locais não foram incluídos. Nenhum backup foi incluído ou criado; os 13 baselines e a base operacional permaneceram intocados.

## 8. Prontidão e pendências

**Gate A: PASS — DASHBOARD READY.** Dez tabelas, 55 medidas, onze pastas, 21 relações, ausência de ciclos/erros, reconciliações SQL × DAX, comportamento temporal e filtros principais foram validados. Pronto significa que a camada semântica pode ser usada para iniciar a fase de relatórios; não significa que visuais, páginas ou capacidade de publicação estejam implementados/validados.

Antes do primeiro release: revisar queryLimitOption na capacidade-alvo; medir visuais/refresh reais; escolher medidas de acordo com o grão de cada visual. Não iniciar a Fase 5 nesta auditoria, não criar dashboards e não alterar os cálculos homologados.
