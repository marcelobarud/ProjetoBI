# ProjetoBI

Projeto de Business Intelligence para estudo e prática, com foco em construir gradualmente um fluxo completo desde um sistema operacional relacional até relatórios analíticos.

## Objetivo

Criar um ambiente coerente para praticar integração de dados, transformação, modelagem semântica, métricas e visualização. O domínio será uma empresa fictícia do segmento de informática. Os detalhes do negócio e a modelagem são definidos em fases, com revisão antes da implementação.

## Visão geral da arquitetura

- **PostgreSQL** será a fonte de dados e representará o ecossistema operacional da empresa.
- **Python** implementa o gerador sintético determinístico de dados mestres e do núcleo transacional no profile smoke.
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

**Fase 3C — núcleo transacional smoke implementado e validado.** A database `projeto_bi` no PostgreSQL 18.6 mantém 9 schemas e 40 tabelas. Geração de dados mestres e fluxo transacional foram validados em smoke com `ROLLBACK`; confirmação posterior encontrou zero linhas nas 40 tabelas. Foram gerados 300 pedidos e 630 itens, com compras, recebimentos, estoque, descontos e fulfillment. Os perfis `portfolio` e `large` estão configurados, mas não executados. Consulte [`docs/data-generation/implementation.md`](docs/data-generation/implementation.md), [`docs/data-generation/validation-report.md`](docs/data-generation/validation-report.md) e [`docs/database/validation-report.md`](docs/database/validation-report.md).

## Fases previstas

1. Revisar e aprovar o domínio conceitual (concluído) e consolidar a proposta relacional operacional (Fases 2A e 2A.1 concluídas).
2. Implementar e validar o esquema operacional no PostgreSQL 18 (Fases 2B, 2B.1 e 2B.2 concluídas; sem dados de negócio persistidos).
3. Planejar e desenvolver a geração de dados sintéticos consistentes em Python. Fases 3A, 3B e 3C concluídas: o pacote gera e valida dados mestres e núcleo transacional do profile smoke, com integração PostgreSQL estritamente com rollback. Próximo escopo recomendado: planejar a Fase 3D.
4. Explorar e selecionar os dados que farão parte da camada analítica.
5. Construir as transformações, o modelo semântico e as medidas no Power BI.
6. Desenvolver e revisar os relatórios, mantendo documentação e versionamento alinhados.

As fases são uma visão de alto nível; decisões detalhadas serão registradas quando cada etapa for iniciada.
