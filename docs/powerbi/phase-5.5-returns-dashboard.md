# Fase 5.5 — Dashboard de Devoluções InfoTech

**Status:** `PARTIAL — FUNCTIONAL OR VISUAL VALIDATION PENDING`
**Data da inspeção no Desktop:** 2026-10-14
**Projeto:** `powerbi/ProjetoBI.pbip`
**Design System:** InfoTech v0.2 permanece vigente; componentes desta página são candidatos à v0.3.

## Resultado

A quinta página PBIR, **Devoluções**, foi criada em Full HD 1920 × 1080 e inserida após Custos e Margens. Ela reutiliza o cabeçalho InfoTech com monograma, navegador nativo, botão Filtros, filtros sincronizados e bookmarks de abrir/fechar. A abertura do PBIP no Power BI Desktop exibiu a página sem erro. A inspeção visual nesta sessão confirmou quatro cartões, a evolução mensal, o ranking completo por categoria e o Top 5 por produto. O gráfico mensal apresenta valores em R$ mil.

Capturas reais da janela do Power BI Desktop:

- [Página Devoluções com filtros fechados](evidence/phase-5.5/01-devolucoes-filtros-fechados.png)
- [Página Devoluções com painel aberto](evidence/phase-5.5/02-devolucoes-painel-aberto.png)
- [Resumo verificável da validação](evidence/phase-5.5/validation-summary.json)
- [Pacote ZIP das evidências](evidence/archives/fase-5.5-evidencias.zip)

As imagens registram o viewport disponível durante a inspeção (1152 × 544 px da janela, zoom do Desktop variando entre 27% e 36% por causa dos painéis laterais); não equivalem à inspeção em Fit to Page, Fit to Width ou escala real do canvas. Os filtros exibiam o intervalo salvo no relatório, sem impor Jan–Set/2026. Não foi executada atualização de dados.

## Composição implementada

| Componente | Conteúdo |
|---|---|
| KPIs | Valor comercial devolvido por data do pedido; reversão de custo sellable por data do pedido; perda non-sellable por data do pedido; percentual de devoluções comerciais |
| Evolução | Valor comercial devolvido por mês do pedido, em R$ mil |
| Categoria | Valor comercial devolvido por coorte do pedido, por categoria |
| Produto | Top 5 produtos por valor comercial devolvido, com SKU no eixo |
| Filtros | Período Between (campos e slider), Canal e Loja compartilhados; painel recolhível |
| Nota semântica | Perda non-sellable já permanece incorporada ao COGS analítico ajustado; não deve ser deduzida novamente. A série representa a coorte da data do pedido, não recebimentos no mês. Reembolso efetivo não está disponível no modelo semântico. |

O navegador de página inclui cinco destinos com nomes completos. A inspeção ao abrir e fechar o painel mostrou os controles de período, canal e loja; nesta sessão o bookmark “Filtros — fechar” ocultou o painel. O usuário também confirmou que o clique no botão “Fechar filtros” funciona. Isso não substitui os testes direcionais completos de sincronização ou interação entre todas as páginas.

## Rastreabilidade semântica

As medidas foram conferidas no TMDL de `_Medidas`; não foram criadas medidas, colunas ou relações novas nesta fase.

| Indicador | Medida do modelo | Grão e data | Uso nesta página |
|---|---|---|---|
| Itens de devolução | `Itens de Devolução` | Linhas de `FatoDevolucoes`; relação ativa com data de recebimento | Não usado como KPI da coorte: a contagem não possui variante aprovada por data do pedido |
| Unidades recebidas | `Unidades Recebidas em Devolução` | Soma de `quantity_received`; data de recebimento | Não usada com o filtro comercial compartilhado |
| Dedução comercial | `Valor Comercial Devolvido — Data do Pedido` | Valor em grão de item devolvido, atribuído ao pedido original | KPI, evolução e rankings |
| Reembolso efetivo | Não há medida correspondente no modelo | Fato de pagamentos/refunds não está carregada na camada semântica aprovada | Não implementado; não é tratado como equivalente à dedução comercial |
| Reversão sellable | `Reversão COGS Sellable — Data do Pedido` | Custos dos itens elegíveis, por coorte do pedido | KPI; tooltip/contexto deve preservar o conceito de custo |
| Perda non-sellable | `Perda Non-Sellable — Data do Pedido` | Itens recebidos em condição non-sellable, atribuídos à coorte do pedido | KPI informativo; já incluída no COGS ajustado |
| Taxa comercial | `Percentual de Devoluções Comerciais` | Dedução comercial por coorte sobre receita de produtos antes das devoluções | KPI; percentual não é aditivo |

`FatoDevolucoes` tem grão de item de devolução, com chaves de pedido/item/produto e campos de datas de pedido e recebimento. A data comercial é a política principal porque é o contexto compartilhado nas páginas existentes. Medidas baseadas em recebimento não foram ligadas ao mesmo slider, evitando misturar evento operacional e coorte. A possibilidade operacional permanece futura; os campos de recebimento existentes, por si só, não justificam outro contexto visual com as medidas atuais.

### Limites de métricas

