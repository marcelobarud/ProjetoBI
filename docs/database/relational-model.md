# Proposta de modelo relacional operacional

**Fase 2A — proposta para revisão.** Este documento descreve uma estrutura física candidata para PostgreSQL 18. Nada aqui foi executado no PostgreSQL; a database proposta é `projeto_bi`. O Server Group `ProjetoBI` do pgAdmin é apenas organização local e não foi acessado.

O modelo representa o sistema operacional da empresa brasileira, com valores monetários em BRL. Não é um modelo estrela, não prescreve tabelas para o Power BI e não inclui views analíticas. A documentação é uma proposta para revisão humana antes da Fase 2B.

## Resumo da proposta

- **Database proposta:** `projeto_bi` (não criada nesta fase).
- **PostgreSQL:** versão 18, sem extensões externas obrigatórias.
- **Schemas:** 9.
- **Tabelas:** 40.
- **Identificadores:** `BIGINT GENERATED ALWAYS AS IDENTITY` para as PKs técnicas; códigos de negócio ficam em atributos separados e únicos quando necessários.
- **Nomenclatura:** inglês, `snake_case`, tabelas no plural, PK `<singular>_id`, FK com o nome da chave referenciada, constraints `pk_`, `fk_`, `uq_`, `ck_` e índices `idx_`.
- **Exclusões:** registros cadastrais usados por transações não são apagados em cascata; as relações usam restrição de exclusão e cadastros são inativados.
- **Estados:** `VARCHAR` com `CHECK` para conjuntos pequenos e estáveis; tabelas de referência para cadastros operacionais que precisam ser administrados (canais, formas de pagamento, funções, motivos não foram todos separados em tabelas).

## Schemas e tabelas

### `core` — organização e funcionários

| Tabela | Finalidade | PK e principais FKs | Cardinalidades e histórico |
| --- | --- | --- | --- |
| `stores` | Pontos físicos de operação e retirada. | `store_id`; nenhuma FK obrigatória. | Uma loja pode possuir locais de estoque e vínculos de funcionários; mantém estado atual e datas de abertura/fechamento. |
| `employees` | Cadastro operacional de funcionários, inclusive vendedor. | `employee_id`; nenhuma FK obrigatória. | Um funcionário pode ter vários vínculos históricos; desligamento não apaga vendas nem movimentos. |
| `employee_roles` | Catálogo enxuto de funções. | `employee_role_id`; nenhuma FK obrigatória. | Uma função pode aparecer em muitos vínculos; função desativada permanece referenciada pelo histórico. |
| `employee_assignments` | Períodos de função e lotação de um funcionário. | `employee_assignment_id`; FKs para `employees`, `employee_roles` e, opcionalmente, `stores`. | Um funcionário pode ter vários períodos/funções; vigência usa datas civis e não sobrescreve o histórico. |

### `crm` — clientes, perfis e dados de contato

| Tabela | Finalidade | PK e principais FKs | Cardinalidades e histórico |
| --- | --- | --- | --- |
| `customers` | Identidade cadastral comum para PF ou PJ identificadas. | `customer_id`; nenhuma FK obrigatória. | Pode ter um perfil PF ou PJ, contatos, endereços e pedidos. Venda presencial anônima não cria registro nesta tabela. |
| `individual_profiles` | Informações específicas de cliente pessoa física. | `customer_id` como PK/FK para `customers`. | Relação 1:0..1 com cliente; correspondência do tipo é validada pela aplicação/gerador, sem trigger nesta proposta. |
| `business_profiles` | Informações específicas de cliente pessoa jurídica. | `customer_id` como PK/FK para `customers`. | Relação 1:0..1; a aplicação/gerador garante perfil compatível com `customer_type`. |
| `customer_contacts` | Contatos atuais de clientes. | `customer_contact_id`; FK para `customers`. | Cliente 1:N contatos; alterações ficam cobertas pelo `updated_at`, sem histórico integral de cada edição nesta versão. |
| `customer_addresses` | Endereços brasileiros cadastrados. | `customer_address_id`; FK para `customers`. | Cliente 1:N endereços; o endereço selecionado para venda é copiado para o snapshot do pedido. |

