# Fase 4.2 — conexão PostgreSQL e fundação do modelo analítico

**Estado:** PARTIAL — role PostgreSQL read-only criada e validada; conexão/importação no Power BI Desktop e reabertura após refresh pendentes.

**Data:** 2026-10-12.

**Checkpoint Git de entrada:** `38740b36d77e32704e0a6186385a6fe0a469f004` (`main`). Havia alterações locais não commitadas em quatro definições PBIP/TMDL/PBIR quando a fase começou. Elas foram preservadas sem edição; veja `git status` e o diff da worktree.

## 1. Conexão e autenticação

- A conexão administrativa de inspeção apontou para `projeto_bi`, PostgreSQL 18.6. Antes dos privilégios, o catálogo não continha a role `projetobi_pbi_ro`.
- Foi criada a role `projetobi_pbi_ro` com login, sem SUPERUSER, CREATEDB, CREATEROLE, REPLICATION ou BYPASSRLS e sem associação a outras roles.
- Privilégios concedidos à role: `CONNECT` em `projeto_bi`, `USAGE` somente nos schemas `sales`, `catalog`, `crm` e `core`; `SELECT` explícito somente nas sete tabelas relacionadas abaixo. Não recebeu `CREATE` em schemas nem privilégios de escrita, truncamento ou alteração nas tabelas. Não há concessão em sequences.
- `default_transaction_read_only=on` foi configurado para essa role nessa database como proteção adicional. As restrições efetivas de ACL foram verificadas em conexão autenticada separada e continuam sendo a barreira principal.
- `TEMP` na database aparece efetivo por causa da ACL padrão `PUBLIC` do PostgreSQL; não foi concedido diretamente à role. Isso permite somente objetos temporários de sessão, não escrita nas tabelas/esquemas do projeto. Remover a ACL pública afetaria outros usuários e ficou fora do escopo aprovado.
- A senha forte foi gerada localmente, não foi impressa nem gravada no repositório e foi guardada no Windows Credential Manager deste usuário. Nenhum segredo ou string de conexão foi adicionado ao PBIP, TMDL, Power Query, `.env` ou Git.
- A conexão de verificação executou consultas SELECT nas sete tabelas e confirmou `current_database() = projeto_bi`, `current_user = projetobi_pbi_ro` e `transaction_read_only = on`. Para cada tabela, `SELECT=true` e `INSERT/UPDATE/DELETE/TRUNCATE/REFERENCES/TRIGGER=false`; nos quatro schemas, `USAGE=true` e `CREATE=false`.
- A database, seus dados, schemas e migrations foram preservados. As verificações ocorreram em transações somente leitura; não houve carga, DDL operacional, migration, view nem alteração de dados comerciais.

## 2. Inspeção e primeira seleção

As contagens a seguir foram executadas como a role read-only por SQL direto no PostgreSQL. Elas são a referência para reconciliar o Power Query depois que a importação estiver disponível.

| Tabela | Grão confirmado | PostgreSQL | Power BI | Estado |
|---|---|---:|---:|---|
| `sales.sales_orders` | Uma linha por pedido | 120.000 | N/A | Importação pendente |
| `sales.sales_order_items` | Uma linha por item de pedido | 241.637 | N/A | Importação pendente |
| `catalog.products` | Um SKU/produto | 1.000 | N/A | Importação pendente |
| `catalog.categories` | Uma categoria | 42 | N/A | Importação pendente |
| `crm.customers` | Uma identidade de cliente identificada | 45.000 | N/A | Importação pendente |
| `core.stores` | Uma loja | 10 | N/A | Importação pendente |
| `sales.sales_channels` | Um canal | 4 | N/A | Importação pendente |

