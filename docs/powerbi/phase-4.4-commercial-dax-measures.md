# Fase 4.4 — Medidas DAX Comerciais e Inteligência Temporal

**Status: PASS — medidas, reconciliações, refresh e reabertura validados.**
**Modelo:** `powerbi/ProjetoBI.pbip`
**Checkpoint base:** `d8081d7` — `feat(powerbi): implementa modelo estrela comercial`

## Escopo e organização

Foram definidas 28 medidas nos fatos existentes, sem tabela de medidas artificial e sem alterar tabelas, relacionamentos ou consultas Power Query:

- 24 medidas em [`FatoPedidos.tmdl`](../../powerbi/ProjetoBI.SemanticModel/definition/tables/FatoPedidos.tmdl), para cabeçalho, pedidos, valores comerciais e tempo.
- 4 medidas em [`FatoItensPedido.tmdl`](../../powerbi/ProjetoBI.SemanticModel/definition/tables/FatoItensPedido.tmdl), para linhas, unidades, pedidos com itens e participação de unidades.

Todas têm expressão DAX, formato, Display Folder e descrição com regra, grão e limitações. A tabela de pedidos está organizada nas pastas `01 | Pedidos`, `02 | Faturamento`, `03 | Descontos`, `04 | Ticket Médio`, `06 | Inteligência Temporal` e `07 | Indicadores Percentuais`. A tabela de itens usa `05 | Produtos e Itens` e `07 | Indicadores Percentuais`.

## Catálogo de medidas

| Display Folder | Medidas | Grão e regra |
|---|---|---|
| `01 | Pedidos` | Total de Pedidos; Pedidos Concluídos; Pedidos Cancelados; Pedidos Confirmados | Contagem distinta de `sales_order_id` em `FatoPedidos`; os estados são os atuais/finais do conjunto. |
| `02 | Faturamento` | Valor Total dos Pedidos — Todos os Status; Valor Bruto de Produtos — Pedidos Concluídos; Receita Líquida de Produtos — Antes de Devoluções; Frete Cobrado — Pedidos Concluídos; Valor Total — Pedidos Concluídos | Somas do cabeçalho. A receita líquida é subtotal menos desconto de cabeçalho, antes de devoluções; frete permanece separado. |
| `03 | Descontos` | Descontos — Pedidos Concluídos | Soma do desconto comercial no cabeçalho dos pedidos concluídos; não é rateio por item. |
| `04 | Ticket Médio` | Ticket Médio — Pedidos Concluídos | Valor total concluído incluindo frete dividido por pedidos concluídos, com `DIVIDE`. |
| `05 | Produtos e Itens` | Total de Linhas de Itens; Unidades Pedidas; Pedidos Distintos com Itens no Contexto | Contagem/soma/distinct count na granularidade de `FatoItensPedido`. Quantidade é originalmente pedida, não atendida nem líquida de devolução. |
| `06 | Inteligência Temporal` | Pedidos no Ano Anterior; Variação Absoluta de Pedidos YoY; Variação Percentual de Pedidos YoY; Pedidos YTD; Receita de Produtos no Ano Anterior — Antes de Devoluções; Variação Absoluta de Receita YoY — Antes de Devoluções; Variação Percentual de Receita YoY — Antes de Devoluções; Receita YTD — Antes de Devoluções; Receita YTD Ano Anterior — Antes de Devoluções; Variação Percentual de Receita YTD YoY — Antes de Devoluções | Medidas reutilizam os indicadores-base e `DATEADD`, `DATESYTD` e `DIVIDE`; dependem de contexto de calendário para comparação. |
| `07 | Indicadores Percentuais` | Taxa de Conclusão; Taxa de Cancelamento; Participação de Pedidos por Status; Participação de Unidades no Contexto de Produto | Divisões seguras; ver abaixo o universo do denominador. |

### Filtros e denominadores

As medidas de pedidos e valores do cabeçalho respeitam calendário, canal, cliente e loja, inclusive o membro em branco, pois essas dimensões se relacionam à fato de pedidos. Elas retornam `BLANK()` quando `DimProduto` está diretamente filtrada. Produto/categoria só filtra `FatoItensPedido`; repetir totais de cabeçalho em cada produto criaria uma atribuição comercial enganosa. `Valor Total dos Pedidos — Todos os Status` também remove qualquer filtro de status explicitamente aplicado. Não foram criadas relações bidirecionais nem fato-fato.