### `catalog` — catálogo, fornecedores associados e preços

| Tabela | Finalidade | PK e principais FKs | Cardinalidades e histórico |
| --- | --- | --- | --- |
| `categories` | Categorias e eventual relação hierárquica entre elas. | `category_id`; autorreferência opcional a `categories`. | Categoria pode ter subcategorias e muitos produtos. A hierarquia é uma proposta física para a hipótese conceitual ainda revisável. |
| `brands` | Marcas associadas ao catálogo. | `brand_id`; nenhuma FK obrigatória. | Uma marca pode estar em muitos produtos; inativação preserva o histórico. |
| `products` | SKU efetivamente comercializável. | `product_id`; FKs para `categories` e, opcionalmente, `brands`. | Um SKU aparece em preços, fornecedores, compras, vendas e estoque; descontinuação mantém referências históricas. Atributos técnicos livres não são implementados nesta versão. |
| `product_suppliers` | Associação N:N entre produto e fornecedor, com referência comercial do fornecedor. | `product_supplier_id`; FKs para `products` e `procurement.suppliers`. | Produto pode ter vários fornecedores; uma associação pode ser marcada como preferencial (no máximo uma preferencial ativa por produto). |
| `product_prices` | Histórico de preços de venda por SKU e canal, com vigência. | `product_price_id`; FKs para `products`, `sales.sales_channels` e, opcionalmente, `core.employees`. | Um produto/canal pode ter vários períodos; não sobreposição de vigências é validada pela aplicação/gerador. |

### `sales` — canais e pedidos

| Tabela | Finalidade | PK e principais FKs | Cardinalidades e histórico |
| --- | --- | --- | --- |
| `sales_channels` | Canais físicos, e-commerce próprio e marketplaces. | `sales_channel_id`; nenhuma FK obrigatória. | Um canal pode ter muitos pedidos e preços. O tipo pertence a um conjunto `CHECK` curto. |
| `sales_orders` | Cabeçalho do pedido, situação comercial e snapshots de destinatário/endereço. | `sales_order_id`; FKs para canal, cliente opcional, loja opcional, vendedor opcional e endereço cadastrado opcional. | Um pedido tem um ou mais itens, eventos de status, descontos, pagamentos, remessas e devoluções. Cliente é nulo permitido apenas em venda física; a proposta usa `channel_type` redundante protegido por FK composta e `CHECK` para permitir validação pelo banco sem trigger. |
| `sales_order_items` | Itens/SKUs vendidos e seus snapshots comerciais e de custo. | `sales_order_item_id`; FK para pedido e FK para produto; chave única composta `(sales_order_id, sales_order_item_id)` dá suporte a relacionamentos que validam o pedido da linha. | Pedido 1:N itens; cada item pode ser dividido entre vários atendimentos e referenciado em várias devoluções. Quantidade, preço unitário e custo unitário histórico permanecem fixos para preservar o evento. |
| `order_status_history` | Eventos imutáveis de mudança de situação do pedido. | `order_status_history_id`; FKs para `sales_orders` e, opcionalmente, `core.employees`. | Pedido 1:N eventos; sequência e situação atual devem ser mantidas em uma transação pela aplicação. |
| `applied_discounts` | Descontos efetivamente aplicados a itens, incluindo rateio de desconto de pedido. | `applied_discount_id`; FK composta para o item e pedido. | Um item pode receber vários registros de desconto. Não há cadastro de campanhas nem motor promocional; referência/nome de campanha é snapshot opcional. Descontos de pedido são alocados a itens para permitir reconciliação do valor por item. |

### `procurement` — fornecedores, compras e recebimentos

