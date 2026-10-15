# InfoTech — Design System v0.3

**Versão vigente:** InfoTech Design System v0.3, consolidada na Fase 5.6C em 2026-10-14. O usuário aprovou explicitamente a estética atual das cinco páginas após a Fase 5.6B.1. Esta versão documenta e governa a implementação existente; não redesenha páginas, não muda o modelo e não certifica acessibilidade ou responsividade universal.

**Preservação de histórico:** as seções 1–18 registram a v0.2 e os retratos das fases em que foram escritos, incluindo estados “candidato” ou “pendente” corretos à época. A referência normativa consolidada atual é a seção 19; ela resolve esses estados conforme PBIR, evidências reais e testes posteriores, sem reescrever fases passadas. “Implementado” descreve PBIR; “funcionalmente validado” limita-se aos cenários identificados; “aprovado esteticamente” registra a decisão explícita do usuário.

## 1. Identidade

| Elemento | Definição |
|---|---|
| Empresa fictícia | InfoTech |
| Identidade analítica | InfoTech |
| Segmento | Comércio de produtos de informática e tecnologia |
| Posicionamento | Inteligência comercial, financeira e operacional baseada em dados |
| Personalidade | Tecnológica, confiável, objetiva, moderna e profissional |

O nome vigente e o wordmark são **InfoTech**, acompanhados pelo monograma geométrico I/T. A identidade inicial “InfoTech Intelligence” pertence ao histórico das fases anteriores, não ao nome atual. A navegação deve privilegiar nomes de área; títulos de página descrevem a pergunta analítica. O rodapé, quando útil, informa o intervalo de dados e a perspectiva temporal, nunca presume que a data de hoje seja a última atualização. Não criar endereço, CNPJ, história, número de funcionários ou outros dados institucionais. Manter o nome em um único ponto de configuração visual para permitir substituição futura.

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

- Na implantação histórica, o tema exibido era `InfoTech Intelligence — Light v0.1`; desde a Fase 5.4.2.1, seu nome de exibição é `InfoTech — Light v0.1`. O Desktop havia aceitado a importação e indicado o tema como atual. Ao registrar o tema, expandiu `dataColors` de oito para 480 cores, mantendo os oito tokens iniciais na mesma ordem e sem alterar as demais propriedades do tema-fonte.
- A página reutilizada foi definida em Full HD 1920×1080, com cabeçalho tipográfico, filtros compactos, quatro cartões, uma linha temporal e duas barras horizontais.
- Os sete testes manuais foram aprovados pelo usuário na Fase 5.1.2: período, canal, loja, combinação, categoria, acessibilidade/desempenho e persistência. O relato é evidência manual, sem valores detalhados para cada seleção.
- À época da homologação da Visão Executiva, o cabeçalho continha InfoTech Intelligence e Visão Executiva; o período atual era identificado no slicer. A inspeção confirmou quatro KPIs, quatro canais, cinco categorias, ausência de cortes nos nomes e ausência de scrollbar no ranking. O nome do cabeçalho foi atualizado para InfoTech na Fase 5.4.2.1.
- A exportação local `PowerBIPerformanceData.json` contém 153 eventos completos de ciclo de vida de visual, entre 45 e 408 ms, e ações de slicer/cross-highlight. Esses intervalos são calculados dos timestamps da sessão anterior ao refinamento; não equivalem a tempo de carregamento inicial da página, SLA ou benchmark após a mudança. Condições de cache e atribuição exata aos cenários não estão registradas. Ver o relatório da Fase 5.1.2.
- Contraste dos tokens continua com as medições documentadas; leitor de tela e escala de cinza não são declarados testados.

## 11. Biblioteca de componentes

### DS-C01 — Cabeçalho corporativo

**Linha de base v0.2:** wordmark 30 pt, nome da página 12 pt, cores Text Primary/Text Secondary; textbox em x=36, y=22, 1848 × 76 px na Visão Executiva. Usar o nome da página sem período estático quando o slicer permitir outras datas. Texto alternativo também deve evitar datas fixas.

**Candidato à v0.3 — Fases 5.4.2/5.4.2.1:** símbolo monograma vetorial 48 × 48 px em x=36, y=36 e textbox da marca em x=96, y=22, 520 × 76 px. O wordmark atual é InfoTech em 30 pt e o nome da página em 12 pt. A composição foi aplicada às quatro páginas, mantendo o Page Navigator a partir de x=636 e o botão Filtros. A inspeção anterior observou o símbolo nos quatro cabeçalhos; a nova homologação visual não foi concluída, e a composição aguarda revisão estética final.

**Biblioteca candidata:** `powerbi/branding/infotech/infotech-monogram.svg` é a variante aplicada, com viewBox 64 × 64, traços azul Primary `#2563EB` e verde-petróleo Secondary `#0F9D92`, fundo transparente e geometria original I/T sem dependência de fontes. Recomenda-se área de apresentação mínima de 40 × 40 px e manter proporção quadrada, sem recortar, recolorir, adicionar sombra ou esticar. `infotech-monogram-mono.svg` é alternativa monocromática; `infotech-horizontal.svg` usa apenas InfoTech e não está aplicada. Manter respiro visual ao redor e usar apenas sobre fundo claro. O arquivo vetorial aplicado foi registrado no pacote de recursos do PBIP; reabertura final no Desktop continua pendente.