As FKs confirmadas no catálogo são: `sales_orders.customer_id → crm.customers.customer_id` (opcional); `sales_orders.store_id → core.stores.store_id` (opcional); `sales_orders.sales_channel_id` e `channel_type → sales_channels.sales_channel_id` e `channel_type` pela FK composta; `sales_order_items.sales_order_id → sales_orders.sales_order_id`; `sales_order_items.product_id → products.product_id`; e `products.category_id → categories.category_id`. A PK de cada dimensão candidata é única. Há FKs adicionais do pedido para endereço e funcionário, que não serão importados nesta etapa.

Não há FK nula nas linhas de item nem em `products.category_id`. Existem 19.829 pedidos anônimos sem `customer_id` e 57.420 pedidos sem `store_id`; os nulos serão preservados, sem imputar clientes ou lojas. `sales_orders` contém 116.305 `completed`, 3.265 `cancelled` e 430 `confirmed` no estado atual da base.

## 3. Estado do Power BI Desktop, PBIP, TMDL e refresh

- O projeto oficial permanece `powerbi/ProjetoBI.pbip`; Desktop instalado: `2.158.1177.0` (26.09). O processo Desktop já estava aberto com o projeto `ProjetoBI` quando esta fase começou.
- O conector PostgreSQL do Desktop foi aberto e configurado para `127.0.0.1:5432`, database `projeto_bi`, em modo Import. A caixa de credenciais Database está aberta e aguarda o usuário inserir localmente o usuário `projetobi_pbi_ro` e a senha armazenada no Windows Credential Manager; credenciais não foram automatizadas nem expostas.
- Nenhuma tabela foi importada nesta execução. As contagens Power BI, os tipos vistos no preview, nulos no Power Query, refresh e reabertura após refresh estão **pendentes**; não declarar PASS para esses gates.
- O modelo TMDL no disco ainda não contém tabelas nem relações. O relatório PBIR permanece o arquivo de definição existente. As alterações locais iniciais — inclusive `queryLimitOption` no `report.json` e as diferenças de whitespace em TMDL — foram preservadas integralmente e não fazem parte desta fase.
- O modo previsto para o primeiro refresh é **Import**; DirectQuery e importação automática das 41 tabelas não foram usados.

### Tipos e política temporal para a importação

- Chaves PostgreSQL `BIGINT` devem permanecer inteiros de 64 bits (`Int64.Type` / Whole number); `INTEGER` também inteiro. Não converter IDs para decimal nem para texto.
- Valores PostgreSQL `NUMERIC(19,2)` não devem ser arredondados durante ingestão. Preferir Fixed decimal/Currency no modelo, conferindo que o limite observado caiba nessa representação; os registros consultados têm `sales_orders.total_amount` máximo de R$ 81.462,08 e soma de R$ 980.010.657,75. Não trocar silenciosamente para ponto flutuante quando a exatidão monetária for necessária.
- `DATE` permanece Date. `TIMESTAMPTZ` deve ser tratado primeiro como instante com zona e só depois convertido de modo explícito para a data comercial `America/Sao_Paulo`. O intervalo de `placed_at` confirmado após essa conversão vai de 2023-01-02 09:00 a 2026-09-29 09:00; não usar conversão implícita pela timezone da máquina nem alterar o instante UTC sem necessidade. A visualização/coluna de data comercial deve seguir a política de `readiness.md`.
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

- **Ação manual necessária:** autenticar na caixa aberta do Desktop como `projetobi_pbi_ro`; depois importar apenas as sete tabelas listadas, validar preview/tipos e contagens contra esta referência, atualizar, salvar pelo Desktop e reabrir o PBIP. Então documentar os resultados e reconciliar o diff sem descartar as alterações locais preexistentes.
- Reavaliar se o conector requer driver/componente; nenhuma instalação ou configuração global foi feita.
- Não avançar para implementação do modelo dimensional completo sem autorização da fase correspondente.

**Classificação:** **FASE 4.2 PARTIAL — MANUAL CREDENTIAL ENTRY REQUIRED**. A role read-only está pronta e validada pelo cliente PostgreSQL; a autenticação no Desktop, importação e validação pelo Power BI ainda são gates pendentes.
