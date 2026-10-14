# Fase 5.6A.1 — Fechamento da validação funcional integrada

**Data da execução:** 2026-10-14

**Classificação:** **FASE 5.6A.1 PARTIAL — MANUAL TESTS PENDING**

**Projeto:** `powerbi/ProjetoBI.pbip`

**Base:** `546db92` (`test(powerbi): valida integridade funcional dos cinco dashboards`)
**Identidade / Design System:** InfoTech, monograma I/T / v0.2

## 1. Escopo e segurança

Retomada funcional concentrada na página **Devoluções**, sem refresh. Nenhum DAX, Power Query, tabela, relacionamento, credencial, configuração de PostgreSQL ou dado foi alterado. A auditoria DAX de 5.6A foi reutilizada como linha de base; não foram repetidas consultas financeiras aprovadas.

O estado original observado nos slicers foi 30/04/2025–30/09/2026, Canal `Loja Física` e Loja `Unidade Sintética Campinas`. A seleção local do Top 5 foi limpa após o teste e o painel foi fechado pelo bookmark correspondente. Não foi feita alteração de datas, canal ou loja.

Snapshot protetor das alterações preexistentes: `C:\Users\D2\AppData\Local\Temp\ProjetoBI-Phase-5.6A1-20261014-154559.zip`, SHA-256 `A31B3438C5638C09163679DB98252294946E3FA8FA6A315040F4FDB532B5613E`. Ele contém o estado/diffs da working tree antes desta execução; não é artefato do relatório nem substitui persistência no Desktop.

## 2. Evidências herdadas da Fase 5.6A

Permanecem válidas as reconciliações DAX globais e Jan–Set/2026, os três invariantes financeiros com diferença zero, as 12 categorias sem BLANK e o Top 5 independente no contexto salvo. Os quatro KPIs de Devoluções no contexto salvo também já haviam sido conciliados. Os detalhes originais permanecem em `phase-5.6a-integrated-functional-audit.md` e `evidence/phase-5.6a/`.

## 3. Matriz da operação real

Estado inicial: PBIP aberto sem erro; página Devoluções; período, Canal e Loja acima; seleções temporárias limpas; painel fechado. “NOT TESTED” significa que a operação descrita não foi observada no Desktop.

