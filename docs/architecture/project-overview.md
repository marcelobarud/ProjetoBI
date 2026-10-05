# Visão geral da arquitetura

## Objetivo

Este documento registra o fluxo conceitual previsto para o ProjetoBI. A arquitetura será detalhada em fases futuras, conforme as decisões de negócio e técnicas forem aprovadas.

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

O PostgreSQL representará o sistema e o ecossistema operacional da empresa fictícia. Seu desenho deverá atender a um cenário empresarial coerente, e não apenas aos dados que serão usados por um dashboard. Poderá incluir informações operacionais, administrativas e cadastrais realistas, além dos dados transacionais. A modelagem ainda não foi definida.

### Power Query — seleção e transformação

Power Query será responsável por selecionar, combinar e transformar informações disponíveis na fonte para preparar os dados destinados à análise. Nem todos os campos ou tabelas operacionais precisarão entrar no modelo analítico. A seleção será feita durante a exploração futura; este documento não define quais tabelas irão para o Power BI.

### Modelo semântico — fatos, dimensões e relacionamentos

O modelo semântico definirá fatos, dimensões e relacionamentos para dar estrutura e significado analítico aos dados preparados. Seu desenho será decidido após a exploração das fontes e não está definido nesta fase.

### DAX — métricas e regras analíticas

DAX será utilizado para criar métricas, cálculos e regras analíticas no modelo semântico, conforme os requisitos forem definidos.

### Relatórios — camada visual

A camada visual será construída principalmente de forma manual no Power BI. A composição dos relatórios, suas páginas e visuais será planejada em uma fase futura.

## Limites desta fase

Esta fundação documental não cria nem modifica objetos PostgreSQL e não define tabelas de origem, fatos, dimensões, medidas ou relatórios. Essas decisões pertencem às fases futuras correspondentes.
