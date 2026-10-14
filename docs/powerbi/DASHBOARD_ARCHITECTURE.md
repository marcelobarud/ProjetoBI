# Arquitetura inicial dos dashboards — InfoTech

**Escopo:** arquitetura de cinco páginas para Desktop. A quinta página, Devoluções, foi implementada na Fase 5.5; a validação integrada 5.6A.1 segue PARTIAL enquanto operação dos slicers, sincronização direcional e persistência final aguardam confirmação manual; ver os relatórios das fases. O nome vigente da marca é InfoTech, aprovado na Fase 5.4.2.1; “InfoTech Intelligence” é a denominação histórica das fases iniciais. Design System v0.2 preservado, com novos componentes candidatos à v0.3. Relações, medidas e dados permanecem aprovados. A Fase 5.4 validou reconciliações e parte das interações no Desktop; ver seu relatório para alcance e limitações.

## 1. Contratos do modelo usados no desenho

- 10 tabelas: calendário, produto, cliente, loja e canal; fatos de pedidos, itens, custos de fulfillment e devoluções; `_Medidas`. Quatro fatos e cinco dimensões.
- As 55 medidas ficam em `_Medidas`. Os nomes abaixo foram conferidos em `_Medidas.tmdl`; as descrições ali são a referência para grão, elegibilidade, BLANK e fórmula.
- O calendário vai de 2023-01-01 a 2026-09-30. Nunca inferir atualização até a data atual nem completar outubro–dezembro/2026.
- Perspectivas temporais: pedido/coorte (`order_date`); custo operacional (`movement_date`); recebimento operacional de devolução (`return_received_date`). Relações inativas de coorte para custo e devolução são acionadas por medidas específicas. Não combinar as três perspectivas em uma mesma série sem rótulo explícito.
- Receita, COGS, lucro, margem e devolução por coorte seguem as medidas financeiras homologadas da Fase 4.5C. Perda non-sellable permanece incluída no COGS ajustado; não subtrair de novo. Devolução comercial não é refund financeiro.
- `DimProduto` não filtra fatos de pedidos por uma relação fato-a-fato. Medidas de pedido podem retornar BLANK com filtro de produto. Valores de cabeçalho não podem ser alocados a produto/categoria sem contrato aprovado.

## 2. Estrutura comum

1. **Cabeçalho:** monograma I/T, wordmark InfoTech, nome da área e navegador de páginas nativo horizontal.
2. **Contexto/filtros:** período nomeado pela perspectiva, Canal e Loja em posições constantes; Cliente ou Produto apenas quando útil à página. Mostrar como limpar filtro.
3. **Área principal:** 3–5 KPIs prioritários, um visual temporal e no máximo dois detalhamentos por bloco. Preferir hierarquia, não densidade.
4. **Rodapé opcional:** intervalo efetivo do dataset (até 30 set 2026) e perspectiva das datas; não exibir “última atualização” sem campo de atualização do dataset.

Formato de referência 16:9 (1280×720 conceitual), 12 colunas, 24 px de margem e unidade de espaçamento de 8 px. A página Visão Executiva usa Full HD 1920×1080, conforme orientação do usuário, e margens de 36 px. Reorganizar em mobile por prioridade: filtros, KPIs, série temporal, detalhamentos; esconder visuais secundários somente após testar leitura e navegação. Nenhum mobile layout foi feito na Fase 5.1.

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
| 5. Devoluções | Quatro KPIs: valor comercial, reversão sellable, perda non-sellable e percentual comercial; linha mensal, barra por categoria e Top 5 produtos | `Valor Comercial Devolvido — Data do Pedido`; `Reversão COGS Sellable — Data do Pedido`; `Perda Non-Sellable — Data do Pedido`; `Percentual de Devoluções Comerciais` | Canal, Loja e período compartilhados; categorias/produtos como dimensões dos rankings | Coorte de `order_date`; grão de linha de devolução para valores elegíveis | Não há medida de reembolso efetivo nem contagem/unidades por coorte. Perda non-sellable já está incorporada no COGS ajustado; não deduzir novamente. Página em validação parcial |