As três propostas avaliadas foram: A) monograma geométrico I/T, selecionado pelo usuário; B) estrutura abstrata de nós conectados para sugerir inteligência de dados; C) wordmark com detalhe geométrico discreto. A e suas variações são as únicas desenhadas como vetores locais; B e C permanecem conceitos documentais. A revisão estética final da composição continua pendente.

DS-C02, DS-C03, padrão de cartões secundários e acabamento do Page Navigator seguem **candidatos à v0.3**, não homologados nesta fase. O botão Filtros mantém texto, azul `#1D4ED8`, branco e 16 pt; Fechar filtros mantém `#DBEAFE`, texto `#142238` e 16 pt. Nenhum ícone foi acrescentado ao botão. Os cartões mantêm valores 32 pt e títulos 13 pt, sem alteração de métricas ou números. O navegador nativo permanece sem alterações.

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

## 15. Custos e Margens — Fase 5.4 (candidatos à v0.3)

No registro da Fase 5.4, a versão vigente era **InfoTech Intelligence v0.2**. A base atual continua v0.2, com o nome de marca atualizado para InfoTech na Fase 5.4.2.1. A quarta página reutiliza DS-C01–06 e mantém canvas Full HD de 1920 × 1080 px, fundo `#F5F7FB`, superfícies brancas, Segoe UI, margens de 36 px e espaçamento de 8 px. Os componentes abaixo foram implementados e renderizados no Desktop, mas não promovem automaticamente a versão da biblioteca:

| Componente candidato | Implementação observada | Estado e limites |
|---|---|---|
| Navegação de quatro páginas | Navegador nativo horizontal com os quatro nomes completos, destino ativo azul/branco e faixa superior do cabeçalho | Destinos válidos e página ativa vistos no Desktop. A escala de encaixe depende do viewport; não inferir legibilidade universal em telas pequenas. |
| DS-C02 compartilhado | Between 760 × 112 px, data inicial/final e slider horizontal de duas alças; Canal e Loja em dropdown; grupos `InfoTech.PeriodoComercial`, `InfoTech.Canal` e `InfoTech.Loja` | Canal e Loja filtraram a página e sincronizaram com páginas existentes em testes observados. A alça de período mudou o intervalo e os indicadores; o seletor de data abriu. Não equivale à validação exaustiva dos três filtros em todos os sentidos. |
| KPIs financeiros por coorte | Quatro cartões principais 450 × 136 px, valor 32 pt/título 13 pt: receita após devoluções, COGS ajustado, lucro bruto e margem; faixa complementar com COGS original, reversão sellable, COGS ajustado e perda non-sellable | Custos mantêm a precisão homologada; perda non-sellable é identificada como já incluída. Ver valores e semântica no relatório da Fase 5.4. |
| Evolução monetária de três séries | Linha temporal mensal com receita, COGS ajustado e lucro bruto por coorte do pedido; título 17 pt, eixos 16 pt e legenda 15 pt | Candidato; usar escala monetária comum e não incorporar recebimento de devolução ou movimento de fulfillment nessa coorte. |
| Comparação financeira por dimensão | Barras horizontais de lucro bruto por Canal e Categoria; tooltips com receita, COGS ajustado e margem | Categorias filtram métricas atribuíveis aos itens; indicadores de cabeçalho não são alocados ao produto. Ranking ordenado por lucro bruto. |
| Ponte do COGS | COGS original concluído − reversão sellable = COGS ajustado; cartão informativo de perda non-sellable | Padrão candidato: a perda non-sellable permanece dentro do custo e não deve ser deduzida novamente. Não representa fluxo operacional por data de movimento/recebimento. |

O viewport usado na inspeção do Desktop foi 1152 × 513 px; a captura Fit to Page exibiu a página inteira a 26%, com redução visual dos textos. A definição do canvas permanece Full HD; tamanhos configurados não garantem leitura equivalente em qualquer viewport. Os tamanhos e limites observados, inclusive aspectos de acessibilidade não testados, constam em [Fase 5.4](phase-5.4-costs-margins-dashboard.md). A v0.2 segue vigente até revisão formal posterior.

## 16. Painel recolhível de filtros — Fase 5.4.1 (candidato à v0.3)

No registro da Fase 5.4.1, a versão vigente era **InfoTech Intelligence v0.2**. A base atual permanece v0.2 sob o nome InfoTech. A apresentação permanente de DS-C02 da v0.2 permanece no histórico; a variação abaixo é candidata e não promove automaticamente o design system.

