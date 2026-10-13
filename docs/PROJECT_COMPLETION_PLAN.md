# ProjetoBI — Plano Mestre de Conclusão e Preparação para Power BI

**Status:** M5 PASS — Portfolio persistido e reconciliado; Fases 4.2–4.6 PASS; Fases 4.6.1–4.6.2 PARTIAL; Fase 5.0 PASS; Fase 5.1 PARTIAL, com abertura e componentes confirmados pelo usuário e validação funcional pendente. O modelo semântico tem 10 tabelas, 55 medidas e 21 relações. A página Visão Executiva foi composta em PBIR com canvas Full HD 1920×1080. A configuração de limite de consultas permanece pendente: `Auto` não persistiu no ciclo de reabertura da Fase 4.6.2.
**Diretório:** `D:\Codex\ProjetoBI`
**Objetivo principal:** concluir e validar o dataset Portfolio, disponibilizar baselines SQL confiáveis e preparar a exploração analítica no Power BI.

## 1. Diretriz

Este documento substitui a condução por prompts isolados por uma execução orientada a marcos, dependências, critérios de aceite e recuperação de falhas.

O objetivo não é construir uma simulação comercial perfeita. É entregar um dataset sintético coerente, suficientemente realista, rastreável e analiticamente utilizável.

Não enfraquecer invariantes de integridade ou alterar faixas comerciais aprovadas para acelerar artificialmente a conclusão.

**Definition of Done:** dataset Portfolio validado e persistido, documentação atualizada, baselines executáveis e projeto pronto para iniciar a construção do modelo Power BI.

## 2. Estado inicial conhecido

### Banco

- PostgreSQL 18.6.
- Database `projeto_bi`.
- 9 schemas.
- 41 tabelas operacionais.
- Migrations 001, 002 e 003 aplicadas.
- Migration 003: cancelamento parcial de itens.
- 41 PKs, 72 FKs, 85 CHECKs, 38 UNIQUEs e 154 índices.
- Estado atual (2026-10-10): 3.894.457 linhas nas 41 tabelas, incluindo 120.000 pedidos. O backup lógico da Fase 4.0 está registrado em `docs/database/backup-and-restore.md`; a contagem posterior ao backup permaneceu inalterada.

### Gerador

- Seed raiz `20261005`.
- Fuso `America/Sao_Paulo`.
- Bootstrap: novembro e dezembro de 2022.
- Período comercial: 2023-01-01 até 2026-09-30.
- Profile Portfolio: meta de 120.000 pedidos efetivamente aceitos.
- Geração incremental e sink PostgreSQL existentes.
- Custo médio ponderado com `Decimal` e `ROUND_HALF_UP`.
- Cancelamentos integrais e parciais, refunds, fulfillment, transferências e devoluções implementados.
- Smoke histórico preservado.

### Resultado mais recente

Fase 3E.2c.4: `SUPPLY POLICY READY`, em caráter experimental.

Em 10.000 intenções:

| Indicador | Controle | Política candidata |
|---|---:|---:|
| Pedidos aceitos | 6.127 | 8.529 |
| Recusas físicas | 3.873 | 1.471 |
| Unidades físicas perdidas | 8.937 | 3.850 |
| Backorders parciais vencidos | 686 | 0 |
| Saldo final sem demanda local | 46.472 | 8.243 |

A candidata utiliza distribuição inicial conservativa por SKU, reposição baseada em histórico observado, prior de cold start e transferências reais entre locais.

As transferências tiveram ganho marginal no ensaio e não devem ser ativadas definitivamente sem comparação adicional.

M1 homologou safety 3× e transferências automáticas desligadas no profile; a integração PostgreSQL da configuração aprovada passou em M4 com rollback. A integração 10k da candidata experimental com transferências também passou anteriormente.

### Estado Power BI

1. M5 está concluído: os 120.000 pedidos foram persistidos, conferidos em nova conexão e os 13 baselines SQL foram aprovados e reconciliados.
2. A Fase 4.0 concluiu backup lógico e preparação documental; a Fase 4.1 criou e reabriu o projeto inicial PBIP com TMDL e PBIR, sem carregar dados.
3. A Fase 4.2 criou e validou `projetobi_pbi_ro`; a Fase 4.3 validou duas fatos comerciais, cinco dimensões, calendário e nove relações no Desktop. A Fase 4.5A centralizou as medidas em `_Medidas`; a serialização nativa do Desktop foi regularizada em `74ca3be`. A Fase 4.5B adicionou a fundação financeira/devoluções e a Fase 4.5C implementou 27 medidas financeiras (55 no total), com refresh, reabertura, reconciliações SQL × DAX e precisão inteira escalada. A Fase 4.6 auditou as 10 tabelas, 11 Display Folders, 21 relações, dependências, filtros, política temporal, segurança e desempenho. Na Fase 5.1, o tema foi aplicado e a primeira página foi composta em PBIR; atualização, reconciliação, interações e reabertura ainda dependem de validação no Desktop. O desenvolvimento local de dashboards está autorizado; a pendência de `queryLimitOption=None` não invalida o modelo semântico, mas os limites devem ser revisados antes da publicação.

## 3. Regras de execução

O agente executor deve seguir os marcos em ordem lógica, corrigindo problemas dentro do escopo autorizado.

Quando uma validação falhar:

1. Registrar o erro e seu contexto.
2. Identificar a primeira causa reproduzível.
3. Classificar como falha de código, contrato, distribuição, ambiente, performance ou regra de negócio.
4. Criar um teste direcionado ou reprodução controlada.
5. Corrigir a causa, sem contornar a validação.
6. Executar o teste direcionado.
7. Reexecutar o gate afetado.
8. Retomar o plano a partir do último marco válido.

Permitir ciclos adicionais enquanto houver progresso técnico demonstrável.

Depois de três tentativas sem progresso mensurável sobre a mesma causa, interromper essa linha de solução e produzir diagnóstico alternativo. Escalar ao usuário se houver necessidade de nova decisão.

Não repetir uma carga integral de 120 mil pedidos para diagnosticar problemas que possam ser reproduzidos em escalas menores.

Não fazer retries automáticos idênticos de operações custosas ou persistentes.

## 4. Marco M0 — Consolidar o estado técnico

**Objetivo:** garantir que o projeto tenha uma referência verificável antes da execução autônoma.

Atividades:

- Ler integralmente `AGENTS.md` e as regras de subagentes.
- Inspecionar branch, HEAD, working tree e diff.
- Inventariar alterações locais ainda não commitadas.
- Confirmar versões de migrations, schema, CLI, testes e guards.
- Reconciliar documentação histórica com o código vigente.
- Identificar artefatos temporários e relatórios finais pendentes.
- Verificar que o banco não possui dados operacionais persistidos.
- Registrar baseline atual de testes e métricas.
- Confirmar se a implementação da política candidata está atrás de flags/overrides ou já se tornou comportamento padrão.

**Gate M0:** estado reproduzível, mudanças preexistentes preservadas, documentação de checkpoint e ausência de divergência estrutural desconhecida.

## 5. Marco M1 — Homologar o abastecimento

