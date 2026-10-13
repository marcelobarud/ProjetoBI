# InfoTech Intelligence — Design System v0.2

**Estado:** v0.2 consolidada na Fase 5.1.2. Os sete cenários de homologação receberam aprovação manual do usuário, com ressalva de tipografia corrigida nos três gráficos e reinspecionada por captura do Desktop. Ver `phase-5.1.2-executive-dashboard-homologation.md` para evidências e limitações.

**Proposto** significa orientação ainda sem implementação validada; **implementado** significa presente no PBIP; **homologado** significa implementado e validado no Desktop por relato manual ou inspeção visual identificada. A homologação se limita aos cenários e ao ambiente documentados. Navegação futura, mobile, mensagens especiais de ausência de dados, tooltips personalizados e compatibilidade com leitor de tela continuam propostos ou não verificados.

## 1. Identidade

| Elemento | Definição |
|---|---|
| Empresa fictícia | InfoTech |
| Identidade analítica | InfoTech Intelligence |
| Segmento | Comércio de produtos de informática e tecnologia |
| Posicionamento | Inteligência comercial, financeira e operacional baseada em dados |
| Personalidade | Tecnológica, confiável, objetiva, moderna e profissional |

Usar “InfoTech Intelligence” como wordmark tipográfico no cabeçalho e “InfoTech” em identificação institucional compacta ou rodapé. A navegação deve privilegiar nomes de área; títulos de página descrevem a pergunta analítica. O rodapé, quando útil, informa o intervalo de dados e a perspectiva temporal, nunca presume que a data de hoje seja a última atualização. Não criar logotipo, endereço, CNPJ, história, número de funcionários ou outros dados institucionais nesta fase. Manter o nome em um único ponto de configuração visual para permitir substituição futura.

## 2. Tokens de cor

| Token | Valor preservado | Uso | Contraste de texto medido |
|---|---|---|---|
| Primary | `#2563EB` | Seleção, links e destaque principal | 5,17:1 em branco; 4,82:1 no fundo |
| Secondary | `#0F9D92` | Série secundária e elementos de apoio | 3,36:1 em branco; usar em marcas/gráficos, não em texto pequeno |
| Background | `#F5F7FB` | Canvas claro configurado manualmente | Com Surface: 1,05:1; separação visual, não texto |
| Surface | `#FFFFFF` | Cards e áreas de conteúdo | Base para texto e gráficos |
| Text Primary | `#142238` | Títulos, números e texto principal | 15,96:1 em branco; 14,88:1 no fundo |
| Text Secondary | `#5B6B82` | Rótulos e contexto auxiliar | 5,43:1 em branco; 5,06:1 no fundo |
| Border | `#E2E8F0` | Divisores e contornos não textuais | Não usar como cor de texto |
| Positive | `#15803D` | Resultado favorável quando o significado justificar | 5,02:1 em branco; 4,68:1 no fundo |
| Negative | `#B91C1C` | Resultado desfavorável e alertas | 6,47:1 em branco; 6,03:1 no fundo |
| Warning | `#B45309` | Atenção e condição intermediária | 5,02:1 em branco; 4,68:1 no fundo |

O tom de texto secundário foi escurecido tecnicamente em relação à sugestão inicial `#64748B`: este tinha 4,44:1 sobre o canvas e não atingia 4,5:1. `#5B6B82` passa no cálculo sobre o canvas e a superfície. Valores de contraste usam a fórmula WCAG para texto normal; o teste não substitui avaliação visual de cores adjacentes ou estados interativos.

### Sequências e semântica