- Em quatro páginas Full HD, Período Between, Canal e Loja ficam em grupo horizontal nativo aberto/fechado por bookmarks. O estado fechado é inicial; os filtros continuam aplicados.
- Datas e slider de duas alças preservam DS-C02; Canal/Loja usam dropdowns existentes. `InfoTech.PeriodoComercial`, `InfoTech.Canal` e `InfoTech.Loja` continuam sincronizados. Categoria e Produto pesquisável são locais à página Produtos e Categorias.
- A superfície é branca `#FFFFFF` com contorno claro `#E2E8F0`. O botão de abertura usa `#1D4ED8` com texto branco, fonte Semibold 16 pt e contraste calculado de 6,70:1; o botão de fechamento usa `#DBEAFE` com texto `#142238`, fonte Semibold 16 pt e contraste calculado de 13,08:1. A renderização foi conferida em Fit to Width; escala de cinza, foco por teclado completo e certificação WCAG não foram testados.
- Geometria do grupo: x24/y96, largura 1872 px; altura 136 px nas páginas regulares e 224 px em Produtos e Categorias. A posição dos membros internos é relativa à origem do grupo; manter fundo, controles e fechamento dentro dos limites.
- Navegador nativo: x636/y30, 1000 × 56 px; botão Filtros: x1652/y30, 232 × 56 px. Os quatro destinos aparecem integralmente no desktop testado.
- O painel aberto sobrepõe parte do conteúdo analítico; no estado fechado os visuais usam o espaço recuperado. Não há indicador dinâmico de valores de filtro no botão; os controles continuam acessíveis ao abrir o painel.

Ações abrir/fechar, preservação de seleção, sincronização compartilhada, contraste visual, navegador, reabertura do PBIP e disposição local de Categoria/Produto foram conferidos no Desktop. A captura usou viewport 1152 × 513 px em Fit to Width. Leitor de tela, percurso completo por Tab, escala de cinza e contraste automatizado não foram testados. O Performance Analyzer registrou somente atualização aquecida; não homologar como benchmark frio. Ver [relatório da Fase 5.4.1](phase-5.4.1-collapsible-filter-panel.md) e [pacote de evidências](evidence/archives/fase-5.4.1-evidencias.zip).

## 17. Regularização da marca — Fase 5.4.2.1

O nome vigente é **InfoTech**; **InfoTech Intelligence** permanece somente como denominação histórica nas fases anteriores. O monograma I/T é o símbolo escolhido pelo usuário. Os cabeçalhos das quatro páginas foram vistos no Desktop em 47% de zoom e exibem consistentemente o monograma e o wordmark InfoTech. A composição continua candidata à v0.3 até a inspeção ampliada e revisão estética final.

Na página Custos e Margens, o rótulo acima dos cartões secundários usa 31 px de altura e o título “Composição do custo analítico — corte do pedido”. O título da tendência mensal usa “por mês de corte”. Essas propriedades foram conferidas nos arquivos PBIR e em captura real da página Custos e Margens no Desktop. A visão geral das quatro páginas foi examinada em 47% de zoom; a leitura ampliada e Fit to Page permanecem pendentes.

Botões, cartões KPI e Page Navigator permanecem com os estilos previamente registrados. A aparência geral foi conferida nas quatro páginas, sem refinamento novo; bordas, padding, foco e detalhes tipográficos requerem revisão ampliada. A v0.2 segue como base; a futura v0.3 depende da inspeção real dos quatro dashboards, dos cartões, dos controles e da revisão estética. Consulte [relatório da Fase 5.4.2.1](phase-5.4.2.1-infotech-branding-closure.md).

## 18. Devoluções — Fase 5.5 (candidatos à v0.3)

A quinta página preserva **InfoTech v0.2** como referência vigente. A composição foi implementada no canvas Full HD, mas a inspeção desta fase foi parcial e não promove estes componentes a padrão homologado.

| Componente candidato | Implementação observada | Estado e limite |
|---|---|---|
| Page Navigator de cinco destinos | Destinos Visão Executiva, Análise Comercial, Produtos e Categorias, Custos e Margens e Devoluções; fonte ajustada a 14 pt e faixa alargada com alteração mínima do cabeçalho | Nomes completos visíveis na janela do Desktop; escala de 36% e sem revisão em Fit to Page/100%. Não homologar universalmente em viewports menores |
| DS-C02 na página Devoluções | Between com dois campos de data e slider horizontal; Canal e Loja compartilhados; painel via bookmarks | Painel aberto foi capturado; bookmark de fechar ocultou o painel e o usuário confirmou o clique em Fechar filtros. Arrasto, edição das datas e sincronização completa ainda não foram testados |
| KPIs de devoluções | Valor comercial por pedido, reversão sellable, perda non-sellable e percentual comercial; rótulos com perspectiva explícita | Renderizaram no Desktop; DAX e contextos combinados não foram reconciliados nesta fase |
| DS-C04 temporal | Valor comercial devolvido por mês da data do pedido, eixo em R$ mil | Renderizou em escala observada; escala temporal Jan–Set/2026 e variação de viewport pendentes |
| DS-C05 categorias e produtos | Barra por valor comercial devolvido por categoria e Top 5 produtos | Renderizaram em escala observada; filtragem/cross-highlighting, nomes longos e casos sem dados pendentes |
| Contexto de custos de devolução | Sellable reduz COGS analítico; non-sellable já está incorporado | Nota exibida; a perda não pode ser deduzida novamente. A v0.2 não aprova uma soma de impacto financeiro total |

