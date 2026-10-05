# Distribuições de negócio planejadas — Fase 3A

São bandas orientadoras para o profile `portfolio`, não quotas fixas nem resultados-alvo. Variação por seed é permitida dentro das faixas; correlações estruturais e integridade prevalecem sobre ruído. Crescimento, Black Friday e diferença de margem devem emergir do conjunto, sem hard-code dos insights finais.

## Calendário, crescimento e sazonalidade

- Volume total portfolio: cerca de 120 mil pedidos, distribuídos por 2023 completo, 2024 completo, 2025 completo e jan–set/2026. Faixas indicativas por período: 2023 20–26 mil; 2024 25–32 mil; 2025 32–40 mil; jan–set/2026 27–34 mil. Ajustar a soma à faixa de 110–130 mil pedidos. Comparar crescimento de 2026 com os mesmos nove meses de 2025, não com o ano fechado.
- Crescimento anual deve ser geralmente positivo e moderado (aprox. 12–28% entre anos completos), com variação de seed e maturação de canais/lojas. Não impor crescimento positivo em todos os meses.
- Pesos mensais variam; novembro tem aumento de pedidos/unidades, dezembro fica acima de mês comum mas normalmente abaixo de novembro, janeiro tende a desacelerar após festas. Fevereiro/volta às aulas favorece computadores/periféricos e ciclos corporativos favorecem compras PJ em janelas plausíveis. Pesos mensais podem ficar em torno de 0,75–1,35 da média mensal, Black Friday em torno de 1,25–1,60; novembro não é multiplicador extremo.
- Black Friday apenas em 2023, 2024 e 2025, com janela promocional curta definida em configuração (por exemplo semana da última sexta de novembro). Impacta pedidos, mix de categoria, incidência/desconto e margens; 2026 não contém evento após cutoff.
- Dia útil concentra mais pedidos PJ e operação de compra; físico pode concentrar fins de semana. Variação por dia da semana moderada (aprox. 0,75–1,30 da média diária) e adequada a cada canal.

## Canais, clientes e recorrência

| Dimensão | Banda / comportamento |
|---|---|
| Canal | Físico 50–55%; e-commerce 25–32%; marketplaces em conjunto 15–22%, divididos entre dois canais. A fatia digital cresce gradualmente de 2023 a 2026; pesos somam 100% em cada período. |
| Tipo de cliente identificado | PF 88–92%; PJ 8–12%. Calcular sobre clientes identificados, não sobre pedidos. |
| Pedido anônimo | 25–35% dos pedidos físicos sem `customer_id`; zero anônimos no e-commerce/marketplace. Não criar cadastro genérico. |
| Recorrência | Como proporção de clientes identificados ativos no horizonte: 35–50% com um pedido; 30–40% com 2–4; 10–18% com 5–10; 2–6% com 11 ou mais. Normalizar categorias para 100% dentro das bandas; limitar concentração. PJ tem maior recorrência média que PF. |
| Ticket PF/PJ | Ticket PJ tipicamente 1,5–3,0x o PF, com variância e sobreposição; parcela PJ na receita pode ficar em 18–32%, sem transformar toda PJ em grande comprador. |
| Geografia | Predomínio Sul/Sudeste, com presença menor de Centro-Oeste, Nordeste e Norte; usar concentração comercial fictícia, não proporção populacional perfeita. Cidade/UF de lojas vêm de `core.stores`; cidade/UF de clientes/pedidos vêm de endereço sintético. Derivar região da UF por mapeamento versionado; não inferir localização do nome da loja nem usar endereço do cliente como endereço da loja. |

Distribuir pedidos repetidos entre coortes. `customer.created_at <= placed_at`; frequência depende de tipo PF/PJ, canal, tempo desde cadastro e atividade. Clientes não compram antes do cadastro e frequência extrema permanece rara.

## Produtos, lojas e vendedores

- Catálogo: 35–50 categorias/subcategorias, 50–80 marcas, ~1.000 SKUs; 40–50 fornecedores. SKU líder responde por poucos pontos percentuais das unidades (em geral até 1–2%); uma cauda de aproximadamente 10–20% dos SKUs concentra demanda baixa, e o restante forma o meio. Medir concentração e calibrar sem uniformidade.
- Produtos de maior preço têm menos unidades por pedido. Componentes e periféricos podem formar cestas complementares; notebooks/desktops tendem a 1 unidade, especialmente ticket alto. `specifications` usa templates por família, JSON object snake_case, sem mistura impossível de configurações.
- As 10 lojas variam por abertura, volume, mix, ticket e equipe. Participação de pedidos físicos por loja pode ficar aproximadamente entre 5–16%, ponderada por dias abertos e tamanho; nenhuma loja domina metade das vendas. Novas lojas abrem após o início do período para criar evolução orgânica.
- 80–100 funcionários, 6–8 funções; aproximadamente 35–50% vendedores, 20–30% estoque/logística, restante gestão, compras e administrativo. Lotação compatível com vínculo e função. Desempenho de vendedor varia moderadamente (fator aproximado 0,7–1,4 da média do grupo comparável), condicionado a tempo de atuação e loja, sem ranking ditado por ruído extremo.
- Fornecedores: ~70–85% dos SKUs com um fornecedor ativo, 15–30% com dois ou três; no máximo um fornecedor preferencial ativo por produto. Volume de compra acompanha giro, estoque mínimo, lead time e fornecedor, não seleção aleatória independente.

## Cesta, preço, desconto e margem