- Série categórica inicial, nesta ordem: `#2563EB`, `#0F9D92`, `#D97706`, `#7C3AED`, `#B91C1C`, `#475569`, `#0891B2`, `#A16207`. Usar poucas séries por gráfico; não depender de cor como única codificação. Complementar com rótulos, posição, marcador ou padrão quando houver sobreposição.
- Sequencial: variações claras a escuras do azul Primary, escolhidas e verificadas no próprio visual conforme quantidade, escala e fundo. Não aplicar a categorias sem ordem.
- Divergente: negativo `#B91C1C`, centro neutro `#F5F7FB`, positivo `#15803D`; usar somente quando zero ou um alvo aprovado for um ponto neutro significativo. Os tokens globais `minimum`, `center`, `maximum` e `null` fornecem uma base para gradientes, mas a configuração de cada regra ainda precisa ser validada no visual.
- Positive/Negative nunca comunicam o resultado sozinhos: acrescentar rótulo, sinal, ícone com texto alternativo ou comparação numérica. Não inferir que aumento é sempre favorável; receita, custo e devolução têm interpretações diferentes.
- Branco e cinza claro são superfícies. Evitar fundos coloridos para todos os KPIs, sombras decorativas e contornos fortes.

## 3. Tipografia

Segoe UI e Segoe UI Semibold são usadas no Power BI. A escala abaixo registra as propriedades configuradas na Visão Executiva após o refinamento da Fase 5.1.2. A inspeção nativa da Fase 5.2 identificou que o modo responsivo pode reduzir fontes ao renderizar; configuração não garante tamanho efetivo em todos os viewports. Os ajustes locais dos visuais prevalecem sobre as classes gerais do tema. Ver a ressalva e a variação comercial na seção 13.

| Papel | Referência configurada | Alinhamento/peso |
|---|---:|---|
| Wordmark principal | 30 pt | À esquerda, Segoe UI Semibold |
| Nome da página | 12 pt | Segoe UI, texto secundário; sem período fixo |
| Título dos três gráficos | 17 pt | Segoe UI Semibold |
| Valor KPI | 32 pt | Segoe UI Semibold; unidade explícita |
| Título dos cartões e filtros | 13 pt | Segoe UI Semibold |
| Valores dos slicers | 13 pt configurados | Segoe UI; tamanho final sujeito ao controle nativo |
| Eixos X/Y e categorias dos três gráficos | 16 pt | Segoe UI |
| Legenda temporal | 15 pt | Segoe UI |
| Tabelas, notas e rodapé futuros | Proposto: 12–14 pt / 11–12 pt | Revalidar no visual implementado |

O canvas é Full HD e foi inspecionado em Fit to Page, com capturas nas escalas 1 e 2 do bridge. A captura ampliada não representa uma troca do zoom do Desktop para 100%. Fit to Page reduz também as fontes conforme o espaço disponível: para 45 meses, o eixo categórico nativo inclina os rótulos e a leitura fica limitada em viewports pequenos. Esse comportamento denso não é um padrão homologado para qualquer intervalo; preferir uma janela temporal apropriada ou maior área de apresentação, preservando os pontos da série.

Usar sentence case em títulos e rótulos. Evitar CAIXA ALTA contínua, excesso de pesos, itálico decorativo e textos abaixo de 10 pt. Reduzir conteúdo antes de reduzir tipografia.

## 4. Grid e densidade

- Referência implementada para as próximas páginas desktop: Full HD de 1920 × 1080 px (16:9), conforme solicitação do usuário, com margens de 36 px. A referência conceitual anterior de 1280 × 720 é histórica; suas dimensões não devem ser copiadas mecanicamente.
- Grid conceitual de 12 colunas, margem externa de 24 px e base de espaçamento de 8 px. Usar intervalos de 8, 16, 24 ou 32 px; elementos equivalentes compartilham largura, altura e alinhamento.
- Referência vertical: cabeçalho 64 px; contexto/filtros 56 px; intervalos de 16 px; área analítica aproximada de 496 px; margem inferior 24 px e rodapé opcional até 24 px. Ajustar a área útil à página real e ao navegador.
- Uma linha de filtros no desktop; evitar painéis que espremam os visuais. Reservar largura para títulos completos e rótulos pt-BR.
- Cards e visuais devem ter respiro interno constante. Arredondamento discreto pode ser aplicado manualmente quando suportado pelo tipo de visual; a forma não é garantida globalmente pelo tema.

## 5. Componentes

### KPI prioritário e secundário

