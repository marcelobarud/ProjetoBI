# Fase 5.4 — Dashboard de Custos e Margens

**Estado:** `FASE 5.4 PARTIAL — VISUAL OR FINANCIAL VALIDATION PENDING`

**Escopo implementado:** quarta página `Custos e Margens`, canvas 1920 × 1080, no PBIP local. Design System InfoTech v0.2 mantido. Nenhuma medida, tabela, relação, consulta Power Query, fonte de dados, objeto PostgreSQL ou baseline SQL foi alterado nesta fase.

## Resumo analítico

A página usa a coorte da data comercial do pedido. Receita analítica, COGS, reversão, lucro e margem permanecem associados ao período do pedido conforme medidas aprovadas. O frete não integra a receita analítica; refunds não substituem a dedução comercial por devolução. Perda non-sellable é informativa e continua incorporada ao COGS ajustado.

Componentes implementados:

- Quatro KPIs principais: receita após devoluções, COGS ajustado, lucro bruto analítico e margem bruta.
- Ponte complementar: COGS original concluído, reversão sellable, COGS ajustado e perda non-sellable já incluída.
- Evolução mensal de receita, COGS ajustado e lucro bruto, por coorte do pedido.
- Barras de lucro bruto por Canal e Categoria, com receita, COGS ajustado e margem em tooltips.
- Período Between, Canal e Loja, reutilizando os grupos de sincronização existentes.
- Page Navigator nativo com os quatro destinos e estado ativo.

Não foram incluídos visuais para custo por data de movimento ou devolução por data de recebimento, nem uma quinta página de Devoluções. Esses fluxos usam perspectivas temporais diferentes e seguem fora do escopo implementado.

## Reconciliação DAX somente leitura

Valores consultados no modelo Import local do Desktop pelas medidas já aprovadas. Precisão técnica permanece no arquivo de evidências; apresentação monetária arredonda a centavos.

| Medida | Global | Jan–Set/2026 |
|---|---:|---:|
| Receita Analítica Após Devoluções | R$ 922.588.975,445 | R$ 228.660.758,740 |
| COGS Original Concluído — Data do Pedido | R$ 725.466.564,623508 | R$ 177.849.100,500723 |
| Reversão COGS Sellable — Data do Pedido | R$ 8.010.914,363863 | R$ 1.778.950,410881 |
| COGS Analítico Ajustado | R$ 717.455.650,259645 | R$ 176.070.150,089842 |
| Lucro Bruto Analítico | R$ 205.133.325,185355 | R$ 52.590.608,650158 |
| Margem Bruta Analítica | 22,2345% | 22,9994% |
| Perda Non-Sellable — Data do Pedido | R$ 12.296.704,234136 | R$ 2.752.994,199333 |

Reconciliações verificadas: `COGS ajustado = COGS original concluído − reversão sellable`; `lucro bruto = receita após devoluções − COGS ajustado`. O non-sellable não é deduzido de novo. O COGS de movimentos de todos os status não substitui a população de pedidos concluídos.

As consultas adicionais por Canal e Categoria estão em [phase-5.4-dax-reconciliation.json](evidence/phase-5.4-dax-reconciliation.json). Os resultados por Canal reconciliaram à receita, ao COGS ajustado e ao lucro globais dentro da precisão interna, sem arredondamentos intermediários.

## Desktop, filtros e navegação

O PBIP abriu sem erro e a quarta página renderizou antes e depois de fechar/reabrir. A captura [phase-5.4-costs-margins-final.jpg](evidence/phase-5.4-costs-margins-final.jpg) mostra a página inteira em Fit to Page. A sessão do Desktop tinha viewport de 1152 × 513 px; o relatório coube a 26%, por isso a captura reduz os textos. O canvas continua Full HD e deve ser lido ampliado em monitor compatível. Não se infere legibilidade universal a partir desse viewport reduzido.

Validações manuais observadas:

