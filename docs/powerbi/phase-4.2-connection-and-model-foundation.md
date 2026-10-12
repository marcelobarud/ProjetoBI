# Fase 4.2 — conexão PostgreSQL e fundação do modelo analítico

**Estado:** CONCLUÍDA — conexão read-only, importação das sete tabelas, reconciliação, refresh e reabertura do PBIP validados.

**Data:** 2026-10-12.

**Checkpoint Git de entrada:** `38740b36d77e32704e0a6186385a6fe0a469f004` (`main`). Havia alterações locais não commitadas em quatro definições PBIP/TMDL/PBIR quando a fase começou. Elas foram preservadas sem edição; veja `git status` e o diff da worktree.

## 1. Conexão e autenticação

- A conexão administrativa de inspeção apontou para `projeto_bi`, PostgreSQL 18.6. Antes dos privilégios, o catálogo não continha a role `projetobi_pbi_ro`.
- Foi criada a role `projetobi_pbi_ro` com login, sem SUPERUSER, CREATEDB, CREATEROLE, REPLICATION ou BYPASSRLS e sem associação a outras roles.
- Privilégios concedidos à role: `CONNECT` em `projeto_bi`, `USAGE` somente nos schemas `sales`, `catalog`, `crm` e `core`; `SELECT` explícito somente nas sete tabelas relacionadas abaixo. Não recebeu `CREATE` em schemas nem privilégios de escrita, truncamento ou alteração nas tabelas. Não há concessão em sequences.
- `default_transaction_read_only=on` foi configurado para essa role nessa database como proteção adicional. As restrições efetivas de ACL foram verificadas em conexão autenticada separada e continuam sendo a barreira principal.
- `TEMP` na database aparece efetivo por causa da ACL padrão `PUBLIC` do PostgreSQL; não foi concedido diretamente à role. Isso permite somente objetos temporários de sessão, não escrita nas tabelas/esquemas do projeto. Remover a ACL pública afetaria outros usuários e ficou fora do escopo aprovado.
- Após tentativas de autenticação, a senha da role foi redefinida no PostgreSQL com autorização expressa do usuário e sincronizada manualmente no Windows Credential Manager. O valor não foi exibido nem registrado no repositório. Nenhum segredo ou string de conexão com credenciais foi adicionado ao PBIP, TMDL, Power Query ou Git.
- A conexão de verificação executou consultas SELECT nas sete tabelas e confirmou `current_database() = projeto_bi`, `current_user = projetobi_pbi_ro` e `transaction_read_only = on`. Para cada tabela, `SELECT=true` e `INSERT/UPDATE/DELETE/TRUNCATE/REFERENCES/TRIGGER=false`; nos quatro schemas, `USAGE=true` e `CREATE=false`.
- A database, seus dados, schemas e migrations foram preservados. As verificações ocorreram em transações somente leitura; não houve carga, DDL operacional, migration, view nem alteração de dados comerciais.

## 2. Inspeção e primeira seleção

As contagens do PostgreSQL foram executadas como a role read-only e comparadas com consultas DAX ao modelo semântico aberto no Power BI Desktop após refresh e reabertura. Todas as sete contagens coincidiram:

| Tabela | Grão confirmado | PostgreSQL | Power BI | Estado |
|---|---|---:|---:|---|
| `sales.sales_orders` | Uma linha por pedido | 120.000 | 120.000 | Coincide |
| `sales.sales_order_items` | Uma linha por item de pedido | 241.637 | 241.637 | Coincide |
| `catalog.products` | Um SKU/produto | 1.000 | 1.000 | Coincide |
| `catalog.categories` | Uma categoria | 42 | 42 | Coincide |
| `crm.customers` | Uma identidade de cliente identificada | 45.000 | 45.000 | Coincide |
| `core.stores` | Uma loja | 10 | 10 | Coincide |
| `sales.sales_channels` | Um canal | 4 | 4 | Coincide |

