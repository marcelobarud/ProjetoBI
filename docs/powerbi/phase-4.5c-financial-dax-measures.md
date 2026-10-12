# Fase 4.5C — medidas DAX financeiras e margem analítica

**Status: PASS — medidas financeiras, refresh, persistência e reabertura validados.**

**Checkpoint de entrada:** `f813c14` — Fase 4.5B.

**Projeto:** `powerbi/ProjetoBI.pbip`
**Definições:** `powerbi/ProjetoBI.SemanticModel/definition/tables/_Medidas.tmdl`

## Escopo e decisão temporal

Foram adicionadas 27 medidas financeiras definitivas em `_Medidas`; as 28 medidas comerciais existentes foram preservadas. O total agora é 55 medidas. Não foram criadas páginas, dashboards, medidas de pagamento/refund ou relacionamentos.

A margem analítica é uma **coorte da data comercial do pedido**. Receita, COGS concluído, devolução comercial, reversão sellable e perda non-sellable usam a data local do pedido. Para custos e devoluções, `USERELATIONSHIP` ativa explicitamente a relação inativa `order_date`, substituindo, no contexto da medida, a data operacional ativa.

As medidas operacionais permanecem separadas:

- COGS de fulfillment por `movement_date`.
- Devoluções, reversões e perdas por `return_received_date`.

Elas respondem a perguntas de fluxo operacional e não são combinadas com receita de coorte para formar uma margem mensal. O modelo conserva 21 relações: 19 ativas e duas inativas para as datas de pedido; as relações permanecem unidirecionais e muitos-para-um.

O calendário cobre 2023-01-01 a 2026-09-30. Para comparar 2026 com o período equivalente de 2025, filtrar 2026 e usar a medida “YTD Ano Anterior”; ela desloca a janela para janeiro–setembro de 2025. Não comparar o ano completo de 2025 com os nove meses de 2026. As medidas não usam `TODAY()`.

## Medidas implementadas

Todas ficam em `_Medidas`, têm descrição de negócio com grão, unidade, data/filtros e tratamento de ausência, e usam os formatos monetários ou percentuais apropriados. As expressões completas e propriedades TMDL estão no arquivo indicado acima.

| Display Folder | Medidas |
|---|---|
| `08 | Devoluções` | Itens de Devolução; Unidades Recebidas em Devolução; Valor Comercial Devolvido — Data do Recebimento; Valor Comercial Devolvido — Data do Pedido |
| `09 | Custos e COGS` | Perda Non-Sellable — Data do Recebimento; Perda Non-Sellable — Data do Pedido; COGS de Fulfillment — Data do Movimento; COGS Original Concluído — Data do Movimento; COGS Original Concluído — Data do Pedido; Reversão COGS Sellable — Data do Recebimento; Reversão COGS Sellable — Data do Pedido; COGS Analítico Ajustado |
| `10 | Lucro e Margem` | Receita de Produtos — Antes de Devoluções (Itens); Receita Analítica Após Devoluções; Lucro Bruto Analítico; Margem Bruta Analítica; Participação do COGS Ajustado na Receita; Percentual de Devoluções Comerciais; Participação da Reversão Sellable no COGS; Participação Non-Sellable no COGS Ajustado |
| `11 | Análise Financeira Temporal` | Receita Analítica YTD; Receita Analítica YTD Ano Anterior; Variação Absoluta de Receita Analítica YTD; Variação Percentual de Receita Analítica YTD; COGS Analítico Ajustado YTD; Lucro Bruto Analítico YTD; Margem Bruta Analítica YTD |

As 28 medidas comerciais permanecem nas sete pastas originais. Nenhuma medida auxiliar oculta foi necessária.

## Contratos financeiros