**Objetivo:** escolher uma política operacional coerente e sustentável, não simplesmente a variante com maior conversão.

Atividades:

- Reproduzir controle e candidata no mesmo código e seed.
- Garantir conservação exata do estoque inicial por SKU.
- Comparar política com e sem transferências automáticas.
- Verificar se as transferências justificam complexidade adicional.
- Documentar prior de cold start, cobertura, segurança, lead times e inbound.
- Garantir que previsão utilize somente histórico disponível no instante.
- Preservar FIFO, 14 dias, cancelamentos parciais e refunds.
- Avaliar ruptura, vendas perdidas, estoque ocioso e compras.
- Investigar a expansão da fila de eventos e medir memória.
- Escolher parâmetros determinísticos explícitos no profile.

**Gate M1:** política oficialmente configurada, causal, reproduzível, com conservação física/financeira e sem piora operacional relevante não justificada.

A escolha de parâmetros técnicos dentro das regras aprovadas pode ser feita pelo executor. Mudanças de regra comercial precisam de aprovação.

## 6. Marco M2 — Calibrar o Portfolio

**Objetivo:** produzir 120.000 pedidos aceitos, com distribuições coerentes.

### 6.1 Pedidos e intenções

Manter contadores separados:

- Intenções planejadas.
- Intenções processadas.
- Pedidos aceitos.
- Intenções recusadas.
- Motivos de recusa.
- Unidades de demanda perdida.
- Tentativas restantes.

O alvo de 120.000 refere-se exclusivamente a pedidos efetivamente criados.

Utilizar geração determinística com limite explícito de tentativas.

Não duplicar intenções previamente recusadas, criar pedidos retroativos nem produzir eventos após o cutoff.

### 6.2 Distribuição anual

Faixas:

- 2023: 20–26 mil.
- 2024: 25–32 mil.
- 2025: 32–40 mil.
- Jan–Set/2026: 27–34 mil.

Aplicar quotas sobre pedidos aceitos, respeitando cronologia e sazonalidade.

Preservar Black Friday de 2023, 2024 e 2025; dezembro mais forte; janeiro mais fraco.

Não gerar Black Friday 2026, pois o cutoff ocorre em setembro.

### 6.3 Canais

Distribuição sobre pedidos aceitos:

- Físico: 50–55%.
- E-commerce: 25–32%.
- Marketplaces combinados: 15–22%.

Não renormalizar os resultados silenciosamente após recusas físicas.

Planejar as intenções por período e canal para alcançar a composição de pedidos aceitos, mantendo as recusas como resultado real da simulação.

Verificar que quotas anuais, mensais e por canal sejam compatíveis.

### 6.4 Clientes e recorrência

Preservar PF/PJ conforme regras aprovadas.

Segmentar a população identificada em frequências de compra plausíveis:

- 1 pedido: 35–50%.
- 2–4 pedidos: 30–40%.
- 5–10 pedidos: 10–18%.
- 11+ pedidos: 2–6%.

Usar como denominador clientes identificados elegíveis com compras, conforme o contrato vigente.

Não incluir pedidos anônimos na recorrência.

Preservar maior frequência média para PJ.

### 6.5 Pagamentos

Calibrar probabilidades por canal sem violar elegibilidade operacional.

Referências:

- Cartão: 35–50%.
- Pagamento instantâneo: 30–45%.
- Dinheiro: 8–18%.
- Demais métodos: residual coerente.

Preservar retries, pagamentos divididos, parcelamentos e refunds.

### 6.6 Estados e margem

Referências do Portfolio:

- Completed: 93–97%.
- Cancelled: 2–5%.
- Pending: 0–3%, justificados operacionalmente.

`completed` inclui obrigações comerciais encerradas legitimamente após cancelamento parcial e estorno.

Margem bruta operacional: 8–28%.

Receita líquida realizada e COGS devem utilizar o mesmo conjunto de unidades, considerando descontos, cancelamentos, returns e custo do ledger.

Não alterar preços/custos antes de identificar a causa de eventual desvio de margem.

**Gate M2:** todos os critérios comerciais e financeiros aprovados passam em uma auditoria lógica consistente. Nenhum intervalo é relaxado automaticamente.

## 7. Marco M3 — Auditoria lógica integral e desempenho

**Objetivo:** validar o Portfolio completo antes de qualquer nova tentativa persistente.

Atividades:

- Usar geração incremental e sink descartável/agregador.
- Evitar materializar milhões de registros em memória.
- Validar o contrato do auditor lógico contra resultados SQL em fixture reduzida.
- Executar ensaios progressivos com métricas comparáveis.
- Medir duração, memória, eventos agendados, filas e estados ativos.
- Verificar determinismo entre execuções e batch sizes.
- Executar auditoria lógica de 120.000 pedidos efetivamente aceitos.
- Verificar todas as distribuições do profile.
- Validar stock, lifecycle, refund, cancelamentos e custos.
- Produzir relatório de PASS/WARNING/FAIL para todos os gates.

A auditoria integral deve abortar com diagnóstico se alcançar o limite de tentativas sem atingir 120.000 pedidos aceitos.

**Gate M3:** 120.000 pedidos aceitos; zero erros lógicos críticos; zero falhas distribucionais; comportamento de memória e tempo aceitável e documentado.

## 8. Marco M4 — Homologação PostgreSQL com rollback

**Objetivo:** provar que o resultado calibrado pode ser persistido pelo sink oficial.

Atividades:

- Confirmar migrations 001–003 e 41 tabelas.
- Executar suites unitárias e integrações.
- Executar fixtures PostgreSQL de escala progressiva, inicialmente 10k e 50k pedidos aceitos, conforme custo e necessidade demonstrada.
- Usar transação única por fixture, `ANALYZE` e validações nomeadas.
- Verificar cancelamentos parciais, refunds, pagamentos, transferências, estoque e médias móveis.
- Executar controles negativos para invariantes críticas.
- Verificar ciclo de vida dos IDs transitórios.
- Fazer `ROLLBACK` de cada fixture.
- Confirmar zero linhas nas 41 tabelas em nova conexão.

Não alterar schema sem autorização.

**Gate M4:** integrações e validações aprovadas; banco estruturalmente correto e vazio; evidência suficiente para propor o COMMIT Portfolio.

## 9. Marco M5 — Carga definitiva e baselines

**Objetivo:** persistir o Portfolio validado e preparar sua exploração analítica.

O usuário concedeu autorização controlada para uma única tentativa adicional de COMMIT após a falha de lifecycle anterior. Essa tentativa foi executada em 2026-10-10 e consumiu a autorização. O resultado final está registrado no checkpoint de execução ao fim deste documento e em `docs/data-generation/portfolio-validation.md`.

Após autorização:

1. Confirmar preflight estrutural e banco vazio.
2. Executar uma única transação para master e transações.
3. Executar `ANALYZE` e todas as validações críticas.
4. Executar o gate distribucional no PostgreSQL.
5. Fazer `COMMIT` somente com zero falhas críticas e distribucionais.
6. Verificar os dados persistidos em nova conexão somente leitura.
7. Gerar e executar os baselines SQL.
8. Documentar volumes, finanças, estoque, custos, margens e períodos.
9. Atualizar o relatório final e o README.

