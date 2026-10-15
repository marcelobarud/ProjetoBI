# Fase 5.6B.1 — Acabamento visual final InfoTech

**Status:** PASS técnico; aguarda aprovação estética do usuário.
**Data:** 2026-10-14
**Escopo:** refinamento visual das cinco páginas existentes, sem refresh e sem alterações de modelo, DAX, Power Query, relacionamentos, dados ou PostgreSQL.

## Resultado

A inspeção real no Power BI Desktop identificou rótulos arredondados repetidos nos eixos de moeda (escala automática em milhões) dos gráficos temporais de receita em **Visão Executiva** e **Análise Comercial**. A precisão de rótulo foi ajustada de zero para uma casa decimal apenas nesses dois visuais. O formato de unidade automática em milhões foi preservado; por exemplo, os rótulos passam a distinguir `R$ 1,0M` de `R$ 0,5M`.

A correção está em `powerbi/ProjetoBI.Report/definition/pages/8b8186ab91fc09fae9a2/visuals/a4000000000000000001/visual.json` e `powerbi/ProjetoBI.Report/definition/pages/c5202600000000000001/visuals/b4000000000000000001/visual.json`. Em cada arquivo, a única mudança funcional desta fase é `labelPrecision` de `0L` para `1L`.

## Inspeção visual

O PBIP abriu no Power BI Desktop sem erro. Foram observadas as cinco páginas em Fit to Width e os dois gráficos alterados também em Actual Size/100%. A captura de tela do monitor era 1366×768 px; a área capturada do Desktop era 1366×720 px, com escala do Windows em 100%. Fit to Width exibiu 47%. Em Fit to Width e 100%, os ticks dos dois gráficos de receita ficaram visualmente distintos após o ajuste. A visualização em 100% requer rolagem natural do canvas e não representa a página inteira simultaneamente.

Nas demais páginas, cabeçalho/monograma, navegação, cartões, filtros, gráficos e matriz mantiveram a composição consistente observada. Não foi identificado outro ajuste objetivo com evidência suficiente para esta fase. O painel de filtros aberto pode cobrir parte da faixa de cartões, comportamento existente já previsto pelo layout; páginas mais extensas mantêm rolagem. Esses elementos foram preservados.

## Validações e limites

- JSON dos dois visuais parseado com sucesso; a alteração `labelPrecision` foi confirmada em ambos.
- PBIR abriu no Desktop atualizado pela Microsoft Store (versão 2.158.1304.0); cinco páginas renderizaram.
- Não houve atualização de dados nem interação com filtros ou medidas durante esta revisão visual.
- O Power BI foi fechado escolhendo **Don't save** para descartar somente mudanças transitórias de página/zoom/navegação. A edição PBIR foi feita externamente antes da abertura de validação.
- Não foi executada auditoria formal de contraste WCAG, acessibilidade assistiva nem teste em outros tamanhos físicos de tela. A inspeção em 100% e Fit to Width não certifica legibilidade universal.
- A configuração é candidata a padrão tipográfico futuro. O Design System v0.2 permanece inalterado até aprovação estética explícita; não consolidar a Fase 5.6C nesta etapa.

## Evidências

- Antes: `evidence/phase-5.6b.1/before/`.
- Depois: `evidence/phase-5.6b.1/after/`.
- Comparação visual e inventário com SHA-256: `evidence/phase-5.6b.1/comparisons/` e `evidence/phase-5.6b.1/validation/`.
- Pacote: `evidence/archives/fase-5.6b.1-evidencias.zip`.

As capturas são evidências visuais do Desktop nas condições descritas; não são medições de legibilidade nem aprovação estética do usuário.