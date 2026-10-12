# ProjetoBI

Projeto de Business Intelligence para estudo e prática, com foco em construir gradualmente um fluxo completo desde um sistema operacional relacional até relatórios analíticos.

## Objetivo

Criar um ambiente coerente para praticar integração de dados, transformação, modelagem semântica, métricas e visualização. O domínio será uma empresa fictícia do segmento de informática. Os detalhes do negócio e a modelagem são definidos em fases, com revisão antes da implementação.

## Visão geral da arquitetura

- **PostgreSQL** será a fonte de dados e representará o ecossistema operacional da empresa.
- **Python** implementa o gerador sintético determinístico de dados mestres e do ecossistema transacional no profile smoke.
- **Power BI** será a camada analítica, incluindo Power Query, modelo semântico, DAX e relatórios.
- **Git/GitHub** será usado para versionar o código, a documentação e os arquivos de projeto apropriados. A configuração de um remoto ocorrerá em uma fase futura, se necessário.

O banco operacional deverá representar um ecossistema empresarial coerente, e não apenas as necessidades imediatas de um dashboard. A seleção das tabelas e dos campos analíticos será decidida mais adiante, durante a exploração dos dados.

## Estrutura de diretórios

| Diretório/arquivo | Finalidade |
| --- | --- |
| `database/migrations/` | Migrações SQL versionadas do banco operacional. |
| `database/seeds/` | Futuras cargas iniciais controladas. |
| `database/queries/` | Consultas SQL do projeto. |
| `database/tests/` | Verificações estruturais e smoke tests SQL transacionais. |
| `data-generator/src/` | Pacote Python de configuração, geração, validação e smoke transacional reversível. |
| `data-generator/tests/` | Testes unitários e teste de integração PostgreSQL com `ROLLBACK`. |
| `powerbi/` | Projeto Power BI Desktop em PBIP, com modelo TMDL e relatório PBIR; fluxo documentado em [`powerbi/README.md`](powerbi/README.md). |
| `docs/architecture/` | Documentação conceitual de arquitetura. |
| `docs/business/` | Escopo, regras e conceitos do domínio empresarial. |
| `docs/database/` | Documentação futura do banco de dados. |
| `docs/powerbi/` | Documentação futura da camada Power BI. |
| `scripts/` | Scripts auxiliares do projeto. |
| `.env.example` | Modelo sem credenciais para configuração local futura. |
| `AGENTS.md` | Orientações para futuras execuções do Codex neste projeto. |

## Estado atual

**M0–M6, M5 e Fases 4.0–4.4 concluídos.** O Portfolio sintético de 120.000 pedidos está persistido no PostgreSQL 18.6, validado em conexão somente leitura e conciliado com os 13 baselines SQL. O PBIP [`powerbi/ProjetoBI.pbip`](powerbi/ProjetoBI.pbip) contém o modelo estrela comercial e 28 medidas DAX comerciais; medidas, reconciliações, atualização e reabertura foram validadas no Power BI Desktop. Dashboards, medidas de margem e COGS permanecem fora do escopo atual. Consulte [`docs/powerbi/phase-4.3-commercial-star-model.md`](docs/powerbi/phase-4.3-commercial-star-model.md), [`docs/powerbi/phase-4.4-commercial-dax-measures.md`](docs/powerbi/phase-4.4-commercial-dax-measures.md), [`powerbi/README.md`](powerbi/README.md), [`docs/PROJECT_COMPLETION_PLAN.md`](docs/PROJECT_COMPLETION_PLAN.md) e [`docs/data-generation/portfolio-validation.md`](docs/data-generation/portfolio-validation.md).

## Fases previstas

1. Revisar e aprovar o domínio conceitual (concluído) e consolidar a proposta relacional operacional (Fases 2A e 2A.1 concluídas).
2. Implementar e validar o esquema operacional no PostgreSQL 18 (Fases 2B, 2B.1 e 2B.2 concluídas; o dataset Portfolio foi persistido depois, na Fase M5).
3. Planejar e desenvolver a geração de dados sintéticos consistentes em Python. Fases 3A–3E.1 e M0–M5 concluídos; o Portfolio foi carregado e os baselines reconciliados. O registro operacional está em [`portfolio-validation.md`](docs/data-generation/portfolio-validation.md) e no [`plano mestre`](docs/PROJECT_COMPLETION_PLAN.md).
4. Explorar e selecionar os dados que farão parte da camada analítica.
5. Construir e validar o modelo semântico comercial e as medidas DAX no Power BI (Fases 4.3 e 4.4 concluídas).
6. Desenvolver e revisar os relatórios, mantendo documentação e versionamento alinhados.

As fases são uma visão de alto nível; decisões detalhadas serão registradas quando cada etapa for iniciada.