Baselines esperados: controle total, vendas, meses, canais, lojas, categorias, produtos, clientes, pagamentos, devoluções, estoque, margem e YoY/YTD.

Não reproduzir fanout ao juntar várias tabelas fato.

Após o COMMIT, não executar testes que dependam de banco vazio na mesma database e nunca resetar a base para contornar falhas.

**Gate M5: PASS.** Dataset persistido e verificado, 120.000 pedidos aceitos, 13 baselines aprovados e reconciliados, documentação final e zero divergências críticas ou distributivas. `M5 PERFORMANCE READY` foi apenas o gate de desempenho anterior à carga; não deve ser confundido com a conclusão desta fase.

## 10. Marco M6 — Preparação analítica e transição para Power BI

**Objetivo:** permitir começar a modelagem BI com segurança.

Atividades:

- Inventariar as entidades analíticas das 41 tabelas.
- Identificar fatos e dimensões candidatos.
- Documentar chaves, granularidade e cardinalidade.
- Diferenciar pedidos, itens, fulfillment, pagamentos, refunds, returns e cancelamentos.
- Definir métricas de negócio em linguagem neutra.
- Identificar relações potencialmente ambíguas e fanouts.
- Preparar consultas exploratórias e amostras verificáveis.
- Documentar política temporal para 2026 YTD.
- Preparar orientação de conexão do Power BI ao PostgreSQL com acesso somente leitura.
- Registrar limitações e decisões que devem ser tomadas durante a modelagem.

Este marco não autoriza criação automática do modelo semântico definitivo nem medidas DAX. Essas decisões continuam reservadas à fase BI.

Parte do trabalho documental e exploratório de M6 pode ocorrer em paralelo a M2–M4, desde que não dependa de dados persistentes ainda inexistentes.

**Gate M6:** fontes, métricas candidatas, contratos de granularidade e consultas de referência disponíveis para iniciar Power BI.

## 11. Uso de subagentes

O agente principal mantém responsabilidade exclusiva por decisões integradas, estado Git, gates e resultados finais.

Delegar atividades independentes quando houver ganho real:

- **Banco e invariantes:** inspeção do schema, SQL, constraints e validações.
- **Gerador e performance:** perfil, escala, determinismo e memória.
- **Distribuições e qualidade:** métricas comerciais e auditor lógico.
- **Documentação e BI:** plano, dicionário analítico e baselines preparatórios.

Não executar múltiplas mutações concorrentes sobre os mesmos arquivos.

Não permitir duas cargas PostgreSQL simultâneas.

Subagentes devem entregar diagnóstico, testes propostos e alterações delimitadas. O principal integra e valida.

Usar apenas subagentes disponíveis e compatíveis com `AGENTS.md` e `.codex/`.

## 12. Segurança e versionamento

- Preservar a working tree inicial.
- Proibir operações Git destrutivas.
- Permitir commits Git locais por marcos somente quando a instrução de execução os autorizar explicitamente.
- Não executar push, merge ou tags automaticamente.
- Nunca incluir `.env`, credenciais, `.venv`, dumps ou dados privados.
- Não executar `DROP`, `TRUNCATE`, `DELETE` ou reset operacional.
- Não aplicar migration fora do escopo.
- Não fazer COMMIT PostgreSQL de carga Portfolio sem autorização.
- Não enfraquecer validações para atingir métricas.

## 13. Condições de parada

Interromper e solicitar decisão quando:

1. For necessária alteração de regra de negócio aprovada.
2. For necessária migration adicional não autorizada.
3. Houver risco de perda ou corrupção de dados persistidos.
4. Uma solução exigir relaxar gates críticos.
5. A mesma causa permanecer sem progresso após investigação e tentativas razoáveis.
6. For necessário o primeiro COMMIT permanente do Portfolio.
7. Houver conflito de autoridade documental ou instruções de agentes.

Não interromper a execução apenas por falha corrigível de teste, bug ou diferença de distribuição cujo ajuste já esteja autorizado.

## 14. Registro de progresso

Manter no próprio documento ou arquivo auxiliar:

- Marco atual.
- Subtarefas concluídas.
- Gates aprovados.
- Bloqueios ativos.
- Tentativas e causas.
- Último checkpoint válido.
- Testes realizados.
- Próxima ação.
- Commits locais associados.

Não reescrever o histórico para esconder falhas anteriores.

## 15. Critério final

O objetivo completo será alcançado quando:

- A Fase 3E.2 estiver concluída.
- Os 120.000 pedidos Portfolio estiverem confirmados e validados.
- As 41 tabelas tiverem os dados esperados.
- Todas as conciliações críticas estiverem corretas.
- Baselines SQL estiverem executados e reconciliados.
- A documentação do dataset estiver completa.
- O ProjetoBI estiver pronto para iniciar o trabalho no Power BI.

**Status final esperado: `PROJECTBI READY FOR POWER BI`.**

## 16. Registro de execução

### Checkpoint M0 — 2026-10-08

- **Status:** PASS. Estado Git, documentação de negócio, configuração do gerador, CLI, migrations, testes e estado atual do PostgreSQL foram inspecionados; as mudanças locais acumuladas foram preservadas.
- **Git:** branch `main`, HEAD inicial `2a876f06eb8d40fe8459ba6a5e0e2486b70d234c`. Na entrada havia 29 arquivos versionados modificados e 19 não rastreados, sem staging. `git diff --check` não apresentou erros. O `.env` existe, está ignorado por `.gitignore` e não é rastreado; `.env.example` contém apenas variáveis vazias.
- **Ambiente:** Python 3.13.15, pytest 8.4.2, gerador 0.1.0/configuração 1. A execução `full --profile portfolio --plan` informa 219.009 linhas mestre, alvo configurado de 120.000 pedidos, 264.000 itens estimados e 2.200.000 linhas transacionais estimadas; confirma que não gerou dados, não conectou ao banco e não persiste.
- **PostgreSQL (somente leitura):** conexão em `BEGIN READ ONLY`; database `projeto_bi`, servidor 18.6, 9 schemas, 41 tabelas aprovadas e 0 linhas operacionais. A guarda estrutural validou a estrutura correspondente às migrations 001–003. A transação foi revertida.
- **Testes de referência:** `113 passed, 6 skipped` em 20,64 s. Os seis skips são as integrações PostgreSQL condicionais. A integração candidata 10k descrita no relatório da Fase 3E.2c.4 passou em 150,50 s, com `ROLLBACK` e verificação independente de 41 tabelas vazias.
- **Documentação reconciliada:** resumo do README atualizado sem declarar o Portfolio completo. `generation-plan.md` permanece como artefato histórico da Fase 3A; seus números de 40 tabelas e status antigos não descrevem o schema vigente.
- **Divergência funcional crítica identificada para M2:** o CLI `--plan` expõe `sales_orders=120000`, porém `generate_full_transactions_incremental` percorre esse valor como número de intenções; em 10.000 intenções foram aceitos 8.529 pedidos na candidata. O alvo semântico do plano é 120.000 pedidos aceitos. O calibrador deverá separar intenções processadas, aceitos e recusados e impor limite determinístico de tentativas.
- **Risco de persistência:** `full --profile portfolio --commit` executa `COMMIT` PostgreSQL. O comando não foi executado. M5 permanece `WAITING APPROVAL`; o primeiro COMMIT permanente só ocorrerá após autorização explícita.
- **Limitações conhecidas:** memória ainda não foi medida; a política de abastecimento permanece experimental e M1 deverá comparar com/sem transferências antes de configurar a candidata oficial. M2–M4 não estão homologados.
- **Próximo passo:** M1 — reproduzir comparações de abastecimento, medir memória e fila, escolher configuração técnica dentro das bandas aprovadas e registrar a decisão sem alterar regras comerciais.

