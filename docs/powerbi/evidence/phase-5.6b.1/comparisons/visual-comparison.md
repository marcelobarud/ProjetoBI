# Comparação visual — Fase 5.6B.1

Capturas feitas no Power BI Desktop real, no mesmo equipamento, resolução física 1366×768 px, área de captura 1366×720 px e escala Windows 100%. A comparação usa os contextos de página capturados antes/depois; não representa um teste em tamanhos de tela distintos.

| Página/visual | Antes | Depois | Observação registrada |
|---|---|---|---|
| Visão Executiva — linha mensal de receita e lucro | [Fit to Width, painel fechado](../before/01-executiva-fit-width-painel-fechado.jpg); [100%, eixo](../before/01-executiva-100-segmento-direito.jpg) | [Fit to Width](../after/01-executiva-fit-width.jpg); [100%, eixo](../after/01-executiva-100-eixo-1-decimal.jpg) | O eixo monetário tinha unidade automática em milhões e precisão zero; ticks próximos podiam repetir o valor arredondado. Com uma casa decimal, os ticks observados ficaram distintos. |
| Análise Comercial — gráfico temporal de receita | [Fit to Width, painel aberto](../before/02-comercial-fit-width-painel-aberto.jpg); [100%, cartões/eixo](../before/02-comercial-100-cartoes-e-eixo.jpg) | [Fit to Width](../after/02-comercial-fit-width-ajuste.jpg); [100%, eixo](../after/02-comercial-100-eixo-1-decimal.jpg) | Mesma correção de precisão, sem mudar unidade automática, medida ou contexto analítico. |
| Produtos e Categorias | [Fit to Width](../before/03-produtos-fit-width-painel-fechado.jpg) | [Fit to Width](../after/03-produtos-fit-width-pos-ajuste.jpg) | Inspeção da composição; nenhum ajuste adicional justificado. |
| Custos e Margens | [Fit to Width, painel fechado](../before/04-custos-fit-width-painel-fechado.jpg) | [Fit to Width](../after/04-custos-fit-width-pos-ajuste.jpg) | Inspeção da composição; nenhum ajuste adicional justificado. |
| Devoluções | [Fit to Width](../before/05-devolucoes-fit-width-painel-fechado.jpg) | [Fit to Width](../after/05-devolucoes-fit-width-pos-ajuste.jpg) | Inspeção da composição; nenhum ajuste adicional justificado. |

A visualização Actual Size/100% mostra o gráfico ampliado e exige rolagem do canvas. Fit to Width (47% neste Desktop) mostra a página completa; fontes e marcas parecem menores por causa da escala de apresentação. O painel de filtros aberto pode cobrir a faixa de cartões conforme o layout existente. Nenhuma captura demonstra contraste certificado, acessibilidade assistiva ou aprovação estética final.