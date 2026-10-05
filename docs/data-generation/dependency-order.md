# Ordem de dependências de geração — Fase 3A

O roteiro cobre as **40 tabelas físicas** da migration inicial em 41 estágios de uso, pois `inventory.stock_movements` participa tanto do bootstrap de recebimentos como dos eventos comerciais posteriores. FKs opcionais podem receber NULL quando o processo não se aplica. Constraints permanecem habilitadas. A ordem é por dependência de criação; dentro de transações, eventos seguem ordem cronológica e podem exigir dois passes para referências que só surgem depois (por exemplo, movimento apontando para item de fulfillment/devolução).

## Master data e relações de referência

1. `core.stores` — preparar lojas e datas de abertura/fechamento. Geografia estruturada está pendente de decisão humana; não codificar cidade em `name`.
2. `core.employee_roles` — catálogo curto de funções.
3. `core.employees` — funcionários e vínculos temporais básicos.
4. `core.employee_assignments` — função/loja por período, cobrindo somente períodos ativos.
5. `sales.sales_channels` — canal físico, e-commerce e dois marketplaces fictícios.
6. `payments.payment_methods` — meios de pagamento usados.
7. `procurement.suppliers` — fornecedores 100% fictícios.
8. `logistics.carriers` — transportadoras genéricas fictícias.
9. `catalog.categories` — pais antes de filhos; manter grafo sem ciclos.
10. `catalog.brands` — marcas fictícias sem equivalência deliberada a fabricante real identificável.
11. `catalog.products` — SKUs associados a categoria/marca, specification object e datas de disponibilidade.
12. `catalog.product_suppliers` — associação de produto-fornecedor após ambos existirem; uma preferência ativa no máximo.
13. `catalog.product_prices` — vigências SKU/canal não sobrepostas, gravadas em ordem temporal; funcionário criador opcional.
14. `crm.customers` — identidade comum identificada, tipo PF/PJ.
15. `crm.individual_profiles` e `crm.business_profiles` — exatamente a extensão que corresponde ao tipo do cliente.
16. `crm.customer_contacts` — contatos com domínios reservados de e-mail.
17. `crm.customer_addresses` — CEP/cidade/UF sintéticos estruturados. Geografia regional derivada da UF.

## Estado inicial de suprimento e estoque

18. `inventory.stock_locations` — locais associados a loja ou centros independentes.
19. `procurement.purchase_orders` — datas de bootstrap em 2022-11-01..2022-12-31 para estoque inicial; compras posteriores vinculadas à demanda prevista.
20. `procurement.purchase_order_items` — quantidades/custos planejados por SKU.
21. `procurement.goods_receipts` — recebimentos no local, após ordem e lead time.
22. `procurement.goods_receipt_items` — aceite/rejeição e custo aquisição. Aceite nunca excede quantidade pedida acumulada.
23. `inventory.stock_movements` — movimento `receipt` para cada entrada aceita do bootstrap; esta tabela é o ledger.
24. `inventory.stock_positions` — criar/atualizar em conjunto com cada movimento aceito, somente a partir do saldo resultante, preservando `average_unit_cost`. Ledger e projeção confirmam atomicamente.

Depois do bootstrap, compras/recebimentos adicionais são gerados no loop operacional cronológico, não antecipados de modo a violar disponibilidade.

## Operação comercial e estados relacionados

25. `sales.sales_orders` — em ordem temporal, respeitando cadastro/abertura/atribuição, canal, identificação e preço aplicável; snapshot de endereço quando disponível.
26. `sales.sales_order_items` — itens/quantidades, snapshot de SKU/nome e preço vigente; cabeçalho/itens/descontos reconciliam.
27. `sales.order_status_history` — evento inicial e mudanças válidas, com `occurred_at` crescente e status final consistente com o pedido.
28. `sales.applied_discounts` — desconto por linha e/ou rateio de pedido; inserido com cálculo de totais para assegurar que alocação total não excede elegível.
29. `inventory.stock_reservations` — reservar somente após regra de confirmação e disponibilidade; parcial por local se necessário. Cancelar/liberar antes de saída física.
30. `payments.payments` — tentativa/captura/declínio no ciclo do pedido, com método e valor. Uma recusa não reconhece recebimento.
31. `payments.payment_installments` — criar parcelas após operação parcelada e repartir centavos deterministicamente.
32. `logistics.fulfillments` — reservar local/origem e modalidade delivery/store_pickup coerente com canal.
33. `logistics.fulfillment_items` — associar quantidade alocada e atendida a pedido/item da mesma ordem. Não superar vendido/reservado acumulado.
34. `logistics.fulfillment_events` — sequência operacional coerente por fulfillment, com latências plausíveis.
35. `inventory.stock_movements` — após o item de atendimento existir, gravar saída `fulfillment`, quantity_delta negativo e `unit_cost` médio vigente. Atualizar `stock_positions` na mesma transação.
36. `inventory.stock_transfers` — operação rara por necessidade de reposição/rebalanceamento; locais origem/destino distintos.
37. `inventory.stock_transfer_items` — quantidade planejada/enviada/recebida; gravar `transfer_out` e `transfer_in` pareados no ciclo de despacho/recebimento com o mesmo custo histórico.
38. `after_sales.returns` — somente depois de pedido/atendimento elegível; solicitado, decidido e recebido em tempos próprios.
39. `after_sales.return_items` — apontar `sales_order_item_id` e `source_fulfillment_item_id` do mesmo pedido/linha; limitar recebido ao atendido, definir condição e destino no recebimento. Se houver movimento `customer_return`, inserir ledger e ajustar posição no mesmo commit; apenas destino `sellable` aumenta o saldo disponível.
40. `payments.refunds` — operação financeira posterior à elegibilidade e ao evento de retorno quando aplicável; manter refund acumulado dentro do valor elegível.

### Observação sobre dependências circulares de evento

O schema tem referências operacionais cruzadas: `inventory.stock_movements` pode referenciar `logistics.fulfillment_items`, `after_sales.return_items` e `inventory.stock_transfer_items`, enquanto essas linhas dão origem aos movimentos. Resolver no nível de evento com transações atômicas depois de criar a linha-fato (fulfillment/return/transfer item) e inserir seu movimento antes do commit; não quebrar FK nem desativá-la. `stock_positions` é projeção derivada dos movimentos/reservas e deve ser conciliada após cada evento confirmado.

## Classificação por camada

- **Master data:** lojas, funcionários, funções, canais, meios, fornecedores, carriers, categorias, marcas, produtos, clientes/perfis, contatos, endereços, associações SKU-fornecedor e preços.
- **Transactional data:** purchase orders/linhas/recebimentos/linhas; pedidos/itens/status/descontos; pagamentos/parcelas/refunds; fulfillments/itens/eventos; transferências/itens; devoluções/itens; reservas e movimentos.
- **Derived operational state:** `inventory.stock_positions` (saldo/custo atual) e estado corrente de cabeçalhos, que deve ser conciliável com movimentos/eventos. Embora persistidos, não são fatos independentes para volume: são atualizados a partir da sequência de eventos.

## Entidades por nome SQL

Para conferência da cobertura, todas as tabelas aparecem no roteiro: `core` (4), `crm` (5), `catalog` (5), `inventory` (6), `payments` (4), `logistics` (4), `after_sales` (2), `sales` (5) e `procurement` (5), total **40**. O ledger `inventory.stock_movements` reaparece como estágio de eventos posteriores; não é uma tabela adicional.