### Checkpoint M1 — 2026-10-08

- **Status:** PASS. Profile Portfolio homologado tecnicamente com bootstrap 65% para lojas, reposição por cobertura ligada, segurança 3× e transferências automáticas da política desligadas. As 12 transferências estruturais configuradas permanecem separadas dessa flag.
- **Evidência de política:** matriz controlada de 10.000 intenções, mesma seed/código e mesmo digest de intenções em todas as variantes; conservation do estoque inicial por SKU confirmada. Safety 3 foi escolhido frente a safety 2 (19 aceitos adicionais, 56 unidades perdidas a menos, 3 pedidos a menos no cutoff; custo adicional de 8.677 unidades ordenadas e redução de 326.729,73 dias/1.103 episódios de ruptura). Safety 4 foi rejeitado pelo ganho marginal frente ao custo adicional. Transferências automáticas foram desligadas por desempenho ligeiramente pior e economia de apenas 46 unidades de procurement no teste safety 2.
- **Escala/memória:** em 25.000 intenções com sink descartável, bootstrap 65% levou 95,93 s e teve pico incremental Python de 44,2 MiB; cobertura safety 3 levou 107,06 s e pico de 34,1 MiB. Ambos limitaram batches a 5.000 e fila a 11.496 eventos. Estados ativos, pedidos e backorders foram medidos; detalhes estão em `docs/data-generation/validation-report.md`.
- **Validação:** configuração coberta por teste unitário; suíte atual: 114 passed/6 skipped em 21,84 s. A integração PostgreSQL da candidata safety 2 + transferências repetiu e passou em 504,78 s com rollback e 41 tabelas vazias. A integração específica do perfil M1 fica para o M4.
- **Git:** working tree acumulada preservada. Sem commit nesta subfase conforme instrução explícita da Fase 3E.2c.4; sem push.
- **Limitações:** o resultado 25k é diagnóstico de desempenho, não confirma as distribuições comerciais de 120k. A variante oficial ainda não foi executada em PostgreSQL; isso está planejado em M4.
- **Próximo passo:** M2 — separar alvo de pedidos aceitos de intenções e calibrar volumes anuais/canais/clientes/pagamentos sem alterar as faixas aprovadas.

### Checkpoint M2 — execução Portfolio descartável (2026-10-09)

- **Execução final:** profile Portfolio, seed `20261005`, meta de 120.000 pedidos aceitos, gerador incremental e sink de agregação/descarte. Não conectou ao PostgreSQL nem persistiu linhas. Duração transacional 110,68 s, master 1,61 s, 4.350.830 linhas encaminhadas ao sink, batch máximo 5.000 e fila máxima 11.496 eventos.
- **Pedidos/tempo/canais:** exatamente 120.000 aceitos; 176.292 intenções processadas, 214.604 planejadas, 38.312 puladas por quota preenchida e cap de tentativas 230.000. Quotas realizadas: 2023 24.000 (20%), 2024 30.000 (25%), 2025 36.000 (30%) e jan–set/2026 30.000 (25%). Mix anual de canal foi exatamente o configurado: físico 54/53/52/50%; e-commerce 29/29/29/31%; marketplaces combinados 17/18/19/19%. Sem novembro de 2026.
- **Distribuições:** 116.305 completed (96,92%), 3.265 cancelled (2,72%) e 430 confirmed no cutoff (0,36%); canais totais físico/e-commerce/marketplace 52,15/29,50/18,35%; anonimato físico 31,69%. Recorrência PF: 42/38/16/4% e PJ: 25/45/25/5% nas quatro faixas; média PJ 4,0779 pedidos versus PF 3,2446. Cartão/instantâneo/dinheiro/transferência 48,08/42,96/8,19/0,76%; descontos 38,74%, incidência Black Friday 54,69% versus 37,27% nos demais meses; pedidos completed com devolução 5,95%; participação de receita completed PJ 19,12%; ticket médio PJ/PF 1,6944×.
- **Financeiro — regra aprovada pelo usuário e aplicada:** preservar COGS original nos movimentos fulfillment; deduzir da margem apenas o custo histórico das devoluções `sellable` reintegradas; identificar `non-sellable` como perda que permanece incluída no COGS analítico. Benchmark: receita BRL 922.588.975,44; COGS original BRL 725.466.564,62; reversão vendável BRL 8.010.914,36; COGS analítico BRL 717.455.650,26; perda não vendável identificada BRL 12.296.704,23; margem 22,23%. Reconciliação fecha ao centavo e a margem está dentro de 8–28%.
- **Reconciliação financeira:** COGS completed original BRL 725.466.564,62 menos reversão sellable BRL 8.010.914,36 = COGS analítico BRL 717.455.650,26. Perda non-sellable BRL 12.296.704,23 é um subconjunto do COGS analítico mantido e não foi abatida novamente.
- **Gate M2: PASS.** Quotas mensais/canais e alvo aceito conferidos célula a célula; classificador Portfolio reportou zero falhas críticas, zero falhas distribucionais e zero avisos. Receita, COGS, reversão e perda reconciliados conforme a regra aprovada.

### Checkpoint M3 — auditoria/replay Portfolio 120k (2026-10-09)