| Tabela | Finalidade | PK e principais FKs | Cardinalidades e histórico |
| --- | --- | --- | --- |
| `suppliers` | Cadastro de fornecedores e referências de contato/comerciais. | `supplier_id`; nenhuma FK obrigatória. | Fornecedor pode estar em várias associações de produto e pedidos de compra; inativar em vez de excluir. |
| `purchase_orders` | Cabeçalho de ordem de compra. | `purchase_order_id`; FK para `suppliers` e, opcionalmente, funcionário responsável. | Uma compra tem vários itens e pode ter vários recebimentos. Estado atual e datas administrativas não substituem os recebimentos. |
| `purchase_order_items` | Quantidade solicitada e custo de aquisição originalmente pedido por produto. | `purchase_order_item_id`; FKs para compra e `catalog.products`; chave única composta `(purchase_order_id, purchase_order_item_id)` permite referenciar uma linha no contexto da compra. | Compra 1:N itens; quantidade recebida acumulada é confrontada transacionalmente, não por `CHECK` simples. |
| `goods_receipts` | Cada evento de recebimento de uma compra em um local. | `goods_receipt_id`; FKs para compra, `inventory.stock_locations` e, opcionalmente, funcionário conferente; chave única `(purchase_order_id, goods_receipt_id)` dá contexto de compra ao recebimento. | Compra 1:N recebimentos; cada recebimento pode ser parcial. Criar/aprovar compra não gera movimento físico. |
| `goods_receipt_items` | Quantidades recebidas, aceitas/rejeitadas e custo de entrada aplicado. | `goods_receipt_item_id`; FK composta para recebimento/compra e FK composta para item/compra. | Recebimento 1:N linhas; somente `accepted_quantity` gera entrada de estoque e alimenta o custo médio após validação transacional. |

### `inventory` — locais, saldos, movimentos, reservas e transferências

| Tabela | Finalidade | PK e principais FKs | Cardinalidades e histórico |
| --- | --- | --- | --- |
| `stock_locations` | Locais de estoque vinculados ou não a uma loja. | `stock_location_id`; FK opcional para `core.stores`. | Local possui posições, movimentos, reservas e pode ser origem/destino de remessas/transferências. |
| `stock_positions` | Projeção persistida do saldo físico e reservado por produto/local. | `stock_position_id`; FKs para `catalog.products` e `stock_locations`; UNIQUE produto/local. | Uma linha por SKU/local; disponibilidade é coluna gerada `on_hand_quantity - reserved_quantity`. Atualização ocorre atomicamente com movimentos/reservas. |
| `stock_movements` | Trilha operacional de entradas e saídas confirmadas. | `stock_movement_id`; FKs para produto/local e, conforme o tipo, recebimento, item de remessa, item de devolução ou item de transferência. | Muitos movimentos por SKU/local; movimentos são append-only por convenção de aplicação. Saldo e trilha devem ser conciliáveis. |
| `stock_reservations` | Quantidade comprometida a um item do pedido antes da saída física. | `stock_reservation_id`; FKs compostas para item/pedido e FKs para produto/local. | Um item pode ter reservas por local; liberação/expiração/consumo atualiza a posição em transação. Reserva não é movimento de saída. |
| `stock_transfers` | Transferência rastreável entre dois locais. | `stock_transfer_id`; FKs para locais de origem/destino e funcionários solicitante/conferente opcionais. | Transferência 1:N itens; estados propostos cobrem rascunho, trânsito, conclusão e cancelamento. Origem e destino devem ser diferentes. |
| `stock_transfer_items` | SKU e quantidade planejada/enviada/recebida por transferência. | `stock_transfer_item_id`; FKs para transferência e produto. | Item pode gerar movimentos pareados de saída/entrada; tolerâncias e diferenças são verificadas pela aplicação. |

### `payments` — cobrança, parcelas e reembolsos

