# Fase 5.6A — Auditoria integrada de integridade analítica e funcional

**Data:** 2026-10-14

**Classificação:** **FASE 5.6A PARTIAL — ANALYTICAL OR FUNCTIONAL VALIDATION PENDING**

**Projeto:** `powerbi/ProjetoBI.pbip`
**Base:** `fc26429` (`feat(powerbi): implementa dashboard de devolucoes`), `main`; a worktree já tinha alterações locais extensas antes da auditoria.

## 1. Objetivo e escopo

Auditar as cinco páginas existentes, reconciliar as medidas financeiras/devoluções usando consultas DAX somente leitura no modelo Import e inspecionar filtros, navegação e serialização PBIR. Não foram alterados DAX, TMDL semântico, relacionamentos, Power Query, fontes, credenciais, PostgreSQL ou dados. Não foi feita atualização de dados.

## 2. Estado inicial

O snapshot externo, com estado/diffs e hashes das mudanças preexistentes, está em `C:\Users\D2\AppData\Local\Temp\ProjetoBI-Phase-5.6A-20261014-132430.zip` (SHA-256 `ED7248E5C52AA97284B09C8AE2032CB6B96293AA5720081E35439ED83257DF8B`). As mudanças locais em PBIR, `pt-BR.tmdl`, exportações e arquivos históricos foram mantidas fora deste commit.

## 3. Integridade do modelo

| Item | Resultado | Evidência |
|---|---|---|
| Cinco páginas / 10 tabelas | PASS | Inventário em `evidence/phase-5.6a/inventory.json`. |
| 55 medidas / 11 Display Folders | PASS | Contagem estática dos TMDLs. |
| 21 relacionamentos (19 ativos, 2 inativos) | PASS | Inventário estático de `relationships.tmdl`. |
| Calendário 2023-01-01 a 2026-09-30 | PASS | Definição existente de calendário. |
| 117 arquivos JSON PBIR válidos | PASS | Parser JSON sem arquivos inválidos. |
| Sincronização: Período, Canal e Loja | PASS estrutural | Há 5 instâncias por grupo (uma por página); operação cruzada integral não foi testada. |
| DAX/TMDL/relacionamentos/Power Query/PostgreSQL/dados modificados | PASS | Nenhuma alteração intencional; refresh não executado. |

## 4. Reconciliação das devoluções

As consultas foram executadas no DAX Query View do modelo já carregado. As expressões usadas estão em `evidence/phase-5.6a/dax/`; resultados em `results/dax-reconciliation.csv`, `results/category-returns.csv`, `results/monthly-jan-sep-2026.csv` e `results/context-top5.tsv`.

As medidas de cada contexto foram projetadas juntas em uma consulta `ROW`/`SUMMARIZECOLUMNS`, em vez de repetir uma chamada separada para cada indicador. A extração é independente dos cartões/gráficos, mas não registra execuções separadas por medida como solicitado no protocolo; essa limitação permanece explícita.

### 4.1 Totais globais

| Medida | Resultado direto | Referência | Veredito |
|---|---:|---:|---|
| Valor Comercial Devolvido — Data do Pedido | R$ 26.730.788,745 | R$ 26.730.788,745 | PASS |
| Reversão COGS Sellable — Data do Pedido | R$ 8.010.914,36386281 | R$ 8.010.914,363863 | PASS (precisão subcentavo) |
| Perda Non-Sellable — Data do Pedido | R$ 12.296.704,23413595 | R$ 12.296.704,234136 | PASS (precisão subcentavo) |
| Receita de Produtos — Antes de Devoluções (Itens) | R$ 949.319.764,19 | R$ 949.319.764,19 | PASS |
| Percentual de Devoluções Comerciais | 2,8157834434% | medida real do modelo | PASS |

O percentual é razão de devolução comercial sobre receita de produtos antes das devoluções; não é aditivo. Dedução comercial não representa refund financeiro. Reversão sellable reduz o COGS e a perda non-sellable já permanece incluída no COGS ajustado.

### 4.2 Jan–Set/2026

| Indicador | Resultado DAX | Referência | Veredito |
|---|---:|---:|---|
| Receita analítica após devoluções | R$ 228.660.758,74 | R$ 228.660.758,74 | PASS |
| COGS analítico ajustado | R$ 176.070.150,08984238 | R$ 176.070.150,09 | PASS (arredondamento apenas na exibição) |
| Lucro bruto analítico | R$ 52.590.608,65015763 | R$ 52.590.608,65 | PASS |
| Margem bruta analítica | 22,9994026697% | 23,00% | PASS |
| Devolução comercial por data do pedido | R$ 5.943.004,03 | DAX independente | PASS |
| Reversão sellable / perda non-sellable | R$ 1.778.950,41088067 / R$ 2.752.994,19933278 | DAX independente | PASS |

O gráfico mensal Jan–Set soma R$ 5.943.004,03 para a medida comercial. Setembro retorna BLANK para as três medidas de devolução/custo nessa granularidade, preservado como BLANK; não foi convertido em zero. A receita anterior a devoluções do intervalo é R$ 234.603.762,77.

