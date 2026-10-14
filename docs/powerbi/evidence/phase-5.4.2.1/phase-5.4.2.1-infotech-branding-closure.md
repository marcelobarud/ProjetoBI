# Fase 5.4.2.1 — Regularização da marca InfoTech

**Resultado:** `PARTIAL — FINAL VISUAL VALIDATION PENDING`
**Nome oficial vigente:** InfoTech
**Design System:** v0.2 preservado; revisão visual e promoção à v0.3 pendentes.

## Decisão e alcance da identidade

O usuário aprovou **InfoTech** como nome oficial em substituição a **InfoTech Intelligence**. O monograma geométrico I/T selecionado anteriormente foi preservado. A denominação anterior continua registrada nos documentos e evidências históricos das Fases 5.0–5.4.2, sem substituição global.

Referências atuais foram atualizadas nos quatro cabeçalhos, nos textos alternativos dos cabeçalhos e do monograma, nos SVGs-fonte vigentes, no nome de exibição do tema, no Design System, na arquitetura e no README do Power BI. A versão horizontal agora mostra apenas InfoTech; o recurso monocromático também usa o nome atual. As cópias dentro das evidências antigas continuam históricas.

Nomes internos e caminhos técnicos foram preservados, inclusive `InfoTech_Intelligence___Light_537872542319678.json`, o item registrado do SVG, IDs das páginas/visuais/bookmarks, diretórios e nome do PBIP. A identidade foi alterada sem regravar as medidas, tabelas, relacionamentos ou fontes.

## Correção solicitada em Custos e Margens

Na página Custos e Margens, o visual de texto acima dos cartões financeiros secundários mantém x=36, y=272 e largura de 1848 px; sua altura passou de **24 px para 31 px**. O título visível foi corrigido para **“Composição do custo analítico — corte do pedido”**. O título do gráfico de linhas passou para **“Receita, COGS e lucro bruto por mês de corte (R$ milhões)”**. Os textos alternativos que descrevem esses títulos foram alinhados à grafia solicitada. Nenhuma medida nem interpretação DAX foi alterada.

## Recursos e cabeçalho

- Fonte principal: `powerbi/branding/infotech/infotech-monogram.svg`; proporção quadrada, 48 × 48 px no PBIR, fundo transparente, azul `#2563EB` e verde-petróleo `#0F9D92`.
- Variantes vigentes: `infotech-monogram-mono.svg` e `infotech-horizontal.svg`; a horizontal não está aplicada no PBIP.
- Símbolo registrado no PBIP permanece no mesmo item técnico; a descrição acessível agora identifica InfoTech.
- Cabeçalhos mantêm monograma x=36/y=36, 48 × 48 px; wordmark InfoTech em Segoe UI Semibold 30 pt; página abaixo em Segoe UI 12 pt; navegador e botão de filtros permanecem nas geometrias anteriores.

## Componentes não refinados nesta etapa

Os estilos existentes de cartões, botões e Page Navigator foram preservados; nenhum novo refinamento de borda, canto, ícone, padding ou estado foi implementado. As quatro páginas renderizaram e foram inspecionadas visualmente no Desktop em 47% de zoom. A composição geral foi conferida, mas faltam inspeção ampliada dos detalhes e as capturas específicas previstas para cabeçalho, cartões e botões; por isso esses refinamentos não são classificados como homologados.

## Verificações — registro anterior à retomada final