- **Quotas e distribuições:** 120.000/120.000 aceitos; 0 células mensais por canal divergentes; classificador Portfolio: 0 critical fails, 0 distributional fails, 0 warnings. A suíte de memória completa passou 117 testes e 6 integrações PostgreSQL ficaram ignoradas por opção de execução.
- **Replay independente de estoque:** 675.382 eventos reproduzidos em ordem causal e média móvel; 13.837 posições em 1.000 SKUs; 11.949 unidades iniciais; saldo final 10.089 unidades físicas/disponíveis; zero posições com divergência em quantidade, reserva ou custo médio; zero saldo disponível final sem demanda. Rupturas agregadas: 7.342.024,68 dias-item e 166.369 episódios.
- **Performance/memória:** auditoria descartável com replay, sem tracemalloc: 113,19 s de transações e 1,61 s de master; batch máximo 5.000; 11.496 eventos pendentes no pico; 745 pedidos ativos e 609 backorders ativos no pico, sem estados ativos após encerramento. Medição final com tracemalloc da versão que inclui o auditor lógico: 662,81 s, pico de heap Python 923,64 MiB e heap corrente 515,98 MiB. O working set observado em amostra chegou a pelo menos 2,35 GiB; não é um medidor de pico do processo.
- **Auditoria lógica descartável:** 9 de 9 gates passaram nos 120k: totais de item/desconto; fulfillment/cancelamentos; parcelas; pagamentos/refunds; returns contra fulfillment original; lifecycle de eventos logísticos; links/valores de refunds; COGS analítico e perda sem dupla contagem; pares de movimentos de transferências. Sink reteve agregados de 120.000 pedidos, 241.637 itens, 237.742 linhas de fulfillment, 127.380 pagamentos e 7.129 itens de devolução; descartou as linhas relacionais após agregação. Resultado: zero divergências.
- **Fixture SQL reduzida:** 300 pedidos do profile smoke, PostgreSQL major 18. A geração streaming independente teve contagens idênticas às do fixture PostgreSQL; 39 checks SQL ficaram em zero; os cinco agregados financeiros (receita, COGS original, reversão vendável, perda não vendável e COGS analítico) coincidiram com o baseline SQL; nove gates lógicos passaram; `ROLLBACK` e nova conexão confirmaram zero linhas nas 41 tabelas. Duração da fixture 2,55 s.
- **Determinismo:** teste entre batch sizes 73 e 127 passou, comparando integralmente as linhas coletadas e as contagens. M3: PASS. A medição de memória é documentada como alta e deve ser considerada ao planejar escalas de persistência; o sink continua descartável.
- **Próximo naquele checkpoint:** M4 — fixtures PostgreSQL rollback-only para 10.000 e 50.000 pedidos aceitos. O checkpoint M4 abaixo registra a conclusão dessas verificações; M5 continua aguardando autorização explícita para COMMIT permanente.

### Checkpoint M4 — homologação PostgreSQL rollback-only (2026-10-09)

- **Status:** PASS. As fixtures Portfolio de 10.000 e 50.000 pedidos aceitos concluíram no PostgreSQL 18, cada uma em transação única com `ANALYZE`, validações e `ROLLBACK` explícito.
- **Fixture 10k:** 10.000 pedidos; 341.396 linhas transacionais; 39 invariantes SQL sem falhas; 41 tabelas vazias verificadas após rollback; duração 466,99 s. Os controles negativos rejeitaram cancelamento acima da quantidade elegível e validaram refund dividido em pagamentos, dentro de savepoints revertidos.
- **Fixture 50k:** 50.000 pedidos; 1.454.848 linhas transacionais; 39 invariantes SQL sem falhas; zero IDs transacionais retidos; 41 tabelas vazias verificadas após rollback; duração 8.597,54 s. O cenário teve 53.082 pagamentos, 81.993 parcelas, 3.022 refunds, 2.992 returns, 163.833 movimentos de estoque e 217.220 eventos logísticos.
- **Conciliação financeira SQL 50k:** receita líquida de fulfillments completed BRL 385.445.464,80; COGS original de fulfillment BRL 302.895.054,13; reversão dos custos de returns `sellable` BRL 3.313.558,21; COGS analítico BRL 299.581.495,92; perda `non-sellable` identificada BRL 5.076.322,25. O COGS original permanece no ledger; a perda `non-sellable` é subconjunto do COGS analítico, sem dedução dupla.
- **Estado do banco:** verificação independente após a conclusão, em conexão nova, confirmou 41 tabelas, zero tabelas não vazias e zero linhas operacionais. Nenhuma carga Portfolio foi commitada.
- **Próximo:** M5 aguarda autorização explícita para o primeiro `COMMIT` permanente. Nenhuma persistência, baseline dependente de dados ou trabalho no Power BI foi iniciado.

### Checkpoint M6 — prontidão analítica documental (2026-10-09)

- **Status:** PASS documental. O inventário cobre 41 entidades e suas granularidades/PKs; registra fatos e dimensões candidatos, métricas neutras, relações temporais, fanouts, política de margem, datas locais e limites do snapshot corrente.
- **Consultas:** quatro SELECTs de referência em `database/queries/powerbi_readiness/` foram executados dentro da fixture smoke PostgreSQL de 300 pedidos: 300 linhas em pedido, 17 grupos de margem canal/categoria, 2 anos na consulta YTD e 35 posições correntes; 23, 10, 8 e 13 colunas. Os 39 invariantes SQL passaram; `ROLLBACK` e nova conexão confirmaram 41 tabelas vazias. A inspeção de schema separada foi `READ ONLY`; nenhuma linha permaneceu persistida.
- **Fonte verificada:** PostgreSQL 18, 9 schemas, 41 tabelas, 72 FKs e zero linhas operacionais em inspeção somente leitura. Uma amostra de métricas financeiras 50k rollback-only foi documentada com a conciliação M4, sem apresentá-la como dado persistido.
- **Limites:** não foram criados usuário/role nem privilégios; a orientação read-only está documentada. Não foi criado PBIP, modelo semântico, Power Query, DAX ou relatório.
- **Gate M6: PASS para iniciar a futura modelagem.** M5 continua à espera da autorização explícita do usuário para o primeiro COMMIT definitivo.

### Preflight M5 — pronto, sem persistência (2026-10-09)

- **Configuração/alvo:** carregamento local de configuração sem expor credenciais; a conexão read-only confirmou database `projeto_bi`, PostgreSQL major 18, 9 schemas, 41 tabelas, guard estrutural PASS e zero linhas.
- **Plano sem escrita:** `python -m projectbi_generator.cli full --profile portfolio --plan` retornou alvo de 120.000 pedidos aceitos, 219.009 linhas mestre estimadas, 2.200.000 linhas transacionais estimadas e batch 5.000; `database_connected=false`, `generated=false` e `persistent_write=false`.
- **Revisão do caminho de persistência:** o CLI só aceita `--commit` com profile Portfolio; `run_portfolio_commit` revalida estrutura e vazio em conexão read-only e em uma única transação, executa validações críticas/distribucionais antes do COMMIT e verifica a base em nova conexão read-only depois. A criação/execução dos 13 baselines ocorre após o COMMIT.
- **Baselines pré-validados sem persistência:** os 13 SQLs oficiais foram executados dentro de fixture smoke de 300 pedidos; 00 retornou 41 tabelas, 11 reconciliou COGS, reversão vendável, perda não vendável e margem, 12 trouxe 2025/2026, e os cinco critérios de reconciliação do validador passaram. A fixture passou 39 invariantes e reverteu todas as linhas. Os arquivos definitivos de baseline continuam destinados à etapa M5 depois do COMMIT.
- **Correção preventiva de M5:** essa execução encontrou `sales_order_id` ambíguo na métrica pré-COMMIT `margin_return_costs`; a junção agora declara `o.sales_order_id=ri.sales_order_id`. Também foi atualizado o rótulo do resultado do baseline de controle de 40 para 41 tabelas. O novo teste de integração para os 13 baselines passou em 11,79 s. Suíte local: 117 passados e 7 integrações condicionais ignoradas.
- **Gate de autorização:** nenhum comando `--commit` foi executado. A verificação `--plan` não gerou dados; a fixture smoke usada para validar as consultas existiu somente na transação rollback-only. Nenhum dado Portfolio foi persistido, staged ou publicado. O plano para no M5, aguardando autorização explícita para iniciar a carga definitiva.