As FKs confirmadas no catálogo são: `sales_orders.customer_id → crm.customers.customer_id` (opcional); `sales_orders.store_id → core.stores.store_id` (opcional); `sales_orders.sales_channel_id` e `channel_type → sales_channels.sales_channel_id` e `channel_type` pela FK composta; `sales_order_items.sales_order_id → sales_orders.sales_order_id`; `sales_order_items.product_id → products.product_id`; e `products.category_id → categories.category_id`. A PK de cada dimensão candidata é única. Há FKs adicionais do pedido para endereço e funcionário, que não serão importados nesta etapa.

No modelo semântico foram criadas seis relações de negócio: categorias→produtos; produtos→itens; lojas→pedidos; clientes→pedidos; canais→pedidos; pedidos→itens. Além delas, o Desktop criou 17 relações auxiliares entre colunas de data e tabelas locais de inteligência automática de tempo. A unicidade das chaves no lado 1 foi verificada no PostgreSQL. A chave de canal é única e a validação da FK composta (`sales_channel_id`, `channel_type`) não encontrou órfãos. O grafo das seis relações de negócio não apresenta caminhos alternativos entre as tabelas selecionadas. A relação entre pedidos e itens liga grãos diferentes; manter medidas de cabeçalho separadas de somas por item para evitar fanout.

Não há FK nula nas linhas de item nem em `products.category_id`. Existem 19.829 pedidos anônimos sem `customer_id` e 57.420 pedidos sem `store_id`; os nulos serão preservados, sem imputar clientes ou lojas. `sales_orders` contém 116.305 `completed`, 3.265 `cancelled` e 430 `confirmed` no estado atual da base.

## 3. Estado do Power BI Desktop, PBIP, TMDL e refresh

- O projeto oficial permanece `powerbi/ProjetoBI.pbip`; Desktop instalado: `2.158.1177.0` (26.09). O processo Desktop já estava aberto com o projeto `ProjetoBI` quando esta fase começou.
- O conector PostgreSQL do Desktop foi configurado para `127.0.0.1:5432`, database `projeto_bi`, em modo Import. O usuário inseriu as credenciais localmente; nenhuma credencial foi automatizada nem exposta.
- As sete tabelas da seleção foram carregadas e salvas no PBIP. Depois do refresh, o arquivo foi fechado e reaberto no Desktop; consultas DAX executadas no mecanismo local confirmaram que o modelo estava disponível e que as contagens coincidiam com a origem.
- O TMDL contém as sete tabelas importadas e seis relações correspondentes ao grafo de FKs selecionado. O relatório PBIR existente foi preservado; alterações locais preexistentes no início da fase não foram descartadas.
- O modo previsto para o primeiro refresh é **Import**; DirectQuery e importação automática das 41 tabelas não foram usados.
- Foram incluídas somente as sete tabelas aprovadas. A validação do mecanismo semântico após reabertura retornou 120.000 pedidos, 241.637 itens, 1.000 produtos, 42 categorias, 45.000 clientes, 10 lojas e 4 canais. O intervalo de `placed_at` no modelo foi 2023-01-02 09:00–2026-09-29 09:00; nulos em `customer_id` e `store_id` foram preservados (19.829 e 57.420).

### Tipos e política temporal para a importação

- Chaves PostgreSQL `BIGINT` devem permanecer inteiros de 64 bits (`Int64.Type` / Whole number); `INTEGER` também inteiro. Não converter IDs para decimal nem para texto.
- As cinco colunas monetárias `sales_orders.subtotal_amount`, `discount_amount`, `shipping_amount`, `total_amount` e `sales_order_items.unit_sale_price` usam Fixed decimal (`Currency.Type`) na consulta M e `decimal` no TMDL, evitando ponto flutuante. Após refresh, `total_amount` máximo foi 81.462,08, soma 980.010.657,75 e `unit_sale_price` máximo 18.797,57; os valores observados cabem na representação.
- `DATE` permanece Date. `TIMESTAMPTZ` (`placed_at`) foi importado como DateTime, com valores observados entre 2023-01-02 09:00 e 2026-09-29 09:00 no modelo. A conversão explícita para data comercial `America/Sao_Paulo` e a coluna calendário ficam para a modelagem autorizada; não usar conversão implícita pela timezone da máquina nem alterar o instante UTC sem necessidade.
- Quantidades PostgreSQL `BIGINT` permanecem inteiras. Flags `BOOLEAN` permanecem booleanas; status/códigos permanecem categóricos. `JSONB specifications` é nulo e opcional, mas não faz parte da seleção inicial.
- A cultura do modelo já existente é `pt-BR`; a cultura de origem/interpretação deve ser definida explicitamente quando necessária, independentemente do idioma inglês do Desktop.