| Item | Estado | Evidência / limite |
|---|---|---|
| Fontes SVG atuais e recurso PBIP | Estruturalmente verificados | XML bem-formado, mesmo item técnico e descrição InfoTech |
| Cabeçalhos e texto alternativo | Verificados no PBIR e na visão geral do Desktop | As quatro páginas mostram InfoTech e monograma sem cortes visíveis na captura geral; inspeção ampliada pendente |
| Título e altura acima dos cartões secundários | Verificados no PBIR e na captura Desktop | Altura 31 px; “corte do pedido” aparece inteiro acima da segunda faixa de cartões |
| Título do gráfico de linhas | Verificado no PBIR e na captura Desktop | Usa “corte”; título completo visível na página Custos e Margens |
| Tema | Verificado estaticamente | Nome de exibição atualizado para “InfoTech — Light v0.1”; arquivo/item técnico preservado |
| PBIR JSON | Verificado estaticamente | 96 definições parseadas, sem JSON inválido |
| Modelo semântico | Verificado estaticamente | 10 tabelas, 55 medidas, 11 Display Folders e 21 relações (19 ativas, 2 inativas) |
| Power BI Desktop | Verificado parcialmente | As quatro páginas renderizaram e foram percorridas no Desktop em 47% de zoom. Os cabeçalhos mostram InfoTech; o texto de 31 px e os títulos “corte” aparecem na página Custos e Margens. Não foram vistas falhas de renderização na visão geral; a revisão ampliada continua pendente |
| Capturas obrigatórias | Parciais | Foram salvas capturas reais das quatro páginas em estado fechado e uma de Custos e Margens com filtros abertos. Faltam os detalhes ampliados de cabeçalho, cartões principais, cartões secundários e botões |
| Filtros e bookmarks | Verificados parcialmente | Em Custos e Margens, os bookmarks existentes Filtros — abrir/fechar alternaram o painel. Os KPIs permaneceram visualmente iguais após fechar; filtros/sincronização não foram alterados nem testados nesta retomada |
| Baselines financeiros e reabertura | Pendentes nesta fase | Não executados; não houve refresh nem acesso ao PostgreSQL |
| Cartões, botões, navegação e acessibilidade visual | Parciais / pendentes | Cartões, séries e Page Navigator aparecem nas capturas das quatro páginas; faltam inspeção ampliada, teste de teclado/foco, Fit to Page e evidências detalhadas dos botões |

## Inventário de referências

| Grupo | Tratamento |
|---|---|
| Marca vigente em PBIR, SVG atual, tema e guias correntes | Atualizada para InfoTech |
| Relatórios e evidências das fases anteriores, inclusive o pacote 5.4.2 | Preservados como registro histórico de InfoTech Intelligence |
| IDs, caminhos registrados, nome do PBIP e identificadores do modelo | Preservados por serem técnicos |
| SVG horizontal | Atualizado para InfoTech; não aplicado ao relatório |
| Nome de exibição dentro dos dois arquivos do tema | Atualizado; identificador/arquivo registrados preservados |

O inventário de verificação está em `docs/powerbi/evidence/phase-5.4.2.1/phase-5.4.2.1-validation.json`. O pacote `fase-5.4.2.1-evidencias.zip` reúne os SVGs atuais, a auditoria estática, este relatório e as cinco capturas reais; as capturas detalhadas ainda pendentes estão listadas neste documento.

**Classificação final:** PARTIAL. A identidade e os ajustes textuais foram conferidos tecnicamente e na visão geral do Desktop; quatro páginas e o painel aberto possuem capturas reais. Persistem pendências de inspeção ampliada, operação do botão no canvas, filtros/sincronização, baselines, persistência e refinamentos candidatos. Fase 5.5 não iniciada.

## Homologação final — retomada de 2026-10-14

Esta seção atualiza o registro histórico acima. O resultado permanece **`PARTIAL — FINAL VISUAL VALIDATION PENDING`**: a validação funcional foi concluída, mas ainda faltam capturas ampliadas comparáveis de todos os cabeçalhos/cartões e a revisão assistiva de acessibilidade. Nenhum critério visual pendente foi convertido em aprovação por inspeção estática.

### Terminologia financeira

O contrato DAX e a documentação de Custos e Margens atribuem Receita após devoluções, COGS ajustado e Lucro bruto à coorte da data comercial do pedido. Os dois rótulos foram ajustados para **“Composição do custo analítico — por data do pedido”** e **“Receita, COGS e lucro bruto por mês do pedido (R$ milhões)”**. Os textos alternativos correspondentes identificam a data comercial do pedido/coorte. A caixa de texto permanece com 31 px; não houve ajuste de geometria, medidas, filtros ou relações.

### Inspeção visual e funcional

- As quatro páginas foram novamente observadas no Power BI Desktop em escala Fit to Width (aproximadamente 38–47%). Em Custos e Margens, uma captura adicional a 100% mostra o monograma I/T, wordmark InfoTech, valores dos cartões principais e secundários e o título corrigido sem corte na parte visível. Em Fit to Width, os dois títulos financeiros aparecem integralmente. O zoom de 100% não representa prova para as outras três páginas.
- A identidade InfoTech, a navegação de quatro destinos e os estilos v0.2 foram preservados. Não foi feita alteração visual de cartões, botões ou navegação por não haver evidência suficiente de uma melhoria objetiva aplicável; o Design System continua v0.2, sem promoção a v0.3.
- No Desktop, os bookmarks existentes de abrir/fechar foram exercitados nas quatro páginas. O estado dos filtros foi preservado ao alternar a apresentação. A ação foi disparada pelo painel Bookmarks; a ativação independente do botão “Fechar filtros” dentro do canvas continua sem confirmação.
- Após receber o resultado, o usuário confirmou manualmente que o clique no botão nativo “Fechar filtros” funciona corretamente. Esse registro é confirmação do usuário, sem captura de tela associada.
- O período Between aceitou datas digitadas nos dois campos e as duas alças do slider alteraram o intervalo e recalcularam os indicadores. Canal e Loja foram testados isoladamente e combinados; uma combinação sem resultado exibiu BLANK. Limpar um filtro manteve o outro. Não se substituiu BLANK por zero.
- A sincronização de Período, Canal e Loja foi observada entre Executiva, Comercial, Produtos e Custos nos quatro sentidos registrados nas capturas. Categoria e Produto foram selecionados localmente em Produtos e Categorias e não alteraram os KPIs de Custos e Margens.
- A navegação entre as quatro páginas funcionou. Foram observados o estado ativo e os destinos existentes.

