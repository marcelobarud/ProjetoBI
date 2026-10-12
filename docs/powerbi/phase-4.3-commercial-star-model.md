# Fase 4.3 — modelo estrela comercial

**Status:** PASS — refresh, reconciliação no mecanismo semântico e reabertura do PBIP concluídos no Power BI Desktop.

## Escopo e fonte

O modelo utiliza somente as sete tabelas comerciais aprovadas na Fase 4.2, com PostgreSQL `projeto_bi`, role read-only `projetobi_pbi_ro` e modo Import. Não foram alterados o banco, schemas, tabelas, dados, migrations, usuário ou credenciais. O PBIP permanece na pasta `powerbi/`.

## Grãos e tabelas

| Tabela | Grão | Origem e observações |
|---|---|---|
| `FatoPedidos` | Uma linha por `sales_order_id` | Cabeçalho e seus valores, status, instante original `placed_at`, atributos e chaves do pedido. Não se relaciona diretamente com a fato de itens. |
| `FatoItensPedido` | Uma linha por `sales_order_item_id` | Quantidades, preço unitário e snapshots originais do item. Recebe data, cliente, loja e canal do pedido por junção esquerda na chave única `sales_order_id`; não replica valores monetários do cabeçalho. |
| `DimCalendario` | Uma linha por data de 2023-01-01 a 2026-09-30 | Calendário contínuo com ano, mês, ano-mês, trimestre, dia, dia da semana e indicador de fim de semana. Cultura pt-BR; chaves/ordens auxiliares ficam ocultas. |
| `DimProduto` | Uma linha por `product_id` | Produto unido à categoria e sua categoria pai direta. Preserva campos do produto e expõe código/nome da categoria, categoria pai e status ativo. A hierarquia observada tem apenas raiz e filho; não requer dimensão recursiva. |
| `DimCliente` | Uma linha por `customer_id` | Cadastro de clientes. |
| `DimLoja` | Uma linha por `store_id` | Cadastro e localização das lojas. |
| `DimCanal` | Uma linha por `sales_channel_id` | Código, nome, tipo e estado do canal. |

## Relações

As nove relações do desenho são muitos-para-um a partir das fatos e filtram em uma direção da dimensão para a fato:

- `DimCalendario` → `FatoPedidos` e `FatoItensPedido`.
- `DimCliente` → `FatoPedidos` e `FatoItensPedido`.
- `DimLoja` → `FatoPedidos` e `FatoItensPedido`.
- `DimCanal` → `FatoPedidos` e `FatoItensPedido`.
- `DimProduto` → `FatoItensPedido`.

Não há relação fato-a-fato, produto-pedido, muitos-para-muitos ou caminho bidirecional. Isso mantém o valor do cabeçalho no grão do pedido e deixa análises de produto no grão do item.

## Datas comerciais e Auto date/time

As consultas M preservam `placed_at` como instante e derivam `order_date` no PostgreSQL com `(placed_at AT TIME ZONE 'America/Sao_Paulo')::date`; o calendário não depende do fuso do Windows. A consulta de itens propaga a mesma `order_date`. A coluna derivada é Date, separada do timestamp original.

O TMDL declara `DimCalendario` como calendário (`dataCategory: Time`, coluna chave `Data`) e `__PBI_TimeIntelligenceEnabled = 0`. As 16 tabelas `LocalDateTable_*`, a `DateTableTemplate_*` e as 17 relações auxiliares da Fase 4.2 foram removidas do modelo; após salvar e reabrir no Desktop, os arquivos auxiliares não reapareceram.

## Power Query e tipos

- Pedidos: `Value.NativeQuery` com SELECT da tabela de pedidos e projeção explícita da data local; colunas de cabeçalho monetárias passam por `Currency.Type`.
- Itens: SELECT somente de leitura com `LEFT JOIN` pedidos pela chave; preserva as linhas dos itens e `unit_sale_price` continua em `Currency.Type`.
- Produto: SELECT somente de leitura com junção externa de produtos, categoria e pai direto.
- Cliente, loja e canal: mantêm as navegações PostgreSQL aprovadas.
- As consultas nativas declaram `EnableFolding = true`. Nenhuma view persistente foi criada.
- IDs permanecem inteiros de 64 bits; quantidades permanecem inteiras; códigos e estados permanecem categóricos; colunas monetárias preservam Fixed decimal.

## Nulos, fanout e limites de interpretação

Pedidos sem cliente (19.829) ou sem loja (57.420) permanecem sem chave dimensional; nenhum cliente/loja fictício foi criado. O comportamento de totais e do membro em branco deve ser confirmado após o refresh. A junção de pedido para item usa a chave única do pedido; a validação da contagem de itens e de ausência de fanout está pendente no mecanismo semântico.

Não foram criadas medidas DAX financeiras definitivas. Preço unitário não é tratado como receita realizada, e não se calcula margem. Status, descontos, devoluções e definição de receita precisam seguir os baselines comerciais aprovados em qualquer fase futura de medidas. A dimensão de cadastro não representa histórico SCD.

## Validação

### Verificações estáticas executadas