- Valor em destaque, nome curto e unidade. BRL, contagem ou percentual no próprio visual.
- Comparação aparece apenas com medida existente e janela compatível. Escrever o período ou referência no rótulo auxiliar.
- KPI prioritário pode ocupar duas colunas conceituais; secundários usam largura/altura comuns. Não usar sombra como hierarquia.
- BLANK deve ser reconhecido como ausência de valor ou denominador, não convertido em zero. Texto sem dados pode ser configurado no visual quando disponível.

### Cards analíticos

Fundo branco; título de gráfico em 17 pt e de KPI em 13 pt; contorno discreto ou separação por espaço; margens internas uniformes. As superfícies atuais foram inspecionadas no Desktop. Raio de canto, borda e sombra de outros tipos de visual exigem validação própria; não são garantidos pelo tema.

### Filtros

- Preferir segmentações nativas. Período/ano-mês usa calendário; Canal e Loja usam nomes legíveis. Controles têm posição e rótulos fixos.
- Explicitar seleção única/múltipla, seleção limpa e estado sem resultado. Evitar segmentações longas; usar lista suspensa quando a cardinalidade for grande.
- Política de sincronização detalhada em `DASHBOARD_ARCHITECTURE.md`. Filtro de produto não será sincronizado para páginas de métricas de cabeçalho de pedido.

### Navegação

**Implementado e validado nas duas páginas reais na Fase 5.2; candidato à v0.3:** Page Navigator nativo horizontal e compacto com Visão Executiva e Análise Comercial. Página ativa Primary/branco; demais Surface/Text Primary. Páginas futuras e drill-through continuam propostos e exigem validação própria. Um navegador nativo acompanha renomeação e ordenação de páginas.

### Tooltips

Explicar unidade, período, grão e perspectiva temporal relevante. Não repetir o mesmo número em vários formatos nem misturar receita por coorte com evento de recebimento. Usar descrição textual concisa; tooltips não substituem rótulo ou contexto no visual principal.

### Tabelas e matrizes

Cabeçalho distinto dos valores, totais identificáveis, BRL/contagem/% consistentes e alinhamento numérico. Formatação condicional moderada, com legenda/texto além da cor. Limitar linhas com Top N e ordenação explícita; permitir drill-down onde a hierarquia real do catálogo suportar.

### Estados

| Estado | Apresentação proposta para novos componentes |
|---|---|
| Sem dados | Mensagem “Sem dados para os filtros selecionados”; não simular zero |
| Filtro sem resultado | Manter filtros visíveis e explicar como limpar seleção |
| Não aplicável/denominador inválido | Preservar BLANK, não renderizar 0% |
| Resultado negativo | Valor com sinal e texto; cor negativa apenas como reforço |
| Zero válido | Renderizar zero com unidade apropriada, distinto de BLANK |

## 6. Formatação numérica

- Cartões financeiros em BRL com apresentação pt-BR (`R$`, milhar e decimal), confirmada no Desktop; percentual com duas casas e Pedidos concluídos como inteiro.
- Os eixos monetários dos três gráficos usam milhões, precisão visual zero e fonte 16 pt. O Desktop renderiza o sufixo nativo `M`, que significa milhões; não presumir um sufixo personalizado `mi`. O tooltip nativo mantém a formatação do campo em BRL; tooltips personalizados não foram homologados.
- Percentuais com duas casas por padrão; contagens inteiras; unidades abreviadas (mil, mi) somente quando preservarem leitura e houver contexto completo no tooltip.
- Usar a formatação já homologada das medidas. Não alterar DAX nem arredondar valores intermediários para efeito visual. Não somar percentuais nem calcular margem pela média de margens mensais.
- Valores zero permanecem zero; BLANK permanece vazio ou recebe estado “Sem dados”, conforme o visual. Tooltips, eixos, cards e tabelas compartilham unidade e precisão.

## 7. Regras para gráficos