### Checkpoint M5 — diagnóstico final de desempenho/capacidade (2026-10-09)

- **Causa reproduzida:** `_write_stock` executava `UPDATE inventory.stock_positions` e `INSERT inventory.stock_movements` de forma individual para cada evento de estoque. Na fixture 10k, isso somou 76.565 comandos de update (120,35 s) e 41.968 inserts individuais (40,78 s). O backend PostgreSQL atingiu 74–102% de um núcleo, sem wait event; Python ficou entre 0–34% e a I/O observada permaneceu abaixo de 1 MiB/s. A migration 003 também atualiza `sales_order_items` por trigger para cada `fulfillment_item`: 20.205 itens e 20.206 updates contabilizados no teste, com 32,40 s antes da correção e 9,84 s depois; esse comportamento é necessário à integridade e não foi alterado.
- **Correção:** o sink agora mantém o estado causal em memória durante cada lote, insere `stock_movements` em lote na ordem original e atualiza cada posição tocada uma vez por lote. Em database vazia, a criação inicial da posição retorna também seus valores, evitando um `SELECT ... FOR UPDATE` adicional; colisões continuam fazendo o `SELECT ... FOR UPDATE`. Nenhuma migration, constraint, regra comercial ou seed foi alterada.
- **Medição comparável 10k:** o probe anterior à correção fechou em 374,08 s (351,28 s geração transacional, 345,34 s em `consume`, 176,99 s em `_write_stock`, com partes sobrepostas). Após batch writes, fechou em 131,77 s: queda de 64,8%; 109,53 s geração transacional, 5,79 s fora do sink, 103,74 s em `consume`, 39,51 s no writer de estoque, 1,83 s `ANALYZE` e 1,45 s validações SQL. O sink passou de 155.527 para 53.024 round trips aproximados. 1.412 flushes, batch máximo 5.000, 341.396 linhas relacionais e 0 IDs transitórios ao final.
- **Validação de dados:** a fixture 10k pós-correção passou os 39 invariantes, terminou com `ROLLBACK` e confirmou zero linhas nas 41 tabelas em conexão nova e numa conferência independente. O smoke PostgreSQL de 300 pedidos passou após a otimização adicional de `_position`; digest do gerador e os cinco agregados oracle permaneceram aprovados. A suíte completa passou 117 testes; 7 integrações condicionais foram ignoradas na execução sem a flag de integração.
- **Capacidade observada:** durante a fixture, RAM livre ficou aproximadamente entre 7,36 e 8,16 GiB de 15,87 GiB; working set privado Python ~155 MiB e backend PostgreSQL ~20 MiB; pagefile manteve ~292 MiB usados (26 GiB alocados). O volume D tinha 385,39 GiB livres. PostgreSQL 18.6: database 332 MB, diretório WAL 621 MB/37 arquivos ao final; o WAL emitido pelo probe otimizado foi 323.406.408 bytes incluindo master e transações. `max_wal_size=1 GiB` é limite brando; espaço disponível é suficiente, embora checkpoints possam afetar duração. `track_io_timing=off` e `pg_stat_statements` ausente limitam a atribuição de latência física/por query; os tempos por chamada vieram da instrumentação temporária do cliente e amostras WMI do processo.
- **Projeção/limites:** a simples multiplicação do 10k otimizado projeta ~26 minutos para 120k, antes de variação por maior volume, validação pós-COMMIT e baselines; use apenas como ordem de grandeza, sem garantia. Os 50k/120k não foram executados após a correção por limite desta etapa. A evidência de CPU/memória/disco é suficiente para `M5 PERFORMANCE READY`, com monitoramento contínuo na futura carga única.
- **Estado naquele checkpoint:** nenhum `--commit`, migration ou escrita permanente havia sido executado; a autorização inicial ainda não estava consumida. Esse checkpoint cobria apenas desempenho/capacidade. A retomada e a segunda tentativa autorizada estão registradas abaixo e no relatório de validação.

### Estado dos marcos