Não há medida de reembolso efetivo no modelo. As medidas disponíveis para contagem de itens/unidades usam recebimento, enquanto o slider compartilhado está definido como coorte do pedido; elas não foram promovidas a KPIs dessa página. A operação por data de recebimento fica para estudo futuro com contratos temporais e filtros próprios. Nenhuma tipografia de devoluções é classificada como padrão homologado sem leitura ampliada em Full HD e Fit to Page. Ver [relatório da Fase 5.5](phase-5.5-returns-dashboard.md) e [capturas reais](evidence/phase-5.5/).

## 19. Referência normativa — InfoTech Design System v0.3

Esta seção é a referência atual para reproduzir e manter as cinco páginas. Se um registro histórico das seções 1–18 divergir por refletir o estado anterior, prevalecem aqui os valores atuais verificados. A v0.3 consolida padrões existentes; não cria um tema instalável, template independente nem nova funcionalidade.

### 19.1 Identidade, princípios e fontes

- Marca oficial: **InfoTech**. “InfoTech Intelligence” fica somente como identificação histórica dos primeiros artefatos; não usar como nome atual.
- Símbolo aplicado: monograma vetorial geométrico I/T, com traços azul e verde-petróleo, fundo transparente e proporção quadrada. Fonte `powerbi/branding/infotech/infotech-monogram.svg`; recurso PBIR `powerbi/ProjetoBI.Report/StaticResources/RegisteredResources/infotech-monogram6402263922348279.svg`. Ambos têm viewBox 64 × 64 e SHA-256 `29CA228E30EF819E4EF204C8864CCA155F31EB9C979E6E25E779E736667B343A`. Não redesenhar, esticar, recortar, recolorir ou adicionar sombra nesta fase.
- Princípios: minimalismo, superfícies claras, hierarquia analítica, azul como destaque, verde-petróleo moderado, bordas discretas e elementos decorativos contidos. Não depender somente da cor para transmitir significado.
- Fontes de verdade: PBIR atual para propriedades/posições; capturas reais em `evidence/phase-5.6b/` e `evidence/phase-5.6b.1/`; testes F01–F14/S01–S07 em `phase-5.6a.2-desktop-test-automation.md`; relatórios históricos para o alcance de cada fase.

### 19.2 Tokens cromáticos

A paleta permanece inalterada. Os pares de contraste são verificações específicas, não uma auditoria de todos os pixels do relatório.

| Token | Valor | Uso consolidado |
|---|---|---|
| Primary | `#2563EB` | Seleção ativa, links e destaque principal |
| Secondary | `#0F9D92` | Série secundária e traço do monograma; evitar texto pequeno sobre branco |
| Background | `#F5F7FB` | Canvas claro |
| Surface | `#FFFFFF` | Cartões, navegador inativo e conteúdo |
| Text Primary | `#142238` | Wordmark, títulos, números e texto principal |
| Text Secondary | `#5B6B82` | Nome de página e texto auxiliar |
| Border | `#E2E8F0` | Divisores, contornos e hover do Page Navigator; não usar como texto |
| Filter Button | `#1D4ED8` | Preenchimento de Filtros |
| Filter Close Surface | `#DBEAFE` | Superfície de Fechar filtros |

Positive `#15803D`, Negative `#B91C1C` e Warning `#B45309`, preservados da v0.2 e disponíveis no tema, são semânticos; não significam que cada KPI use essas cores. A sequência categórica começa `#2563EB`, `#0F9D92`, `#D97706`, `#7C3AED`, `#B91C1C`, `#475569`, `#0891B2`, `#A16207`; limitar séries e complementar cor por rótulo/posição quando necessário.

Checagens registradas: Primary/branco 5,17:1; Secondary/branco 3,36:1; Text Primary/branco 15,96:1; Text Secondary/branco 5,43:1; texto branco no botão `#1D4ED8` 6,70:1; Text Primary `#142238` em `#DBEAFE` 13,08:1. Secondary não é padrão para texto pequeno sobre branco. As razões correspondem a pares de tokens específicos, não a todos os elementos, fundos e estados. Não declarar conformidade WCAG global.

### 19.3 Canvas, escala e estrutura