### 4.3 Categorias e produtos

As 12 categorias retornaram valores ordenados em ordem decrescente. Não apareceu categoria BLANK. A soma é R$ 26.730.788,745, igual ao total global. Valores completos e rótulos constam no CSV da evidência.

O Top 5 global foi consultado independentemente e, sob o estado salvo do relatório — 30/04/2025 a 30/09/2026, `Loja Física`, `Unidade Sintética Campinas` — o Top 5 foi:

| SKU | Produto | Devolução comercial |
|---|---|---:|
| SKU-NOT-00913 | Notebook Vértice 913 | R$ 16.119,41 |
| SKU-DES-00122 | Desktop Orbe 122 | R$ 15.565,63 |
| SKU-DES-00806 | Desktop Fluxo 806 | R$ 14.658,43 |
| SKU-NOT-00661 | Notebook Fluxo 661 | R$ 14.165,09 |
| SKU-NOT-00757 | Notebook Orbe 757 | R$ 13.863,32 |

Os três primeiros conferem com as barras legíveis no visual sob o mesmo contexto. Os outros dois itens do visual estavam abaixo do recorte visível e não foram confirmados por leitura no canvas. Produtos sem devolução, seleção de produto, BLANK e negativos não foram exercitados no Desktop.

### 4.4 Contexto salvo e KPIs visíveis

| Medida | DAX | Cartão do visual | Veredito |
|---|---:|---:|---|
| Devolução comercial | R$ 420.582,305 | R$ 420.582,31 | PASS |
| Reversão sellable | R$ 88.812,47859743 | R$ 88.812,48 | PASS |
| Perda non-sellable | R$ 235.478,1538917 | R$ 235.478,15 | PASS |
| Percentual comercial | 2,13745966496% | 2,14% | PASS |

## 5. Reconciliação financeira integrada

Os valores globais e Jan–Set/2026 das medidas financeiras foram lidos independentemente no modelo. Os três invariantes consultados resultaram em diferença interna zero:

- COGS original concluído − reversão sellable − COGS ajustado = 0.
- Receita após devoluções − COGS ajustado − lucro bruto = 0.
- Margem bruta − lucro bruto / receita após devoluções = 0.

Perda non-sellable não foi subtraída uma segunda vez. Nenhuma atribuição de valores do cabeçalho a produtos foi criada.

## 6–9. Filtros, sincronização, filtros locais, interações e navegação

| Verificação | Resultado | Evidência/limite |
|---|---|---|
| Presença dos três grupos em cinco páginas | PASS estrutural | 15 instâncias no PBIR; nomes mantidos. |
| Estado combinado salvo de data, canal e loja | PASS | Contexto DAX reproduziu os quatro cartões da página Devoluções. |
| Abrir painel na página Devoluções | PASS | Painel aberto no Desktop e os três slicers estavam visíveis. |
| Fechar painel, reabrir preservando seleção | NOT TESTED nesta sessão | Usuário já homologou o botão em fase anterior; essa regressão específica não foi repetida. |
| Digitar datas e mover cada alça do slider | NOT TESTED | Requer operação funcional explícita no Desktop. |
| Matriz direcional entre as cinco páginas | NOT TESTED | Contagem/configuração PBIR não prova propagação runtime. |
| Canal/Loja isolados, limpeza e contexto vazio | NOT TESTED | A consulta combinada representa somente um contexto. |
| Bookmarks | PASS estrutural / NOT TESTED funcional | Dez bookmarks em pares por página; os de Devoluções restringem visibilidade ao grupo do painel e suprimem dados e seção ativa. |
| Interações cross-filter / cross-highlight | NOT TESTED | Não houve clique de seleção nos visuais para observar respostas. |
| Page Navigator | PASS parcial | Os cinco destinos e rótulos existem; percurso entre pares e uso por teclado não foi realizado. |

Ver a matriz ampliada em `evidence/phase-5.6a/functional-matrix.md`. Inspeção PBIR não foi tratada como substituto da operação no Desktop.

## 10. Desempenho

**NOT TESTED:** nenhuma campanha Performance Analyzer foi iniciada nesta auditoria. Não há medição fria nem dados novos de mediana/máximo. Exportação histórica permanece fora deste commit e não foi reclassificada como medição atual.

## 11. Acessibilidade funcional

**NOT TESTED** para tab order, foco, operação de slicers por teclado, textos alternativos e tratamento assistivo. Nenhuma declaração de conformidade WCAG ou teste de leitor de tela é feita. Pendência para a revisão visual/assistiva posterior.

## 12. Persistência

**NOT TESTED nesta auditoria:** não houve alteração de relatório que justificasse salvar, nem ciclo controlado de salvar-fechar-reabrir após os testes. O PBIP abriu sem erro e as páginas Execução/Custos e Devoluções foram acessadas, mas isso não demonstra persistência final. O Desktop não recebeu atualização de dados.

## 13. Defeitos e correções

