# Fase 5.4.1 — Painel de filtros recolhível

**Resultado:** PASS visual e funcional no Power BI Desktop. O Analisador de Desempenho foi registrado em atualização aquecida; carregamento frio não foi medido em separado.

## Escopo e preservação

Implementado o painel nativo de filtros em Visão Executiva, Análise Comercial, Produtos e Categorias e Custos e Margens. Os quatro canvases permanecem Full HD (1920 × 1080 px). A Fase 5.5 não foi iniciada. DAX, modelo semântico, relacionamentos, Power Query, contratos analíticos e PostgreSQL não foram alterados por esta etapa. Nenhuma atualização da fonte foi executada.

A definição manteve os filtros existentes e os grupos `InfoTech.PeriodoComercial`, `InfoTech.Canal` e `InfoTech.Loja`. Categoria e Produto permanecem filtros locais na página Produtos e Categorias. Os filtros não foram duplicados.

## Diagnóstico visual

A revisão visual reforçou a leitura dos botões do painel em escala reduzida. O fundo continua branco `#FFFFFF`; Filtros usa azul mais escuro `#1D4ED8`, texto branco e fonte Semibold de 16 pt; Fechar filtros usa `#DBEAFE`, texto navy `#142238` e fonte Semibold de 16 pt. Os contrastes calculados são 6,70:1 e 13,08:1, respectivamente, sobre os fundos dos botões. O cálculo de luminância relativa não substitui teste visual de todos os estados nem certificação WCAG; os rótulos dos filtros foram conferidos sobre branco.

As capturas históricas `referencia-antes-*` permitem comparação com as versões anteriores das quatro páginas. O estado fechado foi capturado após a mudança para comprovar a área analítica recuperada.

## Arquitetura dos bookmarks

Cada página possui dois bookmarks próprios, sem estado de dados:

- **Data = Off:** `suppressData=true`.
- **Display = On:** a visibilidade do grupo selecionado é aplicada; os testes no Desktop confirmaram que o bookmark só alterna o estado de exibição do grupo.
- **Selected visuals:** `applyOnlyToTargetVisuals=true` e `targetVisualNames` contém somente o grupo da página.
- **Current page = Off:** a seção ativa é suprimida (`suppressActiveSection=true`).

Os bookmarks alteram apenas `isHidden` do grupo. A inspeção e os testes confirmaram os requisitos PBIR do Desktop, incluindo `visualContainers` presente e vazio na seção. Os grupos ficam ocultos por padrão. O painel abre pelo botão Filtros e fecha por Fechar filtros; em modo de edição, o Desktop indica que a ação requer Ctrl+clique. A validação da ação foi executada na interface com o visual selecionado e a combinação Ctrl+Space.

As coordenadas internas dos visuais agrupados são relativas à origem do grupo. Após a primeira inspeção, a composição foi corrigida para manter fundo, Período, Canal, Loja e fechamento contidos no grupo. Em Produtos e Categorias, Categoria e Produto também ficam dentro da superfície branca.

| Página | Origem/tamanho do grupo | Controles dentro do painel |
|---|---:|---|
| Visão Executiva | x24, y96; 1872 × 136 px | Período 760 × 112; Canal 450 × 80; Loja 402 × 80 |
| Análise Comercial | x24, y96; 1872 × 136 px | Período 760 × 112; Canal 450 × 80; Loja 402 × 80 |
| Produtos e Categorias | x24, y96; 1872 × 224 px | Compartilhados; Categoria 760 × 80 e Produto pesquisável 868 × 80 |
| Custos e Margens | x24, y96; 1872 × 136 px | Período 760 × 112; Canal 450 × 80; Loja 402 × 80 |

O botão Filtros fica em x1652, y30, 232 × 56 px. O Page Navigator nativo ocupa x636, y30, 1000 × 56 px, preservando os quatro nomes oficiais e o destino ativo destacado. Os visuais analíticos foram reposicionados para o estado fechado; a composição aberta pode cobrir temporariamente a primeira faixa de cartões enquanto o usuário ajusta os filtros.

## Validação no Desktop

O PBIP reabriu sem erro após as alterações PBIR. A abertura mostrou o painel fechado por padrão. O botão abriu e fechou o painel nas quatro páginas. O Page Navigator superior navegou de Custos e Margens para Visão Executiva e atualizou o destaque ativo. As páginas também foram abertas pelas guias inferiores.

Para exercitar a preservação, o Canal foi temporariamente alterado de Loja física para E-commerce próprio em Custos e Margens: os cartões/gráficos mudaram para BLANK no contexto sem resultado. Loja física foi restaurado e os valores reapareceram. O painel foi fechado e reaberto; Período, Canal e Loja permaneceram selecionados. Ao navegar pelas quatro páginas, os campos exibiram o mesmo intervalo (30/04/2025–30/09/2026), Canal Loja física e Loja Unidade Sintética Campinas. Esses valores já eram o estado do relatório e foram preservados.

A inspeção em Fit to Width confirmou fundo claro, textos escuros, rótulos dos botões, duas alças do slider de período, títulos completos dos cartões financeiros e quatro destinos de navegação. O estado fechado não apresentou sobreposição de visuais visíveis ou elementos fora do canvas na auditoria estática. A página de Produtos manteve os campos de Categoria e Produto no painel.

O teste funcional de isolamento das seleções locais não foi repetido nesta etapa; Categoria e Produto não têm grupo de sincronização e a Fase 5.3 já registra testes e evidências funcionais desses controles. Leitor de tela, paleta em escala de cinza, contraste automatizado e percurso completo de foco por Tab não foram testados. O layout foi observado no viewport de 1152 × 513 px em Fit to Width; a definição Full HD não implica legibilidade universal em telas pequenas.

## Desempenho

O Performance Analyzer foi iniciado com o relatório aberto e os visuais aquecidos; em seguida foi usado **Refresh visuals**, sem atualizar o modelo Import nem a fonte PostgreSQL. A exportação `evidence/phase-5.4.1/phase-5.4.1-performance-warm.json` contém 170 eventos e 15 ciclos de contêiner visual. Todos registram `initialLoad=false`; durações individuais observadas: 132–338 ms. Os eventos de visuais podem ocorrer em paralelo e não devem ser somados. Não houve medição de carregamento frio nesta sessão, portanto estes valores não são benchmark de abertura nem comparação com outra fase.

## Evidências e arquivos

- Capturas de estado aberto/fechado das quatro páginas e captura do Page Navigator em [`evidence/phase-5.4.1/`](evidence/phase-5.4.1/).
- Exportação aquecida do Performance Analyzer e `validation-summary.json` na mesma pasta.
- Referências visuais históricas das fases 5.1–5.4 identificadas como `referencia-antes-*`.
- Pacote portátil: [`evidence/archives/fase-5.4.1-evidencias.zip`](evidence/archives/fase-5.4.1-evidencias.zip).

## Limites e resultado

A tela aberta ocupa parte da área analítica por desenho; os gráficos cobertos não precisam ser acionados enquanto o painel está aberto. Não foi criado resumo dinâmico de filtros no botão Filtros, pois isso exigiria estado adicional não homologado. O botão informa que há filtros e o painel os expõe para revisão e limpeza. A Fase 5.4.1 conclui a experiência visual/funcional de filtros recolhíveis no Desktop, mantendo documentados os limites de acessibilidade e a ausência de benchmark frio.