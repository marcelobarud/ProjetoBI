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
| `powerbi/` | Futuros arquivos do Power BI, incluindo o formato Power BI Project quando a fase correspondente começar. |
| `docs/architecture/` | Documentação conceitual de arquitetura. |
| `docs/business/` | Escopo, regras e conceitos do domínio empresarial. |
| `docs/database/` | Documentação futura do banco de dados. |
| `docs/powerbi/` | Documentação futura da camada Power BI. |
| `scripts/` | Scripts auxiliares do projeto. |
| `.env.example` | Modelo sem credenciais para configuração local futura. |
| `AGENTS.md` | Orientações para futuras execuções do Codex neste projeto. |

## Estado atual

**M0–M4 concluídos; M6 documental aprovado; M5 PERFORMANCE READY.** O Portfolio de 120.000 pedidos passou pelas auditorias lógica, distributiva e de estoque; as fixtures PostgreSQL de 10.000 e 50.000 pedidos passaram com rollback e confirmação independente de zero linhas nas 41 tabelas. O sink foi otimizado e revalidado em 10.000 pedidos com rollback. A autorização controlada para um único `COMMIT` foi concedida, mas a carga definitiva ainda não foi iniciada; os baselines finais dependem dela. A construção do modelo Power BI aguarda o encerramento do M5. Consulte [`docs/PROJECT_COMPLETION_PLAN.md`](docs/PROJECT_COMPLETION_PLAN.md), [`docs/powerbi/readiness.md`](docs/powerbi/readiness.md), [`docs/data-generation/implementation.md`](docs/data-generation/implementation.md) e [`docs/data-generation/validation-report.md`](docs/data-generation/validation-report.md).

## Fases previstas

1. Revisar e aprovar o domínio conceitual (concluído) e consolidar a proposta relacional operacional (Fases 2A e 2A.1 concluídas).
2. Implementar e validar o esquema operacional no PostgreSQL 18 (Fases 2B, 2B.1 e 2B.2 concluídas; sem dados de negócio persistidos).
3. Planejar e desenvolver a geração de dados sintéticos consistentes em Python. Fases 3A–3E.1 e M0–M4 do plano mestre concluídos; a geração Portfolio foi validada em modo descartável e rollback-only. A primeira persistência e seus baselines dependem de autorização explícita e seguem no [`plano mestre`](docs/PROJECT_COMPLETION_PLAN.md).
4. Explorar e selecionar os dados que farão parte da camada analítica.
5. Construir as transformações, o modelo semântico e as medidas no Power BI.
6. Desenvolver e revisar os relatórios, mantendo documentação e versionamento alinhados.

As fases são uma visão de alto nível; decisões detalhadas serão registradas quando cada etapa for iniciada.