| Tabela | Finalidade | PK e principais FKs | Cardinalidades e histórico |
| --- | --- | --- | --- |
| `payment_methods` | Cadastro administrável de meios de pagamento. | `payment_method_id`; nenhuma FK obrigatória. | Um meio pode ser usado por vários pagamentos; inativação não remove transações. |
| `payments` | Uma tentativa/operação de pagamento, com valor e estado próprio. | `payment_id`; FK para pedido e meio de pagamento. | Pedido 1:N operações; tentativa recusada permanece registrada e não é valor recebido. Uma operação pode possuir parcelas. |
| `payment_installments` | Parcelas e vencimentos associados a uma operação. | `payment_installment_id`; FK para `payments`. | Pagamento 1:N parcelas; valores somados e estados são conferidos em transação pela aplicação. |
| `refunds` | Estornos/reembolsos relacionados a pagamento e, quando houver, devolução. | `refund_id`; FKs compostas para pagamento/pedido e, opcionalmente, devolução/pedido. | Uma operação pode ter vários reembolsos; vínculo composto impede relacionar pagamento e devolução de pedidos diferentes. Reembolso tem estado próprio. |

### `logistics` — remessas e eventos de atendimento

| Tabela | Finalidade | PK e principais FKs | Cardinalidades e histórico |
| --- | --- | --- | --- |
| `carriers` | Prestadores de entrega. | `carrier_id`; nenhuma FK obrigatória. | Transportadora é opcional em entrega própria e não se aplica à retirada em loja. |
| `fulfillments` | Unidade de atendimento de parte ou todo um pedido, para entrega ou retirada. | `fulfillment_id`; FK para pedido e FKs opcionais para local, loja de retirada e transportadora; chave única `(sales_order_id, fulfillment_id)` dá contexto às linhas de atendimento. | Pedido 1:N remessas; pode atender itens de locais distintos. Quantidade final atendida por item é controlada transacionalmente. |
| `fulfillment_items` | Quantidade de um item de pedido alocada e efetivamente atendida em uma remessa. | `fulfillment_item_id`; FKs compostas para remessa/pedido e item/pedido. | Pedido e item N:N ao longo de remessas; cada associação tem quantidade alocada/atendida. Não presume que a remessa contenha todos os itens. |
| `fulfillment_events` | Eventos de preparação, despacho, tentativa, entrega ou retirada. | `fulfillment_event_id`; FK para `fulfillments` e funcionário opcional. | Remessa 1:N eventos append-only; evento registra `occurred_at` independente do registro. |

### `after_sales` — devoluções

| Tabela | Finalidade | PK e principais FKs | Cardinalidades e histórico |
| --- | --- | --- | --- |
| `returns` | Solicitação e ciclo administrativo de devolução referenciada a um pedido. | `return_id`; FK para pedido e FKs opcionais para funcionários solicitante/aprovador; chave única `(sales_order_id, return_id)` dá contexto às linhas e reembolsos. | Pedido 1:N devoluções; cliente é obtido do pedido quando identificado. Motivos são um conjunto `CHECK`, evitando tabela de domínio sem necessidade inicial. |
| `return_items` | Quantidades solicitadas, aprovadas, recebidas e destinadas por item vendido. | `return_item_id`; FKs compostas para devolução/pedido e item de venda/pedido. | Devolução 1:N itens; vários retornos podem referenciar um item vendido. Limite agregado de quantidade devolvida é regra transacional da aplicação. |

## Cardinalidades principais

- `customers` 1:N `sales_orders`; a FK do pedido é opcional apenas quando o canal é físico.
- `sales_channels` 1:N `sales_orders` e 1:N `product_prices`.
- `sales_orders` 1:N `sales_order_items`, `order_status_history`, `payments`, `fulfillments` e `returns`.
- `sales_order_items` 1:N `applied_discounts`, `fulfillment_items`, `stock_reservations` e `return_items`.
- Produtos e fornecedores são N:N por `product_suppliers`; compras e produtos são N:N por `purchase_order_items`.
- `purchase_orders` 1:N `purchase_order_items` e 1:N `goods_receipts`; `goods_receipts` 1:N `goods_receipt_items`.
- Produtos e locais de estoque são N:N ao longo do tempo por `stock_movements`; o saldo atual é projetado em `stock_positions`.
- `payments` 1:N `payment_installments` e 1:N `refunds`; uma devolução pode ter 0:N reembolsos.
- `fulfillments` 1:N `fulfillment_items` e 1:N `fulfillment_events`; cada linha de atendimento referencia um item do mesmo pedido.
- `returns` 1:N `return_items`; uma devolução pode ou não ter cliente identificado, conforme o pedido original.