- Sete declarações de tabela TMDL e nove relações presentes.
- A primeira abertura do Desktop localizou um formato de string booleana inválido em `DimProduto.category_is_active`; a expressão foi corrigida usando o formato TMDL já aceito por outras colunas booleanas do projeto. Reabrir no Desktop ainda é necessário para confirmar a correção.
- `model.tmdl` não referencia tabelas automáticas de data; nenhum TMDL da definição ativa contém `LocalDateTable`, `DateTableTemplate` ou marcadores temporários de linhagem.
- As consultas com `Value.NativeQuery` têm `EnableFolding = true` e usam SELECT.
- PBIP, PBIR e `diagramLayout.json` foram lidos como JSON válido.
- `git diff --check` não encontrou novos problemas nos arquivos desta fase. Os avisos remanescentes são linhas em branco finais preexistentes em `definition/cultures/pt-BR.tmdl`, `definition/database.tmdl` e em `definition/model.tmdl`; as duas primeiras permanecem intocadas e a linha de `model.tmdl` foi mantida fora do commit, separada das alterações semânticas.

### Validações funcionais concluídas

O usuário atualizou as consultas, confirmou a opção Data/hora automática desligada no arquivo, salvou, fechou e reabriu o PBIP sem erro. Consultas DAX de diagnóstico foram executadas no mecanismo semântico local:

| Tabela | Linhas | Chaves distintas |
|---|---:|---:|
| `FatoPedidos` (`sales_order_id`) | 120.000 | 120.000 |
| `FatoItensPedido` (`sales_order_item_id`) | 241.637 | 241.637 |
| `DimProduto` (`product_id`) | 1.000 | 1.000 |
| `DimCliente` (`customer_id`) | 45.000 | 45.000 |
| `DimLoja` (`store_id`) | 10 | 10 |
| `DimCanal` (`sales_channel_id`) | 4 | 4 |
| `DimCalendario` (`Data`) | 1.369 | 1.369 |

O calendário vai de 2023-01-01 a 2026-09-30, inclusive. `FatoPedidos[order_date]` cobre 2023-01-02 a 2026-09-29; não há pedido na borda de 2023-01-01 nem em 2026-09-30. Os itens não têm data nem produto em branco. A expressão de origem usa a conversão explícita de timezone PostgreSQL descrita acima.

As distribuições reconciliam com [`portfolio-validation.md`](../data-generation/portfolio-validation.md):

| Agrupamento | Resultado no modelo |
|---|---|
| Status | 116.305 `completed`; 3.265 `cancelled`; 430 `confirmed` |
| Pedidos por ano | 2023: 24.000; 2024: 30.000; 2025: 36.000; 2026: 30.000 |
| Itens por ano | 2023: 48.496; 2024: 60.676; 2025: 71.965; 2026: 60.500 |
| Pedidos por tipo de canal | `physical`: 62.580; `ecommerce`: 35.400; `marketplace`: 22.020 |
| Itens por tipo de canal | `physical`: 120.914; `ecommerce`: 74.283; `marketplace`: 46.440 |

Os valores de cabeçalho por status são R$ 950.106.484,19 (`completed`), R$ 26.036.085,71 (`cancelled`) e R$ 3.868.087,85 (`confirmed`); a soma não filtrada de `FatoPedidos[total_amount]` é R$ 980.010.657,75. Esses valores são totais brutos do cabeçalho por todos os status, não uma medida de receita realizada nem de margem.

Os pedidos sem cliente totalizam 19.829 (38.585 itens) e os sem loja 57.420 (120.723 itens). O agrupamento pelo membro em branco de cada dimensão preserva essas contagens; a soma dos grupos por cliente ou loja volta a 120.000 pedidos e R$ 980.010.657,75.

Agrupar os itens por `DimProduto[category_name]` retorna 241.637 itens. Em cada grupo, `FatoPedidos` continua em 120.000 pedidos e R$ 980.010.657,75; portanto, produto/categoria filtra a fato de itens e não multiplica nem filtra a fato de cabeçalho. Ano e canal filtram as duas fatos pelos relacionamentos conformados.

Após salvar/reabrir, `model.tmdl` mantém `__PBI_TimeIntelligenceEnabled = 0` e não há arquivos `LocalDateTable_*` ou `DateTableTemplate_*` na definição ativa.

**Resultado funcional:** contagens, chaves, grãos, datas, filtros, nulidade aprovada, atualização e reabertura passaram. Não foram identificadas divergências com os contratos de volume, status, ano e canal do Portfolio.

## Alterações Git preexistentes

Foram preservadas fora do escopo quatro alterações anteriores: `powerbi/ProjetoBI.Report/definition/report.json`, `powerbi/ProjetoBI.SemanticModel/definition/cultures/pt-BR.tmdl`, `powerbi/ProjetoBI.SemanticModel/definition/database.tmdl` e a linha em branco final previamente existente em `definition/model.tmdl`. O script TMDL salvo em `ProjetoBI.SemanticModel/TMDLScripts/` também não faz parte da mudança desta fase e não deve ser incluído por acidente.

## Próximos passos autorizados

Revisar o diff, preservar os arquivos preexistentes fora do commit e criar somente o commit local desta fase. Não avançar para medidas, pagamentos, fulfillment, estoque ou dashboards sem nova fase autorizada.