- As cinco páginas medem 1920 × 1080 px, proporção 16:9, e têm `displayOption: FitToWidth` nos `page.json` atuais. O zoom muda o tamanho aparente, não a geometria PBIR.
- Margem de referência 36 px; unidade de espaçamento conceitual 8 px. O grid de 12 colunas é diretriz, não grade física aplicada pelo Power BI. Não inferir geometria uniforme onde as páginas variam.
- **Fit to Width** apresenta a largura do canvas; **Fit to Page** mostra largura e altura, reduzindo o zoom; **Actual Size/100%** inspeciona dimensão lógica e pode exigir rolagem. Fit to Width foi configurado nas cinco páginas, mas não garante leitura em qualquer monitor.
- Fase 5.6B: viewport de Computer Use 1152 × 575 px; Fit to Width entre 36% e 51%, Fit to Page 37% e inspeção a 100%. Fase 5.6B.1: monitor 1366 × 768 px, escala Windows 100%, janela 1366 × 720 px, Fit to Width 47%; as duas linhas de receita foram conferidas também a 100%. São condições observadas, não requisitos universais de hardware.
- Reservar espaço para títulos completos em pt-BR e rolagem nativa onde necessária. Não remover categorias/pontos nem reduzir fontes automaticamente para eliminar rolagem.

### 19.4 DS-C01 — cabeçalho InfoTech

| Elemento | Implementação de referência |
|---|---|
| Monograma | SVG 48 × 48 px, x=36, y=36; viewBox fonte 64 × 64 |
| Caixa de texto marca/página | x=96, y=22, 430 × 76 px |
| Wordmark | InfoTech, Segoe UI Semibold, 30 pt, `#142238` |
| Nome da página | Segoe UI, 12 pt, `#5B6B82`, abaixo do wordmark |
| Navegador | Inicia em x=546, y=30 |

As posições foram conferidas nos cinco `visual.json`. O SVG não contém wordmark: InfoTech é texto PBIR. Não fixar período dinâmico no cabeçalho. A caixa implementada tem 430 px; 520 px é medida de proposta histórica, não da implementação atual.

### 19.5 DS-C07 — Page Navigator nativo

O visual nativo Page Navigator usa uma linha e cinco colunas: Visão Executiva, Análise Comercial, Produtos e Categorias, Custos e Margens e Devoluções. Referência: x=546, y=30, 1090 × 56 px; padding da célula 4 px; Segoe UI Semibold 14 pt. Padrão: fundo branco/texto `#142238`; ativo: `#2563EB`/branco; hover registrado: `#E2E8F0`. Botão Filtros adjacente: x=1652, y=30, 232 × 56 px, texto centralizado Semibold 16 pt, fundo `#1D4ED8` e curva PBIR configurada em 8 px.

Os cinco destinos e os estados ativos foram exercitados. A automação usou seleção do Page Navigator e `Ctrl+Space`; é uma técnica observada nesta versão, não promessa de compatibilidade universal. Não substituir o navegador por cinco botões. Referências: `a7000000000000000001`, `b7000000000000000001`, `d7000000000000000001`, `e7000000000000000001` e `f5500000000000000002` em suas páginas.

### 19.6 DS-C02 — painel recolhível de filtros

O grupo de filtros fica em x=24, y=96, largura 1872 px; altura 136 px nas páginas regulares e 224 px em Produtos e Categorias, com coordenadas internas relativas ao grupo. Aberto, sobrepõe intencionalmente parte da primeira faixa analítica; fechado, libera o conteúdo. Não é uma coluna permanente reservada. Estado aberto/fechado pode variar conforme o estado salvo da página.

| Controle | Geometria/referência | Contrato |
|---|---|---|
| Período comercial | x=36, y=104, 760 × 112 px | `DimCalendario[Data]`, Between; título Semibold 13 pt; dois campos editáveis e slider horizontal de duas alças; fonte/campos 13 pt configurados |
| Canal | x=820, y=112, 450 × 80 px | Dropdown nativo, filtro global |
| Loja | x=1286, y=112, 402 × 80 px | Dropdown nativo, filtro global |
| Filtros | x=1652, y=30, 232 × 56 px | Bookmark para abrir; aparência na seção 19.5 |
| Fechar filtros | Posição relativa à camada agrupada, 180 × 56 px | Bookmark para fechar; `#DBEAFE`, texto `#142238`, Semibold 16 pt |
| Categoria/Produto | Apenas em Produtos e Categorias | Seleções locais, não sincronizadas |

Os três grupos encontrados em cada uma das cinco páginas são `InfoTech.PeriodoComercial`, `InfoTech.Canal` e `InfoTech.Loja`. Datas digitadas/arrastadas, Canal/Loja, combinações/limpeza, efeitos analíticos e sincronização foram testados em F01–F14/S01–S07. Categoria/Produto permaneceram locais nos cenários exercitados; reabrir o painel preservou seleção. Isto não cobre todo estado de filtro possível.

A interação dos botões no canvas e abrir/fechar foi observada. A configuração interna completa dos bookmarks (Display/Data/visuais selecionados) não foi reinspecionada integralmente na 5.6A.2. Alterar bookmark, grupos, visibilidade ou hierarquia é de alto risco e requer regressão funcional. Conferir ambos os estados e o conteúdo sobreposto.

### 19.7 DS-C03 — cartões KPI

Cartões nativos Card, superfície branca; título Segoe UI Semibold 13 pt, valor Semibold 32 pt nos principais. Referência de quatro cartões 450 × 136 px nos x=36, 502, 968 e 1434, espaçados em 16 px. A unidade/contexto deve ser explícita. Não acrescentar sombra, raio ou padding não confirmado no PBIR.

