# Arquitetura inicial dos dashboards — InfoTech Intelligence

**Escopo:** plano de cinco páginas para Desktop. Nenhuma página, visual, medida ou interação foi implementada nesta fase. Relações, medidas e dados permanecem os aprovados no modelo semântico.

## 1. Contratos do modelo usados no desenho

- 10 tabelas: calendário, produto, cliente, loja e canal; fatos de pedidos, itens, custos de fulfillment e devoluções; `_Medidas`. Quatro fatos e cinco dimensões.
- As 55 medidas ficam em `_Medidas`. Os nomes abaixo foram conferidos em `_Medidas.tmdl`; as descrições ali são a referência para grão, elegibilidade, BLANK e fórmula.
- O calendário vai de 2023-01-01 a 2026-09-30. Nunca inferir atualização até a data atual nem completar outubro–dezembro/2026.
- Perspectivas temporais: pedido/coorte (`order_date`); custo operacional (`movement_date`); recebimento operacional de devolução (`return_received_date`). Relações inativas de coorte para custo e devolução são acionadas por medidas específicas. Não combinar as três perspectivas em uma mesma série sem rótulo explícito.
- Receita, COGS, lucro, margem e devolução por coorte seguem as medidas financeiras homologadas da Fase 4.5C. Perda non-sellable permanece incluída no COGS ajustado; não subtrair de novo. Devolução comercial não é refund financeiro.
- `DimProduto` não filtra fatos de pedidos por uma relação fato-a-fato. Medidas de pedido podem retornar BLANK com filtro de produto. Valores de cabeçalho não podem ser alocados a produto/categoria sem contrato aprovado.

## 2. Estrutura comum

1. **Cabeçalho:** wordmark InfoTech Intelligence, nome da área e navegador de páginas nativo horizontal.
2. **Contexto/filtros:** período nomeado pela perspectiva, Canal e Loja em posições constantes; Cliente ou Produto apenas quando útil à página. Mostrar como limpar filtro.
3. **Área principal:** 3–5 KPIs prioritários, um visual temporal e no máximo dois detalhamentos por bloco. Preferir hierarquia, não densidade.
4. **Rodapé opcional:** intervalo efetivo do dataset (até 30 set 2026) e perspectiva das datas; não exibir “última atualização” sem campo de atualização do dataset.

Formato de referência 16:9 (1280×720 conceitual), 12 colunas, 24 px de margem e unidade de espaçamento de 8 px, sujeito a confirmação de página no Desktop. Reorganizar em mobile por prioridade: filtros, KPIs, série temporal, detalhamentos; esconder visuais secundários somente após testar leitura e navegação. Nenhum mobile layout será feito na Fase 5.0.

## 3. Matriz funcional