As medidas de itens respeitam produto/categoria e as dimensões conformadas propagadas à fato de itens. `Participação de Pedidos por Status` usa como denominador os mesmos filtros dimensionais, removendo apenas `FatoPedidos[order_status]`; portanto mede composição por status, não participação de canal ou produto. `Participação de Unidades no Contexto de Produto` remove todos os filtros de `DimProduto` no denominador e preserva calendário, canal, cliente e loja; funciona tanto ao agrupar produto quanto categoria.

As divisões sem denominador e as comparações sem período anterior disponível retornam em branco. As medidas de receita mantêm em branco quando o contexto não contém dados; não transformam ausência em zero.

## Contratos financeiros e reconciliação de referência

Campos monetários da origem permanecem Fixed decimal (`Currency.Type` nas consultas Power Query); medidas agregam os valores do cabeçalho sem conversões para ponto flutuante ou rateio por item. Referências aprovadas nos baselines SQL `01_sales_overview.sql`, `02_sales_monthly.sql`, `03_sales_by_channel.sql`, `04_sales_by_store.sql`, `05_sales_by_category.sql` e `12_yoy_ytd.sql`:

| Medida | Baseline |
|---|---:|
| Valor Total dos Pedidos — Todos os Status | R$ 980.010.657,75 |
| Valor Bruto de Produtos — Pedidos Concluídos | R$ 971.645.716,62 |
| Descontos — Pedidos Concluídos | R$ 22.325.952,43 |
| Receita Líquida de Produtos — Antes de Devoluções | R$ 949.319.764,19 |
| Frete Cobrado — Pedidos Concluídos | R$ 786.720,00 |
| Valor Total — Pedidos Concluídos | R$ 950.106.484,19 |
| Ticket Médio — Pedidos Concluídos | R$ 8.169,094056… (apresentação a centavos: R$ 8.169,09) |

Identidades aprovadas: `971.645.716,62 − 22.325.952,43 = 949.319.764,19`; `949.319.764,19 + 786.720,00 = 950.106.484,19`. O `total_amount` agregado de todos os status não é faturamento realizado. Nenhuma medida representa pagamento capturado, refund, valor após devolução, COGS ou margem.

## Política temporal

`DimCalendario[Data]` é a única fonte temporal; a tabela cobre 2023-01-01 a 2026-09-30 e o modelo tem `__PBI_TimeIntelligenceEnabled = 0`. Não há referência a `TODAY()`. YoY requer filtro/linha de calendário; sem esse contexto retorna em branco. O ano de 2023 não tem período comparável no calendário e, portanto, medidas do ano anterior retornam em branco. Quando a data anterior existe, as variações percentuais usam `DIVIDE` e retornam em branco se o denominador for zero.

YTD acumula de janeiro até a última data do contexto. Para comparar os anos parciais, selecionar 2026 em calendário até 30 de setembro; `Receita YTD Ano Anterior — Antes de Devoluções` desloca essa janela para janeiro–setembro de 2025. Baselines de `12_yoy_ytd.sql`:

| Jan–setembro | Receita líquida de produtos antes de devoluções |
|---|---:|
| 2025 | R$ 209.080.826,98 |
| 2026 | R$ 234.603.762,77 |

Não interpretar 2025 YTD como ano completo nem inferir qualquer venda em outubro–dezembro de 2026.

## Validação