| Marco | Status | Evidência/pendência |
|---|---|---|
| M0 — estado técnico | PASS | Checkpoint acima; schema e banco atuais verificados. |
| M1 — abastecimento | PASS | Profile técnico configurado; trade-offs, transferências, conservação e medição incremental documentados. |
| M2 — calibrar Portfolio | PASS | Alvo 120k, quotas mensais/canais, bandas de negócio e reconciliação da margem passaram em 2026-10-09. |
| M3 — auditoria lógica/escala | PASS | Quotas, distribuições, replay, 9 gates lógicos em 120k, determinismo entre batches e comparação com 39 checks SQL em fixture reduzida passaram. Pico heap Python medido em 923,64 MiB; working set observado em amostra >=2,35 GiB. |
| M4 — PostgreSQL rollback | PASS | Fixtures 10k e 50k, 39 invariantes SQL por fixture, controles negativos de cancelamento/refund e confirmação independente das 41 tabelas vazias passaram. |
| M5 — persistência/baselines | PASS | COMMIT único em 2026-10-10; 120.000 pedidos, 41 tabelas conferidas em nova conexão read-only, zero falhas críticas/distributivas e 13 baselines SQL reconciliados. Ver `docs/data-generation/portfolio-validation.md`. |
| M6 — preparação analítica | PASS | Inventário, grãos, fatos/dimensões candidatos, métricas, política temporal, precauções de fanout e quatro consultas executáveis documentados. |
| Fase 4.0 — backup e preparação PBIP/TMDL | PASS documental | Backup lógico custom verificado em `D:\Backups\ProjetoBI`; hash, limites de verificação, estrutura PBIP proposta e pendências analíticas estão documentados. Nenhum projeto Power BI foi criado. |
| Fase 4.1 — projeto inicial PBIP/TMDL/PBIR | PASS | Desktop 2.158.1177.0 gerou `powerbi/ProjetoBI.pbip`; o modelo usa TMDL, o relatório usa PBIR, o projeto foi reaberto e não contém tabelas nem conexão. Detalhes em `docs/powerbi/phase-4.1-initial-project.md`. |
| Fase 4.2 — conexão e fundação do modelo | PASS | Role read-only validada, sete fontes importadas e reconciliadas, PBIP salvo/reaberto e refresh concluído. Ver `docs/powerbi/phase-4.2-connection-and-model-foundation.md`. |
| Fase 4.3 — modelo estrela comercial | PASS | Refresh/reabertura no Desktop; 120.000 pedidos, 241.637 itens, dimensões e calendário reconciliados; filtros por ano, canal e categoria e preservação de membro em branco verificados. Ver `docs/powerbi/phase-4.3-commercial-star-model.md`. |
| Fase 4.4 — medidas DAX comerciais | PASS | 28 medidas em `FatoPedidos` e `FatoItensPedido`; erros DAX/TMDL zerados no mecanismo local, reconciliações comerciais e YTD aprovadas, refresh e reabertura sem erro. Ver `docs/powerbi/phase-4.4-commercial-dax-measures.md`. |
| Fase 4.5A — centralização das medidas | PASS | 28 medidas movidas para `_Medidas`, validação TMDL/DAX aprovada, confirmação visual das sete pastas e ciclo salvar/fechar/reabrir concluídos sem erro. Ver `docs/powerbi/phase-4.5a-measures-centralization.md`. |
| Fase 4.5A.1 — formatação DAX em TMDL | BLOCKED | O Desktop reformatou oito expressões simples para a mesma linha da declaração ao salvar; ver `docs/powerbi/phase-4.5a1-dax-formatting.md`. |
| Fase 4.5A.1 — regularização da serialização nativa | PASS | O commit `74ca3be` registra apenas as oito normalizações de formatação do Desktop; as 28 medidas e seus metadados foram verificados equivalentes. |
| Fase 4.5B — fundação financeira e de devoluções | PASS | Grãos e relações validados; grants mínimos, refresh e reabertura aprovados; somas `Int64` escaladas, amostras por canal/categoria/período e regressão comercial reconciliadas SQL × DAX. Nenhuma medida financeira definitiva foi criada. Ver `docs/powerbi/phase-4.5b-financial-model-foundation.md`. |
| Fase 4.5C — medidas DAX financeiras e margem analítica | PASS | 27 medidas novas (55 no total), refresh Desktop, erro DAX zero, persistência, fechamento e reabertura sem erro; reconciliações PostgreSQL × DAX por 1.000 produtos, 144 combinações canal/categoria/ano, 45 meses, destinos, datas operacionais/coorte e YTD passaram. Ver `docs/powerbi/phase-4.5c-financial-dax-measures.md`. |
| Fase 4.6 — auditoria integrada e working tree | PASS | 10 tabelas, 55 medidas em 11 pastas, 21 relações; validações SQL × DAX, filtros, datas e desempenho concluídas. Working tree inicial de 15 arquivos classificada e preservada, com plano seguro de regularização; dashboard não iniciado. Ver `docs/powerbi/phase-4.6-semantic-model-audit.md` e `docs/git/POWERBI_WORKTREE_AUDIT.md`. |
| Fase 4.6.1 — regularização PBIP e working tree | PARTIAL | Diagrama preservado, PBIP reaberto, estrutura (10 tabelas, 55 medidas, 11 pastas, 21 relações) e oito regressões DAX verificadas. Auto não persistiu (`queryLimitOption=None`); o Desktop reintroduziu linhas em branco finais nos 13 TMDLs aprovados e em `_Medidas.tmdl`. Ver `docs/git/POWERBI_WORKTREE_REGULARIZATION.md`. |
| Fase 4.6.2 — estabilização PBIP e serialização TMDL | PARTIAL | Os 14 TMDLs foram hash-estáveis após salvar/fechar/reabrir. `.gitattributes` limita a supressão de `blank-at-eof` aos TMDLs; testes confirmaram que espaços finais continuam detectáveis. Desktop 2.158.1177.0 abriu o modelo (10 tabelas, 55 medidas, 21 relações). A única tentativa de gravar `Auto` apareceu na interface, mas voltou a `No query limits` após reabrir; `report.json` foi restaurado ao original `None` e permanece fora dos commits. Naquele checkpoint, dashboards/publicação ainda não estavam autorizados. A Fase 5.1 autorizou desenvolvimento local; revisar os limites antes de publicar. A pendência não invalida o modelo semântico homologado. Ver `docs/git/POWERBI_WORKTREE_STABILIZATION.md`. |
| Fase 5.0 — identidade InfoTech e arquitetura dos dashboards | PASS | InfoTech Intelligence e Design System v0.1 definidos; matriz relaciona as cinco páginas a medidas existentes, dimensões, perspectivas temporais e riscos; tema JSON criado com propriedades documentadas no schema oficial publicado mais recente. Nenhuma página foi criada e o tema não foi aplicado ao PBIP. A Fase 5.1 permanece planejada, não iniciada. Ver `docs/powerbi/INFOTECH_DESIGN_SYSTEM.md`, `docs/powerbi/DASHBOARD_ARCHITECTURE.md` e `docs/powerbi/phase-5.0-dashboard-design.md`. |
| Fase 5.1 — Visão Executiva InfoTech | PARTIAL | Tema registrado e página PBIR montada em Full HD 1920×1080 com cabeçalho, filtros, quatro KPIs, tendência mensal, barras de canal e Top 5 categorias. O PBIR passa na validação estrutural local e os campos referenciam o TMDL vigente. A abertura e a presença dos componentes foram confirmadas pelo usuário; revisão visual detalhada, refresh/valores, filtros reais, reconciliação DAX, acessibilidade e Performance Analyzer aguardam validação no Desktop. O desenvolvimento local é permitido com `queryLimitOption=None`; revisar essa pendência antes de publicação. Ver `docs/powerbi/phase-5.1-executive-dashboard.md`. |

### Execução definitiva M5 — 2026-10-10

- **Checkpoint do código gerador:** `61aacc284f5e05b5c4922f1e676f5930d69ebe61` (`fix: corrige lifecycle de IDs PostgreSQL`); era o HEAD limpo e confirmado antes da execução. `.env` permaneceu ignorado e não foi incluído.
- **Carga única:** seed `20261005`, profile `portfolio`, 120.000 pedidos aceitos. O processo executou em uma transação, usou `ANALYZE`, validou invariantes críticas e gates distributivos antes do COMMIT. COMMIT concluído em 2026-10-10 06:17:06 (-03:00).
- **Volumetria:** 3.675.448 linhas transacionais inseridas e 846.799 updates; 1.546 flushes, batch máximo 5.000, 4.673.957 linhas recebidas do emissor, pico/final de IDs 11.614/0. As contagens totais persistidas nas 41 tabelas somam 3.894.457.
- **Qualidade pré e pós-COMMIT:** zero falhas críticas, zero falhas distributivas e zero warnings distributivos. As 39 invariantes SQL passaram; contagens, validações críticas e distribuição foram repetidas em nova conexão read-only.
- **Baselines:** os 13 SQLs em `database/queries/baselines/` executaram em conexão `READ ONLY`; todas as 41 contagens reconciliaram. Reconciliações de vendas/descontos, pagamentos/refunds, COGS canônico, reversão de custo apenas para devoluções sellable, perda non-sellable sem dupla contagem, margem e YTD passaram. Resultados detalhados estão em `docs/data-generation/portfolio-validation.md`.
- **Indicadores financeiros:** pedidos concluídos 116.305; receita líquida de produto BRL 949.319.764,19; capturado BRL 953.974.572,04; refunds concluídos BRL 26.727.257,07; COGS fulfillment canônico BRL 725.981.540,99143845; COGS analítico ajustado BRL 717.455.650,25964524; perda non-sellable identificada BRL 12.296.704,23413595; lucro bruto analítico BRL 205.133.325,18535476; margem 22,23%. Valores e definições completos constam no relatório.
- **Duração:** pipeline transacional 24.006,6 s; validações SQL pré-COMMIT 40,3 s; validação pós-COMMIT 32,7 s; baselines 38,75 s; total até pós-validação 24.098,2 s e total com baselines 24.136,9 s (aprox. 6h42). Pico de memória durante a carga não foi medido.
- **Resultado:** `M5 PASS — PROJECTBI READY FOR POWER BI`. Nenhum Power BI, PBIP, Power Query ou DAX foi iniciado. Não fazer nova carga Portfolio; a base já contém dados.
- **Checkpoint final de documentação/baselines:** registrado no commit local associado a esta execução; sem push.

