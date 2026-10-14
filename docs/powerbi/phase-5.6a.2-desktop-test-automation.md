# Fase 5.6A.2 — Automação funcional no Power BI Desktop

**Data:** 2026-10-14
**Classificação:** **FASE 5.6A.2 PASS — AUTOMATED FUNCTIONAL VALIDATION COMPLETED**
**Projeto:** `powerbi/ProjetoBI.pbip`
**Design System:** InfoTech v0.2 (preservado)
**Base Git:** `a91ea05` (`test(powerbi): conclui validacao funcional integrada`)

## 1. Escopo e segurança

A execução automatizou os controles funcionais restantes no Power BI Desktop. Não foi feita atualização de dados e não foram alterados DAX, Power Query, relacionamentos, modelo semântico, PostgreSQL, credenciais, nem dados. Não foi iniciada a Fase 5.6B ou 5.6C.

O snapshot protetor externo anterior às interações foi preservado em `C:\Users\D2\AppData\Local\Temp\ProjetoBI-Phase5.6A2-preflight-20261014-184617.zip`, SHA-256 `781A9F22CE1EA3CCB7B29ED505CF29E04AEA3F40CC1D6C747B69A99472B82C1A`. O Desktop foi fechado ao fim sem salvar filtros temporários; o contexto salvo previamente permaneceu como baseline.

## 2. Ambiente e automação

- Power BI Desktop da Store: `2.158.1304.0 (26.09)+a43ace043425e30778f23721b943ff885c2214e5`.
- Controle local de janelas e entrada do Windows via Computer Use (`@oai/sky`), com captura da janela observada antes de cada ação. A lista de aplicativos foi atualizada; uma janela única “ProjetoBI” foi identificada.
- Desktop em modo de edição; zoom variou entre 36% e 67% para operar os controles. A sessão não executou refresh.
- O mecanismo anteriormente incapaz de editar datas, arrastar o slider e acionar o Page Navigator foi substituído por interação direta no campo nativo, arraste real com mouse e seleção do navegador seguida de `Ctrl+Space`.

## 3. Provas de conceito

| POC | Ação confirmada | Estado |
|---|---|---|
| POC-01 — botão | Acionou Filtros e Fechar filtros no canvas em modo de edição; o painel abriu e fechou | PASS |
| POC-02 — data | Focou o campo nativo, substituiu e confirmou uma data; o texto do campo e o seletor refletiram a data | PASS |
| POC-03 — navegador | Acionou destino do Page Navigator e retornou a Devoluções por `Ctrl+Space`; página ativa mudou | PASS |

## 4. Datas e slider

F01–F06 passaram. As datas puderam ser digitadas nos dois campos e a referência de 01/01/2026–30/09/2026 foi aplicada. Com Canal e Loja em Todos, o KPI comercial mostrou **R$ 5.943.004,03**, coerente com a reconciliação DAX da Fase 5.6A. A evolução mensal respondeu ao período. O teste não converteu BLANK em zero.

O arraste físico da alça inicial mudou o intervalo para 02/06/2025–30/09/2026; o arraste da alça final mudou para 02/06/2025–09/08/2026. As duas datas exibidas e os visuais responderam. O painel foi fechado e reaberto com a seleção preservada.

## 5. Canal, Loja e sincronização

F07–F14 passaram: Canal isolado, Loja isolada, combinação, combinação com período, limpeza seletiva, contexto sem resultado e limpeza completa foram efetivamente observados. E-commerce + Campinas produziu visuais sem dados (BLANK), que foi distinguido de zero. Após limpar Canal ou Loja, os demais filtros permaneceram selecionados conforme o cenário.

S01–S07 passaram em runtime. Os filtros Período, Canal e Loja foram alterados na origem e conferidos na página de destino. S04 e S05 foram repetidos nesta retomada usando o Page Navigator, não as abas inferiores:

- S04 Custos e Margens → Devoluções: 01/03/2026–31/08/2026 e Loja Física apareceram no destino; a série e os indicadores reagiram.
- S05 Devoluções → Visão Executiva: 01/01/2026–30/09/2026, E-commerce próprio e Unidade Sintética Equatorial apareceram no destino; a combinação sem resultado permaneceu coerente.

