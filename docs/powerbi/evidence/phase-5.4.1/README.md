# Evidências — Fase 5.4.1

As imagens `referencia-antes-*` são capturas históricas das fases anteriores, usadas como referência visual. Os arquivos `*-fechado` e `*-aberto` são capturas após a reestruturação, no Power BI Desktop com o canvas Full HD em Fit to Width.

A validação final no Desktop confirmou abertura do PBIP sem erro; estado inicial fechado; abrir/fechar por botão nas quatro páginas; preservação dos filtros; sincronização visual de Período, Canal e Loja; quatro nomes completos no Page Navigator; alinhamento dos filtros locais de Produtos e Categorias; e ausência de sobreposição entre visuais visíveis no estado fechado. A última revisão escureceu o botão Filtros para `#1D4ED8` (texto branco, 16 pt, contraste calculado 6,70:1) e definiu `#DBEAFE` para Fechar filtros (texto `#142238`, 16 pt, 13,08:1). A captura atualizada de Custos e Margens mostra os dois estados.

`phase-5.4.1-performance-warm.json` é a exportação do Performance Analyzer após Refresh visuals com o relatório já aberto. Os 15 ciclos observados têm `initialLoad=false`; esta evidência cobre atualização visual aquecida, não carregamento frio. Não houve atualização da fonte ou de dados no PostgreSQL.

As capturas mostram o viewport usado nesta sessão (1152 × 513 px). A definição de cada página continua em 1920 × 1080 px. Leitor de tela, escala de cinza e teste automatizado de contraste não foram executados.