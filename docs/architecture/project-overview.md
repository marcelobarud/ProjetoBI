# Visão geral da arquitetura

## Objetivo

Este documento registra o fluxo conceitual do ProjetoBI. O modelo operacional foi aprovado e sua implementação local PostgreSQL está em `database/migrations/`; a aplicação à instância alvo depende da configuração de conexão documentada em `docs/database/implementation.md`.

## Fluxo analítico futuro

```text
PostgreSQL
    ↓
Power Query
    ↓
Modelo semântico Power BI
    ↓
DAX
    ↓
Relatórios
```

### PostgreSQL — sistema operacional

O PostgreSQL representa o sistema e o ecossistema operacional da empresa fictícia. Seu desenho atende a um cenário empresarial coerente, e não apenas aos dados de um dashboard. O modelo relacional aprovado, as migrations e as regras transacionais estão documentados em `docs/database/` e `database/`.

### Power Query — seleção e transformação

Power Query será responsável por selecionar, combinar e transformar informações disponíveis na fonte para preparar os dados destinados à análise. Nem todos os campos ou tabelas operacionais precisarão entrar no modelo analítico. A seleção será feita durante a exploração futura; este documento não define quais tabelas irão para o Power BI.

### Modelo semântico — fatos, dimensões e relacionamentos

O modelo semântico definirá fatos, dimensões e relacionamentos para dar estrutura e significado analítico aos dados preparados. Seu desenho será decidido após a exploração das fontes e não está definido nesta fase.

### DAX — métricas e regras analíticas

DAX será utilizado para criar métricas, cálculos e regras analíticas no modelo semântico, conforme os requisitos forem definidos.

### Relatórios — camada visual

A camada visual será construída principalmente de forma manual no Power BI. A composição dos relatórios, suas páginas e visuais será planejada em uma fase futura.

## Limites desta fase

Esta visão arquitetural não define fatos, dimensões, medidas ou relatórios. Esses elementos analíticos pertencem às fases futuras correspondentes. O estado real da database é informado no README e no guia de implementação.