- O modelo não oferece reembolso efetivo para esta página.
- O modelo não oferece quantidade de itens ou unidades devolvidas atribuída à data do pedido. As medidas disponíveis para quantidade usam a data de recebimento; por isso não foram colocadas como KPIs sob o filtro de coorte comercial.
- A ausência dessas medidas não impede os quatro KPIs comerciais/financeiros implementados, mas deixa sem resposta duas perguntas do escopo original. Uma extensão de modelo ou medidas requer fase autorizada própria.
- Nenhum “impacto financeiro total” foi calculado pela soma de dedução, reembolso, reversão de custo e perda.

## Estado de validação

| Verificação | Resultado | Evidência/limite |
|---|---|---|
| PBIP abriu na sessão atual | Validado visualmente, sem mensagem de erro | Inspeção do Desktop em 2026-10-14 |
| Cinco páginas e destino Devoluções | Validado visualmente | Cinco destinos visíveis no Desktop |
| Quatro KPIs, gráfico mensal e rankings | Validado visualmente | Capturas; números não reconciliados por DAX nesta execução |
| Eixo mensal em R$ mil | Validado visualmente | Sem os rótulos arredondados em R$ milhões vistos antes da correção |
| Painel aberto e fechado | Validado parcialmente | Estado aberto capturado; bookmark de fechar funcionou; usuário confirmou botão Fechar filtros. Layout em Fit to Page e escala real pendentes |
| Datas editáveis, slider e duas alças | Parcial | Campos e slider de duas alças visíveis; edição digitada e movimento funcional não exercitados nesta execução |
| Filtros sincronizados nas cinco páginas | Pendente | Não foram executados testes de propagação nas duas direções |
| Interações categoria/produto e casos extremos | Pendente | Não testados nesta execução |
| Reconciliações DAX global, Jan–Set/2026, por categoria/produto e combinações | Pendente | Nenhuma consulta de reconciliação DAX foi executada nesta execução; valores dos screenshots são evidência de renderização, não de reconciliação |
| Indicadores financeiros globais de referência | Pendente nesta fase | Nenhuma consulta DAX independente foi executada |
| Desempenho / Performance Analyzer | Pendente | Não medido |
| Acessibilidade, teclado, foco e tab order | Pendente | Não certificados nem exercitados nesta fase |
| Salvar, fechar e reabrir após a implementação | Pendente | O Desktop foi fechado sem salvar o estado temporário de inspeção; não foi reaberto depois. A abertura atual foi validada antes do fechamento |
| Dados, modelo, DAX, relacionamentos e PostgreSQL | Preservados nesta fase | Nenhuma atualização de dados nem mudança semântica intencional foi feita. Inventário estático: 10 tabelas, 55 medidas e 21 relações; nenhum TMDL está staged para esta fase. Alterações locais preexistentes foram mantidas fora do commit |

## Documentação e governança

### Acompanhamento posterior — auditoria integrada 5.6A (2026-10-14)

A Fase 5.5 permanece historicamente **PARTIAL** como entregue. Na auditoria 5.6A, os valores globais e Jan–Set/2026 das medidas de devolução/custos foram consultados diretamente em DAX; as 12 categorias reconciliaram com o total global; o Top 5 sob o contexto salvo e os quatro cartões foram conferidos. A classificação desta validação integrada permanece **PARTIAL** porque slider/digitação, sincronização direcional entre páginas, interações locais, persistência, desempenho e acessibilidade ainda não foram exercitados. Portanto, a homologação funcional da página não está concluída. Ver `phase-5.6a-integrated-functional-audit.md` e `evidence/phase-5.6a/`.

O Design System v0.2 continua vigente. A navegação com cinco destinos, o painel recolhível na quinta página, os cartões de devolução, o ranking por valor, a evolução por coorte e os rótulos de sellable/non-sellable foram registrados como candidatos à v0.3. A Fase 5.6 continua separada e não foi iniciada.

Commit local criado com a mensagem `feat(powerbi): implementa dashboard de devolucoes`. As alterações anteriores fora do escopo permaneceram na working tree; nenhum push, merge, rebase ou tag foi executado.

### Complemento de validação — Fase 5.6A.1 (2026-10-14)

A implementação continua historicamente parcial quanto à validação funcional completa. Na retomada, o Desktop abriu sem erro; bookmarks abriram/fecharam o painel; a seleção do quinto produto atualizou os cartões e a série, e o clique repetido limpou a seleção; os cinco SKUs do Top 5 foram vistos e os dois últimos conferem com a evidência DAX herdada. O Performance Analyzer exportou uma amostra aquecida. O ciclo salvar/fechar/reabrir restaurou Custos e Margens sem erro; Devoluções também renderizou ao ser acessada, mas após reabertura o painel apareceu aberto e seus quatro KPIs/destinos não foram verificados no ciclo. Digitação/slider, filtros de Canal/Loja, sincronização direcional, isolamento cross-page, Page Navigator e teclado continuam pendentes. Ver [`phase-5.6a.1-functional-closure.md`](phase-5.6a.1-functional-closure.md) e `evidence/phase-5.6a/functional-closure/`. A classificação desta retomada é PARTIAL; não foi declarada homologação funcional completa.