| ID / área | Ação e esperado | Observado | Estado / evidência |
|---|---|---|---|
| O01 — abertura | Abrir PBIP; cinco páginas e visuais devem carregar | Abriu sem erro; página Devoluções renderizou com quatro KPIs, série, categoria e Top 5 | PASS, abertura desta sessão; demais páginas não foram revalidadas uma a uma |
| O02 — contexto inicial | Confirmar os três filtros compartilhados | 30/04/2025–30/09/2026, Loja Física, Unidade Sintética Campinas | PASS, valores lidos nos controles |
| B01 — bookmark abrir | Aplicar “Filtros — abrir | Devoluções”; painel deve mostrar filtros | Painel exibiu Período, Canal e Loja | PASS, acionado pelo painel Bookmarks |
| B02 — bookmark fechar | Aplicar “Filtros — fechar | Devoluções”; painel deve recolher | Painel fechou e a página ficou disponível | PASS, acionado pelo painel Bookmarks; não substitui clique independente no botão do canvas |
| U01 — botão Fechar filtros | Acionar botão no canvas | Sem novo teste nesta execução; há confirmação manual anterior do usuário de que o clique funciona | PASS manual herdado, sem captura associada; ver registro em 5.5 |
| I01 — seleção Top 5 | Selecionar produto; KPIs e série devem responder | Quinta barra filtrou os cartões para devolução comercial de R$ 13.863,32; série ficou em um ponto e as outras barras foram atenuadas. Repetir o clique limpou a seleção e restaurou o contexto | PASS, observado no Desktop; valor coincide com DAX previamente reconciliado |
| T01 — itens finais Top 5 | Tornar as duas últimas barras visíveis e conferir ordem/rótulo | Os cinco SKUs foram vistos; quarto SKU-NOT-00661 e quinto SKU-NOT-00757, na mesma ordem do resultado DAX prévio. Nomes completos/valores são evidência DAX herdada, não lidos novamente no tooltip | PASS para posição e SKU no canvas; DAX herdado para nome/valor |
| PA01 — Performance Analyzer | Registrar um ciclo representativo aquecido sem somar eventos paralelos | Um comando “Refresh visuals” na sessão carregada gerou 180 eventos exportados, incluindo 18 ciclos de container com `status=1`. Ciclos observados: cartões 424–425 ms; evolução/categoria/Top 5 445–449 ms. Medidas de ciclo por visual; execução única, sem benchmark frio | PASS parcial, export bruto em `evidence/phase-5.6a/functional-closure/performance-analyzer-devolucoes.json`; sem mediana/max de campanha repetida |
| F01 — editar data inicial | Digitar data válida; início muda e fim permanece | Não foi possível inserir texto com o controle de computador: o foco permaneceu no canvas/visual; calendário apareceu, mas nenhuma data foi confirmada | NOT TESTED; limitação da automação, não defeito do slicer comprovado |
| F02 — editar data final | Digitar data válida e confirmar intervalo | Não realizada | NOT TESTED |
| F03 — Jan–Set/2026 | Definir 01/01–30/09/2026 e conferir quatro KPIs/gráficos e contexto nas páginas | Não realizada; resultados DAX herdados não equivalem à operação do slicer | NOT TESTED |
| F04 — alça inicial | Arrastar alça inicial e observar recalculo | Não foi possível iniciar arraste em modo de edição pela automação | NOT TESTED; limitação da automação |
| F05 — alça final | Arrastar alça final e observar recalculo | Não realizada | NOT TESTED; limitação da automação |
| F06 — período no painel | Fechar/reabrir painel após alterar datas e preservar intervalo | Datas não foram alteradas; bookmarks abriram/fecharam painel preservando o contexto inicial | NOT TESTED para persistência de seleção alterada |
| F07–F14 — Canal/Loja | Canal e Loja isolados, combinados, combinados com período, limpeza seletiva, sem resultado e limpeza completa | Nenhuma seleção foi alterada nesta retomada | NOT TESTED; não foi criado artificialmente um estado sem resultado |
| S01–S07 — sincronização | Propagar mudanças/limpeza nas sete direções especificadas entre as cinco páginas | Nenhum filtro compartilhado foi alterado; grupos/instâncias estáticos anteriores permanecem apenas evidência estrutural | NOT TESTED em runtime |
| L01 — isolamento local | Seleção local de Categoria/Produto não deve filtrar outras páginas | Seleção de produto respondeu localmente em Devoluções; navegação cruzada com seleção ativa não foi exercitada | NOT TESTED para isolamento entre páginas |
| I02 — categoria | Selecionar categoria, conferir resposta e limpar | Não realizada | NOT TESTED |
| N01 — Page Navigator | Destinos, estado ativo, retorno, salto não adjacente e preservação do contexto | Não foi possível executar o botão nativo em modo de edição com a automação; a troca por abas inferiores não foi usada como substituto | NOT TESTED; limitação da automação |
| A01 — teclado/acessibilidade | Ordem de tabulação, foco, texto alternativo, teclado e botões | Não realizado | NOT TESTED; leitor de tela/WCAG fora deste teste mínimo |
| P01 — persistência | Restaurar estado, salvar, fechar, reabrir e confirmar páginas/visuais | Ciclo executado: página Custos e Margens, contexto original, painel fechado e quatro KPIs visíveis reapareceram sem erro. Em seguida, Devoluções também abriu/renderizou filtros e gráficos, sem refresh; o painel de filtros estava aberto (botão “Fechar filtros” visível). Não foram conferidos após reabertura os quatro KPIs de Devoluções nem os cinco destinos completos | PASS parcial; estado do painel divergiu do esperado/pretendido e a persistência completa não foi aprovada |
| G01 — integridade | Semântica/DAX/Power Query/PostgreSQL e dados permanecem intactos | Nenhum desses artefatos foi modificado; nenhum refresh nem conexão de banco foi usado nesta execução | PASS para escopo desta execução |

### Limites de automação

O Desktop estava em modo de edição. A automação conseguia selecionar visuais e abrir calendário, mas não manter Ctrl pressionado para ativar os controles do canvas nem digitar de forma confiável em seus campos. O uso de bookmarks pelo painel correspondente permitiu testar a mudança de visibilidade do painel. Isso não demonstra que slider, slicers ou Page Navigator falharam; esses itens continuam pendentes para operação manual.

## 4. Desempenho

O Performance Analyzer foi iniciado às 16:00 (America/Sao_Paulo), com o modelo já carregado; o export registra um ciclo aquecido. Foram 180 eventos no JSON, incluindo eventos auxiliares e 18 ciclos visuais com estado `1`. Nos cartões, ciclos de 424–425 ms; nos três gráficos, 445–449 ms. Esses tempos representam a duração do ciclo individual do container, que inclui trabalho assíncrono de consulta/renderização; os eventos são concorrentes e não devem ser somados como duração total da página. Não houve medição fria, campanha repetida, seleção de período/canal/loja ou amostra com filtros alterados; portanto não foi calculada mediana/máximo representativo. JSON: SHA-256 `D0D31B791DC213ECC07AD53ADBF2517E5066BB583222B23E7B6B15398E543F69`.