### Reconciliação e persistência

No Desktop, o contexto global apresentou Receita após devoluções de **R$ 922.588.975,45**, COGS ajustado de **R$ 717.455.650,26**, Lucro bruto de **R$ 205.133.325,19** e Margem bruta de **22,23%**. No intervalo Jan–Set/2026, os valores foram **R$ 228.660.758,74**, **R$ 176.070.150,09**, **R$ 52.590.608,65** e **23,00%**, respectivamente. O detalhamento confirmou que a perda non-sellable já integra o COGS ajustado.

O projeto foi salvo com o estado de filtro anterior aos testes (30/04/2025–30/09/2026, Loja física, Unidade Sintética Campinas, painel fechado) e fechado normalmente. As duas correções de título/alternativo foram feitas somente com o Desktop fechado. O PBIP reabriu sem erro, exibiu os títulos novos e manteve o período, Canal e Loja anteriores e KPIs consistentes. Não houve atualização de dados nem acesso ao PostgreSQL. A sessão reaberta foi encerrada sem salvar apenas a mudança transitória de zoom para 100%.

### Verificações técnicas, evidências e limites

- Os arquivos PBIR dos dois títulos foram parseados e o relatório abriu após a alteração. A auditoria estrutural vigente registra 10 tabelas, 55 medidas, 11 Display Folders, 21 relações (19 ativas, 2 inativas) e quatro páginas; nenhum arquivo do modelo semântico, DAX ou fonte de dados foi alterado nesta retomada.
- Os oito bookmarks existentes mantêm `suppressData=true`, alvo visual específico e estado da página não suprimido; os estados aberto/fechado foram exercitados em tela. Nenhum bookmark foi recriado.
- As capturas em `docs/powerbi/evidence/phase-5.4.2.1/` são imagens reais do Desktop; a relação, os hashes e as dimensões constam no JSON de validação. Incluem contextos financeiros, período/slider, filtros, navegação, sincronização e seleção local de Produto/Categoria.
- A captura a 100% é apenas uma janela de leitura da página Custos e Margens. Permanecem pendentes close-ups ampliados das três outras páginas, uma inspeção ampliada independente dos dois botões e comprovação em leitor de tela, tabulação/foco e conformidade WCAG. Não se declara certificação de acessibilidade.
- Uma cópia externa dos arquivos candidatos à mudança foi preservada em `C:\Users\D2\AppData\Local\Temp\ProjetoBI-Phase-5.4.2.1-close-20261014-105616.zip` (SHA-256 `2A870BC02C099240A95E437F6648E83040A1F54C0877809D80CF7572AB9E0967`). Todas as mudanças de PBIR já existentes em outros visuais, `report.json`, `pt-BR.tmdl` e evidências anteriores foram preservadas fora do commit.

### Gates finais

| Gate | Resultado | Base |
|---|---|---|
| Visual | **PARTIAL** | Quatro páginas observadas em Fit to Width e Custos ampliada; faltam close-ups comparáveis nas demais páginas e nos botões. |
| Funcional | **PASS local** | Datas, duas alças, Canal, Loja, BLANK, sincronização, filtros locais, navegação e bookmarks testados no Desktop; o usuário confirmou que “Fechar filtros” funciona corretamente. |
| Técnico | **PASS para serialização e integridade desta retomada** | Salvar, fechar, editar com Desktop fechado, reabrir sem erro, conferir títulos/contexto; modelo e banco não alterados. |

**Classificação de encerramento:** `FASE 5.4.2.1 PARTIAL — VALIDATION PENDING`. InfoTech e o monograma I/T permanecem como identidade corrente e os componentes v0.2 podem orientar trabalhos futuros com as limitações acima; a Fase 5.5 não foi iniciada.
