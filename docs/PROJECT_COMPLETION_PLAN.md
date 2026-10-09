# ProjetoBI — Plano Mestre de Conclusão e Preparação para Power BI

**Status:** EM EXECUÇÃO — M0 concluído; próximo marco M1
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
- Nenhum dado operacional persistido após os testes relatados.

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

Última suíte sem integração: 113 aprovados, 6 ignorados. Integração PostgreSQL da candidata aprovada com rollback e 41 tabelas vazias.

### Pendências conhecidas

1. Homologar a política oficial de abastecimento.
2. Controlar 120.000 pedidos aceitos, distinguindo intenções e recusas.
3. Calibrar volumes anuais e sazonalidade.
4. Calibrar distribuição por canal.
5. Calibrar recorrência e segmentos PF/PJ.
6. Calibrar métodos de pagamento por canal.
7. Validar lifecycle, descontos, returns e margem após os ajustes.
8. Comprovar determinismo, performance e memória em escala.
9. Executar auditoria lógica integral sem persistência.
10. Executar integração PostgreSQL representativa com rollback.
11. Executar carga definitiva somente após autorização de persistência.
12. Criar baselines, validação final e preparar a entrada no Power BI.

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

Este marco exige autorização explícita para o primeiro COMMIT de dados Portfolio.

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

**Gate M5:** dataset persistido e verificado, 120.000 pedidos aceitos, baselines aprovados, documentação final e zero divergências críticas.

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

### Estado dos marcos

| Marco | Status | Evidência/pendência |
|---|---|---|
| M0 — estado técnico | PASS | Checkpoint acima; schema e banco atuais verificados. |
| M1 — abastecimento | IN PROGRESS | Matriz 10k experimental aprovada; ainda falta homologar a configuração e medir memória. |
| M2 — calibrar Portfolio | PLANNED | 120k aceitos e distribuições finais não executados. |
| M3 — auditoria lógica/escala | PLANNED | Falta auditoria dos 120k aceitos e memória. |
| M4 — PostgreSQL rollback | PLANNED | 10k intenções já passou para candidata; falta validar a configuração homologada e as escalas progressivas exigidas. |
| M5 — persistência/baselines | WAITING APPROVAL | Nenhuma carga persistente; exige autorização explícita para COMMIT. |
| M6 — preparação analítica | PLANNED | Pode iniciar trabalho documental independente sem ler dados persistentes. |
