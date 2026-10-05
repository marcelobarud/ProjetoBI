# Revisão de lacunas do schema para geração — Fase 3A

## Escopo e base da revisão

Pergunta: o schema operacional existente consegue representar a operação sintética e as análises previstas? Revisão realizada a partir da documentação aprovada e leitura da migration `001_initial_schema.sql`, incluindo as 40 definições de tabela, FKs e CHECKs. Não foi necessário consultar PostgreSQL; nenhum SQL foi executado. Nenhuma estrutura foi alterada.

## Resultado

# SCHEMA CHANGES RECOMMENDED

Não foi identificado **BLOCKER** para integridade ou geração de vendas, pagamentos, compras, estoque, logística e devoluções. Existe uma recomendação antes do gerador: `core.stores` não contém endereço ou atributos geográficos estruturados. Sem essa informação, análises e mapa por cidade/UF de loja não podem ser feitos a partir do ponto de venda; inferir localização do nome da loja ou de pedidos vinculados não é equivalente e criaria uma geografia falsa.

### Recomendação — geografia estruturada da loja

- **Classe:** RECOMMENDED; decisão humana necessária antes da Fase 3B.
- **Problema/impacto:** `core.stores` tem código, nome, status e datas operacionais, mas não cidade, UF, CEP ou endereço. `sales.sales_orders.store_id` permite performance por loja, mas não geografia da unidade. `inventory.stock_locations` pode apontar para uma loja, porém não resolve localização quando a loja não está georreferenciada.
- **Sugestão para avaliação em fase própria:** adicionar atributos estruturados de endereço da unidade (no mínimo `city` e `state_code`, preferencialmente também `postal_code` e `country_code`) ou criar uma tabela de endereço de loja se histórico/múltiplos endereços forem requisitos. O escopo atual não exige histórico de endereço de loja; não se recomenda criar uma dimensão geográfica completa sem requisito aprovado.
- **Por que não resolver apenas no Power Query:** transformação não consegue recuperar cidade/UF ausente sem fonte de referência verdadeira. Embutir a cidade em `name` ou inferir pela associação do pedido perde a semântica de local físico e pode atribuir ao estabelecimento a geografia do cliente/entrega.
- **Momento:** deliberar antes de gerar master data. Se aprovada, implementar migration específica numa fase de schema (por exemplo 2B.2), atualizar dicionário/relatório e validar antes da 3B. Se rejeitada, aceitar explicitamente que análises geográficas de lojas não estarão disponíveis; não inventar a localização no gerador.

## Revisão por área