- Pedidos: média de 2,0–2,3 linhas distintas por pedido; muitos pedidos com uma linha, maioria restante com 2–4, cauda pequena maior. Média de unidades por linha geralmente 1,05–1,35; PJ desloca distribuição para quantidades maiores.
- Preço selecionado da vigência por SKU/canal no instante do pedido. Alterações ao longo do tempo moderadas; evolução geral pode acompanhar inflação/câmbio fictícios sem referenciar taxa real. Custo nasce de recebimentos e custo médio móvel, sem margem fixa universal.
- Desconto em aproximadamente 30–45% dos pedidos. Para pedidos descontados, faixas usuais de 2–8% do valor elegível; eventos Black Friday elevam incidência e podem alcançar 5–12% para os itens elegíveis. Limite por item: líquido nunca negativo. Parte relevante dos pedidos permanece sem desconto.
- Margem de produto varia por categoria, marca, preço e fornecedor. Faixa indicativa comum de margem bruta realizada de 8–28%, com categorias e SKUs fora da faixa central sem artificialmente tornar vendas amplamente negativas. Promoções comprimem margem; não usar um markup global fixo.
- Frete cobrado é independente do preço do produto e de custo logístico não alocado. Pedidos de retirada podem ter frete zero; entrega gratuita pode ter valor cobrado zero. Não somar frete como receita de produto ao calcular métricas definidas.

## Pagamentos e estados comerciais

- Histórico: cerca de 93–97% dos pedidos encerrados como `completed`; 2–5% `cancelled`; no máximo 1–3% permanecem `placed`/`confirmed` perto do cutoff, com idade curta e justificativa operacional. Não deixar pendências antigas.
- Operações de pagamento derivam de pedido: 1 pagamento bem-sucedido na maioria, pequenas parcelas com split ou nova tentativa; tentativas declinadas/falhas em cerca de 2–6% das operações, sempre sem reconhecer recebimento.
- Meios: cartão 35–50% dos pedidos, PIX/instant 30–45%, dinheiro 8–18% (predominantemente físico), transferência/outros residuais (aprox. 2–8% agregados). Ajustar dentro de canais e bandas totais.
- Parcelamento: dinheiro/PIX não parcelados; ticket baixo tende a pagamento à vista; cartão de ticket alto tem mais parcelas. A maioria dos pagamentos no cartão é 1–4 parcelas; 5–10 apenas para tickets maiores, sem distribuição uniforme. Parcelas conciliam ao valor da operação respeitando precisão de centavos.
- Pedido e pagamento são ciclos independentes. Captura/liquidação compatível com status e total elegível; cancelamento não conta como receita recebida. Os baselines definirão a medida financeira usada.

## Compras, estoque e logística

- Comprar para cobrir demanda prevista, estoque mínimo e lead time; produtos populares têm maior cobertura/reposição, produtos caros e lentos mantêm estoque menor. Compra recebida nunca supera quantidade pedida; parte das compras pode ser recebida parcialmente.
- Usar 12–15 locais: ~10 locais de loja mais 2 centros e 0–3 pontos adicionais de expedição/estoque se aprovados no setup conceitual. Diferenciar capacidade/escala sem preencher todas as combinações SKU-local.
- Atendimento de pedido válido: em torno de 90–97% dos pedidos não cancelados completamente; a maioria usa uma unidade de fulfillment. 3–10% dos pedidos atendidos podem exigir divisão entre mais de uma unidade; itens/quantidades atendidos nunca excedem vendas.
- Físico: retirada/atendimento na loja é comum. E-commerce: entrega majoritária e alguma retirada. Marketplace: entrega muito predominante. Eventos são sequenciais (`prepared` antes de `dispatched`, entrega após despacho; retirada `pickup_ready` antes de `picked_up`). Latência varia de minutos/dias, não um timestamp único.
- Transferências representam aproximadamente 0,5–2,0% dos eventos de reposição/saída, somente quando a demanda/estoque local justifica. Cada saída e entrada têm a mesma quantidade recebida e custo unitário transferido; quantidades em trânsito não aparecem no disponível do destino.
- Ajustes são raros (bem abaixo de 0,5% dos movimentos), motivados por contagem/dano/perda/encontrado; não simulam saldo inicial nem erro proposital.

## Devoluções e reembolsos

- Retorno em aproximadamente 4–8% dos pedidos concluídos ou 2–5% das unidades atendidas, dependendo da métrica. Online ligeiramente acima do físico; categorias e produtos têm incidência diferenciada; PJ tende a incidência menor. Repetição por cliente/produto limitada.
- Maioria de itens recebidos em condição boa/fechada pode voltar `sellable`; proporção menor vai a `quarantine`, `repair` ou `discard`. Quantidade cumulativa retornada não ultrapassa o efetivamente atendido pela origem.
- 70–90% do valor aprovado para reembolso pode gerar pedido/solicitação de refund dentro do cutoff; o restante pode ter troca, crédito ou decisão ainda em processo se o status permitir. Reembolso concluído nunca supera elegibilidade nem captura original.
- Solicitação, decisão, recebimento físico e refund têm timestamps separados e ordenados. `source_fulfillment_item_id` aponta para a origem correta; custo do retorno vendável segue movimentos `fulfillment` dessa origem.

## Ruído e calibração

Adicionar ruído dentro das bandas com sub-seeds, mas manter a hierarquia: integridade e regras causais > tendências sazonais/comerciais > variação aleatória. Após geração, guardar distribuição observada e comparar com estas bandas; se uma banda for excedida, ajustar algoritmo/configuração, nunca editar dados para forçar uma métrica final desejada.