| Tipo | Usar para | Limites |
|---|---|---|
| Linha | Evolução mensal e comparação temporal | Eixo temporal ordenado pelo calendário; séries comparáveis; não ligar datas operacionais e coortes como se fossem uma só |
| Coluna | Comparar poucos períodos ou grupos | Evitar dezenas de categorias; eixo zero para comparação de magnitude |
| Barra horizontal | Ranking de canal, produto, categoria ou loja | Top N explícito e ordenação decrescente; nomes legíveis |
| Coluna/barra empilhada | Composição de grupos com poucas séries | Não usar 100% quando o total importa; evitar muitas categorias |
| Matriz | Detalhe hierárquico por categoria/produto ou dimensões | Subtotais conscientes do grão e formatos uniformes |
| Cartão/KPI | Medida prioritária ou comparação temporal homologada | Não usar sem unidade/período; distinguir BLANK de zero |
| Pizza/rosca | Poucas categorias mutuamente exclusivas | Evitar muitas fatias; preferir barra para ranking |
| Cascata | Decomposição com componentes que conciliam | Disponível nativamente; usar apenas se os componentes e a ponte estiverem definidos, sem inventar valores |

Sem 3D, eixo truncado sem aviso, excesso de decimais, legenda longa ou visuais decorativos. Para produtos, Top N e drill-down; nunca tentar exibir todo o catálogo de uma vez. Maps só se uma decisão futura justificar uma pergunta geográfica e o campo de localização confiável; não estão previstos na primeira versão.

## 8. Acessibilidade e interação

O usuário aprovou manualmente o cenário de acessibilidade/desempenho entre os sete testes, sem detalhar teclas, estados de foco ou leitor de tela. Os onze visuais têm texto alternativo e tab order 0–10. A confirmação manual não comprova compatibilidade com leitor de tela, escala de cinza ou todos os estados de contraste; essas verificações específicas seguem não exercitadas.

- Texto relevante com contraste ≥ 4,5:1 sobre o fundo real. Texto grande pode seguir o mínimo WCAG de 3:1, mas o sistema prioriza os valores acima. Não usar Border como texto.
- Acrescentar título que descreva a pergunta e nomes de eixo com unidade. Definir texto alternativo para visuais, ordem de tabulação e foco visível no Desktop.
- Garantir que filtros possam ser operados por teclado e que o estado selecionado não dependa apenas de cor.
- Cores de séries devem ser acompanhadas por posição, rótulo/legenda e, quando necessário, marcador. Validar em escala de cinza e com simulador de deficiência de visão de cores na revisão visual.
- Testar interação entre visuais. Clique em categoria não pode sugerir que medidas de cabeçalho sejam atribuídas àquela categoria.

## 9. Limites do tema e do Desktop

O tema `powerbi/themes/infotech-light.json` configura nome, cores de série e status, gradiente, cores estruturais e classes tipográficas. Na inspeção histórica da Fase 5.0, o schema encontrado era `reportThemeSchema-2.157.json` e o Desktop instalado era 2.158.1177.0. A importação foi aceita na Fase 5.1; a renderização da Visão Executiva foi reinspecionada na Fase 5.1.2. A revisão documental v0.2 preserva o tema registrado v0.1 e acrescenta padrões locais validados.

O tema não define por si só tamanho/fundo da página, grid/posicionamento, filtros sincronizados, interações, texto alternativo, ordem de tabulação ou regras de formatação condicional. Raio de canto, sombra, estado do Page Navigator, unidades, eixos, rótulos e tooltips podem depender do visual e de ajuste manual. Propriedades só devem ser incluídas em `visualStyles` após conferir o visual, o caminho suportado e a renderização. Novas páginas exigem inspeção própria no Desktop.

O Desktop instalado expôs estes visuais nativos durante a inspeção do painel: barras/colunas agrupadas e empilhadas, 100% empilhadas, linha, área, combinações linha-coluna, ribbon, cascata, funil, dispersão, pizza/rosca, treemap, mapas, gauge, Card, KPI, slicer, tabela, matriz, visuais R/Python, Key influencers, decomposition tree, Narrative, imagem e outros. “Goals” e “List slicer” apareceram como Preview; componentes externos e versões Preview não são dependências da arquitetura v0.1. Page Navigator é nativo no menu de navegação do Power BI, separado da galeria de visuais.