- **Receita de produtos antes das devoluções:** soma, na linha comercial, de unidades atendidas multiplicadas pelo preço unitário histórico líquido do desconto pré-agregado naquela chave de pedido/item. O conjunto de pedidos é limitado a `completed`; `TREATAS` aplica os IDs concluídos à fato de itens, sem relacionamento fato-fato. Frete não integra a receita.
- **Valor comercial devolvido:** usa somente o rateio homologado em `returned_commercial_value_x1e8` para unidades efetivamente recebidas de pedidos concluídos. Não usa `payments.refunds`. Há versões por data de recebimento e por data do pedido.
- **Receita analítica após devoluções:** receita de produtos atribuída aos itens antes das devoluções menos o valor comercial das devoluções recebidas. Não arredonda os componentes antes da subtração.
- **COGS original:** soma `fulfillment_cogs_x1e8` no grão de `stock_movement_id`. A medida de todos os status usa a data do movimento; a medida de pedidos concluídos é fornecida por data do movimento e por coorte do pedido.
- **Reversão sellable:** soma apenas `sellable_cogs_reversal_x1e8`, isto é, custo efetivamente reintegrado em destino vendável. Possui versões por recebimento e por pedido.
- **COGS ajustado:** COGS original de pedidos concluídos menos a reversão sellable da mesma coorte. Os inteiros escalados são somados antes da conversão por (10^8).
- **Perda non-sellable:** `quarantine`, `repair` e `discard), apresentada por data operacional ou coorte. É informativa e permanece dentro do COGS ajustado; não é deduzida outra vez no lucro.
- **Lucro e margem:** lucro = receita após devoluções − COGS ajustado; margem = lucro ÷ receita após devoluções. Frete fica fora. `DIVIDE` retorna BLANK sem denominador válido.

Os percentuais complementares documentam os denominadores: devoluções comerciais ÷ receita antes de devoluções; COGS ajustado ÷ receita após devoluções; reversão sellable ÷ COGS original concluído; perda non-sellable ÷ COGS ajustado.

## Reconciliações globais

PostgreSQL foi consultado em transação `READ ONLY`; o alvo confirmado foi database `projeto_bi`, e `transaction_read_only=on`. O modelo foi consultado no mecanismo semântico local do Power BI Desktop.

| Indicador | PostgreSQL / DAX | Apresentação |
|---|---:|---:|
| Pedidos; concluídos; linhas de itens | 120.000; 116.305; 241.637 | Contagens idênticas |
| Itens de devolução; unidades recebidas | 7.129; 7.128 | Contagens idênticas |
| Receita líquida de produtos antes de devoluções | R$ 949.319.764,19 | R$ 949.319.764,19 |
| Valor comercial das devoluções recebidas | R$ 26.730.788,745 | R$ 26.730.788,75 |
| Receita analítica após devoluções | R$ 922.588.975,445 | R$ 922.588.975,45 |
| COGS fulfillment — todos os pedidos | R$ 725.981.540,99143845 | R$ 725.981.540,99 |
| COGS original — pedidos concluídos | R$ 725.466.564,62350805 | R$ 725.466.564,62 |
| Reversão COGS sellable | R$ 8.010.914,36386281 | R$ 8.010.914,36 |
| COGS analítico ajustado | R$ 717.455.650,25964524 | R$ 717.455.650,26 |
| Perda non-sellable, já incluída no COGS | R$ 12.296.704,23413595 | R$ 12.296.704,23 |
| Lucro bruto analítico | R$ 205.133.325,18535476 | R$ 205.133.325,19 |
| Margem bruta analítica | 22,2345302886815% | 22,23% |

As quatro identidades financeiras fecharam:

1. R$ 949.319.764,19 − R$ 26.730.788,745 = R$ 922.588.975,445.
2. R$ 725.466.564,62350805 − R$ 8.010.914,36386281 = R$ 717.455.650,25964524.
3. R$ 922.588.975,445 − R$ 717.455.650,25964524 = R$ 205.133.325,18535476.
4. Lucro bruto ÷ receita após devoluções = 22,2345302886815%.

O mecanismo semântico retornou R$ 922.588.975,45, R$ 717.455.650,26 e R$ 205.133.325,19 ao aplicar arredondamento de apresentação a centavos; a margem exibida foi 22,23%. Um teste `ROUND` temporário confirmou esses valores sem arredondar componentes permanentes. Em 2026-09-30, data sem pedidos, receita e margem retornaram BLANK.

## Precisão e validações dimensionais

As somas escaladas comparadas entre SQL e DAX coincidiram como inteiros, inclusive o total de COGS de todos os pedidos, que excede (2^{53}). O maior total escalado é 72.598.154.099.143.845, abaixo do limite de Int64. A divisão DAX do COGS ajustado apresentou a diferença binária já medida na Fase 4.5B: R$ 0,00000002 em relação ao decimal PostgreSQL. Não alterou a apresentação em centavos nem foi mascarada por arredondamento intermediário.

| Contexto validado | Grupos | Maior diferença absoluta DAX × SQL | Resultado |
|---|---:|---:|---|
| Produto | 1.000 IDs | receita R$ 0,0000000004; COGS R$ 0,0000000004; lucro R$ 0,0000000006 | Todos reconciliam ao centavo |
| Canal × categoria × ano comercial | 144 | receita R$ 0,000000003; COGS R$ 0,000000002; lucro R$ 0,0000000022 | Todos reconciliam ao centavo |
| Mês comercial | 45 | receita R$ 0,000000003; COGS R$ 0,000000003; lucro R$ 0,0000000045 | Todos reconciliam ao centavo |
| Destino físico da devolução | 5, incluindo destino em branco | Inteiros escalados idênticos | PASS |
| Ano operacional | 2023–2026 | Inteiros escalados idênticos por ano | PASS |

Os testes por destino retornaram 2.851 itens sellable, 1.426 quarantine, 1.425 repair, 1.426 discard e um item sem destino/recebimento; o total de unidades recebidas foi 7.128. Os totais de valor comercial, reversão sellable e perda non-sellable por destino coincidiram com o PostgreSQL nos inteiros escalados.

Por data operacional, foram comparados movimentos de fulfillment por `movement_date` e devoluções/reversões/perdas por `return_received_date`. Em 2026, por exemplo, o COGS de movimento em todos os status foi R$ 181.025.690,79 e o COGS concluído R$ 180.510.714,43; estes números são fluxo por data operacional, não a coorte comercial.

Filtros de cliente, loja, canal e ano foram combinados e comparados ao SQL: loja `ST-PO-003`, cliente sintético 2793808, canal físico e 2025 produziram um pedido concluído, receita R$ 1.355,02, COGS R$ 1.515,063124 e lucro R$ -160,043124. Os membros em branco também foram verificados: cliente anônimo teve 19.318 pedidos concluídos e loja em branco 55.442; receitas, COGS e lucros reconciliaram ao centavo com o SQL.

## YTD e regressão comercial

As medidas comerciais existentes continuaram a retornar 120.000 pedidos, 116.305 concluídos, 241.637 linhas e receita antes de devoluções de R$ 949.319.764,19. O YTD comercial repetiu R$ 209.080.826,98 em jan–set/2025 e R$ 234.603.762,77 em jan–set/2026, crescimento de 12,2072100816979%.

Na margem financeira por coorte, jan–set/2025 foi comparado à mesma janela de 2026:

| Jan–set | Receita antes de devoluções | Receita após devoluções | COGS ajustado | Lucro bruto | Margem |
|---|---:|---:|---:|---:|---:|
| 2025 | R$ 209.080.826,98 | R$ 202.919.051,225 | R$ 156.266.342,56480376 | R$ 46.652.708,66019624 | 22,9907977484415% |
| 2026 | R$ 234.603.762,77 | R$ 228.660.758,74 | R$ 176.070.150,08984235 | R$ 52.590.608,65015765 | 22,9994026696798% |

A receita após devoluções cresceu 12,685702677792% na janela comparável. A igualdade em centavos foi confirmada; pequenas diferenças subcentésimas de ponto flutuante permanecem documentadas.

## Power BI Desktop e estado final

O PBIP foi aberto em uma instância nova após as alterações TMDL; o mecanismo carregou 55 medidas, sem `ErrorMessage`. O refresh completo do modelo local retornou sucesso. Depois do refresh, as 27 medidas novas foram avaliadas, os totais e YTD centrais foram repetidos, e o DMV confirmou 21 relações (19 ativas, duas inativas) e zero erros de medida.

Após a confirmação do usuário de que salvou, fechou e reabriu o PBIP sem erros, consultei novamente o modelo semântico carregado: 55 medidas, zero erros, 21 relações (19 ativas e duas inativas), as 11 pastas esperadas e os totais comerciais e financeiros centrais reconciliados. A persistência e a reabertura após o refresh estão validadas.

## Arquivos, limites e próximos passos

- Alterado: `powerbi/ProjetoBI.SemanticModel/definition/tables/_Medidas.tmdl` — 27 novas medidas.
- Criado: este relatório de fase.
- Atualizados: README do Power BI e plano mestre.
- Sem alteração: PostgreSQL, 28 medidas comerciais, 21 relações, baselines SQL, grãos factuais e relatório PBIR.
- As alterações locais anteriores em PBIR/TMDL/diagrama foram mantidas fora do escopo do commit.

Nenhum dashboard ou fase posterior foi iniciado. A Fase 4.5C atende aos critérios de aceite; dashboards permanecem para uma fase futura autorizada.