## 4. Arquitetura dimensional proposta

### Núcleo comercial

Fatos operacionais distintos, sem declarar medidas finais:

| Fato candidato | Grão | Chaves principais | Observação |
|---|---|---|---|
| Fato de pedidos | Uma linha por `sales_order_id` | data do pedido, canal, cliente opcional, loja opcional | Métricas de cabeçalho permanecem aqui; estado é o estado atual/final, não um evento de status. |
| Fato de itens comerciais | Uma linha por `sales_order_item_id` (único no conjunto de itens) | pedido, produto/SKU | Quantidade e preço de linha; `sku_snapshot` e `product_name_snapshot` são snapshots e não devem ser substituídos sem decisão pelos atributos correntes do cadastro. |
| Dimensão produto | Uma linha por `product_id` | categoria | Cadastro atual; contém também `brand_id` e `specifications`, que não exigem uma dimensão adicional agora. |
| Dimensão categoria | Uma linha por `category_id` | categoria-pai opcional | Hierarquia autorreferenciada. Pode ser achatada na futura `DimProduto`; evitar uma cadeia ambígua de relações recursivas no primeiro modelo. |
| Dimensão cliente | Uma linha por `customer_id` identificado | chave do cliente | Pedidos físicos anônimos ficam sem cliente; não fabricar identidade. |
| Dimensão loja | Uma linha por `store_id` | loja | Só atende pedidos com `store_id`; não derivar loja de outro campo sem regra aprovada. |
| Dimensão canal | Uma linha por `sales_channel_id` | canal e tipo | A integridade entre canal e `channel_type` é garantida pela FK composta da origem. |
| Dimensão calendário | Uma linha por dia comercial | papéis para os timestamps usados | Não existe fisicamente no PostgreSQL; será uma tabela do modelo quando a modelagem for autorizada. |

Cardinalidades candidatas e filtro: `sales_channels 1 → * sales_orders`; `customers 1 → * sales_orders` e `stores 1 → * sales_orders` (relações opcionais na ponta do pedido); `sales_orders 1 → * sales_order_items`; `products 1 → * sales_order_items`; `categories 1 → * products`. Usar direção simples da dimensão para o fato. A relação pedido→itens é válida no OLTP, mas conecta dois grãos de fato; sua ativação no semântico deve aguardar decisão explícita de desenho/medidas, para evitar que valores de cabeçalho sejam repetidos por item. Uma alternativa posterior é usar dimensões conformadas e manter os fatos separados.

Sem estratégia comprovada, não relacionar diretamente fatos de pedidos, itens, pagamentos, fulfillments, refunds, devoluções e movimentos. Para fatos filhos, pré-agregar ao grão requerido ou ligá-los a dimensões conformadas. Preservar linhas sem referência dimensional como nulas no estágio inicial; política de membro desconhecido fica para a modelagem e para cada indicador.

### Fatos candidatos posteriores

| Fato | Grão | Relacionamentos e cuidado |
|---|---|---|
| Fulfillment/COGS | Uma linha por movimento de estoque do tipo `fulfillment` | `stock_movement_id`, `fulfillment_item_id`, produto, local e instante; um item atendido pode ter vários movimentos/custos. |
| Pagamentos | Uma tentativa/captura por `payment_id` | Vários por pedido por retry ou divisão; status e instante próprios. Não é receita de venda. |
| Parcelas | Uma linha por `payment_installment_id` | Fato separado de pagamento e recebimento; não somar os dois grãos. |
| Refunds | Uma linha por `refund_id` concluído/estado financeiro | Ligado a pagamento e opcionalmente à devolução/cancelamento; não multiplicar pelos itens. |
| Devoluções | Uma linha por `return_item_id` | Liga item vendido e fulfillment de origem; quantidades e destino físico distintos do refund. |
| Movimentos de estoque | Uma linha por `stock_movement_id` | Ledger de mudanças físicas/custo; transferências de entrada/saída não são vendas. |
| Posição de estoque | Uma linha corrente por produto/local | Snapshot atual, não histórico diário; não somar com movimentos como um só fato. |

