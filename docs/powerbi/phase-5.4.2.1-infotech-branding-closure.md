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

## Verificações

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
