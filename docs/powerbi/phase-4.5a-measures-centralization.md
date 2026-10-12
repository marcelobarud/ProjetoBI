# Fase 4.5A — Centralização das Medidas DAX

**Status: PASS — medidas centralizadas; validação estrutural, DAX, confirmação visual e reabertura concluídas.**
**Checkpoint base:** `253179aa2242fabf4bacce8470376f7b3baef8e4`
**Projeto:** `powerbi/ProjetoBI.pbip`

## Objetivo e método

A Fase 4.5A moveu para `_Medidas` as 28 medidas aprovadas na Fase 4.4: 24 que estavam em `FatoPedidos` e quatro que estavam em `FatoItensPedido`. A operação foi organizacional; expressões, nomes, descrições TMDL `///`, formatos e pastas foram copiados sem alteração.

A tabela segue o padrão do Power BI para tabelas de medidas: uma coluna técnica `_Apoio`, oculta e sem agregação, com uma linha calculada em branco (`ROW ( "_Apoio", BLANK () )`). Não contém dados de negócio nem consulta PostgreSQL. `_Medidas` não participa de relacionamento. A documentação da Microsoft descreve a tabela de medidas com coluna auxiliar oculta e tabela visível ([criar e usar medidas](https://learn.microsoft.com/en-us/power-bi/transform-model/desktop-measures)); o particionamento calculado DAX é uma forma suportada em TMDL ([visão geral de TMDL](https://learn.microsoft.com/en-us/analysis-services/tmdl/tmdl-overview?view=sql-analysis-services-2025)).

## Inventário antes e depois

| Local | Antes | Depois |
|---|---:|---:|
| `FatoPedidos` | 24 | 0 |
| `FatoItensPedido` | 4 | 0 |
| `_Medidas` | 0 | 28 |
| Total | 28 | 28 |

O inventário comparou os blocos originais e migrados: os 28 blocos completos são idênticos, incluindo fórmulas, referências, descrições, formatos e `Display Folder`. Há 28 nomes únicos e nenhuma definição duplicada. As referências a medidas continuam não qualificadas (`[Nome da Medida]`), portanto não precisaram mudar; referências a colunas físicas permanecem apontando para as fatos.

## Display Folders

| Pasta | Quantidade | Medidas |
|---|---:|---|
| `01 | Pedidos` | 4 | Total de Pedidos; Pedidos Concluídos; Pedidos Cancelados; Pedidos Confirmados |
| `02 | Faturamento` | 5 | Valor Total dos Pedidos — Todos os Status; Valor Bruto de Produtos — Pedidos Concluídos; Receita Líquida de Produtos — Antes de Devoluções; Frete Cobrado — Pedidos Concluídos; Valor Total — Pedidos Concluídos |
| `03 | Descontos` | 1 | Descontos — Pedidos Concluídos |
| `04 | Ticket Médio` | 1 | Ticket Médio — Pedidos Concluídos |
| `05 | Produtos e Itens` | 3 | Total de Linhas de Itens; Unidades Pedidas; Pedidos Distintos com Itens no Contexto |
| `06 | Inteligência Temporal` | 10 | Pedidos no Ano Anterior; Variação Absoluta de Pedidos YoY; Variação Percentual de Pedidos YoY; Pedidos YTD; Receita de Produtos no Ano Anterior — Antes de Devoluções; Variação Absoluta de Receita YoY — Antes de Devoluções; Variação Percentual de Receita YoY — Antes de Devoluções; Receita YTD — Antes de Devoluções; Receita YTD Ano Anterior — Antes de Devoluções; Variação Percentual de Receita YTD YoY — Antes de Devoluções |
| `07 | Indicadores Percentuais` | 4 | Taxa de Conclusão; Taxa de Cancelamento; Participação de Pedidos por Status; Participação de Unidades no Contexto de Produto |

## Integridade estrutural e metadados

- O serializador TMDL do Power BI leu a definição completa: oito tabelas e nove relacionamentos.
- O mecanismo semântico local carregou oito tabelas e as 28 medidas em `_Medidas`; `FatoPedidos` e `FatoItensPedido` não têm medidas.
- Os 28 nomes são distintos, há sete pastas e nenhuma medida tem `ErrorMessage`.
- Todas as medidas mantêm descrição e formato; o inventário textual confirmou igualdade integral dos blocos antes/depois.
- A coluna `_Apoio` aparece oculta no mecanismo. A tabela calculada tem uma linha sem valor de negócio.
- As nove relações dimensionais permaneceram idênticas; `_Medidas` não tem relacionamento.
- Contagens após carregar: pedidos 120.000; itens 241.637; calendário 1.369; produtos 1.000; clientes 45.000; lojas 10; canais 4.
- Não foram alterados Power Query, fontes, tipos, calendário, Auto date/time nem o PostgreSQL.

## Reconciliação pós-migração

As expressões DAX foram consultadas no mecanismo semântico do Desktop após carregar a nova definição. Os totais não filtrados permaneceram:

| Indicador | DAX após a migração |
|---|---:|
| Pedidos; concluídos; cancelados; confirmados | 120.000; 116.305; 3.265; 430 |
| Linhas de itens | 241.637 |
| Valor de pedidos — todos os status | R$ 980.010.657,75 |
| Bruto de produtos concluídos | R$ 971.645.716,62 |
| Descontos concluídos | R$ 22.325.952,43 |
| Receita líquida de produtos antes de devoluções | R$ 949.319.764,19 |
| Frete de pedidos concluídos | R$ 786.720,00 |
| Total de pedidos concluídos | R$ 950.106.484,19 |
| Ticket de pedidos concluídos | R$ 8.169,0941 (apresentação R$ 8.169,09) |

Identidades financeiras preservadas: bruto menos descontos = receita líquida antes de devoluções; receita líquida mais frete = valor total de pedidos concluídos. Não se interpreta a medida como receita após devoluções.

YTD equivalente, com calendário de janeiro a setembro:

| Período | Receita líquida antes de devoluções |
|---|---:|
| Jan–set/2025 | R$ 209.080.826,98 |
| Jan–set/2026 | R$ 234.603.762,77 |
| Variação percentual | +12,2072100817% |

## Contextos de filtro

- Ano/mês: janela março/2025 retornou 2.892 pedidos e R$ 23.342.562,09 de receita líquida antes de devoluções.
- Canal ecommerce: 35.400 pedidos, 34.178 concluídos e R$ 317.845.308,12 em todos os status.
- Cliente 2793808: 13 pedidos, 11 concluídos; totais R$ 74.106,13 e R$ 67.502,88.
- Loja `ST-PO-001` + canal físico + ano 2025: 2.435 pedidos, 2.362 concluídos e R$ 9.774.308,07 em pedidos concluídos.
- Produto 66295: 294 linhas, 308 unidades e 294 pedidos com itens; medida de cabeçalho em branco.
- Categoria `CAT-PROCESSOR`: 20.272 linhas, 21.720 unidades e 19.087 pedidos com itens; medida de cabeçalho em branco.
- Membros em branco: 19.829 pedidos sem cliente e 57.420 sem loja.

Esses resultados preservam os contratos de grão da Fase 4.4: dimensões de produto/categoria filtram itens, não atribuem cabeçalho, e as dimensões conformadas continuam filtrando ambas as fatos.

## Estado do ciclo Desktop

O usuário confirmou visualmente no Power BI Desktop que `_Medidas` aparece com as sete pastas e que `FatoPedidos` e `FatoItensPedido` não exibem medidas. O projeto foi salvo, fechado e reaberto sem erro. Após a reabertura, a consulta ao mecanismo semântico confirmou 28 medidas exclusivamente em `_Medidas`, zero medidas nas duas fatos, sete pastas, zero erros e descrição e formato em todas as medidas. A reconciliação DAX pós-reabertura confirmou 120.000 pedidos, 116.305 concluídos, R$ 949.319.764,19 de receita de produtos antes de devoluções e R$ 234.603.762,77 de receita YTD 2026.

Não iniciar a Fase 4.5B nesta etapa.