## Identificadores, convenções e tipos transversais

Todas as PKs técnicas propostas são `BIGINT GENERATED ALWAYS AS IDENTITY`, com nomes previsíveis. Códigos legíveis (pedido, SKU, fornecedor, loja, canal) são atributos `VARCHAR` com `UNIQUE` e nunca substituem a chave técnica. Não há mistura com UUID.

Tabelas e colunas são em inglês e `snake_case`; tabelas em plural. FKs seguem o nome da PK de destino (`customer_id`, `sales_order_id`). Constraints: `pk_<table>`, `fk_<table>_<target>`, `uq_<table>_<meaning>`, `ck_<table>_<meaning>`; índices: `idx_<table>_<columns>`.

Todos os horários de evento e auditoria são `TIMESTAMPTZ` (instantes inequívocos; clientes apresentam no fuso local). Datas civis, nascimento e validade por dia são `DATE`. Valores monetários comerciais e de caixa usam `NUMERIC(19,2)` em BRL. Custos unitários médios/históricos usam `NUMERIC(20,8)` para reduzir erro acumulado em custo médio; nunca `FLOAT`/`REAL`. Quantidades de unidades são `BIGINT` inteiros positivos. Vigências de preço usam intervalos semiabertos `[valid_from, valid_to)` e `TIMESTAMPTZ`.

Estados pequenos e estáveis usam `VARCHAR` mais `CHECK`; canais, meios de pagamento, funcionários, fornecedores, produtos e locais que precisam de manutenção têm tabelas próprias. A ampliação de valores de `CHECK` será feita por migração futura revisada.

## Estratégias de histórico e valores

1. **Dados cadastrais mutáveis:** estado atual e `created_at`/`updated_at`; não há auditoria integral de cada edição nesta versão.
2. **Preços comerciais:** `catalog.product_prices` com vigência; venda guarda o preço efetivo em `sales_order_items`.
3. **Lotações:** `core.employee_assignments` guarda função, loja e datas civis de vigência.
4. **Status de pedido e logística:** estado atual no cabeçalho e eventos append-only (`order_status_history`, `fulfillment_events`). Atualização do estado corrente e inserção do evento devem ocorrer na mesma transação.
5. **Endereço/destinatário:** pedido guarda referência opcional ao endereço cadastrado e snapshot brasileiro utilizado no momento da venda; alterações cadastrais não reescrevem o pedido.
6. **Custo médio:** o saldo/custo médio corrente por SKU/local será persistido na posição de estoque (coluna proposta `average_unit_cost`); recebimentos aceitos guardam custo de entrada; item vendido guarda `unit_cost_snapshot`. Movimento guarda custo unitário aplicado quando relevante. A aplicação recalcula e atualiza movimento, posição e item da venda atomicamente; fórmula, ordem de concorrência, arredondamento e momento de reconhecimento ainda precisam de revisão.
7. **Devoluções:** aprovação no cabeçalho/itens, recebimento e eventual movimento para saldo vendável, e reembolso são eventos distintos. A aprovação não altera automaticamente estoque ou pagamento.

### Valores persistidos versus derivados

- `stock_positions.on_hand_quantity` é um saldo operacional persistido, conciliado aos movimentos; `reserved_quantity` é mantido com as reservas ativas. `available_quantity` é gerada pelo banco como `on_hand_quantity - reserved_quantity`.
- Custo médio por SKU/local (`average_unit_cost`) é persistido para atualizações operacionais eficientes; o total de custo do saldo pode ser derivado de quantidade e custo médio.
- `sales_order_items.unit_cost_snapshot` é persistido por unidade vendida. Custo histórico total do item pode ser derivado de quantidade × custo unitário snapshot.
- Preço unitário, desconto aplicado e valores totais do cabeçalho são snapshots comerciais do evento. Totais de pedido devem ser recalculados/reconciliados transacionalmente com itens, descontos e frete; não se recalculam com preços atuais.
- Quantidade disponível, subtotal de itens, rateio de desconto e totais agregados são derivados para consulta, mas snapshots de total da transação são mantidos para auditoria/reconciliação.