| Página | Objetivo e visual | Medida(s) existente(s) | Dimensões/filtros | Data e grão | Interação e risco analítico |
|---|---|---|---|---|---|
| 1. Visão Executiva | KPIs: receita analítica, lucro, margem, pedidos concluídos, variação YTD e COGS | `Receita Analítica Após Devoluções`; `Lucro Bruto Analítico`; `Margem Bruta Analítica`; `Pedidos Concluídos`; `Variação Percentual de Receita Analítica YTD`; `COGS Analítico Ajustado` | Calendário, Canal e Loja; sem filtro global de Produto | Coorte do pedido para financeiro; pedido concluído no fato de pedidos. YTD compara janelas equivalentes | Seleção de período/canal/loja; Produto não sincroniza: pode tornar pedidos BLANK e muda para análise atribuída aos itens |
| 1. Visão Executiva | Linha mensal de receita e lucro; manter margem em visual separado | `Receita Analítica Após Devoluções`; `Lucro Bruto Analítico`; `Margem Bruta Analítica` | `DimCalendario[AnoMes]`, ordenado por `AnoMesOrdem`; Canal opcional | Coorte comercial; fatos de itens/custo/devolução por order_date | Drill de Ano > Trimestre > mês. Não usar eixo duplo ou misturar BRL e % na mesma escala |
| 1. Visão Executiva | Barras por Canal e composição Top N de categoria | `Receita Analítica Após Devoluções`; `Lucro Bruto Analítico` | `DimCanal[name]`; `DimProduto[category_name]` | Coorte do pedido e receita/custo atribuídos ao grão de item/produto | Seleção de Canal pode cruzar os visuais. Categoria fica Top N; não atribuir valor de cabeçalho à categoria |
| 2. Análise Comercial | KPIs e tendência de volume, conclusão, cancelamento e ticket | `Total de Pedidos`; `Pedidos Concluídos`; `Pedidos Cancelados`; `Taxa de Conclusão`; `Taxa de Cancelamento`; `Ticket Médio — Pedidos Concluídos` | Calendário, Canal, Loja; Cliente conforme pergunta | `FatoPedidos`, coorte por order_date; status atual/final | Filtros e cross-highlight usuais. Status não reconstrói histórico; Ticket Médio e totais devem respeitar contrato do modelo |
| 2. Análise Comercial | Barras comparando Canal/Loja e tabela curta de clientes | `Valor Total — Pedidos Concluídos`; `Receita Líquida de Produtos — Antes de Devoluções` | Canal/Loja/Cliente | Cabeçalho/coorte do pedido; valor monetário de pedido, não margem do item | `DimProduto` fica fora da sincronização desta página. Não usar métrica de pedido num ranking de produtos |
| 2. Análise Comercial | Comparação temporal YoY/YTD de receita comercial | `Receita YTD — Antes de Devoluções`; `Receita YTD Ano Anterior — Antes de Devoluções`; `Variação Percentual de Receita YTD YoY — Antes de Devoluções` | `DimCalendario[Ano]`, `MesNumero`, `AnoMes` | Coorte comercial; 2026 jan–set contra jan–set/2025 | Exigir filtro de calendário para comparáveis. Não comparar 12 meses de 2025 com 9 de 2026 |
| 3. Produtos e Categorias | KPIs de itens/unidades e participação no contexto | `Total de Linhas de Itens`; `Unidades Pedidas`; `Pedidos Distintos com Itens no Contexto`; `Participação de Unidades no Contexto de Produto` | `DimProduto[category_name]`, `name`, `sku`; período/canal/loja | Grão de linha de item; unidades pedidas não equivalem a unidades atendidas ou líquidas de devoluções | Filtro de produto é local a esta página; ranking Top N; participação não somar entre categorias |
| 3. Produtos e Categorias | Barras Top N de receita/lucro por produto; matriz categoria > produto | `Receita de Produtos — Antes de Devoluções (Itens)`; `Receita Analítica Após Devoluções`; `COGS Analítico Ajustado`; `Lucro Bruto Analítico`; `Margem Bruta Analítica` | Produto/categoria e dimensões conformadas | Coorte comercial; receita líquida de produto atribuída aos itens concluídos, COGS de itens | Drill categoria > produto; destacar BLANK quando receita/custo não existe. Não alocar frete ou total de cabeçalho |
| 4. Custos e Margens | Bloco de coorte: receita, COGS ajustado, lucro e margem | `Receita Analítica Após Devoluções`; `COGS Original Concluído — Data do Pedido`; `COGS Analítico Ajustado`; `Lucro Bruto Analítico`; `Margem Bruta Analítica` | Produto/categoria, Canal, Loja | Coorte por order_date, inclusive `USERELATIONSHIP` dos fatos de custo e devolução | Nomear “coorte do pedido” em cada visual. Perda non-sellable já permanece no COGS; não deduzir uma segunda vez |
| 4. Custos e Margens | Bloco de fluxo operacional: custo por movimento e devolução por recebimento | `COGS de Fulfillment — Data do Movimento`; `COGS Original Concluído — Data do Movimento`; `Reversão COGS Sellable — Data do Recebimento`; `Perda Non-Sellable — Data do Recebimento` | Calendário por movimento ou recebimento; Produto, Canal e Loja | Fluxo operacional; `movement_date` versus `return_received_date` | Visuais separados e claramente rotulados; a mesma seleção de calendário opera por relações diferentes. Não chamar esse bloco de margem por coorte |
| 4. Custos e Margens | Participação de custos e tendência de margem | `Participação do COGS Ajustado na Receita`; `Participação da Reversão Sellable no COGS`; `Participação Non-Sellable no COGS Ajustado`; `Margem Bruta Analítica YTD` | Categoria/Canal; calendário conforme painel | Percentuais financeiros por coorte, exceto quando título explicitar fluxo operacional | Não somar percentuais nem deduzir perda non-sellable novamente; não comparar perspectivas temporais numa mesma série |
| 5. Devoluções | KPIs de linhas, unidades recebidas e valor comercial recebido | `Itens de Devolução`; `Unidades Recebidas em Devolução`; `Valor Comercial Devolvido — Data do Recebimento` | Canal, Loja, Cliente, Produto; `FatoDevolucoes[return_status]` | Evento de recebimento; contagem de linhas de devolução vs quantidades efetivamente recebidas | `Itens de Devolução` pode incluir itens ainda sem recebimento; não rotular como “devoluções recebidas” sem validar filtro/status |
| 5. Devoluções | Barras por destino/condição e tendência mensal de recebimentos | `Unidades Recebidas em Devolução`; `Reversão COGS Sellable — Data do Recebimento`; `Perda Non-Sellable — Data do Recebimento` | `stock_destination`, `item_condition`, `return_reason_code`, categoria e Produto | `return_received_date`; linha de item devolvido/evento operacional | Destino e condição são categorias distintas. Não inferir aprovação/recebimento a partir de solicitação; não confundir devolução comercial com refund |
| 5. Devoluções | Detalhe tabular Top N de produtos afetados | `Valor Comercial Devolvido — Data do Recebimento`; `Unidades Recebidas em Devolução` | Produto/categoria, Canal, motivo, destino | Evento pela data de recebimento; linhas de `FatoDevolucoes` | Drill-through futuro pode preservar filtros de Produto/Canal. Nova contagem exclusiva de solicitações efetivamente recebidas é dependência futura, não será inventada nesta fase |