## 10. Evidência de homologação da Visão Executiva

- Aplicados no PBIP o tema `InfoTech Intelligence — Light v0.1` e o fundo `#F5F7FB`; o Desktop aceitou a importação e indicou o tema como atual. Ao registrar o tema, expandiu `dataColors` de oito para 480 cores, mantendo os oito tokens iniciais na mesma ordem e sem alterar as demais propriedades do tema-fonte.
- A página reutilizada foi definida em Full HD 1920×1080, com cabeçalho tipográfico, filtros compactos, quatro cartões, uma linha temporal e duas barras horizontais.
- Os sete testes manuais foram aprovados pelo usuário na Fase 5.1.2: período, canal, loja, combinação, categoria, acessibilidade/desempenho e persistência. O relato é evidência manual, sem valores detalhados para cada seleção.
- O cabeçalho contém somente InfoTech Intelligence e Visão Executiva; o período atual é identificado no slicer. A inspeção posterior ao refinamento confirmou quatro KPIs, quatro canais, cinco categorias, ausência de cortes nos nomes e ausência de scrollbar no ranking.
- A exportação local `PowerBIPerformanceData.json` contém 153 eventos completos de ciclo de vida de visual, entre 45 e 408 ms, e ações de slicer/cross-highlight. Esses intervalos são calculados dos timestamps da sessão anterior ao refinamento; não equivalem a tempo de carregamento inicial da página, SLA ou benchmark após a mudança. Condições de cache e atribuição exata aos cenários não estão registradas. Ver o relatório da Fase 5.1.2.
- Contraste dos tokens continua com as medições documentadas; leitor de tela e escala de cinza não são declarados testados.

## 11. Biblioteca de componentes

### DS-C01 — Cabeçalho corporativo

**Homologado na Visão Executiva.** Wordmark 30 pt, nome da página 12 pt, cores Text Primary/Text Secondary; textbox em x=36, y=22, 1848 × 76 px. Usar o nome da página sem período estático quando o slicer permitir outras datas. Texto alternativo também deve evitar datas fixas. Depende da identidade InfoTech; Page Navigator futuro permanece proposto e precisa de validação dos rótulos e espaço.

### DS-C02 — Barra de filtros

**Homologada por relato manual e captura.** Período Between com `DimCalendario[Data]`, Canal/Loja em dropdowns nativos, um título por filtro e cabeçalho de campo oculto. Fonte configurada 13 pt. Referência x=36/820/1344, y=112; áreas 760/500/540 × 96 px. Usar os nomes das dimensões existentes; `All` representa ausência de restrição no Desktop deste ambiente. Seleção e limpeza passaram nos testes relatados. Não excluir membros em branco artificialmente nem transformar seleção múltipla em seleção única sem necessidade analítica. A presença e a leitura de membros em branco específicos não receberam evidência detalhada; novas páginas devem conferir esse estado. O intervalo salvo localmente após os testes foi limpo e é preservado; Jan–Set/2026 permanece contexto de referência, não texto fixo de cabeçalho.

**Refinamento homologado na Fase 5.2.1 (2026-10-13):** nas duas páginas, o Período comercial conserva o Between e dois campos editáveis, com slider horizontal e duas alças abaixo das datas. Área do período: x36/y104, **760 × 112 px**; título Segoe UI Semibold 13 pt e campos Segoe UI 13 pt configurados. `slider.show=true` e `general.responsive=false` explícitos. O Desktop desta versão apresenta alças em barras verticais (controles nativos de 5 × 17 px), não círculos. Não copiar as alturas compactas anteriores para este componente.

Canal e Loja conservam integralmente suas definições e posições: y112, alturas 96 px na Executiva e 80 px na Comercial. Para reservar 8 px entre a área do período e os KPIs, os doze visuais analíticos comerciais foram deslocados 16 px para baixo, sem mudar suas dimensões; margem inferior final 24 px. A composição executiva permanece na posição anterior. O grupo `InfoTech.PeriodoComercial` e suas duas opções de sincronização permanecem intactos.

