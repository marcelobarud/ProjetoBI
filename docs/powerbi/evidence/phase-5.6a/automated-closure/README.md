# Evidências — Fase 5.6A.2

## Estratégia

Capturas obtidas diretamente da janela real do Power BI Desktop por Computer Use. Antes de cada ação foram observados janela e estado visual; coordenadas e estado eram atualizados após cada ação. Edição de data usou os campos nativos; alças foram arrastadas com o mouse; filtros selecionados nos dropdowns; Page Navigator acionado por seleção do visual + `Ctrl+Space` em modo de edição.

## Ambiente e preservação

- Power BI Desktop Store `2.158.1304.0 (26.09)+a43ace043425e30778f23721b943ff885c2214e5`.
- PBIP local em `powerbi/ProjetoBI.pbip`; sem refresh.
- Snapshot pré-execução: `C:\Users\D2\AppData\Local\Temp\ProjetoBI-Phase5.6A2-preflight-20261014-184617.zip`, SHA-256 `781A9F22CE1EA3CCB7B29ED505CF29E04AEA3F40CC1D6C747B69A99472B82C1A`.
- O ciclo persistente salvo previamente foi reaberto e conferido. Mudanças temporárias finais de filtros e zoom foram descartadas ao fechar; nenhuma seleção transitória foi salva.

## Capturas

| Arquivo | Conteúdo |
|---|---|
| `estado-inicial-devolucoes-restaurado-aberto.png` | Estado observado antes do fechamento persistente |
| `F03-periodo-jan-set-2026.png` | Campo de data e intervalo de referência |
| `F03-devolucoes-jan-set-kpis.png` | KPIs após Jan–Set/2026 |
| `F04-slider-inicio-movido.png` | Alça inicial movida e intervalo resultante |
| `F05-slider-fim-movido.png` | Alça final movida e intervalo resultante |
| `F06-painel-reaberto-periodo-preservado.png` | Reabertura do painel com período preservado |
| `S04-custos-selecao-origem.png` | Custos: período, canal, loja e visuais antes da navegação |
| `S04-devolucoes-periodo-canal-sincronizados.png` | Devoluções: sincronização S04 no destino |
| `S05-devolucoes-para-executiva-sync.png` | Executiva: sincronização S05 dos três filtros |
| `S06-produtos-filtros-compartilhados-todos.png` | Produtos: filtros compartilhados limpos |
| `S07-executiva-para-devolucoes.png` | Devoluções: destino S07 |
| `products-local-product-selected.png` | Seleção local de SKU em Produtos |

Hashes SHA-256 e tamanhos estão em `manifest.json`. As entradas dentro de `fase-5.6a.2-evidencias.zip` são conferidas pelo mesmo manifesto.

## Matriz e limites

Consulte `test-matrix.md`. F01–F14 e S01–S07 passaram. Tab/foco/acessibilidade por teclado, clique originado por cartão KPI e inspeção interna das opções de bookmark ficaram **NOT TESTED**. Isso não é evidência de falha do relatório.
