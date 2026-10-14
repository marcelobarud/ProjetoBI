# Matriz de testes automatizados — Fase 5.6A.2

Power BI Desktop Store `2.158.1304.0 (26.09)+a43ace043425e30778f23721b943ff885c2214e5`; sessão real do PBIP, sem refresh.

| ID | Verificação | Resultado observado | Estado | Evidência |
|---|---|---|---|---|
| POC-01 | Botões Filtros / Fechar filtros no canvas | Abrir e fechar alteraram o painel | PASS | F06 e teste POC no Desktop |
| POC-02 | Digitar data | Data mudou no campo/controle | PASS | F03 período Jan–Set; F01/F02 |
| POC-03 | Page Navigator | Destino e página ativa mudaram com Ctrl+Space | PASS | S01–S07 |
| F01 | Digitar data inicial | Campo e período foram atualizados | PASS | F03-periodo-jan-set-2026.png |
| F02 | Digitar data final | Campo e período foram atualizados | PASS | F03-periodo-jan-set-2026.png |
| F03 | 01/01–30/09/2026 sem filtros adicionais | KPI comercial R$ 5.943.004,03; série respondeu | PASS | F03-devolucoes-jan-set-kpis.png |
| F04 | Arrastar alça inicial | Intervalo passou a 02/06/2025–30/09/2026 | PASS | F04-slider-inicio-movido.png |
| F05 | Arrastar alça final | Intervalo passou a 02/06/2025–09/08/2026 | PASS | F05-slider-fim-movido.png |
| F06 | Fechar/reabrir painel | Seleção foi preservada | PASS | F06-painel-reaberto-periodo-preservado.png |
| F07 | Canal isolado | E-commerce filtrou KPIs/série | PASS | contexto registrado na sessão |
| F08 | Loja isolada | Campinas alterou os indicadores | PASS | contexto registrado na sessão |
| F09 | Canal + Loja | Combinação selecionada alterou os visuais | PASS | estado inicial e teste sem resultado |
| F10 | Canal + Loja + período | Combinação de três filtros alterou os visuais | PASS | F03 e contextos combinados |
| F11 | Limpar Canal, manter Loja | Canal voltou a Todos; Loja permaneceu selecionada | PASS | sessão Desktop |
| F12 | Limpar Loja, manter período | Loja voltou a Todos; período permaneceu | PASS | sessão Desktop |
| F13 | Contexto sem resultado | E-commerce + Campinas mostrou série sem dados (BLANK) | PASS | diagnóstico de BLANK observado |
| F14 | Limpeza completa | Canal/Loja limpos; intervalo remanescente confirmado | PASS | sessão Desktop |
| S01 | Executiva → Comercial, período | Intervalo sincronizou no destino | PASS | sessão Desktop |
| S02 | Comercial → Produtos, canal | E-commerce sincronizou no destino | PASS | sessão Desktop |
| S03 | Produtos → Custos, loja | Campinas sincronizou e alterou KPIs | PASS | sessão Desktop |
| S04 | Custos → Devoluções, período + canal | 01/03–31/08/2026 e Loja Física no destino; visuais responderam | PASS | S04-custos-selecao-origem.png; S04-devolucoes-periodo-canal-sincronizados.png |
| S05 | Devoluções → Executiva, período + canal + loja | Jan–Set/2026, E-commerce próprio e Unidade Sintética Equatorial no destino | PASS | S05-devolucoes-para-executiva-sync.png |
| S06 | Devoluções → Produtos, limpar filtros compartilhados | Filtros globais em Todos; filtros locais permaneceram locais | PASS | S06-produtos-filtros-compartilhados-todos.png |
| S07 | Executiva → Devoluções, intervalo novo | Datas apareceram no destino | PASS | S07-executiva-para-devolucoes.png |
| L01 | Categoria local | Computadores de mesa alterou visuais de Produtos; seleção limpa | PASS | sessão Desktop |
| L02 | Produto local | SKU-ACC-00036 alterou categoria/ranking; seleção limpa | PASS | products-local-product-selected.png |
| L03 | Isolamento cross-page | Categoria/Produto não propagaram a Custos/Devoluções; filtros comuns continuaram sincronizados | PASS | sessão Desktop |
| I01 | Categoria em Devoluções | Gráfico mensal e ranking responderam; limpeza restaurou contexto | PASS | sessão Desktop |
| I02 | Produto Top 5 | Série reduziu a um ponto e barras foram realçadas; limpeza restaurou contexto | PASS | sessão Desktop e evidência herdada Fase 5.6A.1 |
| I03 | Ponto mensal | Seleção de mês realçou categoria/produto | PASS | sessão Desktop |
| I04 | Clique em cartão KPI para originar interação | Não observado | NOT TESTED | — |
| N01–N05 | Page Navigator nos cinco percursos planejados | Destino correto/estado ativo confirmado; sem erro | PASS | S04/S05 capturas e observações de sessão |
| B01 | Botão Filtros no canvas | Abriu painel em edição | PASS | POC-01 |
| B02 | Botão Fechar filtros no canvas | Fechou painel e seleção permaneceu | PASS | POC-01/F06 |
| B03 | Bookmarks via painel | Abrir/fechar foram observados na Fase 5.6A.1 | PASS | matriz herdada 5.6A.1 |
| B04 | Opções internas Display/Data/visuais | Não repetidas nesta execução | NOT TESTED | — |
| P01 | Salvar, fechar e reabrir PBIP | Reabriu sem erro na página Devoluções; painel fechado | PASS | captura de estado reaberto registrada na sessão anterior |
| P02 | KPIs após reabrir | Quatro valores coincidiram com o contexto baseline | PASS | R$ 420.582,31; R$ 88.812,48; R$ 235.478,15; 2,14% |
| A01 | Tab, foco e operação básica por teclado | Não realizado | NOT TESTED | — |
| A02 | Leitor de tela/WCAG | Fora do escopo de validação realizada | NOT TESTED | — |
| T01 | Abrir PBIP | Abertura sem erro observada | PASS | sessão Desktop |
| T02 | Não alterar fontes/semântica/dados; não executar refresh | Nenhuma alteração feita pela fase; refresh não acionado | PASS | diff e snapshot preflight |

## Resultado

F01–F14 e S01–S07: **PASS**. Navegação, botões/bookmarks, filtros locais, interações observadas e persistência: **PASS**, com exceções claramente classificadas **NOT TESTED** para clique no KPI, opções internas de bookmark e acessibilidade de teclado. Nenhum **FAIL** ou **BLOCKED** funcional foi comprovado.