- Navegação de Visão Executiva → Custos e Margens e retorno; as outras páginas existentes também abriram e voltaram sem erro.
- Selecionar `Loja física` alterou os cartões e gráficos; essa seleção apareceu na Visão Executiva.
- Selecionar `Unidade Sintética Campinas` atualizou KPIs na página financeira e, ao navegar, na Visão Executiva e nas outras páginas compartilhadas.
- Um contexto de loja sem movimento exibiu BLANK nos KPIs; BLANK não foi substituído por zero.
- Mover a alça inicial do período alterou o intervalo e a receita exibida. O campo de data abriu o seletor nativo. Não foi possível comprovar independentemente a digitação nos dois campos e a sincronização resultante em todas as páginas.
- Filtros temporários foram removidos; a reabertura exibiu o estado global de referência. A última captura foi feita com receita global de R$ 922.588.975,45 e margem 22,23%.

As pastas e metadados PBIR incluem quatro destinos, 17 visuais, 30 interações explícitas entre visuais, texto alternativo e tab order. A navegação de quatro destinos e a sincronização de Canal/Loja foram vistas em uso. Não foi concluída uma matriz exaustiva com cada um dos três filtros aplicado, limpo e conferido nos quatro sentidos. A edição digitada dos dois campos de data também não recebeu teste independente completo; por isso, essa parte do gate funcional permanece pendente.

## Tipografia, acessibilidade e limites

Configuração visual respeita as referências vigentes: marca 30 pt, nome da página 12 pt, títulos 17 pt, eixos/categorias 16 pt, legenda 15 pt, cartões 32 pt e títulos de cartão 13 pt. A página foi inspecionada no Desktop em Fit to Page; eixos e rótulos ficam pequenos no viewport usado quando toda a página é reduzida. A captura não certifica acessibilidade.

Tab order e alt text estão serializados nos visuais. Não foram executados testes completos por teclado, leitor de tela, daltonismo, contraste automatizado ou escala de cinza. Não declarar conformidade ou certificação de acessibilidade.

## Performance Analyzer

Exportação local do Performance Analyzer: [phase-5.4-performance-analyzer.json](evidence/phase-5.4-performance-analyzer.json). A sessão registrou 1.889 eventos, incluindo 169 ciclos de contêiner visual e 14 ações de usuário entre 2026-10-13 23:48:22Z e 23:52:30Z. Incluiu atualização visual em modelo Import já aberto, alterações de slicer e navegação; não houve atualização de dados.

Na atualização visual aquecida, o intervalo da ação de refresh ao último ciclo de contêiner foi cerca de 402 ms. No primeiro ciclo observado, os tempos de contêiner variaram de 166 ms (textbox) a 450 ms (linha mensal); Page Navigator 196 ms; Período 391 ms; Canal 192 ms; Loja 191 ms; cartões 294–360 ms; barra por Canal 402 ms e barra por Categoria 365 ms. Eventos dos visuais ocorrem em paralelo: não somar esses valores para obter duração total. São medições desta máquina/sessão/cache e não benchmark comparável à Fase 5.3.

## Persistência, modelo e Git

Verificações locais após reabertura: quatro páginas; 55 medidas em `_Medidas`; 21 relações no modelo; nenhuma alteração de DAX, relacionamento, Power Query ou PostgreSQL. `pages.json` recebeu o quarto ID e os três navegadores existentes foram atualizados. A alteração anterior de `report.json`, a serialização preexistente de `pt-BR.tmdl`, visuais preexistentes e a exportação de desempenho antiga foram preservados e ficaram fora do staging.

**Gates:** visual — PASS no Desktop local, com a limitação de escala registrada; técnico — PASS para abertura, estrutura e reconciliação do modelo; funcional — PARTIAL porque nem todos os sentidos dos filtros e os dois campos de data foram validados independentemente. Resultado geral permanece **PARTIAL**, mesmo após o commit local.

Verificação estrutural da página e revisão Git final ficam registradas no fechamento da fase. Commit autorizado: `feat(powerbi): implementa dashboard de custos e margens`.

Fase 5.5 — Devoluções — não iniciada.