| Página | Variação legítima observada |
|---|---|
| Visão Executiva | Quatro KPIs em y=128: receita líquida, lucro, margem e pedidos concluídos |
| Análise Comercial | Quatro principais em y=128; quatro subordinados de 450 × 100 px em y=280 |
| Produtos e Categorias | Quatro KPIs financeiros em y=128; grão de item/produto |
| Custos e Margens | Quatro KPIs em y=128; quatro complementares de 450 × 112 px em y=304; legenda de seção 1848 × 31 px em y=272 |
| Devoluções | Quatro KPIs em y=128 com contexto explícito para devolução comercial, reversão sellable, perda non-sellable e percentual |

O tamanho configurado não assegura escala renderizada universal. Não atribuir total de cabeçalho a Produto/Categoria nem deduzir perda non-sellable do COGS ajustado novamente. Zero válido permanece zero; BLANK não é zero. Não calcular margem agregada como média de margens.
### 19.8 DS-C04 — gráficos temporais e DS-C05 — rankings/matriz

| Componente e referência | Construção consolidada | Variações/limites |
|---|---|---|
| Linha receita/lucro executiva, `a4000000000000000001` | x=36, y=284, 1848 × 340 px; título 17 pt; eixos 16 pt; legenda 15 pt; eixo em milhões | Receita líquida e lucro por mês; eixo usa `labelPrecision=1L` desde 5.6B.1 |
| Receita mensal comercial, `b4000000000000000001` | x=36, y=396, 912 × 320 px; título 17 pt; eixos 16 pt; legenda 15 pt; milhões | Coorte por data do pedido; `labelPrecision=1L`; rolagem temporal preserva todos os pontos |
| Volume mensal, `b4000000000000000002` | x=972, y=396, 912 × 320 px | Série de contagem, não eixo monetário |
| Custos por coorte, `e5000000000000000001` | x=36, y=432, 1848 × 248 px; título 17 pt, eixos 16 pt, legenda 15 pt | Receita após devoluções, COGS e lucro por data do pedido; precisão de eixo 0 |
| Produtos, `d5000000000000000001/2` | Duas barras 912 × 340 px em x=36/972, y=284; título 17 pt; categoria 16 pt; moeda 14 pt | Top 5 por SKU com nome completo em tooltip; 12 categorias. Rolagem de categorias é intencional |
| Matriz `d6000000000000000001` | x=36, y=648, 1848 × 396 px; Categoria → Produto, inicialmente recolhida | Unidades, linhas, receitas, COGS, lucro e margem preservam o grão; rolagem vertical |
| Devoluções `f5500000000000000016/17/18` | Linha em R$ mil e barras por categoria/Top 5 produto | Linha e rankings por coorte do pedido; tooltip identifica produto |

Títulos de gráfico usam Segoe UI Semibold 17 pt; eixos/categorias em geral 16 pt; legenda temporal 15 pt. Exceção: eixos monetários de rankings comerciais/de produto podem usar 14 pt conforme densidade. Unidades, escalas, responsividade e precisão são locais a cada visual. `labelPrecision=1L` vale apenas para os dois eixos temporais de receita da Executiva e Comercial, quando zero casas arredondava ticks próximos em rótulos repetidos/ambíguos. A precisão das medidas DAX não mudou. Outros eixos mantêm suas configurações locais.

### 19.9 Números, tempo e contexto analítico

- Cultura visual pt-BR: `R$`, ponto de milhar e vírgula decimal; moeda em cartões/tabelas com duas casas segundo a medida; percentual com duas casas; contagem inteira. Valor negativo mantém sinal explícito conforme o formato do campo. Rótulos abreviados nativos não substituem o valor completo em cartão/tooltip.
- Unidade/escala é propriedade local: há eixos em milhões (`labelDisplayUnits=1000000D`), milhares (`1000D`) e valores sem abreviação. Só os dois eixos temporais de receita aprovados usam uma casa; demais visuais têm precisão própria. Não arredondar medidas intermediárias para aparência.
- Período comercial usa `DimCalendario[Data]` em Between. Os dois campos são editáveis; slider permite ajuste gráfico e não substitui digitação para data exata em zoom reduzido.
- Perspectivas: coorte/data do pedido para receita financeira/comercial, produto e devolução; `movement_date` para movimento operacional de custos; `return_received_date` para recebimento operacional de devolução. Não misturar as séries como uma cronologia. O dataset termina em 30/09/2026; não extrapolar pelo relógio atual.
- Valor comercial devolvido não é refund efetivo. Reversão sellable reduz COGS analítico; perda non-sellable já está incluída no COGS ajustado. Definições completas ficam nas descrições de `_Medidas.tmdl` e em `DASHBOARD_ARCHITECTURE.md`.

### 19.10 DS-C06 — interações, estados e reutilização