### Fase 4.0 — backup definitivo e preparação PBIP/TMDL (2026-10-10)

- **Git de entrada:** branch `main`; commits `61aacc284f5e05b5c4922f1e676f5930d69ebe61` e `fb28dab69a9781072cf67837e0157ab26e2c414a` presentes; working tree limpa antes da fase; `.env` ignorado.
- **Origem somente leitura:** PostgreSQL 18.6, database `projeto_bi`, 9 schemas, 41 tabelas, migrations 001–003 confirmadas pelos guards estruturais e presença das colunas da migration 003; 120.000 pedidos e 3.894.457 linhas. Tamanho lógico observado: 1.193.948.863 bytes.
- **Backup:** `pg_dump` 18.6 em formato custom; exit code 0; 68.365.155 bytes; `pg_restore --list` exit code 0, 9 schemas e 41 entradas de dados de tabelas; SHA-256 `76C2AA25C02F8C70CA697E5AB5D5CBBD9BAFAA0A68EECE2E3018049B4CFA453D`. Local: `D:\Backups\ProjetoBI\ProjetoBI_projeto_bi_20261010T102821-0300.backup`.
- **Verificação posterior:** inspeção read-only repetiu 3.894.457 linhas e 120.000 pedidos. O catálogo do archive foi lido com sucesso, mas não se fez restore de teste nem se criou database de teste; recomenda-se uma cópia em unidade física independente.
- **Preparação analítica:** decisão documental por PBIP/TMDL e PBIR quando compatível, layout proposto e conjunto inicial de tabelas candidatas registrado. O Desktop não foi localizado na máquina; nenhum PBIP/TMDL incompleto foi criado. Credencial Power BI read-only separada segue pendente.
- **Entidades vazias:** cancelamentos por linha (0) e transferências/itens de transferência (0) documentados com seus limites analíticos. O relatório não permite provar qual guarda de elegibilidade/cutoff impediu as 12 transferências estruturais declaradas; não foram inventados dados nem alterada a base.
- **Documentação:** README, plano mestre, implementação do gerador, prontidão analítica e `.gitignore` atualizados. Veja `docs/database/backup-and-restore.md` e `docs/powerbi/phase-4.0-preparation.md`.
- **Próxima fase:** interromper aqui. A construção do projeto Power BI e qualquer acesso interativo permanecem para solicitação/aprovação específica.

### Fase 4.1 — projeto inicial PBIP/TMDL/PBIR (2026-10-12)

- **Git de entrada:** branch `main`, HEAD `bdfd009db6986ed1d955a9698bba368a90b02379` presente; working tree limpa antes da fase.
- **Desktop:** instalação local em `D:\Apps\Microsoft Power BI Desktop`; versão `2.158.1177.0` (ProductVersion `2.158.1177.0 (26.09)`). As opções PBIP, TMDL e PBIR já estavam habilitadas em Recursos de visualização; nenhuma configuração foi alterada.
- **Projeto gerado pelo Desktop:** `powerbi/ProjetoBI.pbip`, `powerbi/ProjetoBI.SemanticModel/` com definição TMDL e `powerbi/ProjetoBI.Report/` com definição PBIR. O modelo está vazio (zero tabelas); há uma página padrão em branco e nenhuma fonte/conexão de dados configurada.
- **Reabertura:** o PBIP foi aberto pelo próprio Desktop; a janela exibiu `ProjetoBI` e o painel Dados informou que nenhum dado foi carregado.
- **Preservação:** nenhuma conexão ao PostgreSQL, consulta ao banco, importação de tabelas, alteração de dados, credencial ou mudança no backup foi feita nesta fase. A referência documentada do banco permanece 120.000 pedidos e 3.894.457 linhas.
- **Versionamento/documentação:** `.gitignore` ignora `**/.pbi/` (cache e estado local) sem excluir definições PBIP/TMDL/PBIR. `powerbi/README.md` descreve o fluxo Desktop, VS Code e Codex. Ver `docs/powerbi/phase-4.1-initial-project.md`.
- **Limite:** esta fase não define modelo dimensional, consultas Power Query, medidas DAX ou dashboards; interromper após o checkpoint Git local desta fase.

### Fase 4.2 — conexão PostgreSQL e fundação do modelo analítico (2026-10-12)

- **Git de entrada:** branch `main`, HEAD `38740b36d77e32704e0a6186385a6fe0a469f004`; a worktree já continha quatro alterações locais em definições PBIR/TMDL, preservadas integralmente.
- **PostgreSQL:** conexão read-only confirmou `projeto_bi`, PostgreSQL 18.6, schemas previstos e role ausente antes da criação. `projetobi_pbi_ro` foi criada com atributos mínimos, CONNECT, USAGE em quatro schemas e SELECT somente nas sete tabelas da seleção comercial; sem CREATE em schemas ou privilégios de escrita nas tabelas. `default_transaction_read_only=on` é proteção complementar. A senha foi guardada somente no Windows Credential Manager.
- **Verificação independente:** login como a nova role, conexão à database correta, transação read-only, SELECT nas sete tabelas e verificação de cada privilégio efetivo passaram. Contagens: pedidos 120.000; itens 241.637; produtos 1.000; categorias 42; clientes 45.000; lojas 10; canais 4. Datas de pedido locais verificadas entre 2023-01-02 e 2026-09-29; pedidos sem cliente 19.829 e sem loja 57.420.
- **Power BI:** `PBIDesktop.exe` versão 2.158.1177.0 conectou a `projeto_bi` via PostgreSQL local, em modo Import. O usuário concluiu a autenticação no Desktop. As sete tabelas foram carregadas e salvas no PBIP; após ajuste das cinco colunas monetárias para Fixed decimal, o PBIP foi reaberto e atualizado. Consultas DAX no mecanismo local reconciliaram as contagens com o PostgreSQL: pedidos 120.000; itens 241.637; produtos 1.000; categorias 42; clientes 45.000; lojas 10; canais 4.
- **Arquitetura:** grãos, FKs confirmadas, proposta de fatos/dimensões, cardinalidades, direção de filtro, nulos, fanout e contratos M5 estão em `docs/powerbi/phase-4.2-connection-and-model-foundation.md`. O modelo dimensional e medidas continuam sem implementação.
- **Resultado:** Fase 4.2 concluída. A fundação inclui sete tabelas importadas, cinco colunas monetárias em Fixed decimal/Currency.Type, seis relações compatíveis com as FKs selecionadas e refresh/reabertura validados. A modelagem dimensional, calendário comercial, medidas DAX e relatórios ficam para fase posterior autorizada.