Nenhuma divergência semântica foi observada nas consultas executadas e nenhum defeito novo foi comprovado que justificasse mudança de PBIR. Portanto, não houve correção de PBIR nesta auditoria. Os testes funcionais pendentes continuam impeditivos para o gate funcional completo.

## 14. Evidências

- `evidence/phase-5.6a/inventory.json` — inventário estático e snapshot de entrada.
- `evidence/phase-5.6a/dax/*.dax` — expressões DAX de consulta.
- `evidence/phase-5.6a/results/*.csv` e `*.tsv` — resultados diretos do modelo.
- `evidence/phase-5.6a/functional-matrix.md` — observações runtime e limites.
- Snapshot externo de proteção: caminho/hash na seção 2 e inventário.

## 15. Gate e classificação

| Gate | Resultado | Motivo |
|---|---|---|
| Analítico | PASS parcial | DAX global, Jan–Set, finanças/invariantes, categorias e um Top 5 contextual reconciliaram. Faltam casos extremos, seleção por visual e leitura dos dois itens finais do Top 5 no canvas. |
| Funcional | NOT PASS / PENDING | Slider digitado/arrastado, sincronização direcional, filtros locais, interações e persistência não foram testados. |
| Técnico | PASS parcial | Integridade estrutural conferida, nenhum arquivo semântico/dado alterado; persistência pós-teste não verificada. |
| Desempenho | NOT TESTED | Sem nova campanha do Performance Analyzer. |
| Acessibilidade | NOT TESTED | Operação por teclado e tab order não exercitados. |

**FASE 5.6A PARTIAL — ANALYTICAL OR FUNCTIONAL VALIDATION PENDING.** A pendência decisiva é funcional: operar os controles e validar sincronização/interações/persistência no Desktop. Não iniciar automaticamente 5.6B ou 5.6C.

## 16. Git

Somente este relatório, a atualização histórica de 5.5, o status do plano/arquitetura e as evidências selecionadas pertencem ao commit desta auditoria. Alterações PBIR/TMDL e arquivos históricos preexistentes permanecem fora do stage.

## Complemento posterior — Fase 5.6A.1 (2026-10-14)

A classificação original desta auditoria permanece **PARTIAL** como registro do que foi testado naquela execução. A retomada funcional está documentada em [`phase-5.6a.1-functional-closure.md`](phase-5.6a.1-functional-closure.md), com matriz em `evidence/phase-5.6a/functional-closure/test-matrix.md` e export novo do Performance Analyzer.

Na página Devoluções, foram exercitados no Desktop: abertura sem erro, contexto inicial, bookmarks de abrir/fechar painel, seleção/limpeza do quinto item do Top 5 e leitura dos cinco SKUs visíveis. A seleção filtrou os KPIs e reduziu a série; limpar restaurou os valores. Os dois SKUs finais coincidem com a consulta DAX prévia. Um ciclo aquecido do Performance Analyzer exportou 180 eventos, com 18 ciclos visuais concluídos (`status=1`); trata-se de uma única amostra, sem benchmark frio nem estatística de campanha repetida.

Digitação de datas, alças do slider, Canal/Loja, sincronização direcional, isolamento local entre páginas, Page Navigator e teclado continuam `NOT TESTED`. O ciclo salvar-fechar-reabrir foi executado parcialmente: Custos e Margens abriu sem erro com os quatro KPIs/contexto restaurados; Devoluções também renderizou depois, com o painel aberto, mas seus KPIs e todos os destinos não foram conferidos no ciclo. O Desktop regravou `pages.json` e `pt-BR.tmdl`; após fechamento, ambos foram restaurados byte a byte ao snapshot protetor. O controle de computador não conseguiu operar campos/alças em modo de edição; isso é limitação de automação e não evidência de defeito do relatório. Não houve refresh nem alteração semântica. A Fase 5.6A.1 permanece **PARTIAL — MANUAL TESTS PENDING**; não iniciar 5.6B/5.6C até solicitação explícita.

## Complemento posterior — Fase 5.6A.2 (2026-10-14)

A Fase 5.6A.2 superou a limitação de interação: campos de data foram editados, ambas as alças foram arrastadas, Canal/Loja foram selecionados e limpos, e os cenários F01–F14 e S01–S07 passaram no Desktop. O Page Navigator foi acionado por `Ctrl+Space`; filtros locais permaneceram locais; categoria, produto e mês produziram interações visuais observáveis. O ciclo de persistência retornou com painel fechado e quatro KPIs do contexto salvo conferidos. Não houve refresh nem mudança de DAX, Power Query, modelo, relações, PostgreSQL ou dados. Ver [`phase-5.6a.2-desktop-test-automation.md`](phase-5.6a.2-desktop-test-automation.md) e `evidence/phase-5.6a/automated-closure/`.

**FASE 5.6A.2 PASS — AUTOMATED FUNCTIONAL VALIDATION COMPLETED.** Tab/foco por teclado, clique originado por cartão KPI e opções internas de bookmark ficaram `NOT TESTED`; não são falhas comprovadas. A classificação histórica PARTIAL desta auditoria permanece como registro daquela execução. Não iniciar 5.6B/5.6C automaticamente.