Categoria/Produto filtram ou realçam análises locais de itens nas páginas pertinentes; não atribuem medidas de cabeçalho a produtos. Período/Canal/Loja preservam sincronização nos cenários aprovados; limpeza seletiva conserva as demais seleções testadas. Rankings e matrizes preservam grão, ordenação e Top N reais.

Não converter BLANK em zero, esconder categorias para simular Top N, somar percentuais ou depender apenas de cor. A mensagem personalizada “Sem dados” é recomendação, não estado implementado universalmente. Reutilizar componentes reproduzindo propriedades PBIR e validando o comportamento nativo, não imitando pixels de uma captura.

### 19.11 Acessibilidade — validação parcial

**Observado/testado:** inspeção visual das cinco páginas, checagens de pares de contraste da seção 19.2 e cenários de filtros, navegação, resposta dos KPIs e persistência F01–F14/S01–S07. Parte dos visuais contém propriedades `altText`; sua presença no PBIR não prova qualidade assistiva.

**Não homologado:** percurso completo por Tab, tab order/foco perceptível em todos os controles, operação integral por teclado, nomes acessíveis de todos os elementos, leitor de tela, escala de cinza, cobertura de contraste de todos os textos/estados, avaliação assistiva e certificação WCAG. Aprovação estética não certifica acessibilidade.

**Recomendação para fase autorizada:** conferir cada página por teclado, ordem/foco, campos/slider/botões, nomes acessíveis/texto alternativo, leitor de tela e contraste em estados renderizados; distinguir seleção sem depender só de cor. As recomendações não autorizam alteração PBIR nesta consolidação.

### 19.12 Viewport e responsividade

A referência é desktop 16:9 Full HD. Fit to Width reduz a escala aparente; 47%, 37% e 100% são zooms observados em janelas/sessões específicas. A Fase 5.6B inspecionou todas as páginas em Fit to Width e, em condições documentadas, Fit to Page/100%; a 5.6B.1 conferiu as duas linhas de receita em Fit to Width e 100%. Rolagem de calendário, matriz e listas longas é nativa e preserva categorias/pontos. O painel aberto cobre temporariamente a primeira faixa analítica.

Não há layout mobile específico nem leitura validada em todos os tamanhos/proporções de tela. Não classificar o sistema como universalmente responsivo, nem tratar tipografia configurada como defeito só porque encolhe no zoom reduzido. Conferir a escala efetiva no dispositivo-alvo em fase autorizada.
### 19.13 Governança de mudança

| Risco | Exemplos | Revisão obrigatória |
|---|---|---|
| Baixo | Correção de texto, pequeno espaçamento, borda ou tipografia sem mudar significado | Diff PBIR/documental e comparação da peça afetada em Fit to Width e tamanho real adequado |
| Médio | Geometria de cartões/gráficos, cabeçalho, Page Navigator, densidade e distribuição | Rever página inteira e estados relevantes; verificar cortes/rolagem, os cinco destinos e salvar/fechar/reabrir se PBIR mudar |
| Alto | Bookmarks, grupos sincronizados, interações/DataFilter, perspectiva temporal, DAX, relações, modelo, fontes ou dados | Autorização específica, auditoria técnica/analítica e regressão proporcional; testar origem/destino/persistência. Não chamar de ajuste visual simples |

#### Checklist reutilizável de nova página

- [ ] Confirmar objetivo, grão, medidas autorizadas e perspectiva temporal.
- [ ] Usar marca InfoTech, SVG I/T, tokens existentes e tipografia documentada.
- [ ] Canvas 1920 × 1080; respeitar alinhamentos/margens e ajustar ao conteúdo real.
- [ ] Cabeçalho identifica página; Page Navigator nativo preserva os cinco destinos e estado ativo.
- [ ] Definir filtros globais/locais e preservar os grupos `InfoTech.*` conforme o contrato.
- [ ] KPI inclui nome/unidade, grão, elegibilidade, BLANK/zero, sinal e formato; não atribuir valor de cabeçalho ao produto.
- [ ] Gráfico tem título, eixo/unidade, ordenação e perspectiva identificada; conferir escala/fonte/precisão do visual.
- [ ] Ranking declara Top N e ordenação real; matriz preserva hierarquia e rolagem sem ocultar membros.
- [ ] Separar interação, reconciliação analítica, aprovação visual e revisão assistiva.
- [ ] Conferir Fit to Width e tamanho ampliado; testar estados aberto/fechado do painel.
- [ ] Registrar limitações, links e evidências sem tratá-las como certificação.
- [ ] Se PBIR mudar, validar persistência/reabertura e integridade; refresh somente com autorização explícita.

### 19.14 Rastreabilidade atual