Os demais sentidos e a limpeza sincronizada também foram exercitados. As capturas de S04/S05 nesta pasta mostram estado de origem/destino.

## 6. Filtros locais e interações

Categoria e Produto foram selecionados em Produtos e Categorias; as barras/ranking responderam e a seleção foi limpa. A seleção local não propagou para Custos ou Devoluções; Período, Canal e Loja continuaram compartilhados. Em Devoluções, categoria, produto do Top 5 e mês da série foram selecionados; houve cross-filter/cross-highlight observável e a limpeza restaurou os visuais.

Os cartões KPI foram observados mudando com filtros compartilhados, categoria e produto. Clique em um cartão KPI para verificar interação originada pelo próprio cartão: **NOT TESTED**.

## 7. Page Navigator e bookmarks

As cinco rotas planejadas do Page Navigator foram acionadas em modo de edição, usando seleção do visual e `Ctrl+Space`. Os destinos e estados ativos foram observados, sem erro. Abas inferiores não foram usadas como substituto nos testes de navegação.

Filtros e Fechar filtros atuaram pelo botão no canvas; reabrir preservou as seleções. A aplicação dos bookmarks de abertura/fechamento pelo painel já havia passado na Fase 5.6A.1. A inspeção de suas opções internas de escopo/configuração (Display/Data/visuais selecionados) não foi repetida: **NOT TESTED** nesta execução.

## 8. Persistência

O ciclo controlado anterior restaurou período 30/04/2025–30/09/2026, Loja Física, Unidade Sintética Campinas, seleções locais limpas e painel fechado. O Desktop foi salvo, fechado e reaberto; retornou à página Devoluções, painel fechado, sem erro e com os quatro KPIs esperados no contexto: R$ 420.582,31; R$ 88.812,48; R$ 235.478,15; 2,14%. A geometria previamente corrigida do slicer permaneceu. As interações temporárias desta etapa final foram descartadas ao fechar o Desktop sem salvar.

## 9. Acessibilidade funcional básica

Tabulação, foco visível, nomes acessíveis, ativação do botão por Tab/Enter e operação por teclado dos campos **NOT TESTED**. Não se declara compatibilidade integral com leitor de tela ou conformidade WCAG.

## 10. Defeitos e correções

Nenhum defeito funcional foi comprovado. Não houve correção PBIR nesta fase. Não houve alteração semântica ou atualização de dados. As alterações de PBIR/TMDL anteriores, presentes antes desta fase, foram mantidas fora do commit. Apenas documentação e evidências próprias desta fase foram preparadas para versionamento.

## 11. Gates e limites

| Gate | Resultado | Evidência/limite |
|---|---|---|
| Automação de controles, campos, slider, Canal/Loja e Page Navigator | PASS | POCs e capturas reais; cenários F01–F14, S01–S07 |
| Funcional integrado | PASS | KPIs responderam, filtros locais ficaram isolados, bookmarks/botões e persistência passaram; clique em cartão KPI e configuração interna de bookmark não foram testados |
| Integridade técnica | PASS | PBIP abriu e reabriu; esta execução não alterou modelo, DAX, Power Query, relações, fonte ou dados; sem refresh |
| Acessibilidade de teclado | NOT TESTED | Percurso tab/foco e nomes acessíveis não foram exercitados |

## 12. Evidências

A matriz completa, capturas e hashes estão em `evidence/phase-5.6a/automated-closure/`. O pacote portátil da fase é `evidence/archives/fase-5.6a.2-evidencias.zip`; seu manifesto lista SHA-256 por arquivo. Capturas são imagens reais retornadas pela janela do Power BI, não imagens sintéticas.

**Resultado:** FASE 5.6A.2 PASS — AUTOMATED FUNCTIONAL VALIDATION COMPLETED. A ressalva de acessibilidade básica e as duas interações específicas não testadas estão explícitas acima; não são falhas comprovadas do dashboard. O Design System v0.2 permanece inalterado. Não iniciar 5.6B/5.6C.

## 13. Git

Commit autorizado: `test(powerbi): automatiza validacao funcional integrada`. O staging é seletivo: relatório, matriz, manifesto/README, capturas escolhidas e ZIP da fase. Mudanças preexistentes em PBIR/TMDL, arquivos genéricos de performance e pacotes históricos permanecem fora do commit.