## 5. Risco de fanout e contratos financeiros

- Pedidos→itens é 1:N; somar `total_amount` após detalhar itens multiplica cabeçalhos. Itens podem ter várias alocações de desconto, fulfillments e devoluções; cada filho deve ser agregado antes de combinar fatos.
- Um item pode ter múltiplas saídas de fulfillment e custos distintos; COGS deve começar no grão de `stock_movements` e então ser agregado. Pagamentos podem ser retries/divisões; refunds podem ser múltiplos por pagamento/devolução. Não juntar tabelas filhas cruas entre si.
- Fulfillments e devoluções ligam-se por alocação e referência de origem; isso não torna um refund atribuível a cada item. Necessário rateio aprovado antes de qualquer métrica de margem por SKU/categoria.
- Preservar os contratos homologados M5: receita líquida de produtos concluídos R$ 949.319.764,19; receita analítica após devoluções R$ 922.588.975,45; COGS analítico ajustado R$ 717.455.650,26; lucro bruto analítico R$ 205.133.325,19; margem 22,23%. Receita operacional e receita analítica após devoluções são conceitos diferentes.
- COGS original de fulfillment permanece separado do COGS analítico ajustado. A identidade é `COGS analítico = COGS original de fulfillment − reversão sellable reintegrada`. Perda non-sellable permanece dentro do COGS analítico e não é deduzida novamente. Conciliar futuros cálculos às consultas em `database/queries/baselines/`, especialmente `08_payments_and_refunds.sql`, `09_returns.sql` e `11_cost_and_margin.sql`.
- Não foram criadas medidas DAX definitivas, dashboards ou páginas analíticas.

## 6. Implementação incremental proposta

1. **Núcleo comercial:** concluir importação controlada das sete tabelas, validar tipos/contagens, acordar relações e calendário e manter os dois fatos separados até fechar o tratamento do cabeçalho.
2. **Ajustes financeiros e devoluções:** trazer origem de fulfillment, movimentos de custo e return items na menor seleção necessária para reproduzir receita após devoluções e reversão vendável, respeitando M5.
3. **Pagamentos e recebimentos:** adicionar pagamentos, parcelas e refunds como grãos independentes; separar venda comercial, captura/recebimento e refund.
4. **Estoque e abastecimento:** adicionar ledger, posições, compras, recebimentos e locais conforme perguntas operacionais. Priorizar ledger temporal quando a análise for histórica; snapshot atual não responde ao passado.
5. **Indicadores e análises operacionais:** só após validar fatos/dimensões, relações e reconciliação dos baselines; medidas e relatórios exigem fase autorizada.

Esta sequência começa no núcleo com FKs comprovadas, adiciona primeiro as entidades necessárias aos contratos de margem já homologados e posterga indicadores até que os grãos estejam reconciliados. A ordem detalhada ainda pode depender das perguntas analíticas aprovadas.

## 7. Limitações e próximo passo

- A importação da fase está concluída. O Desktop também gerou 16 tabelas locais `LocalDateTable_*`, uma `DateTableTemplate_*` e 17 relações auxiliares de inteligência automática de tempo; são objetos auxiliares do modelo, não tabelas carregadas do PostgreSQL. Revisar/substituir esse comportamento ao implementar o calendário comercial numa fase autorizada.
- Reavaliar se o conector requer driver/componente; nenhuma instalação ou configuração global foi feita.
- Não avançar para implementação do modelo dimensional completo sem autorização da fase correspondente.

**Classificação:** **FASE 4.2 CONCLUÍDA — NÚCLEO COMERCIAL IMPORTADO E RECONCILIADO**. O modelo dimensional, calendário comercial, medidas DAX definitivas e relatórios continuam fora desta fase e dependem da autorização correspondente.