As duas alças, a edição dos dois campos, os efeitos analíticos, a sincronização nos dois sentidos e a reabertura foram exercitados no Desktop. Fit to Page reduz também a área de clique: campos são preferíveis para datas exatas; o slider não promete precisão diária por pixel em viewport reduzido. Capturas ampliadas do bridge comprovam a composição, não operação em zoom 100%. Evidências e limites em [Fase 5.2.1](phase-5.2.1-period-slider.md). Versão do Design System mantida em v0.2.

### DS-C03 — Cartão KPI

**Homologado.** Quatro cartões nativos de 450 × 136 px, y=224, espaçamento horizontal 16 px; superfície branca e hierarquia título 13 pt / valor 32 pt. Usar medidas existentes de `_Medidas`; BRL e percentual com duas casas, contagens com precisão visual zero. Alinhamento e unidade devem seguir a captura. BLANK não é convertido em zero; mensagens especiais para ausência de dados e novos estados negativos continuam propostas até inspeção específica. Depende do contrato e da formatação do indicador; não copiar a lógica de uma medida entre grãos diferentes.

### DS-C04 — Gráfico temporal

**Homologado para a composição inspecionada, com ressalva de densidade em Fit to Page.** Linha de receita líquida e lucro bruto, `DimCalendario[AnoMes]` ordenado por `AnoMesOrdem`; coorte do pedido. Referência 1848 × 304 px, x=36, y=382. Título 17 pt, eixos 16 pt, legenda 15 pt, eixo monetário em milhões/zero casas; azul e verde-petróleo do tema. Subtítulo automático oculto. Não mudar grão, perspectiva ou escala por estética. O tooltip nativo usa os campos existentes; personalização de tooltip permanece proposta. A série de 45 meses mantém os pontos e rótulos inclinados; não homologar esse layout como solução universal para intervalos densos em telas reduzidas.

### DS-C05 — Ranking horizontal

**Homologado.** Canal e Top 5 em barras horizontais, 912 × 330 px, y=710, x=36/972. Títulos 17 pt; categorias e valores dos eixos 16 pt; milhões/zero casas. Nomes completos e espaçamento nativo foram inspecionados. O ranking usa `VisualTopN.ItemCount=5` e ordenação decrescente pela Receita Analítica Após Devoluções. Filtro e ordenação devem acompanhar o contexto; não simular Top N por recorte ou ocultação. O baseline de Jan–Set/2026 retornou cinco categorias sem empate no limite. Não há política adicional de desempate homologada para futuros dados com empate; qualquer mudança precisa de evidência no visual nativo e do contrato aprovado.

### DS-C06 — Interações e contexto

**Homologado nos cenários manuais relatados.** Período, Canal e Loja são filtros da página; categoria é seleção do gráfico financeiro. A interação categoria → Pedidos concluídos é `NoFilter`, protegendo a métrica de cabeçalho. Não sincronizar Produto/Categoria com páginas de métricas de pedido sem contrato de grão. As regras dependem das relações e medidas vigentes; reutilização exige conferir interações dos novos visuais, não apenas copiar cores e posições.

## 12. Governança e registro de decisões

Adicionar token/cor somente com contraste verificado, significado único, caso de uso, impacto nos visuais e atualização do tema. Novos componentes reutilizam grid, escala tipográfica, rótulos, unidades e estados deste documento. Mudança de identidade incrementa a versão e revisa todas as páginas e tema; páginas existentes não devem depender de cores locais sem decisão registrada.