## 5. Acessibilidade funcional

Ordem de tabulação, foco visível, operação por teclado, textos alternativos no canvas e leitor de tela não foram exercitados nesta retomada. Não se declara conformidade WCAG. Valores BLANK/negativos não foram testados na interface; as observações analíticas anteriores não substituem essa leitura funcional.

## 6. Persistência, defeitos e correções

O ciclo salvar-fechar-reabrir foi realizado após restaurar a página Custos e Margens, o painel fechado e o contexto original. O PBIP reabriu sem erro; os quatro KPIs da página e seus valores/contexto reapareceram. Depois, Devoluções também renderizou ao navegar, sem erro, mas não houve conferência pós-abertura de seus quatro KPIs nem inspeção dos cinco destinos completos. O painel de filtros apareceu aberto na página Devoluções após a reabertura, com o botão “Fechar filtros” visível; isso diverge do estado fechado que se pretendia restaurar e fica como pendência para confirmação/correção manual, pois não foi possível distinguir com segurança estado salvo anterior e efeito da automação. A persistência fica **PASS parcial**, não homologação integral. O Desktop serializou `pages.json` e `pt-BR.tmdl`; após encerrar todas as instâncias, ambos foram restaurados byte a byte ao snapshot externo prévio. Assim, alterações antigas foram preservadas e nenhuma diferença de serialização não relacionada permaneceu. Não houve mudança semântica. Nenhuma consulta DAX foi repetida.

## 7. Roteiro manual necessário para fechar o gate

Na página Devoluções, execute sem atualizar dados:

1. Abra **Filtros**; digite uma data inicial e outra final; confirme e confira mudança dos quatro KPIs, evolução, categoria e Top 5.
2. Arraste cada alça do slider separadamente e confirme que o intervalo e os visuais mudam; depois defina 01/01/2026–30/09/2026.
3. Altere Canal e Loja isoladamente, juntos e com período; limpe um por vez e por completo. Registre os valores e se o caso sem resultado realmente ocorre.
4. Propague as alterações nas direções S01–S07 da matriz original e confirme seleções nas páginas de destino.
5. Selecione uma categoria/produto e confira que o filtro local não vaza a outras páginas; teste limpar. Use Page Navigator em retorno e salto não adjacente.
6. Faça um ciclo curto de teclado (Tab/foco visível) nos filtros e no navegador, sem inferir conformidade assistiva.
7. Confirme o painel de Devoluções fechado; se necessário, feche-o pelo botão e salve com a página inicial/contexto restaurados. Feche e reabra o PBIP; confirme as cinco páginas, quatro KPIs de Devoluções, visuais, painel fechado e filtros sem erros.

Uma confirmação objetiva dos resultados desses passos permitirá atualizar apenas os casos executados. Até então, os casos acima ficam `NOT TESTED`.

## 8. Gates e próximos passos

| Gate | Estado | Motivo |
|---|---|---|
| Integridade analítica herdada | PASS | Reconciliações e invariantes registrados na Fase 5.6A |
| Integridade do escopo técnico | PASS | Nenhuma mudança de modelo/DAX/PQ/dados/PostgreSQL nem refresh nesta retomada |
| Interação do Top 5 e bookmarks | PASS parcial | Seleção do produto e estado do painel exercitados; botão e isolamento cross-page possuem evidência separada/pendente |
| Filtros e sincronização | NOT TESTED | Dependem de operação manual dos slicers |
| Persistência | PASS parcial | Custos e Margens reabriu com quatro KPIs e painel fechado; Devoluções renderizou depois com o painel aberto; investigar/confirmar estado final |
| Desempenho | PASS parcial | Um ciclo aquecido exportado; sem mediana/máximo de campanha repetida ou filtros alterados |
| Acessibilidade funcional | NOT TESTED | Teclado/tab order não exercitados |

**Resultado: FASE 5.6A.1 PARTIAL — MANUAL TESTS PENDING.** Pendências visuais/assistivas devem seguir para planejamento da Fase 5.6B. A Fase 5.6B/5.6C não foi iniciada e o Design System v0.2 permanece vigente.

## 9. Git

O commit desta etapa deve conter somente este relatório, sua evidência bruta e atualizações documentais do status. PBIR/TMDL, `docs/powerbi/PowerBIPerformanceData.json`, ZIPs antigos e demais alterações preexistentes ficam fora do stage. Nenhum push, merge, rebase ou amend será executado.
