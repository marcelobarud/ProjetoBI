# Evidência funcional — Fase 5.6A

Data da inspeção: 2026-10-14. Fonte: PBIP aberto no Power BI Desktop e inspeção estática PBIR.

| Verificação | Resultado | Evidência/limite |
|---|---|---|
| PBIP abre sem erro | PASS | A página Custos e Margens abriu no Desktop; a página Devoluções também foi visitada. |
| Cinco destinos no navegador | PASS parcial | Rótulos/destinos já visíveis; navegação completa por pares e teclado não percorrida nesta auditoria. |
| Abrir painel da página Devoluções | PASS | A ação Filtros + Ctrl+Enter exibiu o painel e seus três filtros. |
| Fechar painel da página Devoluções | NOT TESTED nesta sessão | Botão/bookmark visível; não foi possível confirmar funcionalmente o fechamento nesta interação. O usuário já confirmou o clique nas fases anteriores. |
| Período, Canal e Loja no estado salvo | PASS | Data 2025-04-30–2026-09-30, Loja Física, Unidade Sintética Campinas. Consulta DAX do contexto reproduziu quatro KPIs. |
| Slider, digitação de datas e sincronização | NOT TESTED | Não foram movidas as alças nem digitadas datas; não foi testada propagação entre páginas. |
| DAX Top 5 no contexto salvo | PASS | Consulta independente retorna 5 produtos ordenados; os três primeiros coincidem com os itens legíveis no visual. Resultado em `results/context-top5.tsv`. |
| Bookmarks de filtro | PASS estático / NOT TESTED funcionalmente nesta sessão | Dez definições em cinco pares. `suppressData=true`, `suppressActiveSection=true`, `applyOnlyToTargetVisuals=true`; cada um aponta apenas para o grupo do painel da própria página. |
| Filtros locais, interações, casos extremos | NOT TESTED | JSON inspecionado, mas não equivale a testes de seleção no Desktop. |
| Performance Analyzer | NOT TESTED | Nenhuma nova campanha executada nesta auditoria. |
| Salvar, fechar e reabrir | NOT TESTED | Nenhuma gravação de PBIR foi feita nesta execução; proteção dos arquivos alterados previamente mantida. |
| Atualização de dados/PostgreSQL | NOT APPLICABLE | Não houve refresh nem acesso de escrita ao banco. |

As inspeções da definição PBIR são evidência estrutural, não substituem operação real dos controles no Desktop.
