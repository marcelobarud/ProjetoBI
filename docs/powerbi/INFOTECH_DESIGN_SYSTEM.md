# InfoTech Intelligence — Design System v0.1

**Estado:** v0.1 aplicada na composição PBIR da página Visão Executiva. Tema e canvas foram aceitos pelo Desktop; o usuário confirmou a reabertura e a presença dos componentes, enquanto a revisão visual detalhada ainda está pendente. Os padrões abaixo permanecem base documental até essa revisão visual.

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

| Token | Valor v0.1 | Uso | Contraste de texto medido |
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

Segoe UI e Segoe UI Semibold estão instaladas no ambiente e são usadas pelo Power BI. O tema define somente classes de texto suportadas, sem substituir ajustes específicos que ainda precisam de teste.

| Papel | Faixa de projeto | Alinhamento/peso |
|---|---:|---|
| Título principal da página | 24–28 pt | À esquerda, Segoe UI Semibold |
| Título de seção | 16–18 pt | À esquerda, Semibold |
| Título de visual | 12–14 pt | Frase curta, Semibold |
| Valor KPI | 28–36 pt | Alinhado de forma consistente; unidade explícita |
| Rótulo de KPI | 11–13 pt | Regular, diretamente acima ou ao lado do valor |
| Eixo, legenda e tabela | 10–12 pt | Regular; evitar truncamento |
| Nota/rodapé | 10–11 pt | Secundária; nunca carregar informação essencial |

Usar sentence case em títulos e rótulos. Evitar CAIXA ALTA contínua, excesso de pesos, itálico decorativo e textos abaixo de 10 pt. Reduzir conteúdo antes de reduzir tipografia.

## 4. Grid e densidade

- Referência desktop: widescreen 16:9. A Fase 5.1 adotou, por solicitação do usuário, canvas Full HD de 1920 × 1080 px. A composição implementada usa margens de 36 px e não substitui a referência conceitual compacta de 1280 × 720 px para páginas futuras.
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

Fundo branco; título de 12–14 pt; contorno `#E2E8F0` ou separação por espaço; margens internas uniformes. Arredondamento pequeno, cor de fundo, sombra e borda dependem do visual e devem ser testados na Fase 5.1. O tema v0.1 não finge controlar esses detalhes.

### Filtros

- Preferir segmentações nativas. Período/ano-mês usa calendário; Canal e Loja usam nomes legíveis. Controles têm posição e rótulos fixos.
- Explicitar seleção única/múltipla, seleção limpa e estado sem resultado. Evitar segmentações longas; usar lista suspensa quando a cardinalidade for grande.
- Política de sincronização detalhada em `DASHBOARD_ARCHITECTURE.md`. Filtro de produto não será sincronizado para páginas de métricas de cabeçalho de pedido.

### Navegação

Usar o Page Navigator nativo em orientação horizontal e compacta, se a validação visual da Fase 5.1 confirmar leitura dos cinco rótulos. A página ativa deve ter estado de seleção claramente visível. Usar nomes concisos; ocultar páginas de drill-through se forem adicionadas no futuro. Um navegador nativo acompanha renomeação e ordenação de páginas.

### Tooltips

Explicar unidade, período, grão e perspectiva temporal relevante. Não repetir o mesmo número em vários formatos nem misturar receita por coorte com evento de recebimento. Usar descrição textual concisa; tooltips não substituem rótulo ou contexto no visual principal.

### Tabelas e matrizes

Cabeçalho distinto dos valores, totais identificáveis, BRL/contagem/% consistentes e alinhamento numérico. Formatação condicional moderada, com legenda/texto além da cor. Limitar linhas com Top N e ordenação explícita; permitir drill-down onde a hierarquia real do catálogo suportar.

### Estados

| Estado | Apresentação |
|---|---|
| Sem dados | Mensagem “Sem dados para os filtros selecionados”; não simular zero |
| Filtro sem resultado | Manter filtros visíveis e explicar como limpar seleção |
| Não aplicável/denominador inválido | Preservar BLANK, não renderizar 0% |
| Resultado negativo | Valor com sinal e texto; cor negativa apenas como reforço |
| Zero válido | Renderizar zero com unidade apropriada, distinto de BLANK |

## 6. Formatação numérica

- Valores monetários em BRL; confirmar no Desktop a apresentação pt-BR (`R$`, separadores de milhar e decimal) das medidas existentes antes de homologar a primeira página.
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

- Texto relevante com contraste ≥ 4,5:1 sobre o fundo real. Texto grande pode seguir o mínimo WCAG de 3:1, mas o sistema prioriza os valores acima. Não usar Border como texto.
- Acrescentar título que descreva a pergunta e nomes de eixo com unidade. Definir texto alternativo para visuais, ordem de tabulação e foco visível no Desktop.
- Garantir que filtros possam ser operados por teclado e que o estado selecionado não dependa apenas de cor.
- Cores de séries devem ser acompanhadas por posição, rótulo/legenda e, quando necessário, marcador. Validar em escala de cinza e com simulador de deficiência de visão de cores na revisão visual.
- Testar interação entre visuais. Clique em categoria não pode sugerir que medidas de cabeçalho sejam atribuídas àquela categoria.

