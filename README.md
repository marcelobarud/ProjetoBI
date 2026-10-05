# ProjetoBI

Projeto de Business Intelligence para estudo e prática, com foco em construir gradualmente um fluxo completo desde um sistema operacional relacional até relatórios analíticos.

## Objetivo

Criar um ambiente coerente para praticar integração de dados, transformação, modelagem semântica, métricas e visualização. O domínio será uma empresa fictícia do segmento de informática. Os detalhes do negócio e a modelagem ainda serão definidos em fases futuras.

## Visão geral da arquitetura

- **PostgreSQL** será a fonte de dados e representará o ecossistema operacional da empresa.
- **Python** será usado futuramente para gerar dados sintéticos consistentes para estudo.
- **Power BI** será a camada analítica, incluindo Power Query, modelo semântico, DAX e relatórios.
- **Git/GitHub** será usado para versionar o código, a documentação e os arquivos de projeto apropriados. A configuração de um remoto ocorrerá em uma fase futura, se necessário.

O banco operacional deverá representar um ecossistema empresarial coerente, e não apenas as necessidades imediatas de um dashboard. A seleção das tabelas e dos campos analíticos será decidida mais adiante, durante a exploração dos dados.

## Estrutura de diretórios

| Diretório/arquivo | Finalidade |
| --- | --- |
| `database/migrations/` | Futuras migrações do banco, após aprovação da modelagem. |
| `database/seeds/` | Futuras cargas iniciais controladas. |
| `database/queries/` | Consultas SQL do projeto. |
| `database/tests/` | Verificações relacionadas ao banco e às consultas. |
| `data-generator/src/` | Código-fonte futuro do gerador de dados sintéticos em Python. |
| `data-generator/tests/` | Testes futuros do gerador. |
| `powerbi/` | Futuros arquivos do Power BI, incluindo o formato Power BI Project quando a fase correspondente começar. |
| `docs/architecture/` | Documentação conceitual de arquitetura. |
| `docs/database/` | Documentação futura do banco de dados. |
| `docs/powerbi/` | Documentação futura da camada Power BI. |
| `scripts/` | Scripts auxiliares do projeto. |
| `.env.example` | Modelo sem credenciais para configuração local futura. |
| `AGENTS.md` | Orientações para futuras execuções do Codex neste projeto. |

## Estado atual

**Fase 0 — fundação estrutural, documental e de versionamento.** Nesta fase foram preparados os diretórios e documentos iniciais. Nenhum banco, schema, tabela, usuário ou dado foi criado; também não foi iniciada a modelagem de negócio ou criado um projeto Power BI.

## Fases previstas

1. Definir e aprovar o escopo e a modelagem do ecossistema operacional.
2. Implementar o banco PostgreSQL e documentar sua estrutura, após aprovação explícita da fase.
3. Planejar e desenvolver a geração de dados sintéticos consistentes em Python.
4. Explorar e selecionar os dados que farão parte da camada analítica.
5. Construir as transformações, o modelo semântico e as medidas no Power BI.
6. Desenvolver e revisar os relatórios, mantendo documentação e versionamento alinhados.

As fases são uma visão de alto nível; decisões detalhadas serão registradas quando cada etapa for iniciada.
