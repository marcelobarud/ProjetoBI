# Matriz funcional complementar — Fase 5.6A.1

Data: 2026-10-14. Fonte: Power BI Desktop aberto, automação de UI e export do Performance Analyzer. Para limites e roteiro completo, ver [`phase-5.6a.1-functional-closure.md`](../../../phase-5.6a.1-functional-closure.md).

| ID | Grupo | Status | Evidência/limite |
|---|---|---|---|
| O01–O02 | Abertura e contexto inicial | PASS | PBIP abriu sem erro; período 30/04/2025–30/09/2026, Loja Física, Unidade Sintética Campinas |
| B01–B02 | Bookmarks abrir/fechar | PASS | Painel de filtros abriu e fechou pela lista de bookmarks; valores compartilhados permaneceram no contexto observado |
| U01 | Botão do canvas | PASS manual herdado | Confirmação textual anterior do usuário; não clicado nesta execução |
| I01 | Seleção/limpeza do produto | PASS | Quinto produto recalculou cartões e série; re-clique restaurou os valores do contexto |
| T01 | Últimos itens Top 5 | PASS | SKUs quarto/quinto visíveis conferem com resultado DAX existente; nomes e valores vêm da evidência DAX herdada |
| F01–F06 | Período, campos e slider | NOT TESTED | Calendário chegou a abrir, mas não foi confirmada digitação; automação não conseguiu digitar/arrastar sem alterar visual/foco |
| F07–F14 | Canal, Loja, combinações e limpeza | NOT TESTED | Slicers não alterados |
| S01–S07 | Sincronização direcional | NOT TESTED | Nenhuma seleção compartilhada alterada; presença estrutural prévia não prova propagação |
| L01 | Isolamento local cross-page | NOT TESTED | Seleção local respondeu em Devoluções, mas não foi carregada para outra página enquanto ativa |
| I02 | Seleção de categoria | NOT TESTED | Não exercitada |
| N01 | Page Navigator | NOT TESTED | Não acionado; abas inferiores não foram usadas como substituição |
| PA01 | Performance Analyzer | PASS parcial | Um refresh visual aquecido; export JSON no diretório; 18 ciclos de visual `status=1`, 180 eventos totais |
| A01 | Teclado/acessibilidade | NOT TESTED | Tab order, foco e teclado não exercitados |
| P01 | Salvar/fechar/reabrir | PASS parcial | Custos e Margens reabriu sem erro com quatro KPIs/contexto e painel fechado; Devoluções renderizou depois com painel aberto. KPIs/destinos não foram revisitados e o estado aberto precisa ser confirmado |
| G01 | Integridade técnica escopo | PASS | Sem refresh e sem modificação intencional de DAX, PQ, modelo, DB ou dados |

## Hashes desta evidência

| Arquivo | SHA-256 |
|---|---|
| `performance-analyzer-devolucoes.json` | `D0D31B791DC213ECC07AD53ADBF2517E5066BB583222B23E7B6B15398E543F69` |

Não houve captura de tela nova; não atribuir evidência visual fotográfica a esta matriz.