| ID | Decisão | Justificativa | Data | Estado | Impacto/dependências |
|---|---|---|---|---|---|
| DS-001 | Nome InfoTech / InfoTech Intelligence e wordmark tipográfico provisório | Identidade neutra para comércio de informática, sem inventar dados institucionais | 2026-10-12 | Aprovada como direção | Cabeçalho e futura navegação; sem logotipo |
| DS-002 | Base clara com azul, verde-petróleo e neutros | Leitura corporativa e poucos destaques simultâneos | 2026-10-12 | Aprovada como direção | Paleta tema e páginas |
| DS-003 | Escurecer Text Secondary para `#5B6B82` | `#64748B` resulta em 4,44:1 sobre o canvas, abaixo do alvo 4,5:1 | 2026-10-12 | Proposta técnica v0.1 | Revalidar contraste quando o fundo mudar |
| DS-004 | Usar somente visuais nativos estáveis no desenho inicial | Reduzir risco de compatibilidade e custo de manutenção | 2026-10-12 | Proposta | “Goals” e “List slicer” estão em Preview |
| DS-005 | Between para período e dropdowns para Canal/Loja, rótulo único | Seleção legível e operação aprovada manualmente | 2026-10-12 | Homologado na Visão Executiva | DS-C02; slicers `a200...` |
| DS-006 | Eixos 16 pt, títulos 17 pt e legenda 15 pt no Full HD | Corrigir ressalva de fonte pequena; preservar hierarquia | 2026-10-12 | Homologado na captura, com ressalva de densidade | DS-C04/05; gráficos `a400...`, `a500...`, `a600...` |
| DS-007 | KPI 32 pt, título 13 pt; BRL/% duas casas e contagem inteira | Consistência e leitura; valores reconciliados | 2026-10-12 | Homologado | DS-C03; cartões `a300...` |
| DS-008 | Top N real e ordenação decrescente | Exibir ranking contextual sem barras ocultas | 2026-10-12 | Homologado sem empate no baseline | DS-C05; `VisualTopN=5` |
| DS-009 | Categoria não filtra Pedidos concluídos | Preservar o grão de cabeçalho | 2026-10-12 | Homologado por relato manual | DS-C06; interação `NoFilter` |
| DS-010 | Nome da página sem período estático | Evitar contexto enganoso ao mudar datas | 2026-10-12 | Homologado na captura | DS-C01; textbox `a100...` |

Mudanças pequenas de espaçamento podem ser incorporadas na próxima revisão; mudanças de significado, paleta ou interação recebem novo ID. A v0.2 homologa os componentes explicitamente identificados acima. As direções anteriores DS-001–004 são preservadas como histórico; tema JSON continua com a identidade v0.1, pois a revisão documental não redefine paleta nem exige renomear o recurso registrado.

## 13. Variações comerciais e candidatos à v0.3 — Fase 5.2

A versão permanece v0.2. A Análise Comercial reutiliza DS-C01–06; os padrões abaixo foram implementados e inspecionados nessa composição, mas reutilização em outras páginas exige validação.

- **Navegação real:** 624 × 56 px, x1260/y30, texto 15 pt; dois destinos, estados branco/escuro e azul/branco. Cabeçalho em largura 1200 px nas duas páginas. Navegação nos dois sentidos após salvar/reabrir e após recuperação da queda de energia.
- **Contexto sincronizado:** grupos `InfoTech.PeriodoComercial`, `InfoTech.Canal`, `InfoTech.Loja` nas duas páginas. Produto/Categoria ficam fora. Estado final limpo, sem impor Jan–Set/2026; esse intervalo é janela de teste.
- **Status subordinado:** quatro cartões de 450 × 100 px, valor 24 pt/título 13 pt: Cancelados, Confirmados, Conclusão/Total, Cancelamento/Total. Confirmados não integram os outros status; preservar BLANK e o denominador.
- **Fonte renderizada:** na primeira composição comercial, o Desktop mostrou `Axis font reduced` e 9 pt para eixo configurado em 16 pt. Nos quatro gráficos comerciais, `general.responsive=false` preserva a fonte; o painel nativo confirmou 16 pt. Temporais 912 × 280 px, eixos 16 pt/legenda 15 pt; barras 912 × 268 px, categorias 16 pt/eixo monetário 14 pt; títulos 17 pt. A Visão Executiva não recebeu mudança de responsividade nesta fase; registros históricos de tamanho configurado não são medição universal da fonte renderizada.
- **Densidade temporal:** `AnoMes` ordenado, categoria mínima 80 px; rolagem necessária para intervalos longos, mantendo todos os pontos. Nove meses cabem na janela de teste. Inclinação/rotação é nativa; não reduzir automaticamente fonte para acomodar 45 nomes.
- **Ranking de lojas:** Top 5 contextual incluindo `(Blank)` quando elegível; dez lojas nomeadas permanecem no slicer. Sem scrollbar na composição final. Ticks monetários podem quebrar linha ou truncar o último texto em contextos amplos/viewport reduzido; essa restrição não é padrão universal homologado. Tooltip BRL e título R$ milhões preservam unidade.

