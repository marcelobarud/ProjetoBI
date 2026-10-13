# Fase 5.0 — identidade InfoTech e fundação dos dashboards

**Resultado:** PASS — fundação documental pronta para avaliação visual na Fase 5.1. Nenhuma página foi criada ou alterada no PBIP.

## Escopo e evidência local

- Branch `main`, HEAD antes do trabalho `6e470d36451ece7d47922a771231a02c5e8cedef` (`6e470d3`). Estado inicial: única modificação rastreada em `powerbi/ProjetoBI.Report/definition/report.json`, com `queryLimitOption=None` já registrado pela Fase 4.6.2. Foi mantida fora do escopo e dos commits.
- Lidos `AGENTS.md`, `docs/PROJECT_COMPLETION_PLAN.md`, auditoria semântica 4.6, medidas financeiras 4.5C, `powerbi/README.md`, estabilização 4.6.2 e o catálogo TMDL das 55 medidas.
- Contratos confirmados: 10 tabelas (5 dimensões, 4 fatos e `_Medidas`), 55 medidas, 11 pastas, 21 relações; período 2023-01-01 a 2026-09-30. Medidas de pedido, linha de item, custo por movimento e devolução têm grãos e datas diferentes. Nenhuma medida foi criada.
- Versão local do Desktop lida do executável: `2.158.1177.0 (26.09)+a10b99dd55051d4b25e9e28c4a1747d23f7a4f1f`. Segoe UI e Segoe UI Semibold estão instaladas. Em relatório vazio e não salvo, a interface expôs Page Navigator via recursos nativos e visuais Card, KPI, barras/colunas, linha, matriz, slicer, entre outros; “Goals” e “List slicer” aparecem como Preview. Nenhum PBIP foi aberto nesta inspeção.

## Identidade e design system

A identidade corporativa inicial usa InfoTech, com wordmark “InfoTech Intelligence”, sem narrativa ou dados institucionais inventados. O sistema claro usa azul `#2563EB`, verde-petróleo `#0F9D92`, fundo `#F5F7FB`, superfície branca, texto `#142238` e cores semânticas. O tom secundário de texto mudou de `#64748B` para `#5B6B82`: a alternativa inicial teve contraste 4,44:1 sobre o canvas; o novo tom passou em 5,06:1. Títulos, valores e textos têm Segoe UI, classes e tamanhos indicados no documento principal.

Contrastes de texto medidos (WCAG): Primary 4,82:1 sobre canvas; Text Primary 14,88:1; Text Secondary 5,06:1; Positive 4,68:1; Negative 6,03:1; Warning 4,68:1. Secondary teal, Border e tons claros são reservados a marcas, decoração ou linhas, não a texto pequeno. Cor nunca é o único sinal de interpretação.

## Arquitetura das páginas

1. Visão Executiva — KPIs financeiros por coorte, resultado e janela YTD comparável.
2. Análise Comercial — pedidos, status, receita comercial, ticket, canal, loja e cliente.
3. Produtos e Categorias — unidades e medidas financeiras homologadas no grão de item, com Top N.
4. Custos e Margens — seção de coorte comercial separada de fluxo por movimento/recebimento.
5. Devoluções — solicitações, unidades recebidas, valores e destinação sem confundir evento com refund.

A matriz em `DASHBOARD_ARCHITECTURE.md` usa nomes exatos das medidas TMDL, dimensões/filtros, data e grão, interações e riscos. A sincronização de Produto fica fora das páginas de pedido; Canal e Loja são candidatas a filtros compartilhados. Datas são rotuladas por coorte, movimento ou recebimento; o calendário comum não oferece seleções independentes para todas as perspectivas.

## Tema, schema e limites

`infotech-light.json` usa somente `name`, paleta de dados, cores de status e gradiente, classes de cor estrutural e classes tipográficas. A sintaxe foi validada como JSON, todos os hex são válidos e as propriedades escolhidas existem no schema oficial `reportThemeSchema-2.157.json`. Esta era a versão pública mais recente localizada; não foi encontrada versão 2.158 para corresponder exatamente ao Desktop instalado. O schema do repositório Microsoft esclarece que suas versões são as mesmas usadas pelo Desktop durante a validação de importação.

O tema não é importado nem aplicado ao PBIP nesta fase. O JSON foi validado contra o schema oficial publicado 2.157, a versão mais recente localizada; o Desktop instalado é 2.158 e não foi localizado schema 2.158 para uma validação exata desta versão. A compatibilidade de importação e a renderização visual serão verificadas na Fase 5.1, ao implementar a primeira página. Cores de canvas de página, dimensões do canvas, grid, espaçamento, raio de canto, sombra, estados de navegação, filtros, tooltips, texto alternativo, ordem de tabulação e regras condicionais precisam de configuração/teste no Desktop. Nenhum componente recebe status de homologação visual.

## Decisões pendentes e próximo checkpoint

- Confirmar no Desktop a importação do tema 2.157 no build local 2.158; validar canvas 16:9, comportamento das classes, contraste visual e visualização BRL em pt-BR.
- Testar o Page Navigator horizontal, filtros, página ativa, cross-filter, valores BLANK/zero, drill-down, acessibilidade e desempenho em dados reais ao criar a primeira página.
- Se o requisito precisar contar somente itens efetivamente recebidos, propor medida específica numa fase futura; o catálogo atual não possui medida dedicada.
- Reavaliar tamanhos/responsividade após a composição real. Nada de Fase 5.1 é executado automaticamente.

## Referências técnicas

- Tema customizado: https://learn.microsoft.com/en-us/power-bi/create-reports/report-themes-create-custom
- Aplicação e limitações de temas: https://learn.microsoft.com/en-us/power-bi/create-reports/desktop-report-themes
- Schema oficial e versões por Desktop: https://github.com/microsoft/powerbi-desktop-samples/tree/main/Report%20Theme%20JSON%20Schema
- Page Navigator nativo: https://learn.microsoft.com/en-us/power-bi/create-reports/button-navigators
- Critérios de acessibilidade: https://learn.microsoft.com/en-us/power-bi/create-reports/desktop-accessibility-creating-reports

**Critério de saída:** identidade, Design System v0.1, matriz das cinco páginas e tema JSON entregues; execução da primeira página permanece para aprovação e escopo próprios da Fase 5.1.