| Gate | Esperado | Estado |
|---|---:|---|
| Carga TMDL e compilação das expressões | 28 medidas, zero `ErrorMessage` no mecanismo semântico local do Desktop | **PASS** — as 28 medidas foram consultadas em `$SYSTEM.TMSCHEMA_MEASURES`; nenhuma reportou erro. |
| Pedidos; completed; cancelled; confirmed; linhas de itens | 120.000; 116.305; 3.265; 430; 241.637 | **PASS** — resultados DAX iguais às referências. |
| Sem cliente; sem loja | 19.829; 57.420 | **PASS** — medidas de cliente anônimo e membro em branco da loja conferidas. |
| Seis valores financeiros e ticket | Tabela financeira acima | **PASS** — DAX igual aos seis baselines ao centavo; ticket calculado R$ 8.169,0941 (apresentação R$ 8.169,09); as duas identidades financeiras também fecham. |
| Distribuições anuais | 2023: 24.000/23.348; 2024: 30.000/29.188; 2025: 36.000/35.033; 2026: 30.000/28.736 (pedidos totais/concluídos) | **PASS** — contagens DAX por ano; receita líquida antes de devoluções: R$ 186.335.698,29; R$ 237.714.985,51; R$ 290.665.317,62; R$ 234.603.762,77. |
| Jan–set YTD 2025 e 2026; comparação equivalente | R$ 209.080.826,98; R$ 234.603.762,77; +12,2072100817% | **PASS** — DAX reproduziu as duas referências de `12_yoy_ytd.sql`, com a janela de janeiro a setembro nos dois anos. |
| Canal | Ecommerce: 35.400/34.178 pedidos/concluídos e R$ 317.845.308,12 em todos status; físico e marketplace também verificados | **PASS** — valores DAX reconciliados aos resultados SQL read-only. |
| Loja, cliente e combinação de filtros | `ST-PO-001` físico/2025: 2.435/2.362 pedidos/concluídos; cliente 2793808: 13/11 e R$ 74.106,13/R$ 67.502,88 total/concluídos | **PASS** — seleções conferidas contra SQL read-only; combinação loja + canal + ano também reconciliou valor bruto, desconto e total concluído. |
| Produto/categoria e guardas de grão | Produto 66295: 294 linhas, 308 unidades, 294 pedidos com item; categoria `CAT-PROCESSOR`: 20.272 linhas, 21.720 unidades, 19.087 pedidos com item | **PASS** — DAX igual ao SQL read-only. Medidas de cabeçalho ficaram em branco nas categorias e no produto. |
| Mês sem movimento e sem filtro temporal | YoY em branco sem período comparável; total e YoY em branco em 30/09/2026 sem pedidos | **PASS** — DAX retornou `BLANK()` conforme definido. |
| Refresh pelo Desktop, salvar, fechar e reabrir; repetir consultas após reabertura | Sem erro | **PASS** — o usuário confirmou que o PBIP reabriu sem erro; após a reabertura, o mecanismo local carregou 28 medidas sem erros e repetiu os gates centrais e YTD com os mesmos resultados. |

Na primeira abertura técnica do engine, as propriedades TMDL foram incorporadas ao texto das expressões DAX porque os corpos estavam no mesmo nível de indentação das propriedades; o corpo foi recuado um nível adicional nos dois arquivos. Em seguida, o usuário forneceu um erro do Desktop (`2026-10-12 16:41:15 -03:00`): `Unsupported property - description is not a supported property in the current context!`, documento `./tables/FatoItensPedido`, linha 142. As 28 descrições foram convertidas da propriedade inválida `description:` para blocos `///` imediatamente acima das medidas. Após a correção, o PBIP foi carregado no mecanismo semântico local do Desktop: as 28 medidas apareceram sem erro e suas consultas DAX foram avaliadas. A verificação cruzada read-only encontrou igualdade com os baselines nos contextos documentados acima. O usuário concluiu a atualização, salvamento e reabertura sem erro; após a reabertura, foram repetidos o inventário sem erros, os totais comerciais, os seis valores financeiros, o ticket e os valores YTD/YoY. A fase atende aos gates documentados.

## Limites e próxima etapa

O cabeçalho não atribui faturamento a produto/categoria. As unidades são quantidades pedidas e não devem ser rotuladas como expedidas, efetivamente vendidas ou líquidas de devoluções. Descontos não foram rateados por item. Retornos, pagamentos/refunds, receita pós-devolução, COGS, lucro e margem exigem outros fatos e contratos e permanecem fora da fase. Próximo passo recomendado: iniciar a Fase 4.5 somente após autorização explícita, mantendo dashboards e contratos de receita após devoluções no escopo próprio.