| Área | Classe | Capacidade e limite observado |
|---|---|---|
| Geografia de lojas | **RECOMMENDED** | Sem cidade/UF/endereço em `core.stores`; performance por loja existe, mapa/geografia da loja não. Ver recomendação acima. |
| Geografia de clientes/pedidos | Adequado | `crm.customer_addresses` tem CEP, logradouro, bairro, município, UF e país; `sales.sales_orders` guarda snapshot do endereço. Dados sintéticos podem preencher endereço para digital e deixar vendas presenciais sem entrega conforme contexto. O endereço não é coordenada nem código IBGE, portanto granularidade municipal deve ser interpretada com cautela. |
| Regiões de venda | Adequado com derivação | `state_code`/`state_code_snapshot` permitem derivar região brasileira por mapeamento estável das UFs (N, NE, CO, SE, S). Região não é atributo físico separado; manter mapeamento documentado/versionado no gerador/consulta, sem copiar região arbitrariamente. |
| Canais | Adequado | `sales.sales_channels` distingue `physical`, `ecommerce` e `marketplace`; pedido tem FK composta que preserva o tipo. Referência externa é snapshot. Não há limitação para 4 canais iniciais. |
| Categorias | Adequado | `catalog.categories.parent_category_id` representa hierarquia; constraint impede apenas auto-referência direta, então gerador deve evitar ciclos de qualquer comprimento. Produtos apontam a uma categoria. |
| Marcas | Adequado | `catalog.brands` e FK nullable de produto permitem marcas fictícias e itens sem marca atribuída quando fizer sentido. |
| Vendedores | Adequado com regra de aplicação | Funcionários, funções, lotações e data de desligamento existem; pedido pode apontar vendedor. Gerador deve garantir função/lotação ativa na data e proibir atribuição posterior ao desligamento. Não há quotas/comissão, fora do escopo aprovado. |
| Custos | Adequado | Custo de compra em `goods_receipt_items`, posição com custo médio e `stock_movements.unit_cost`; a fonte do custo realizado é saída `fulfillment`. Não há coluna de custo snapshot no item de venda, conforme decisão aprovada. |
| Margem | Adequado por derivação | Receita por pedido/itens/descontos, frete separado e custo realizado pelos movimentos permitem margem bruta analítica. Frete de compra/acessórios de custo não têm alocação definida e ficam fora da margem/custo de estoque V1, conforme regra transacional aprovada. |
| Estoque | Adequado com invariantes transacionais | Posições, quantidade disponível gerada, reservas, movimentos, transferências e recebimentos existem. Limites entre linhas/tabelas exigem engine transacional/gerador; CHECKs não bastam. Não se pode gerar saldo diretamente sem ledger correspondente. |
| Pagamentos | Adequado com reconciliação de aplicação | Métodos, tentativas, parcelas, BRL e reembolsos existem. Limite acumulado por pedido, conciliação de parcelas e teto de reembolso precisam de validação transacional documentada. |
| Logística | Adequado com correlação temporal | Fulfillments, itens, eventos, origem de estoque, retirada, carrier e tracking existem. Gerador controla ordenação de eventos e quantidade atendida acumulada; status e evento precisam concordar. |
| Devoluções | Adequado | Devolução por item e `source_fulfillment_item_id` composto garantem vínculo ao atendimento do mesmo pedido/item. Destinos e quantidades limitados por CHECKs locais; teto acumulado e custo histórico dependem do gerador/transação. |
| Histórico temporal | Adequado, sujeito a geração | Vigências de preço, lotações, status de pedidos/eventos, timestamps e snapshots preservam contextos-chave. Sobreposição de vigências e coerência temporal entre entidades são responsabilidade futura da engine; dados cadastrais mutáveis não têm auditoria integral. |

### Melhoria opcional — fim do ciclo comercial de SKU

- **Classe:** OPTIONAL.
- `catalog.products.created_at` pode sustentar início sintético de disponibilidade e `status` informa a situação corrente, mas não há `discontinued_at` nem histórico de mudança de estado. Isso não impede vendas e estoque coerentes: a configuração do gerador pode manter a data de fim como regra de execução e evitar novas vendas após ela. O banco, porém, não permitirá reconstruir a data exata do fim de comercialização apenas pelo status atual.
- Se análise de lançamento/descontinuação virar requisito, avaliar campo de vigência ou histórico de status em migration própria; não é necessário para o portfolio analítico atual. Power Query não consegue recuperar uma data que não foi persistida, mas este insight não é gate da Fase 3B.

## Observações de implementação futura

- JSONB já exige raiz `object`; validação semântica de campos por família deve ficar no gerador.
- `catalog.products.unit_of_measure` permanece sem CHECK. O gerador usará `unit` até decisão diferente.
- Regras agregadas (compras, fulfillment, reservas, devolução, reembolso e totais) não são garantidas só por FKs/CHECKs; validar e transacionar conforme `operational-transactions.md`.
- O schema não registra campanha como entidade própria; `applied_discounts` tem snapshots de código/referência/descrição suficientes para distribuição planejada, sem motor de promoção.
- O endereço do cliente/pedido não substitui o endereço da loja. Não popular `city_snapshot` como se fosse geografia do estabelecimento.

## Decisão pendente para revisão

Decidir se a geografia estruturada das lojas deve entrar numa migration anterior ao gerador. Até a decisão, o plano de geração pode ser detalhado, mas a Fase 3B não deve criar lojas com localização inventada no nome ou inferida de pedidos.