| Padrão | Implementação de referência | Evidência | Estado v0.3 |
|---|---|---|---|
| Identidade, cabeçalho e monograma | Cinco cabeçalhos e SVG fonte/registrado | Fases 5.4.2.1/5.6B; capturas 5.6B.1 | Estética aprovada; dimensões conferidas no PBIR |
| Canvas/enquadramento | Cinco páginas 1920 × 1080 em `FitToWidth` | Fase 5.6B e capturas 5.6B.1 | Implementado; viewport universal não homologado |
| Page Navigator | `a700…`, `b700…`, `d700…`, `e700…`, `f550…0002` | Fase 5.6A.2 e F01–F14/S01–S07 | Funcionalmente validado no Desktop; técnica `Ctrl+Space` limitada ao ambiente |
| DS-C02 e grupos | Slicers em cinco páginas; nomes `InfoTech.*` | Fases 5.2.1/5.4.1/5.6A.2 | Cenários funcionais aprovados; opções internas completas dos bookmarks não revalidadas |
| Cartões KPI | Visuais por página e medidas `_Medidas` | Fases 5.6A.2/5.6B/5.6B.1 | Estética aprovada; acessibilidade parcial |
| Linhas, rankings e matriz | Visuais listados em 19.8 | Fases 5.3/5.5/5.6B/5.6B.1 | Composições aprovadas; scroll/densidade são variações |
| Precisão monetária 1L | `a4000000000000000001`, `b4000000000000000001` | Fase 5.6B.1, antes/depois Fit to Width e 100% | Aprovada somente para esses dois eixos |
| Contratos de grão/tempo | Medidas `_Medidas`; `DASHBOARD_ARCHITECTURE.md` | Fases 4.5C/5.3–5.6A.2 | Sem alteração na 5.6C; revisar ao criar página |
| Acessibilidade assistiva | Ainda sem validação completa | Fases 5.6A.2/5.6B | Pendente; sem WCAG PASS |

Páginas PBIR: `8b8186ab91fc09fae9a2` (Executiva), `c5202600000000000001` (Comercial), `d5302600000000000001` (Produtos), `e5402600000000000001` (Custos), `f5502600000000000001` (Devoluções). Abreviações com reticências na tabela são somente de leitura; nomes completos estão nos diretórios do PBIR.

### 19.15 Inventário e histórico de versão

Inventário conferido sem edição: cinco páginas; canvas 1920 × 1080; dez tabelas; 55 medidas em `_Medidas`; 11 valores únicos de Display Folder; 21 relacionamentos. Contagem do TMDL do modelo semântico, não da database operacional.

| Versão | Marco | Registro |
|---|---|---|
| v0.1 | Fase 5.0 | Tema InfoTech Intelligence — Light e tokens iniciais; histórico preservado |
| v0.2 | Fase 5.1.2 e evoluções 5.2–5.5 | Cabeçalho, paleta, tipografia, DS-C01–06 e páginas comerciais; seções históricas 1–18 mantêm decisões/candidatos da época |
| v0.3 | Fase 5.6C, 2026-10-14 | Estética das cinco páginas aprovada explicitamente; geometria PBIR, Page Navigator, DS-C02, variações, precisão 1L específica, governança, rastreabilidade e limitações consolidadas. Documentação-only; sem PBIR, sem nova validação assistiva e sem template instalável |

### 19.16 Estado inicial acordado — Fase 5.8.1

O enquadramento-alvo para abertura das cinco páginas é `FitToPage`, preservando o canvas Full HD de 1920 × 1080. O painel de filtros recolhível começa fechado; o botão Filtros abre a camada e Fechar filtros a recolhe, preservando as seleções. A Visão Executiva permanece como página inicial. A seleção inicial acordada para o PBIX é período 04/01/2026–30/09/2026, Canal e Loja em Todos.

**Status desta fase:** o candidato derivado do commit versionado foi alterado estaticamente para `FitToPage` nas cinco páginas e Visão Executiva como página ativa. A configuração de grupo oculto e os bookmarks de abrir/fechar, com `suppressData=true`, já estavam no commit-base. Persistência após salvar/fechar/reabrir, enquadramento renderizado e interatividade continuam pendentes de validação no Power BI Desktop; o PBIX demonstrativo ainda não foi atualizado. Esta decisão não reescreve as medições históricas de FitToWidth das fases anteriores e não afirma responsividade universal.

### 19.16 Estado inicial acordado — Fase 5.8.1

O enquadramento-alvo para abertura das cinco páginas é `FitToPage`, preservando o canvas Full HD de 1920 × 1080. O painel de filtros recolhível começa fechado; o botão Filtros abre a camada e Fechar filtros a recolhe, preservando as seleções. A Visão Executiva permanece como página inicial. A seleção inicial acordada para o PBIX é período 04/01/2026–30/09/2026, Canal e Loja em Todos.

**Status desta fase:** o candidato derivado do commit versionado foi alterado estaticamente para `FitToPage` nas cinco páginas. A configuração de grupo oculto e os bookmarks de abrir/fechar, com `suppressData=true`, já estavam no commit-base. Persistência após salvar/fechar/reabrir, enquadramento renderizado e interatividade continuam pendentes de validação no Power BI Desktop; o PBIX demonstrativo ainda não foi atualizado. Esta decisão não reescreve as medições históricas de FitToWidth das fases anteriores e não afirma responsividade universal.