## Estoque e custo médio móvel

A proposta adota combinação de **posição persistida + trilha de movimentos**. A posição por `(product_id, stock_location_id)` mantém quantidade física, reservada, disponível gerada e custo médio unitário. `stock_movements` documenta entradas/saídas efetivas e é a trilha para conciliação; movimentos não são apagados nem editados como rotina.

- Recebimento: `goods_receipt_items.accepted_quantity` e `unit_acquisition_cost` são origem da entrada elegível. Somente a aceitação gera movimento positivo e altera a posição/custo médio.
- Reserva: `stock_reservations` aumenta quantidade reservada e reduz disponibilidade, sem alterar quantidade física nem criar movimento de saída.
- Atendimento: `fulfillment_items.fulfilled_quantity` confirma a quantidade entregue/retirada; movimento de saída reduz posição física e guarda o custo histórico unitário aplicado.
- Devolução: `return_items` registra aprovação/recebimento/destino; apenas quantidade destinada a retorno vendável cria entrada positiva, conforme política futura de custo.
- Transferência: itens geram movimentos de saída no local de origem e entrada no destino relacionados ao mesmo `stock_transfer_item_id`; transferência em trânsito não fica disponível no destino antes de concluída.
- Ajustes: movimento positivo/negativo exige motivo e funcionário responsável; o gerador não criará divergências artificiais.

**Não implementado nesta proposta:** fórmula de custo médio, regras de custos elegíveis, sincronização concorrente, precisão operacional e arredondamento. Em especial, a aplicação terá de bloquear/serializar atualizações do mesmo saldo para que entradas e vendas concorrentes usem uma sequência de custo determinística.

## Mapa de entidades da Fase 1

As 37 entidades conceituais foram revistas, não convertidas mecanicamente. O resultado proposto é de **40 tabelas em 9 schemas**.

- **Consolidadas:** endereço usado em pedido é snapshot no cabeçalho, além do cadastro de endereços; perfis PF/PJ são extensões 1:1 do cliente-base; categoria e subcategoria podem compartilhar tabela com autorreferência (a hierarquia ainda é proposta); canal e modalidade de atendimento permanecem conceitos separados; pagamento e tentativa são uma operação com estado; situação atual + tabela de eventos tratam histórico sem tabelas de status.
- **Representadas por tabelas:** cadastro e contato de cliente; produto/SKU; relação produto-fornecedor; preço por vigência; pedido e itens; histórico de status; compras e itens; recebimentos e itens; saldo e movimentos; reservas; transferências; pagamentos, parcelas, reembolsos; remessas, linhas de atendimento e eventos; devoluções e itens.
- **Não mantidas como tabelas próprias na primeira versão:** cadastro/motor de campanhas, categoria de motivo de devolução, cada valor de status como tabela, atributos técnicos genéricos (EAV/JSONB), uma camada de variantes e uma tabela de consumidor anônimo. Descontos guardam a aplicação e referência/campanha em snapshot; motivos/estados são `CHECK`; especificações detalhadas ficam fora da primeira versão; venda anônima é pedido físico com `customer_id` nulo.
- **Adicionadas para fechar necessidades operacionais:** `applied_discounts` para proveniência/rateio de descontos; `fulfillment_items` para quantidades parciais por remessa; `fulfillment_events` para trilha de execução; `stock_transfers` e `stock_transfer_items` para transferências rastreáveis. A projeção de saldo foi escolhida como tabela persistida reconciliável, em vez de tabela derivada somente sob consulta.

## Decisões pendentes para aprovação