As células usam somente medidas existentes. A composição implementada e as limitações de validação da quinta página estão detalhadas em `phase-5.5-returns-dashboard.md`; não interpretar valores exibidos na captura como reconciliação DAX.

## 4. Páginas e ordem recomendadas

1. **Visão Executiva** — leitura em menos de um minuto; poucos KPIs, período e canais, tendência de coorte e comparação Top N.
2. **Análise Comercial** — volume/status de pedidos, receita comercial pré-devolução, ticket e canais/lojas/clientes.
3. **Produtos e Categorias** — comportamento no grão de item com Top N e drill-down real de categoria/produto.
4. **Custos e Margens** — perspectiva de coorte do pedido; fluxos operacionais continuam planejados e devem permanecer em zona própria quando implementados.
5. **Devoluções** — valor comercial e consequências de custo atribuídos à coorte do pedido; recebimento operacional e refund permanecem conceitos distintos e não foram adicionados à composição atual.

Page Navigator horizontal no cabeçalho, com cinco destinos reais e estado ativo. Os nomes completos foram vistos no Desktop na Fase 5.5; testes abrangentes de navegação entre todos os pares ainda estão pendentes. Navegação nativa acompanha páginas. Não criar várias páginas manuais de “detalhe” nem botões um a um na versão inicial.

## 5. Política de filtros compartilhados

| Filtro | Plano de sincronização | Restrição |
|---|---|---|
| Canal | Compartilhar nas cinco páginas | Dimensão conformada; verificar interação em cada visual |
| Loja | Compartilhar nas cinco páginas | Dimensão conformada; não confundir loja de pedido com local de estoque |
| Período | Compartilhar entre as cinco páginas como período comercial da data do pedido/coorte | O calendário e `USERELATIONSHIP` suportam as medidas de coorte. Medidas operacionais por recebimento não usam silenciosamente o mesmo slider; rotular a perspectiva de cada bloco |
| Segmentação Produto/Categoria | Local nas páginas 3–5; não sincronizar para 1–2 | A categoria pode aparecer como eixo de um visual específico da página 1, mas não como segmentação compartilhada. Medidas de pedido podem resultar em BLANK sob filtro de produto; item financeiro não representa cabeçalho |
| Cliente | Local por página quando útil | Não expor dados de contato/notas; usar identificador/nome legível apenas quando necessário |
| Status | Local à análise que define seu significado | `order_status` e `return_status` não são intercambiáveis |

Na página 1, categoria → cartão `Pedidos Concluídos` mantém `NoFilter`. Na Fase 5.2, Período, Canal e Loja passaram a usar grupos sincronizados entre páginas 1–2; seleção, alteração e limpeza foram exercitadas nos dois sentidos. Produto/Categoria não sincronizam. A Comercial usa `DataFilter` explícito entre temporais/rankings e demais cartões/gráficos; seleções de gráficos continuam locais à página. O cabeçalho mostra apenas o nome da página; período aparece no slicer. Não criar calendários desconectados para simular seleções independentes sem autorização do modelo.

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
| 5.1 / 5.1.2 | Visão Executiva homologada no escopo local; sete cenários aprovados manualmente, baseline DAX anterior preservado, eixos 16 pt, títulos 17 pt e legenda 15 pt; componentes e limitações em Design System v0.2 |
| 5.2 | PASS local: quatro KPIs, status, dois temporais com escalas separadas, Canal/Top 5 lojas, navegador e filtros sincronizados. YTD visual deferido como refinamento específico, DAX validado. Sem tabela de clientes no layout atual; nenhuma nova métrica |
| 5.3 | PASS local: quatro KPIs financeiros por coorte, Top 5 produtos, todas as categorias, matriz Categoria → Produto, filtros locais pesquisáveis, contexto geral sincronizado e navegador com três destinos. Sem atribuições de cabeçalho; medidas/modelo preservados. Ver `phase-5.3-products-categories-dashboard.md` |
| 5.4 | PARTIAL local: página Custos e Margens, composição financeira, tendência por coorte e comparação por canal/categoria implementadas; DAX reconciliado e Desktop reaberto. Navegação/sincronização observadas em amostra; fluxos operacionais e validação exaustiva de todas as interações ficam documentados como limites. Ver `phase-5.4-costs-margins-dashboard.md` |
| 5.5 | PARTIAL local: página Devoluções implementada com perspectiva comercial por coorte. Auditoria 5.6A reconciliou valores globais e Jan–Set/2026, invariantes financeiros, 12 categorias e Top 5 sob contexto. Em 5.6A.1, abertura, bookmarks, seleção/limpeza do quinto item Top 5 e uma amostra aquecida do Performance Analyzer foram observados; digitação/slider, filtros Canal/Loja, sincronização direcional, isolamento cross-page, Page Navigator, acessibilidade básica e persistência final seguem pendentes. Design System v0.2 mantido. Ver `phase-5.6a.1-functional-closure.md`. |
| 5.6 | Auditoria integrada visual, funcional, acessível, temporal e de desempenho |