As células usam somente medidas que existem atualmente. Os valores de linha/coluna e campos de dimensão devem ser conferidos no painel de Dados durante a Fase de implementação; qualquer campo que não esteja disponível será tratado como dependência e não substituído por uma medida inventada.

## 4. Páginas e ordem recomendadas

1. **Visão Executiva** — leitura em menos de um minuto; poucos KPIs, período e canais, tendência de coorte e comparação Top N.
2. **Análise Comercial** — volume/status de pedidos, receita comercial pré-devolução, ticket e canais/lojas/clientes.
3. **Produtos e Categorias** — comportamento no grão de item com Top N e drill-down real de categoria/produto.
4. **Custos e Margens** — zonas separadas para coorte do pedido e fluxos operacionais.
5. **Devoluções** — recebimentos e destinação; solicitação, aprovação, recebimento e refund são conceitos distintos.

Page Navigator horizontal no cabeçalho, 5 títulos curtos e estado ativo aparente. Navegação nativa acompanha páginas. Não criar várias páginas manuais de “detalhe” nem botões um a um na versão inicial.

## 5. Política de filtros compartilhados

| Filtro | Plano de sincronização | Restrição |
|---|---|---|
| Canal | Compartilhar nas cinco páginas | Dimensão conformada; verificar interação em cada visual |
| Loja | Compartilhar nas cinco páginas | Dimensão conformada; não confundir loja de pedido com local de estoque |
| Período | Compartilhar entre páginas 1–3 como período de pedido/coorte; page 4 separa visualmente as perspectivas; page 5 usa recebimento | O mesmo calendário filtra datas ativas diferentes e `USERELATIONSHIP` em medidas de coorte. Rotular cada bloco e não comparar como se fossem datas iguais |
| Segmentação Produto/Categoria | Local nas páginas 3–5; não sincronizar para 1–2 | A categoria pode aparecer como eixo de um visual específico da página 1, mas não como segmentação compartilhada. Medidas de pedido podem resultar em BLANK sob filtro de produto; item financeiro não representa cabeçalho |
| Cliente | Local por página quando útil | Não expor dados de contato/notas; usar identificador/nome legível apenas quando necessário |
| Status | Local à análise que define seu significado | `order_status` e `return_status` não são intercambiáveis |

Fase 5.1 deverá testar interações e estado de limpeza dos filtros em dados reais. Seleção de categoria na página 1 não pode alterar silenciosamente `Pedidos Concluídos`; por isso não se sincroniza Produto com essa página. Não criar tabelas desconectadas de data para simular seleções independentes sem autorização de alteração do modelo.

## 6. Riscos e dependências

- A medida `Pedidos Distintos com Itens no Contexto` é um total de pedidos representados por linhas de item, não o total de cabeçalho; restringi-la à página de produto.
- Receita por item usa o contrato de receita atribuído às linhas; frete/total de cabeçalho não se distribuem por produto.
- Margem analítica por coorte e custos por movimento/devolução recebida respondem a perspectivas de calendário diferentes. Separar zonas, títulos, filtros e tooltips.
- `Itens de Devolução` conta linhas da fato e não deve ser interpretado automaticamente como linhas recebidas. Validar distribuição de `quantity_received` e `return_status`; uma medida separada pode ser proposta numa fase futura se o caso exigir.
- Cobertura termina em setembro de 2026. YTD somente com janela equivalente e filtro de calendário; não utilizar `TODAY()`.
- `FatoDevolucoes` distingue devolução comercial, destinação e custos; nada nesta página estima refund financeiro.
- Margem e receita financeira são de coorte; fluxo por movimento é operacional. Não deduzir perdas non-sellable novamente do COGS analítico.

## 7. Planejamento de implementação

| Fase futura | Resultado esperado |
|---|---|
| 5.1 | Implementar Visão Executiva; aplicar o tema, identidade, Page Navigator, KPIs, filtros, visuais e interações; homologar renderização, legibilidade e desempenho no Desktop |
| 5.2 | Implementar Análise Comercial usando componentes aprovados |
| 5.3 | Implementar Produtos e Categorias sem atribuições de cabeçalho |
| 5.4 | Implementar Custos e Margens com coorte e fluxo operacional separados |
| 5.5 | Implementar Devoluções com solicitação e recebimento diferenciados |
| 5.6 | Auditoria integrada visual, funcional, acessível, temporal e de desempenho |

Este roteiro não autoriza a execução das fases seguintes.