## 9. Limites do tema e do Desktop

O tema `powerbi/themes/infotech-light.json` configura nome, cores de série e status, gradiente, cores estruturais e classes tipográficas verificadas no schema publicado. O schema oficial mais recente encontrado foi o `reportThemeSchema-2.157.json`; o Desktop instalado é 2.158.1177.0 e ainda não havia schema 2.158 publicado nesta inspeção. A importação do tema foi aceita pelo Desktop na Fase 5.1; o usuário confirmou que a página abre e os componentes aparecem. A revisão visual detalhada permanece pendente.

O tema não define por si só tamanho/fundo da página, grid/posicionamento, filtros sincronizados, interações, texto alternativo, ordem de tabulação ou regras de formatação condicional. Raio de canto, sombra, estado do Page Navigator, unidades, eixos, rótulos e tooltips podem depender do tipo de visual e ajuste manual. Propriedades visuais só devem ser incluídas em `visualStyles` após confirmar o nome do visual e o caminho da propriedade no schema correspondente e verificar a renderização. Na Fase 5.1, o Desktop aceitou a importação e indicou o tema como atual; confirmar a renderização do tema aplicado aos visuais após reabrir o PBIP.

O Desktop instalado expôs estes visuais nativos durante a inspeção do painel: barras/colunas agrupadas e empilhadas, 100% empilhadas, linha, área, combinações linha-coluna, ribbon, cascata, funil, dispersão, pizza/rosca, treemap, mapas, gauge, Card, KPI, slicer, tabela, matriz, visuais R/Python, Key influencers, decomposition tree, Narrative, imagem e outros. “Goals” e “List slicer” apareceram como Preview; componentes externos e versões Preview não são dependências da arquitetura v0.1. Page Navigator é nativo no menu de navegação do Power BI, separado da galeria de visuais.

## 10. Evidência de implementação da Fase 5.1

- Aplicados no PBIP o tema `InfoTech Intelligence — Light v0.1` e o fundo `#F5F7FB`; o Desktop aceitou a importação e indicou o tema como atual. Ao registrar o tema, expandiu `dataColors` de oito para 480 cores, mantendo os oito tokens iniciais na mesma ordem e sem alterar as demais propriedades do tema-fonte.
- A página reutilizada foi definida em Full HD 1920×1080, com cabeçalho tipográfico, filtros compactos, quatro cartões, uma linha temporal e duas barras horizontais.
- Os valores de contraste aprovados para texto primário e secundário continuam atendendo ao mínimo de 4,5:1 nos fundos previstos. O usuário confirmou a abertura e a presença dos componentes; a inspeção do canvas, escala de cinza, leitor de tela, foco e navegação por teclado ainda não foi concluída.
- O espaçamento do canvas e a hierarquia foram codificados em PBIR, mas ainda não são classificados como visualmente homologados. Manter a versão v0.1; não promover tokens a v0.2 antes de confirmar a renderização no Desktop.

## 11. Governança e registro de decisões

Adicionar token/cor somente com contraste verificado, significado único, caso de uso, impacto nos visuais e atualização do tema. Novos componentes reutilizam grid, escala tipográfica, rótulos, unidades e estados deste documento. Mudança de identidade incrementa a versão e revisa todas as páginas e tema; páginas existentes não devem depender de cores locais sem decisão registrada.

| ID | Decisão | Justificativa | Data | Estado | Impacto/dependências |
|---|---|---|---|---|---|
| DS-001 | Nome InfoTech / InfoTech Intelligence e wordmark tipográfico provisório | Identidade neutra para comércio de informática, sem inventar dados institucionais | 2026-10-12 | Aprovada como direção | Cabeçalho e futura navegação; sem logotipo |
| DS-002 | Base clara com azul, verde-petróleo e neutros | Leitura corporativa e poucos destaques simultâneos | 2026-10-12 | Aprovada como direção | Paleta tema e páginas |
| DS-003 | Escurecer Text Secondary para `#5B6B82` | `#64748B` resulta em 4,44:1 sobre o canvas, abaixo do alvo 4,5:1 | 2026-10-12 | Proposta técnica v0.1 | Revalidar contraste quando o fundo mudar |
| DS-004 | Usar somente visuais nativos estáveis no desenho inicial | Reduzir risco de compatibilidade e custo de manutenção | 2026-10-12 | Proposta | “Goals” e “List slicer” estão em Preview |

Mudanças pequenas de espaçamento podem ser incorporadas na próxima revisão do documento; mudanças de significado, paleta ou interação recebem novo ID. A versão 0.1 é fundação documental, não homologação visual.