YTD visual segue como refinamento específico por falta de espaço; contratos DAX validados. Acessibilidade completa e benchmark da última composição não foram estabelecidos. Ver [relatório da Fase 5.2](phase-5.2-commercial-dashboard.md). A [orientação Microsoft sobre responsividade](https://learn.microsoft.com/en-us/power-bi/create-reports/power-bi-create-mobile-optimized-report-format-visuals) descreve a adaptação nativa; cada componente deve ser conferido no painel e na renderização real.

## 14. Produtos e Categorias — Fase 5.3

A versão permanece **v0.2**. DS-C01–06 foram reutilizados na terceira página Full HD; estes componentes foram implementados e conferidos nessa composição, com candidatos à v0.3 sem promoção automática do tema:

| Componente | Configuração observada | Estado e limite |
|---|---|---|
| DS-C01 + navegador | Cabeçalho 920 × 76 px, x36/y22; Page Navigator 896 × 56 px, x988/y30, três colunas, texto 15 pt | Três nomes completos, ativo azul/branco; somente largura/cabeçalho/navegação ajustados nas páginas anteriores |
| DS-C02 compartilhado | Between 760 × 112 px, slider e duas datas, responsividade desligada; Canal/Loja iguais à referência comercial | Grupos Período/Canal/Loja incluem um controle por página; seleção/limpeza sincronizadas, estado final limpo |
| Faixa local, candidata | Categoria 760 × 80 px e Produto 1064 × 80 px, y224, fonte 13 pt; pesquisa de Produto | Sem sincronização; categoria restringe catálogo; pesquisa, teclado/foco e limpeza independente exercitados |
| DS-C03 | Quatro cartões 450 × 136 px, y312; valor 32 pt/título 13 pt; BRL/% duas casas | Receita após devoluções, COGS ajustado, lucro e margem; BLANK e sinais negativos preservados |
| DS-C05 produto | Top 5 real; SKU no eixo, nome completo no tooltip; 912 × 320 px | Top 10 exigia rolagem; Top 5 sem scrollbar, catálogo completo no filtro/matriz; decrescente por receita |
| DS-C05 categoria | Todas as 12 categorias; 912 × 320 px | Rolagem vertical necessária e testada. Não homologar como componente sem rolagem |
| Tipografia dos rankings | Categoria 16 pt, eixo monetário 14 pt, título 17 pt; `responsive=false` | Escala monetária automática, uma casa nos ticks, título R$; evita ticks repetidos e zeros em recortes pequenos. Tooltip/valores financeiros completos com duas casas |
| Matriz hierárquica, candidata | 1848 × 244 px, y800, fonte 13 pt, Outline, Categoria → Produto; sete valores | Inicialmente recolhida; margem recalculada, BRL/% duas casas; rolagem vertical necessária, sem overflow horizontal observado |
| DS-C06 | DataFilter explícito dos rankings/matriz para outros analíticos | Grão de item/produto; nenhum valor de cabeçalho ou frete atribuído; filtros locais não alteram páginas 1–2 |

Canvas e fontes foram inspecionados em Fit to Page (45% no viewport 1366 × 720), captura ampliada do Desktop e tamanho real 100% por rolagem do canvas. A escala reduzida não torna a página integralmente confortável em qualquer tela; não homologar leitura universal em telas pequenas. Alt text/tab order dos 14 visuais presentes; teclado/foco exercitados no Produto. Leitor de tela, daltonismo e escala de cinza não foram testados nesta fase.

Ver [Fase 5.3](phase-5.3-products-categories-dashboard.md) para reconciliações, capturas, desempenho e restrições. A biblioteca não requer alteração de DAX, relacionamentos, tema-fonte ou banco.