Este roteiro não autoriza a execução das fases seguintes.

## 8. Composição implementada de Produtos e Categorias

Full HD 1920 × 1080, 14 visuais. Receita após devoluções, COGS ajustado, lucro e margem usam medidas financeiras homologadas por coorte do pedido. Métricas de linhas/unidades ficam na matriz e tooltips, com pedidos distintos de itens e participação nos tooltips pertinentes. Nenhum cartão de valor de cabeçalho por produto.

Período, Canal e Loja conservam os três grupos e passam a incluir exatamente um slicer por página 1–3. Categoria/Produto são locais à página 3; pesquisa nativa evita lista permanente do catálogo. As 18 interações explícitas dos rankings/matriz usam DataFilter. Grupos compartilhados não transportam seleções de gráficos nem filtros locais.

Top 5 por receita no eixo SKU, com nome completo no tooltip, após teste do Top 10 com rolagem. Ranking de categorias inclui as 12, com rolagem vertical. Matriz inicialmente recolhida com sete medidas e percentuais recalculados, sem soma de margens. Ranking/matriz não eliminam negativos por filtro de apresentação. Escala monetária automática nos dois novos gráficos atende contextos globais e pequenos; cartões/tooltips conservam valores completos.

Navegador 896 × 56 px e cabeçalho 920 × 76 px nas três páginas, sem mudar definições analíticas das anteriores. O modelo segue com 10 tabelas, 55 medidas, 11 pastas e 21 relações. PostgreSQL não foi acessado nesta fase. Candidatos à v0.3 e limites de densidade/viewport registrados no Design System v0.2.

## Painel de filtros recolhível — implementação local

A Fase 5.4.1 implementou DS-C02 recolhível com bookmarks nativos de exibição em quatro páginas. Os três grupos `InfoTech.*` permanecem compartilhados; Categoria e Produto continuam locais a Produtos e Categorias. O painel aberto é uma sobreposição temporária; fechado, libera espaço real para cartões e gráficos. Consulte `phase-5.4.1-collapsible-filter-panel.md` para geometrias, limitações, evidências e estado de validação. A descrição comum de DS-C02 nesta arquitetura não altera por si só a versão v0.2 nem promove a candidata v0.3.

## 9. Devoluções — implementação Fase 5.5

A quinta página acrescenta quatro cartões sem criar medidas: valor comercial devolvido, reversão COGS sellable, perda non-sellable e percentual comercial, todos por coorte da data do pedido. A visualização temporal apresenta valor comercial por mês do pedido; as barras mostram valor por categoria e Top 5 produtos. Medidas de itens/unidades disponíveis usam data de recebimento e, portanto, não foram usadas sob o período comercial compartilhado. O modelo também não fornece medida de reembolso efetivo. Ver [relatório Fase 5.5](phase-5.5-returns-dashboard.md) para a rastreabilidade e limitações.

O modelo oferece campos de recebimento, mas esta fase não implementa a zona operacional: o filtro compartilhado representa coorte comercial e as validações necessárias de consistência de medidas/filtros não foram concluídas. Perda non-sellable permanece incorporada ao COGS ajustado; não subtrair novamente. A página renderizou no Desktop e o painel aberto/fechado foi observado, mas DAX, sincronização em cinco páginas, cenários de filtro, persistência após salvar/reabrir, acessibilidade e desempenho ainda estão pendentes. A classificação permanece PARTIAL.