1. **Estado do cliente PF/PJ:** a correspondência entre `customers.customer_type` e exatamente um perfil (`individual_profiles` ou `business_profiles`) não é garantida por FK/CHECK simples entre tabelas. **Recomendação:** validar na aplicação/gerador e incluir verificação de consistência transacional; alternativa é trigger ou estrutura de herança por tabelas específicas, com maior complexidade. **Impacto:** integridade do cadastro.
2. **Obrigatoriedade de cliente por canal:** a proposta duplica `channel_type` no pedido, protege a cópia por FK composta ao canal e usa `CHECK` para cliente não nulo nos canais digitais. **Recomendação:** aceitar essa redundância controlada, sem trigger; alternativa é validar somente no serviço/gerador, deixando o banco permitir incoerência. **Impacto:** integridade e simplicidade do esquema.
3. **CPF/CNPJ:** perfis permitem identificadores nulos, com formato numérico e unicidade quando preenchidos; checksum e obrigatoriedade não são definidos. **Recomendação:** manter opcionais nesta fase por não definir política fiscal/legal; alternativa é torná-los obrigatórios conforme canal/cliente após revisão. **Impacto:** cadastro, privacidade e elegibilidade de venda.
4. **Saldo persistido e custo médio:** `stock_positions` materializa saldo/custo médio e é atualizada na mesma transação que os movimentos. **Recomendação:** aprovar a projeção persistida + ledger e revisão por bloqueio transacional; alternativa é derivar saldo do ledger, com consultas mais caras e custo médio mais difícil de materializar. **Impacto:** concorrência, desempenho e reconciliação.
5. **Especificações de SKU:** não há atributos técnicos estruturados nesta versão. **Recomendação:** começar com descrição e referências comerciais, revisitando atributos específicos após catálogo realista ser aprovado; alternativa é JSONB opcional validado por aplicação, sem EAV. **Impacto:** evolução do catálogo e consultas operacionais.
6. **Descontos por pedido:** `applied_discounts` exige item-alvo; desconto de cabeçalho é alocado às linhas. **Recomendação:** guardar alocações por item e ratear no serviço de venda; alternativa é guardar desconto somente no cabeçalho, com margem e devolução por item menos precisas. **Impacto:** totalização, margem histórica e devoluções parciais.
7. **Limites agregados transacionais:** recebimentos acumulados ≤ comprado; remessas atendidas ≤ vendido; devoluções aceitas ≤ vendido; reembolsos ≤ valores elegíveis; períodos de preço/lotações sem sobreposição. **Recomendação:** validar em transações da aplicação/gerador com bloqueio das linhas-pai; alternativa é triggers/exclusões, algumas exigindo extensão `btree_gist`. **Impacto:** integridade sob concorrência e necessidade de código operacional.
8. **Brasil e dados cadastrais:** formatos simples podem usar `CHECK`, mas validação de dígitos verificadores e regras legais não foram definidas. **Recomendação:** permitir os identificadores como opcionais, validar formato na aplicação e postergar checksum/legalidade; alternativa é adicionar validadores depois, com regras claramente aprovadas. **Impacto:** qualidade e requisitos de cadastro.
9. **Custo elegível e devolução:** frete/impostos/custos acessórios e custo atribuído a mercadoria devolvida continuam abertos. **Recomendação:** armazenar custo de aquisição aceito e custo unitário histórico de venda sem fixar nesta fase todos os componentes nem a política de custo de retorno; alternativa é adotar política contábil detalhada antes da modelagem. **Impacto:** custo médio e margem histórica.
10. **Hierarquia de categorias:** a autorreferência permite níveis hierárquicos sem tabela de subcategoria separada. **Recomendação:** manter uma tabela com relação opcional pai/filha, como hipótese revisável; alternativa é usar categorias planas. **Impacto:** manutenção e navegação do catálogo.

## Limites da Fase 2A

Não foram criados database, schemas reais, tabelas, constraints, índices, views, migrations, triggers, funções, procedures, seeds, scripts Python, dados, projeto Power BI ou estrutura analítica. Os nomes e tipos descritos são uma proposta documental para revisão, não SQL executável.
