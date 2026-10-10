# Relatório de validação do gerador — Fases 3B a 3D

## Ambiente

- Sistema: Windows; Python **3.13.15**.
- Banco aprovado: `projeto_bi`, servidor PostgreSQL **18.6**.
- Dependências observadas no ambiente isolado: Faker **39.1.0**, psycopg **3.3.6** (incluindo `psycopg-binary`), pytest **8.4.2**.
- A instalação e o ambiente `.venv/` são locais e ignorados pelo Git. Nenhum valor de credencial foi incluído neste relatório.

## Perfil smoke

Seed raiz: `20261005`; profile: `smoke`; janela comercial: 2023-01-01 a 2026-09-30; bootstrap configurado: 2022-11-01 a 2022-12-31; fuso: `America/Sao_Paulo`.

| Tabela mestre | Linhas geradas |
|---|---:|
| `core.stores` | 2 |
| `core.employees` | 12 |
| `core.employee_roles` | 5 |
| `core.employee_assignments` | 16 |
| `crm.customers` | 20 |
| `crm.individual_profiles` | 18 |
| `crm.business_profiles` | 2 |
| `crm.customer_contacts` | 24 |
| `crm.customer_addresses` | 24 |
| `catalog.categories` | 15 |
| `catalog.brands` | 12 |
| `catalog.products` | 30 |
| `catalog.product_suppliers` | 36 |
| `catalog.product_prices` | 120 |
| `inventory.stock_locations` | 4 |
| `payments.payment_methods` | 4 |
| `logistics.carriers` | 3 |
| `sales.sales_channels` | 4 |
| `procurement.suppliers` | 8 |

`--dry-run` concluiu sem conectar ao banco e retornou `database_connected=false`. Os testes verificam reprodutibilidade com seed constante, isolamento entre RNGs de domínio, CPF/CNPJ, estrutura das especificações, tipos monetários e rejeição de entradas inconsistentes (ciclo de categoria, perfil incompatível, JSON raiz inválida, CPF/CNPJ inválido, fornecedor preferencial duplicado, preço sobreposto, atribuição anterior à admissão e UF/cidade inválida).

## Testes e integração PostgreSQL

Com `PROJECTBI_RUN_INTEGRATION=1`, a suíte completa terminou com **31 passed**.

O smoke real conectou à database aprovada no PostgreSQL 18.6, validou estrutura e zero linhas preexistentes, inseriu as contagens acima em uma transação, recebeu IDs técnicos para as 19 tabelas lógicas, executou validações SQL e fez `ROLLBACK` explícito. Uma conexão nova confirmou **zero linhas em todas as 40 tabelas**. A consulta não criou database, alterou schema nem executou migrations. Nenhum dado sintético permaneceu persistido.

Os perfis `portfolio` e `large` foram carregados apenas para validar sua configuração de dez lojas e pares cidade/UF; não foram gerados nem conectados ao banco.

## Resultado

**Fase 3B validada.** Fundação determinística e geração de dados mestres smoke concluídas. O banco segue sem dados de negócio persistidos.

## Fase 3C — núcleo transacional

Profile `smoke`, seed `20261005`, PostgreSQL **18.6**. A geração determinística validou compras, recebimentos, vendas, descontos, reservas, fulfillment, movimentos e posições de estoque. As 13 tabelas transacionais foram carregadas apenas dentro de uma transação de teste.

| Resultado | Valor |
|---|---:|
| Ordens de compra / itens | 49 / 49 |
| Recebimentos / itens | 50 / 50 |
| Pedidos de venda / itens | 300 / 630 |
| Descontos aplicados | 251 |
| Reservas de estoque | 233 |
| Fulfillments / itens | 193 / 227 |
| Movimentos / posições finais | 277 / 35 |
| Unidades aceitas / expedidas / saldo final | 457 / 238 / 219 |
| Reservado ao final | 0 |
| Custo realizado calculado pelo ledger | BRL 369830.61051434 |
| Pedidos cancelados / com fulfillment dividido | 8 / 23 |

Os pedidos cobriram os quatro canais: físico 161, e-commerce 75, marketplace A 34 e marketplace B 30. Houve 47 pedidos físicos anônimos. Recebimentos parciais e itens rejeitados foram exercitados; o cutoff ficou dentro da janela configurada.

`transactions --profile smoke --dry-run` concluiu com `database_connected=false`. A suíte local terminou com **46 passed, 2 skipped** antes de habilitar os testes de integração. A integração PostgreSQL completa foi executada diretamente: validou 19 mapas de IDs mestres, 9 mapas transacionais e todas as 13 tabelas da fase, incluindo replay do ledger, média móvel e custo realizado. Uma nova conexão confirmou **zero linhas em todas as 40 tabelas**, total de zero dados de negócio persistidos. O teste de integração da Fase 3C também foi adicionado à suíte para execuções futuras com `PROJECTBI_RUN_INTEGRATION=1`.

Não foram executados pagamentos, parcelas, reembolsos, eventos de fulfillment, transferências, devoluções, perfis `portfolio`/`large` ou Power BI. Nenhuma migration foi aplicada e nenhuma linha sintética ficou no banco.

**Fase 3C validada.** A ampliação do ecossistema foi executada e validada na seção seguinte.

## Fase 3D — ecossistema transacional completo

Profile `smoke`, seed `20261005`, PostgreSQL **18.6**. O fluxo foi ampliado com pagamentos, parcelas, eventos de entrega e retirada, transferências de estoque, devoluções e refunds. Os registros base da Fase 3C (pedidos, itens, descontos, reservas, fulfillments e custo realizado) permaneceram iguais após a extensão.

| Resultado | Valor |
|---|---:|
| Pedidos / itens | 300 / 630 |
| Operações de pagamento / tentativas recusadas ou falhas / retries | 314 / 11 / 11 |
| Pedidos com split payment / parcelas | 3 / 587 |
| Fulfillments / itens / eventos | 193 / 227 / 590 |
| Eventos de entrega / retirada | 454 / 331 |
| Transferências / itens / movimentos de saída e entrada | 2 / 2 / 2 + 2 |
| Devoluções / itens / recebimentos vendáveis / não vendáveis | 8 / 8 / 3 / 4 |
| Refunds concluídos | 6 |
| Movimentos de estoque / posições finais / saldo final | 284 / 35 / 222 |
| Unidades aceitas / expedidas / retornadas ao estoque vendável | 457 / 238 / 3 |
| Custo realizado | BRL 369830.61051434 |
| Capturado / refunds / valor líquido | BRL 2791128.94 / 18420.97 / 2772707.97 |

As validações em memória conferiram conciliação integral das capturas por pedido, retries, parcelamento, sequências e cutoff de eventos, pares de transferência com custo igual, origem física das devoluções, custo histórico de retorno, destino de estoque e limite de refunds. O dry-run `full --profile smoke --dry-run` terminou com `database_connected=false`.

A integração `full --profile smoke --load-smoke` conectou ao PostgreSQL 18.6, encontrou a estrutura aprovada vazia, inseriu e validou 19 conjuntos de IDs mestres e 16 conjuntos transacionais em uma transação, validou as 21 tabelas transacionais e executou `ROLLBACK`. Uma nova conexão confirmou zero linhas em cada uma das 40 tabelas. O teste de integração completo da Fase 3D também passou. Não houve migration, persistência de dados ou alteração estrutural.

A suíte total com integrações habilitadas terminou com **56 passed**. Isso inclui os testes de unidade e os três testes PostgreSQL de rollback (dados mestres, Fase 3C e Fase 3D). O comando CLI `full --profile smoke --load-smoke` reportou zero linhas restantes.

**Fase 3D validada.** A evolução da geração maior está em andamento na Fase 3E.1.

## Fase 3E.1 — auditoria/refatoração de escala (não concluída)

### Profiles e regressão

- Profiles declaram alvos de pedidos (smoke 300, portfolio 120.000, large 240.000), estimativa de itens/linhas e batch size. Os dados mestres portfolio e large foram gerados e validados sem conexão ao banco.
- `full --profile portfolio --plan`: 219.009 linhas mestres, 120.000 pedidos, 264.000 itens estimados e 2.200.000 linhas transacionais estimadas. `full --profile large --plan`: 430.505 linhas mestres, 240.000 pedidos, 528.000 itens e 4.400.000 linhas transacionais estimadas. Ambos indicam `generated=false`, `database_connected=false` e `persistent_write=false`.
- A suíte completa com PostgreSQL terminou com **63 passed** (11,62 s), incluindo os três testes de rollback smoke. `full --profile smoke --dry-run` preservou os principais resultados da Fase 3D: 300 pedidos, 630 itens, captured BRL 2.791.128,94, refunds BRL 18.420,97 e custo realizado BRL 369.830,61051434.
- Uma consulta somente leitura em nova conexão confirmou `projeto_bi`, PostgreSQL major 18, 40 tabelas e zero linhas após os rollbacks.

### Benchmark e blocker de arquitetura

Profile base portfolio com override interno de 5.000 pedidos (não é um quarto profile). A geração e os validadores 3C/3D passaram sem conectar ao banco: 10.500 itens e 53.800 registros transacionais materializados, 43,9 s com `tracemalloc` (113,9 pedidos/s) e pico de 95,1 MiB. `tracemalloc` afeta o tempo; essa medição documenta o uso observado, não uma extrapolação exata.

**Fase 3E.1 permanecia aberta nesse estado anterior à subfase 3E.1a.** A engine ainda materializava o histórico completo no caminho legado; não havia consumidor streaming entre event loop e sink. Escritas com `RETURNING` eram individuais e mapas de IDs transacionais cresciam com o dataset. O resultado incremental posterior está descrito na seção 3E.1a. Não foi executado o portfolio completo nem carga persistente. Detalhes em `scalability-review.md`.

### Continuação do contrato de sink

Foi adicionada a base `TransactionSink`/`TransactionBatchEmitter`, um coletor para smoke, um sink contador/descarte com digest SHA-256 lógico por tabela e métricas de buffers/eventos. A suíte atual passou com **63 passed, 3 skipped**; os skips foram os três testes PostgreSQL, que não foram executados porque ainda usam o caminho legado e não validariam o sink novo. Os testes dedicados ao contrato e à fila passaram (20 testes). Os planos foram repetidos sem conexão: portfolio reportou 219.009 linhas mestre, 120.000 pedidos, 264.000 itens e 2.200.000 linhas transacionais estimadas; large reportou 430.505 linhas mestre, 240.000 pedidos, 528.000 itens e 4.400.000 linhas estimadas.

Antes da subfase 3E.1a, o agendamento diário das intenções nos profiles maiores foi exercitado junto ao benchmark, mas o sink ainda não estava integrado ao loop causal. Os benchmarks 1k/5k/10k passaram pela geração e validação no caminho marcado `legacy_materialize_then_validate`: respectivamente 15.644/53.511/101.985 linhas, picos de 77,9/95,1/119,8 MiB e máximos da fila 3D de 2.209/10.873/21.903 eventos. A master reteve 66,1 MiB em cada medição; entre 1k e 10k, o pico total aumentou 41,9 MiB e a agenda 3D quase 10x. O máximo 3C ficou em 1.007 eventos para os três tamanhos por causa do bootstrap mestre e das intenções diárias. O novo resultado incremental, que não substitui esse baseline legado, consta na seção 3E.1a abaixo.

Nenhuma integração multibatch com `ROLLBACK` foi executada, pois não há ainda um PostgreSQL sink novo para testar. Nenhum dado foi escrito no PostgreSQL nesta continuação. O gate segue aberto e não há commit.

## Fase 3E.1a — streaming incremental do núcleo 3C

O modo novo usa o event loop causal já existente com saída incremental para `TransactionSink`; os registros 3C não são agregados em `TransactionData`. O sink `CountingDiscardingSink` conta e calcula digest lógico por tabela, descartando cada lote. O modo legado permanece para o fluxo smoke 3D. O teste de equivalência comparou as coleções 3C e posições finais linha a linha com o caminho legado: 300 pedidos/630 itens; 49 compras; 50 recebimentos; 193 fulfillments/227 itens; 457 unidades recebidas; 238 expedidas; estoque final 219; custo realizado BRL 369830.61051434; 8 pedidos cancelados e 23 com fulfillment dividido. Os digests incrementais e contagens permaneceram iguais com batch sizes distintos.

O benchmark compartilhou a master portfolio validada (219.009 linhas; baseline 65,9 MiB) e executou somente o núcleo incremental 3C, sem conexão ao banco. O batch size configurado foi 5.000; os limites menores observados decorrem do flush diário. Métricas de memória e estado ativo:

| Pedidos | Linhas emitidas | Máx. buffer | Flushes | Pedidos ativos (pico) | Eventos 3C pendentes (pico) | Pico total | Transação acima da master | Duração transacional | Digest lógico |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| 1.000 | 16.245 | 1.013 | 1.100 | 2 | 1.007 | 71,8 MiB | 5,9 MiB | 11,01 s | `7ce7c6b5249bc27019e5a1295b552f6a063f41b4f4efd29811f471e717440f20` |
| 5.000 | 52.773 | 1.033 | 1.388 | 5 | 1.007 | 71,8 MiB | 5,9 MiB | 35,55 s | `f35152acc742d9b00584f831400bdf9c17289acf53e0b91c2c4554e9c050c773` |
| 10.000 | 99.486 | 1.022 | 1.388 | 7 | 1.007 | 71,8 MiB | 5,9 MiB | 62,87 s | `425e141fe7c61f78b61be444ccbcbf217bfabd1cfee3cf3dd772cfac678647f7` |

Nas três execuções não restaram pedidos ativos nem eventos futuros 3C. O máximo de compras ativas foi 240, associado ao bootstrap de compras, e o máximo da fila foi 1.007, associado ao bootstrap/intenção diária. A master foi gerada/validada uma vez (144,98 s) e compartilhada. `tracemalloc` estava ativo durante as medições. Nenhuma integração PostgreSQL foi iniciada nesta subfase.

**Limite do resultado:** este benchmark demonstra emissão incremental e pico de memória estável para o caminho de geração 3C em 1k/5k/10k. Não demonstra integração do repository em batches, lifecycle de IDs PostgreSQL, validação multibatch, nem streaming dos registros de pagamento/logística/devolução da Fase 3D. Portanto, **Fase 3E.1 continua aberta** e não houve commit.

## Fase 3E.1b — incremental completion

### Equivalência full smoke

O caminho `generate_full_transactions_incremental` executou 3C+3D na mesma fila cronológica e pelo mesmo `TransactionBatchEmitter`. Com `CollectingSink`, os validadores transacionais e 3D completos foram executados. Cada linha das 21 tabelas foi comparada com o resultado de referência legado (ignorando ordenação de emissão), e o digest canônico ordenado também coincidiu: `36640f5474a02c02168cb50f983327b2c9f181bd5d8cdaca50ab5513bf23874a`.

Para preservar as regras globais já aprovadas no smoke (menor pagamento de cartão e o piso de devoluções), o runner smoke realiza uma execução incremental de política com sink contador/descarte. Essa execução conserva apenas o índice do pedido vencedor e até o número configurado de candidatos mínimos; não materializa tabelas. A execução full de saída então recria 3C+3D causalmente em uma única fila. Profiles portfolio/large e benchmarks não usam essa prévia; suas decisões usam o fluxo incremental diretamente.

| Resultado | Incremental full smoke |
|---|---:|
| Pedidos / itens | 300 / 630 |
| Pagamentos / falhas ou recusas / retries / pedidos split | 314 / 11 / 11 / 3 |
| Parcelas | 587 |
| Fulfillments / itens / eventos | 193 / 227 / 590 |
| Eventos delivery / pickup | 454 / 331 |
| Transferências / itens / movimentos out e in | 2 / 2 / 2 + 2 |
| Devoluções / itens / recebidas vendáveis / não vendáveis | 8 / 8 / 3 / 4 |
| Refunds concluídos | 6 |
| Movimentos / posições finais | 284 / 35 |
| Unidades recebidas / expedidas / retornadas vendáveis | 457 / 238 / 3 |
| Estoque final | 222 |
| Custo realizado | BRL 369830.61051434 |
| Capturado / refunds / líquido | BRL 2791128.94 / 18420.97 / 2772707.97 |

A extensão 3D não chama `extend_transactions` nem `_replay_extended_stock` nesse caminho. Pagamentos, installments, fulfillment events, transfers, returns e refunds foram enviados ao sink comum. Retorno vendável atualizou a média móvel no instante e um teste confirmou fulfillment posterior no mesmo produto/local usando o custo então vigente. As validações de timeline, quantidade, custo, referências e reconciliação passaram.

### Benchmark full incremental

Master portfolio compartilhada: 219.009 linhas, baseline aproximado de 65,9 MiB. Master e validação: 74,32 s sob `tracemalloc`. Overrides internos somente para benchmark; sem conexão, escrita ou `TransactionData`.

| Pedidos | Linhas | Pico | Delta sobre master | Max buffer | Flushes | Eventos futuros pico | Pedidos / pagamentos / fulfillments ativos pico | Transferências ativas pico | Return eligibility pico | Duração | Digest lógico |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| 1.000 | 20.497 | 73,8 MiB | 7,9 MiB | 1.006 | 1.108 | 1.007 | 2 / 4 / 3 | 4 | 2 | 10,83 s | `e19641ab54f0be54744cd71a56ddd15476701c7f2bef92f204b4241f77d8b44a` |
| 5.000 | 73.631 | 74,3 MiB | 8,2 MiB | 1.021 | 1.389 | 1.007 | 5 / 8 / 6 | 4 | 4 | 35,16 s | `7bd1199247b275e2a044d82332152245e99275db83feebb38145c202e30ed8b9` |
| 10.000 | 141.640 | 75,1 MiB | 9,0 MiB | 1.055 | 1.388 | 1.007 | 7 / 13 / 8 | 4 | 7 | 61,99 s | `bf3133b679f2c7705e1e4ac914b75b83fdad139d8fc5ada53bb330594b47dfd5` |

Ao final de cada execução, pedidos, pagamentos, transferências e elegibilidades ativas estavam em zero. A fila futura permaneceu em 1.007 para 1k/5k/10k; a referência materializada antiga era 2.209/10.873/21.903. O buffer fica limitado pelo threshold/flush diário; crescimento de linhas não resultou em retenção proporcional do histórico. `CountingDiscardingSink` manteve contagens e digest, descartando as linhas por lote.

Eventos agendados/processados: 4.622/4.622, 14.819/14.819 e 28.099/28.099 para 1k/5k/10k. A suíte local terminou com **69 passed, 3 skipped**; os skips são os testes PostgreSQL, que ficaram fora do escopo desta subfase.

### Resultado e limites

**Fase 3E.1b concluída para geração causal incremental 3C+3D. Fase 3E.1 permanece aberta.** Restam para 3E.1c: PostgreSQLTransactionSink, `INSERT/RETURNING` em batches, lifecycle de IDs técnicos e integração multibatch com `ROLLBACK`. Nenhum teste PostgreSQL foi executado como evidência desta subfase; nenhuma carga foi persistida e Power BI não foi iniciado.

## Fase 3E.1c — PostgreSQL incremental sink

### Integração PostgreSQL smoke

Target guard passou: `projeto_bi`, PostgreSQL **18.6**, 9 schemas, 40 tabelas aprovadas, migration 002 vigente e zero linhas antes da carga. O runner usou uma transação para carregar master e o fluxo full incremental pelo novo sink, validar e fazer `ROLLBACK`. Nova conexão confirmou zero linhas nas 40 tabelas.

| Medida | Resultado dentro da transação |
|---|---:|
| Pedidos / itens | 300 / 630 |
| Pagamentos / parcelas | 314 / 587 |
| Fulfillments / itens / eventos | 193 / 227 / 590 |
| Transferências / itens | 2 / 2 |
| Returns / itens / refunds concluídos | 8 / 8 / 6 |
| Stock movements / positions | 284 / 35 |
| Linhas relacionais inseridas | 4.837 |
| Updates de estado | 923 |
| Emissões recebidas / flushes / batch máximo | 5.725 / 484 / 36 |
| `max_transaction_id_entries` / final | 28 / 0 |
| Rollback / contagem em nova conexão | executado / 0 nas 40 tabelas |

As invariantes SQL cobriram conciliação de pedidos/pagamentos/refunds/parcelas, descontos, cutoff, ledger e posições, custo médio, reservas, limites de fulfillment, pares/custos de transferência e origem/quantidade/destino de returns. O custo realizado calculado no SQL foi BRL 369830.61051434.

O digest canônico `36640f5474a02c02168cb50f983327b2c9f181bd5d8cdaca50ab5513bf23874a` foi confirmado pela regressão full incremental contra o oracle legado em memória. O smoke PostgreSQL confirmou contagens e invariantes via SQL; o digest não foi calculado por serialização das linhas relacionais lidas de volta.

### Integração multibatch rollback

Foi usada a master portfolio completa com 219.009 linhas e override interno para 1.000 pedidos. O override não criou um quarto profile; não houve commit nem carga persistente.

| Medida | Resultado |
|---|---:|
| Pedidos | 1.000 |
| Linhas transacionais inseridas | 18.720 |
| Updates | 4.827 |
| Flushes / batch máximo | 1.128 / 1.006 |
| IDs transacionais máximo / final | 626 / 0 |
| Picos por tipo | PO 241; PO item 241; receipt 72; receipt item 72; order 4; order item 13; payment 4; fulfillment 7; fulfillment item 9; return/item 2; transfer/item 4 |
| Duração | 64,33 s |
| Rollback / nova conexão | executado / 0 linhas em 40 tabelas |

Também passou teste sem conexão com 5.000 lifecycles de pedido; o registry reteve até 82 IDs para 41 pedidos ativos e terminou em zero. Uma colisão de nomes de marca na master portfolio foi corrigida com sufixo determinístico somente quando necessário e a validação mestre agora confere a unicidade prevista por `uq_brands_name`.

### Regressões, planos e suíte

`full smoke --dry-run`: 300 pedidos/630 itens; captured BRL 2791128.94; refunds BRL 18420.97; líquido BRL 2772707.97; custo BRL 369830.61051434. Os mesmos agregados foram validados no smoke PostgreSQL.

`portfolio --plan`: 219.009 linhas master, 120.000 pedidos, 264.000 itens estimados, 2.200.000 linhas transacionais estimadas. `large --plan`: 430.505 master, 240.000 pedidos, 528.000 itens, 4.400.000 transações. Ambos passaram com `generated=false`, `database_connected=false`, `persistent_write=false`.

Suíte com `PROJECTBI_RUN_INTEGRATION=1`: **75 passed, 0 skipped** (71,70 s), incluindo as quatro integrações PostgreSQL. Suíte normal: **71 passed, 4 skipped** (10,92 s); os skips são exatamente os quatro testes PostgreSQL desabilitados na execução normal.

### Resultado

Nenhuma migration ou estrutura PostgreSQL foi alterada. Nenhuma linha de negócio permaneceu persistida; portfolio integral, large, baselines SQL finais e Power BI não foram executados. Smoke e multibatch passaram com `ROLLBACK` e zero linhas nas 40 tabelas em conexão nova. A Fase 3E.1 está concluída; a Fase 3E.2 permanece não iniciada.

## Fase 3E.2a — diagnóstico e correção do custo médio

### Primeira tentativa Portfolio interrompida

A tentativa de carga Portfolio de 120.000 pedidos percorreu os períodos configurados, mas falhou antes do `COMMIT` ao validar custo médio móvel. A conexão foi revertida; conexão nova confirmou zero linhas nas 40 tabelas. Nenhum baseline ou relatório final Portfolio foi criado e nenhum commit foi feito.

### Primeira divergência

Fixture determinístico com a seed aprovada e 10.000 pedidos reproduziu a divergência. A primeira diferença cronológica entre a média da engine e o replay legado apareceu no recebimento `GR-SM-1075`, linha 1:

| Campo | Valor |
|---|---:|
| Product ID / SKU | 19964 / `SKU-NET-00742` |
| Stock location ID / código | 547 / `LOC-SM-EXPEDITION` |
| Movement ID (fixture diagnóstico) | 67511 |
| Tipo / timestamp | `receipt` / 2025-08-03 10:33:00 -03:00 |
| Quantidade / custo de entrada | +6 / BRL 517.17371970 |
| Quantidade anterior / média anterior | 2 / BRL 565.20651660 |
| Média exata antes de quantizar | BRL 529.181918925 |
| Engine / PostgreSQL NUMERIC | BRL 529.18191893 (`ROUND_HALF_UP`) |
| Replay anterior | BRL 529.18191892 (`ROUND_HALF_EVEN`) |
| Diferença | BRL 0.00000001 |

Janela cronológica da mesma combinação produto/local; custos e médias antes/depois são BRL por unidade:

| Movement ID | Referência | Tipo / data | Δ qtd. | Custo | Qtd. antes→depois | Média HALF_UP antes→depois | Média HALF_EVEN antes→depois |
|---:|---|---|---:|---:|---:|---:|---:|
| 65866 | `FUL-SM-00976`, linha 4 | fulfillment / 2024-01-10 09:13 | -1 | 565.20651660 | 8→7 | 565.20651660→565.20651660 | 565.20651660→565.20651660 |
| 65879 | `FUL-SM-00990`, linha 3 | fulfillment / 2024-01-14 03:09 | -1 | 565.20651660 | 7→6 | 565.20651660→565.20651660 | 565.20651660→565.20651660 |
| 66535 | `FUL-SM-01579`, linha 2 | fulfillment / 2024-09-08 20:25 | -1 | 565.20651660 | 6→5 | 565.20651660→565.20651660 | 565.20651660→565.20651660 |
| 67080 | `FUL-SM-02062`, linha 4 | fulfillment / 2025-03-12 19:03 | -1 | 565.20651660 | 5→4 | 565.20651660→565.20651660 | 565.20651660→565.20651660 |
| 67491 | `FUL-SM-02419`, linha 2 | fulfillment / 2025-07-28 04:31 | -2 | 565.20651660 | 4→2 | 565.20651660→565.20651660 | 565.20651660→565.20651660 |
| 67511 | `GR-SM-1075`, linha 1 | receipt / 2025-08-03 10:33 | +6 | 517.17371970 | 2→8 | 565.20651660→529.18191893 | 565.20651660→529.18191892 |

Não houve movimento posterior desse SKU/local dentro do fixture de 10.000 pedidos. O ledger registra referências estrangeiras e chaves de domínio, mas não persiste a chave lógica interna do gerador. O replay usa `ORDER BY occurred_at, stock_movement_id`: o sink insere cada movimento ao consumir o respectivo evento de estado, preservando a ordem causal emitida pela engine; a engine desempata por instante, prioridade e chave lógica. Teste direcionado confirmou receipt→fulfillment, customer_return→fulfillment e transfer_in→fulfillment quando os timestamps coincidem.

### Causa e correção

Classificação: **ROUNDING / VALIDATOR**, com o mesmo arredondamento implícito também presente no cálculo transitório do sink. A engine usa `weighted_moving_average`, quantizada explicitamente para oito casas com `ROUND_HALF_UP`, compatível com o arredondamento de `NUMERIC(20,8)` do PostgreSQL. O replay chamava `Decimal.quantize()` sem especificar a regra, herdando `ROUND_HALF_EVEN`; o sink duplicava a fórmula e herdava a mesma regra. No fixture, o valor exato cai em empate na nona casa decimal. O estado final registrado correspondia ao cálculo da engine; o replay era quem se separava primeiro.

A validação e o sink agora reutilizam `weighted_moving_average`, mantendo comparação exata em `Decimal`/`NUMERIC(20,8)`. A validação reporta a primeira saída divergente com produto/SKU, local, referência de origem, instante, quantidades, médias e janela do ledger; a tolerância não foi alterada. Nenhuma engine de negócio, distribuição, schema ou migration foi modificada.

### Evidências após a correção

- Testes direcionados de estoque/custos, transferências, devoluções e replay com timestamps iguais: **32 passed**.
- `full --profile smoke --dry-run`: 300 pedidos, 630 itens; captured BRL 2791128.94; refunds BRL 18420.97; líquido BRL 2772707.97; custo BRL 369830.61051434. A regressão de digest permaneceu coberta pelo teste: `36640f5474a02c02168cb50f983327b2c9f181bd5d8cdaca50ab5513bf23874a`.
- Integração `full smoke` PostgreSQL: **PASS**, com `ROLLBACK`.
- Escalas 1.000 e 5.000 antes da correção: validação SQL passou e rollback confirmou zero linhas.
- Escala 1.000 após a correção: passou na suíte PostgreSQL de integração.
- Escala 10.000 após a correção: validação SQL passou; o replay HALF_UP conciliou posição e ledger. Execução diagnóstica comparou paralelamente HALF_UP/HALF_EVEN para preservar a evidência da primeira divergência; `ROLLBACK` e conexão nova confirmaram zero linhas nas 40 tabelas.
- Suíte normal: **78 passed, 4 skipped**. Suíte com `PROJECTBI_RUN_INTEGRATION=1`: **82 passed, 0 skipped**.

**Fase 3E.2a concluída quanto ao diagnóstico e à correção em escalas intermediárias. Fase 3E.2 permanece aberta; nenhum Portfolio completo foi reexecutado, nenhum dado foi confirmado, nenhum baseline final foi criado e nenhum commit foi feito.** A retomada da carga completa depende de solicitação separada.

## Fase 3E.2b — diagnóstico de validações pré-COMMIT

### Ocorrência anterior e segurança

A tentativa anterior do profile Portfolio com 120.000 pedidos ficou mais de duas horas numa única instrução SQL de validação transacional, contendo 15 subconsultas escalares. O backend foi cancelado manualmente; o PostgreSQL retornou SQLSTATE `57014` (`QueryCanceled`). O tratamento da conexão executou rollback e a conexão nova confirmou as 40 tabelas operacionais vazias. Nenhum dado foi confirmado, nenhum baseline foi criado e nenhum commit foi feito.

O fixture determinístico de 10.000 pedidos foi reproduzido exclusivamente numa transação diagnóstica. Em uma repetição, todas as validações transacionais nomeadas concluíram, mas `EXPLAIN (ANALYZE, BUFFERS)` do bundle original excedeu o timeout local de 120 segundos e foi cancelado (`57014`). O fluxo encerrou a transação com rollback; a conexão nova confirmou zero linhas em 40 tabelas. Não foram tentadas as escalas 25.000, 50.000 ou 120.000.

### Instrumentação e tempos observados

As subconsultas transacionais e as verificações críticas Portfolio agora são executadas individualmente com identificadores estáveis, início, duração, resultado e linhas retornadas. As consultas recebem limite local de 120 segundos; não foi alterado timeout global. As condições lógicas foram preservadas. Não houve mudança em migration, índices permanentes ou regras de negócio. `PROJECTBI_EXPLAIN_VALIDATION` e `PROJECTBI_EXPLAIN_ANALYZE_VALIDATION` permitem selecionar uma validação nomeada para plano e buffers.

Na execução de 10.000 pedidos em que o bundle antigo foi cancelado, algumas verificações individuais tiveram tempos elevados e passaram: validade de preço 71,52 s; leitura ordenada de 4.858 movimentos do ledger 49,28 s; sobreposição de preços mestre 39,18 s; elegibilidade de parcelamento 32,97 s; teto de descontos 31,04 s; reconciliação de parcelas 30,83 s; captura contra pedido 18,77 s; limite de fulfillment 16,31 s; e conciliação de produto das reservas 13,67 s. Os tempos variaram muito entre execuções do mesmo fixture: em outra repetição várias validações equivalentes terminaram em milissegundos. Portanto, o bundle foi isolado como a instrução sem limite que expôs o tempo agregado de várias verificações, mas **o plano agregado não completou e não foi possível atribuir as mais de duas horas a uma única subconsulta**. Não há evidência suficiente para adicionar índice permanente ou alterar uma regra.

O plano individual de `catalog.price_validity`, capturado no fixture de 10.000 pedidos, concluiu em 26,057 ms (planning 0,347 ms), com 1.028 buffers `shared hit`; utilizou varreduras sequenciais em 21.000 itens e 14.000 preços. A consulta normal concluiu em 0,03 s nesse ciclo, apesar de ter levado 71,52 s no ciclo anterior. Isso confirma a variabilidade observada e não justifica uma otimização estrutural isolada dessa consulta.

### Divergência lógica separada

A validação crítica `portfolio.sales_status_history_chronology` falhou no fixture de 10.000: 10.000 eventos anteriores à colocação, todos `draft`; zero outros status. Por exemplo, `SO-SM-0001` tem `draft` às 08:55 e `placed_at` às 09:00. O gerador cria explicitamente o rascunho cinco minutos antes e o status `placed` no instante de colocação. Isso é uma divergência determinística entre o fixture aprovado e a condição atual que proíbe qualquer histórico anterior a `placed_at`, não a causa do timeout do bundle transacional. A regra foi preservada; não se alterou a semântica nem se converteu falha em aviso. A validação Portfolio completa e o gate de commit continuam bloqueados até essa condição ser resolvida pela autoridade apropriada.

### Controle negativo e estado do banco

No fixture temporário, foi aumentado em uma unidade o saldo de uma posição, sem movimento correspondente. `inventory.stock_ledger_balance` retornou uma violação; o log registrou `FAIL`, `violations=1`, demonstrando que a verificação separada ainda detecta o caso inválido. A asserção do script diagnóstico esperava uma exceção, enquanto o helper reporta `FAIL` e retorna a contagem para o chamador agregar; o script de orquestração terminou com essa asserção inadequada, mas executou rollback no `finally`. Uma nova conexão confirmou zero linhas em todas as 40 tabelas. Nenhuma fixture foi persistida.

### Resultado e próximos limites

`compileall` passou após a instrumentação. O conjunto de validações transacionais nomeadas passou em 10.000 pedidos numa repetição; a execução interrompida por timeout também deixou o banco vazio. A validação crítica do Portfolio reprovou pela condição de histórico `draft` descrita acima.

Na primeira suíte de integração desta retomada, `test_postgresql_transaction_smoke_rolls_back_every_table` expôs que a separação havia omitido a guarda original para não exigir conciliação financeira quando a carga smoke exclui o domínio de pagamentos. O split retornou 292 falsos positivos. A guarda `CASE WHEN EXISTS(payments)` foi restaurada sem alterar a validação quando há pagamentos. Após a correção, suíte normal: **78 passed, 4 skipped**; suíte com `PROJECTBI_RUN_INTEGRATION=1`: **82 passed, 0 skipped** (219,54 s). Os quatro testes PostgreSQL concluíram com rollback. A confirmação final em nova conexão está registrada abaixo.

A asserção do script diagnóstico do controle negativo esperava que o helper levantasse exceção, mas sua interface intencionalmente retorna a contagem e imprime o estado. O helper registrou `FAIL` com `violations=1` para a discrepância controlada; o `finally` executou rollback, e conexão nova confirmou zero linhas em 40 tabelas. O erro foi apenas na asserção/orquestração diagnóstica e não no resultado da validação.

Após a suíte de integração, uma conexão nova confirmou novamente zero linhas nas 40 tabelas operacionais.

**Fase 3E.2b permanece aberta.** O problema da instrução SQL agregada foi mitigado por divisão das verificações e timeout local, mas a causa histórica única não foi provada porque o `EXPLAIN ANALYZE` agregado expirou até no fixture de 10.000. A divergência de cronologia impede considerar o Portfolio validado. Nenhum commit, push, carga persistente, baseline final ou atividade Power BI foi executado.

## Continuação final da Fase 3E.2b — cronologia, planner e escala (2026-10-06)

Esta atualização substitui as conclusões provisórias acima sobre a divergência de cronologia e o bloqueio da validação Portfolio. A fase continua aberta; não houve commit, push, carga persistida, baseline final nem atividade Power BI.

### Cronologia e controle negativo

O contrato validado é `draft` estritamente antes de `placed_at`, um único `placed` exatamente em `placed_at`, e nenhum status diferente de `draft` antes desse marco. A ordem temporal do histórico deve ser não decrescente, as transições permitidas continuam `draft→placed`, `placed→confirmed/cancelled` e `confirmed→completed/cancelled`, e o status final deve corresponder ao último evento. O gerador e as regras de negócio não foram alterados.

Foram adicionados quatro testes explícitos: fluxo válido `draft T−5 min → placed T → confirmed → completed`; status não-draft anterior ao marco; `draft` posterior a `placed`; e regressão/ordem temporal inválida. A validação de escala passou a verificar também marcador `placed`, sequência persistida e transições. Em 10k/25k/50k, os eventos `draft` intencionais passaram e as verificações de cronologia, marcador, ordenação e transições retornaram zero violações.

O controle negativo do ledger retornou exatamente `violations=1` e o script agora compara a contagem retornada, sem esperar exception. O controle de cronologia com `confirmed` artificialmente anterior a `placed_at` também retornou `violations=1`. Ambos os cenários foram revertidos por savepoint antes do rollback total.

### Correção monetária encontrada em 25k

A primeira repetição de 25k revelou um caso de borda de meio centavo: o valor unitário elegível calculado era `960.355`, enquanto a geração aplica `ROUND_HALF_UP` para `960.36`. A validação de reembolso foi alinhada ao arredondamento da unidade monetária; o gerador permaneceu intacto. O caso foi coberto por teste e a escala 25k foi repetida integralmente com sucesso.

### Planner e protocolo de escala

Os logs de planejamento mostraram `pg_class.reltuples=0` antes de `ANALYZE` nas tabelas recém-carregadas. Após a operação, as estimativas de linhas passaram a coincidir com `COUNT(*)`. Exemplo em 25k: pedidos 25.000, itens 52.500, histórico 76.502, descontos 19.659, movimentos 8.587, posições 1.005, pagamentos 26.537, parcelas 51.233 e itens de fulfillment 7.115. Em 10k e 50k ocorreu o mesmo padrão. Portanto a hipótese de estatísticas inexistentes foi confirmada para o fixture dentro da transação.

`ANALYZE` nas 40 tabelas operacionais levou 1,52 s (10k), 1,97 s (25k) e 2,40 s (50k). Os planos mudaram de estimativas severamente subestimadas para contagens próximas ou exatas: por exemplo, `catalog.price_validity` estimava 10.335 itens contra 52.500 em 25k antes de `ANALYZE`, e passou a estimar 52.500 depois; `inventory.stock_movement_ledger_read` estimava 237 movimentos antes e 8.587 depois. Predominaram varreduras sequenciais e hash joins para os volumes carregados; verificações de faixa usaram também scans por índice/merge quando apropriado. Não houve mudança de schema, índice ou configuração global.

As validações foram executadas duas vezes na mesma fixture por escala. Todas as 98 validações nomeadas passaram nas duas rodadas após as correções; nenhum `statement_timeout` ocorreu. A duração aproximada somada da primeira rodada foi 0,56 s (10k), 1,21 s (25k) e 1,80 s (50k). O maior tempo individual foi 0,08 s, 0,13 s e 0,25 s, respectivamente. O diagnóstico seletivo `EXPLAIN ANALYZE` foi limitado às três verificações mais lentas em cada fixture, com `TIMING OFF` e coleta de buffers.

| Escala | Pedidos | ANALYZE (40 tabelas) | Tempo total do ensaio | Validações nomeadas | Maior validação | Resultado/rollback |
|---|---:|---:|---:|---:|---:|---|
| 10k | 10.000 | 1,52 s | 107,22 s | 98 × 2 rodadas | 0,08 s | PASS; 40 tabelas vazias |
| 25k | 25.000 | 1,97 s | 468,20 s | 98 × 2 rodadas | 0,13 s | PASS; 40 tabelas vazias |
| 50k | 50.000 | 2,40 s | 169,70 s | 98 × 2 rodadas | 0,25 s | PASS; 40 tabelas vazias |

O tempo total inclui geração e carga; variou de modo não monotônico entre as execuções (25k levou mais que 50k). Não se atribui essa diferença ao SQL de validação: o total dessas validações permaneceu abaixo de dois segundos por rodada em todas as escalas. Não apareceu fanout ou crescimento explosivo nas consultas observadas.

O monitor somente leitura registrou uma atividade por aproximadamente 5,9 s em 50k, com `state=active`, `wait_event_type=NULL`, `wait_event=NULL` e `blockers=[]`; não indicou espera por lock ou I/O. Nenhuma validação individual ultrapassou 0,25 s.

#### Duração de todas as validações nomeadas

Durações da primeira rodada, em segundos, ordenadas pela maior duração observada entre as escalas. As 98 validações constam abaixo; todas passaram nas três escalas e também na segunda rodada.

| Validação | 10k (s) | 25k (s) | 50k (s) |
|---|---:|---:|---:|
| portfolio.sales_status_history_placed_marker | 0.06 | 0.13 | 0.25 |
| catalog.price_validity | 0.02 | 0.04 | 0.17 |
| portfolio.order_item_discount_reconciliation | 0.03 | 0.10 | 0.12 |
| portfolio.commercial_event_cutoff | 0.08 | 0.11 | 0.11 |
| sales.latest_status_history | 0.02 | 0.05 | 0.11 |
| portfolio.sales_status_history_transitions | 0.02 | 0.07 | 0.10 |
| inventory.stock_movement_ledger_read | 0.03 | 0.08 | 0.07 |
| master.customer_profile_exclusivity | 0.07 | 0.08 | 0.08 |
| payments.capture_order_reconciliation | 0.01 | 0.05 | 0.08 |
| portfolio.sales_status_history_ordering | 0.02 | 0.06 | 0.08 |
| logistics.fulfillment_quantity_cap | 0.02 | 0.05 | 0.07 |
| payments.installment_total_reconciliation | 0.02 | 0.05 | 0.07 |
| sales.discount_amount_cap | 0.02 | 0.04 | 0.07 |
| portfolio.sales_status_history_chronology | 0.01 | 0.03 | 0.06 |
| inventory.moving_average_replay | 0.01 | 0.04 | 0.01 |
| portfolio.customer_profile_exclusivity | 0.03 | 0.04 | 0.02 |
| portfolio.refund_eligibility_by_return | 0.01 | 0.03 | 0.04 |
| payments.installment_method_eligibility | 0.01 | 0.01 | 0.03 |
| inventory.active_reservation_balance | 0.01 | 0.02 | 0.02 |
| inventory.reservation_product_match | 0.00 | 0.01 | 0.02 |
| portfolio.sales_cutoff | 0.01 | 0.01 | 0.02 |
| sales.order_total_reconciliation | 0.00 | 0.01 | 0.02 |
| table_count.payments.payment_installments | 0.00 | 0.00 | 0.02 |
| inventory.stock_ledger_balance | 0.00 | 0.01 | 0.01 |
| logistics.event_cutoff_state | 0.00 | 0.01 | 0.01 |
| master.customer_type_distribution | 0.01 | 0.01 | 0.01 |
| master.product_price_nonoverlap | 0.01 | 0.01 | 0.01 |
| master.table_count.crm.customer_addresses | 0.01 | 0.01 | 0.01 |
| master.table_count.crm.customer_contacts | 0.01 | 0.01 | 0.01 |
| payments.declined_timestamps | 0.00 | 0.00 | 0.01 |
| payments.refund_cap | 0.00 | 0.00 | 0.01 |
| portfolio.fulfillment_event_chronology | 0.01 | 0.01 | 0.01 |
| portfolio.sales_updated_at_chronology | 0.00 | 0.01 | 0.01 |
| portfolio.stock_bootstrap_commercial_cutoff | 0.00 | 0.01 | 0.01 |
| sales.channel_customer_compatibility | 0.00 | 0.01 | 0.01 |
| table_count.logistics.fulfillment_events | 0.00 | 0.00 | 0.01 |
| table_count.sales.order_status_history | 0.00 | 0.00 | 0.01 |
| table_count.sales.sales_order_items | 0.00 | 0.00 | 0.01 |
| table_count.sales.sales_orders | 0.00 | 0.00 | 0.01 |
| inventory.movement_cutoff | 0.00 | 0.00 | 0.00 |
| inventory.movement_direction_source_cost | 0.00 | 0.00 | 0.00 |
| inventory.realized_fulfillment_cost | 0.00 | 0.00 | 0.00 |
| inventory.stock_position_bounds | 0.00 | 0.00 | 0.00 |
| inventory.stock_position_replay_compare_input | 0.00 | 0.00 | 0.00 |
| inventory.transfer_movement_pair | 0.00 | 0.00 | 0.00 |
| master.active_stock_locations | 0.00 | 0.00 | 0.00 |
| master.preferred_supplier_active | 0.00 | 0.00 | 0.00 |
| master.product_specifications_json | 0.00 | 0.00 | 0.00 |
| master.product_unit_of_measure | 0.00 | 0.00 | 0.00 |
| master.sales_channel_types | 0.00 | 0.00 | 0.00 |
| master.single_preferred_supplier_per_product | 0.00 | 0.00 | 0.00 |
| master.store_geography | 0.00 | 0.00 | 0.00 |
| master.table_count.catalog.brands | 0.00 | 0.00 | 0.00 |
| master.table_count.catalog.categories | 0.00 | 0.00 | 0.00 |
| master.table_count.catalog.product_prices | 0.00 | 0.00 | 0.00 |
| master.table_count.catalog.product_suppliers | 0.00 | 0.00 | 0.00 |
| master.table_count.catalog.products | 0.00 | 0.00 | 0.00 |
| master.table_count.core.employee_assignments | 0.00 | 0.00 | 0.00 |
| master.table_count.core.employee_roles | 0.00 | 0.00 | 0.00 |
| master.table_count.core.employees | 0.00 | 0.00 | 0.00 |
| master.table_count.core.stores | 0.00 | 0.00 | 0.00 |
| master.table_count.crm.business_profiles | 0.00 | 0.00 | 0.00 |
| master.table_count.crm.customers | 0.00 | 0.00 | 0.00 |
| master.table_count.crm.individual_profiles | 0.00 | 0.00 | 0.00 |
| master.table_count.inventory.stock_locations | 0.00 | 0.00 | 0.00 |
| master.table_count.logistics.carriers | 0.00 | 0.00 | 0.00 |
| master.table_count.payments.payment_methods | 0.00 | 0.00 | 0.00 |
| master.table_count.procurement.suppliers | 0.00 | 0.00 | 0.00 |
| master.table_count.sales.sales_channels | 0.00 | 0.00 | 0.00 |
| payments.refund_relation_time | 0.00 | 0.00 | 0.00 |
| portfolio.cost_columns_numeric_20_8 | 0.00 | 0.00 | 0.00 |
| portfolio.historical_return_cost | 0.00 | 0.00 | 0.00 |
| portfolio.stock_available_generated_column | 0.00 | 0.00 | 0.00 |
| portfolio.terminal_order_reservations | 0.00 | 0.00 | 0.00 |
| portfolio.transfer_endpoints_quantities_cost | 0.00 | 0.00 | 0.00 |
| procurement.receipt_acceptance_balance | 0.00 | 0.00 | 0.00 |
| procurement.receipt_chronology | 0.00 | 0.00 | 0.00 |
| procurement.receipt_quantity_cap | 0.00 | 0.00 | 0.00 |
| returns.cumulative_fulfilled_quantity | 0.00 | 0.00 | 0.00 |
| returns.fulfillment_source_quantity | 0.00 | 0.00 | 0.00 |
| returns.inventory_destination | 0.00 | 0.00 | 0.00 |
| sales.order_cutoff | 0.00 | 0.00 | 0.00 |
| table_count.after_sales.return_items | 0.00 | 0.00 | 0.00 |
| table_count.after_sales.returns | 0.00 | 0.00 | 0.00 |
| table_count.inventory.stock_movements | 0.00 | 0.00 | 0.00 |
| table_count.inventory.stock_positions | 0.00 | 0.00 | 0.00 |
| table_count.inventory.stock_reservations | 0.00 | 0.00 | 0.00 |
| table_count.inventory.stock_transfer_items | 0.00 | 0.00 | 0.00 |
| table_count.inventory.stock_transfers | 0.00 | 0.00 | 0.00 |
| table_count.logistics.fulfillment_items | 0.00 | 0.00 | 0.00 |
| table_count.logistics.fulfillments | 0.00 | 0.00 | 0.00 |
| table_count.payments.payments | 0.00 | 0.00 | 0.00 |
| table_count.payments.refunds | 0.00 | 0.00 | 0.00 |
| table_count.procurement.goods_receipt_items | 0.00 | 0.00 | 0.00 |
| table_count.procurement.goods_receipts | 0.00 | 0.00 | 0.00 |
| table_count.procurement.purchase_order_items | 0.00 | 0.00 | 0.00 |
| table_count.procurement.purchase_orders | 0.00 | 0.00 | 0.00 |
| table_count.sales.applied_discounts | 0.00 | 0.00 | 0.00 |
### Suítes, banco e conclusão

- Suíte normal: **83 passed, 4 skipped** (as quatro integrações PostgreSQL foram puladas conforme esperado).
- Suíte de integração: **87 passed, 0 skipped**.
- Após cada escala, `ROLLBACK` foi concluído e uma nova conexão confirmou zero linhas nas 40 tabelas. A mesma confirmação após as suítes finais também retornou `tables=40 empty=True`.
- Os tempos não justificam índice permanente ou outra mudança estrutural. O bundle antigo de 15 subconsultas não foi reexecutado.
- `ANALYZE` foi integrado ao fluxo Portfolio: tabelas mestre após carga mestre e antes da validação mestre; as 40 tabelas após carga transacional e antes das validações pré-COMMIT.

**READY FOR 120K RETRY.** Os critérios de cronologia, validações equivalentes, controles negativos, estatísticas do planner, escalas 10k/25k/50k, rollback, banco vazio e suítes foram atendidos. A Fase 3E.2 permanece aberta; 120k não foi executado automaticamente e deve ocorrer somente em solicitação posterior.

## Tentativa final Portfolio 120k — 2026-10-07

A autorização para o retry foi exercida após repetir as suítes e gates prévios. O smoke dry-run confirmou 300 pedidos/630 itens e os totais financeiros/digest aprovados; o plano Portfolio confirmou alvo de 120.000 pedidos, 264.000 itens estimados e 2.200.000 linhas transacionais. Preflight em nova conexão: database `projeto_bi`, PostgreSQL 18.6, nove schemas, 40 tabelas, migration 002 refletida e zero linhas.

A carga foi executada em uma única transação. A master de 219.009 linhas foi gerada em 2,2 s, persistida e conferida em 21,1 s; `ANALYZE` mestre levou 1,07 s. Os períodos informados pelo pipeline foram: 2023 761,4 s; 2024 2.040,4 s; 2025 2.265,3 s; Jan–Set/2026 1.740,8 s. `ANALYZE` das 40 tabelas operacionais levou 2,97 s. O último marco de progresso antes da conclusão registrou 119.736 pedidos, 1.460.233 linhas emitidas, 1.307.538 inseridas, 153.700 updates, 1.400 flushes, lote máximo de 1.465 linhas e pico de 1.065 IDs transitórios; é um marco intermediário, não a contagem final.

As validações críticas SQL não registraram falhas antes do gate distribucional. O gate reprovou e impediu o `COMMIT` por estes oito valores:

| Verificação | Observado | Faixa aprovada |
|---|---:|---:|
| Pedidos em 2023 | 31.977 | 20.000–26.000 |
| Pedidos em Jan–Set/2026 | 23.807 | 27.000–34.000 |
| Clientes com um pedido | 27,63% | 35–50% |
| Clientes com 2–4 pedidos | 64,51% | 30–40% |
| Pedidos concluídos | 2,07% | 93–97% |
| Pedidos pendentes | 95,23% | 0–3% |
| Mix de pagamentos por cartão | 58,85% | 35–50% |
| Margem bruta operacional | 61,58% | 8–28% |

O runner encerrou a transação sem commit. Uma nova conexão confirmou zero linhas nas 40 tabelas. Não foram criados baselines, relatório final Portfolio, atualização de README ou commit Git; não houve retry automático. A suíte normal passou (83 passed, 4 skipped) e a suíte PostgreSQL passou antes da carga (87 passed, 0 skipped); nenhuma suíte de integração foi executada contra a base após essa tentativa.

**Resultado da tentativa final: NOT READY FOR PORTFOLIO COMMIT. Fase 3E.2 permanece aberta.** A carga persistente de 120k foi revertida por falha distribucional. Não ajustar dados manualmente nem repetir a carga sem uma etapa posterior autorizada para investigar e corrigir a composição/perfil que gerou esses resultados.

## Fase 3E.2c — diagnóstico inicial de distribuição Portfolio (2026-10-07)

Esta retomada iniciou sem conexão ou escrita no PostgreSQL. O estado local anterior foi preservado. Foi executada uma auditoria lógica descartável de 10.000 pedidos com o gerador incremental e um sink de diagnóstico; nenhum `TransactionData` foi materializado.

### Status e causa raiz

No fixture lógico de 10.000 pedidos, os status finais foram: `confirmed` 9.006 (90,06%), `completed` 724 (7,24%) e `cancelled` 270 (2,70%). Por ano: 2023 teve 2.393 confirmed, 200 completed e 72 cancelled; 2024, 2.396/211/72; 2025, 2.418/182/72; 2026 Jan–Sep, 1.799/131/54. A taxa de cancelamento ficou coerente com os índices determinísticos do gerador; a anomalia é a permanência em `confirmed`.

A causa é `EVENT_NOT_SCHEDULED` por falta de disponibilidade no instante do pedido, seguida de ausência de atendimento do saldo pendente quando há recebimento posterior. A reserva/fulfillment é criado apenas para o estoque disponível durante `create_sale`; o evento de recebimento não reavalia pedidos anteriores. Quando todas as quantidades alocadas terminam, o pedido só vira `completed` se a quantidade atendida igualar a quantidade pedida. A fila causal chega vazia, mas o pedido continua `confirmed`, inclusive se tiver muitos anos.

Exemplos determinísticos do fixture: `ORDER-KEY-0001`, colocado em 2023-01-02 09:00 -03:00, teve pagamento liquidado e dois fulfillments concluídos de 2 unidades cada, mas o pedido especial tinha 5 unidades; ficou faltando 1 unidade e o status permaneceu `confirmed`. `ORDER-KEY-0002`, colocado em 2023-01-02 10:51 -03:00, também teve pagamento liquidado, mas não obteve reserva nem fulfillment e ficou `confirmed`. Não havia evento futuro de conclusão ou cancelamento para nenhum desses pedidos. Assim, pedidos antigos pendentes não são efeito do cutoff ou de pagamento bloqueando; são pendências operacionais sem evento de retomada.

O problema não deve ser corrigido reclassificando esses pedidos como concluídos. Ainda falta definir e implementar a regra operacional para falta de estoque: manter backorder e atender quando o recebimento chegar, ou impedir/comportar a criação da venda até haver cobertura. O planejamento documenta compras/recebimentos e cobertura de demanda, mas não escolhe uma dessas regras nem estabelece uma cobertura de bootstrap por local. Sem essa decisão, um ajuste numérico de estoque inicial não prova término correto de pedidos e poderia esconder a lacuna causal. A correção funcional e o gate de status permanecem pendentes.

### Diagnósticos dos outros desvios

- **Anual — calibração determinística.** A engine distribui os índices de pedido uniformemente pelo número de dias de todo o horizonte. Isso implica pesos proporcionais aos dias corridos: aproximadamente 27,5% para cada ano completo e 20,5% para os nove meses de 2026. Portanto a fórmula favorece 2023 acima do alvo e deixa 2026 abaixo. A proporção explica a direção observada na tentativa final (31.977 em 2023; 23.807 em 2026). A configuração atual não declara quotas anuais; ainda não foi alterada.
- **Recorrência — calibração do algoritmo.** Para cada pedido identificado, o código escolhe um cliente aleatório de toda a população master. Não há segmentos de frequência nem quota por cliente; o denominador SQL é o conjunto de clientes identificados com ao menos um pedido não cancelado, agrupado por tipo PF/PJ. Esse sorteio independente explica a concentração em 2–4 pedidos observada em 120k (27,63% com 1; 64,51% com 2–4), mas PF/PJ e as demais faixas ainda precisam ser comparados no auditor de 120k após a definição dos segmentos.
- **Pagamento — calibração por canal ausente.** O seletor aplica um único comportamento digital para e-commerce e marketplaces (42% instant; restante cartão), e físico aplica 15% dinheiro e, no restante, 28% instant (o restante cartão). Isso produz aproximadamente 59% de cartão antes de pequenos efeitos de PJ/split, consistente com os 58,85% do gate. Não há pesos configuráveis por canal; nenhuma mudança foi feita.
- **Margem — definição atual alinhada em parte, resultado ainda inconclusivo para recalibração.** A consulta do gate soma receita líquida de produto das unidades atendidas menos unidades recebidas em devolução e COGS dos movimentos de fulfillment das mesmas linhas/itens, restringindo-se a pedidos completed; não inclui frete. Logo, a taxa anterior de 61,58% não é a comparação simples entre toda a receita dos pedidos e COGS parcial. Contudo, como mais de 90% dos pedidos ficaram fora do conjunto completed, ela não representa adequadamente o perfil final. Após corrigir o lifecycle, a margem deve ser reavaliada nesse mesmo grão; nenhuma alteração de pricing ou custo foi feita.

### Resultado desta retomada

O auditor de diagnóstico de 10k confirmou a falha de status e detalhou canais (5.170 físicos, 2.790 e-commerce, 2.040 marketplaces) e mix de pagamentos capturados (5.895 cartão, 3.363 instant, 706 dinheiro; transferência residual). Ele ainda não implementa equivalência com as métricas SQL, nem contém o estado agregador necessário para rodar 120k sem reter pedidos. Por consequência, o dry audit completo de 120k, a calibração anual/recorrência/pagamentos, a revisão final de margem, os rollbacks PostgreSQL 10k/50k e as suítes pós-calibração não foram executados nesta retomada. A execução dos rollbacks antes de resolver/calibrar o lifecycle não validaria a candidata de profile corrigida.

**Resultado da Fase 3E.2c: NOT READY.** A causa do status foi reproduzida e classificada, mas ainda não corrigida; as demais calibrações não foram aplicadas. Não foi executada a carga Portfolio 120k no PostgreSQL, nenhum dado foi persistido e nenhum commit ou push foi feito. A Fase 3E.2 permanece aberta.

## Fase 3E.2c.1 — implementação do lifecycle de estoque (2026-10-07)

### Regra e mudanças

Foi adotada a política híbrida aprovada: uma intenção física só cria pedido com disponibilidade local suficiente; pedidos digitais podem aguardar reposição por até 14 dias corridos a partir de `placed_at`, no fuso `America/Sao_Paulo`. O profile Portfolio mantém esse prazo em `max_stock_wait_days`. Uma fila incremental indexada por SKU/local atende em FIFO estável e permite fulfillment parcial. `goods_receipt`, `transfer_in` e `customer_return` vendável despertam a fila imediatamente após a atualização da posição/custo; retornos não vendáveis não adicionam saldo. O pedido continua confirmado até não haver quantidade devida e a logística requerida terminar.

Foi corrigido o fechamento prematuro de pedidos digitais parcialmente atendidos: o estado ativo não é liberado enquanto houver backorder. Pedidos zerados após 14 dias são cancelados e o valor capturado é integralmente reembolsado por `refunds`, com referência nula a return e motivo `other`; nenhuma devolução fictícia é criada. O schema suporta essa referência opcional de return e a faixa de motivo documentada. O validador de pagamentos foi ampliado para reconhecer captura integralmente reembolsada em cancelamento. O schema não registra quantidade cancelada por item nem estorno proporcional, então pedido parcialmente expedido além do prazo causa bloqueio explícito. Nenhum status ou migration foi inventado.

As reposições continuam sendo purchase orders e goods receipts com fornecedor, lead time, movimentos e custo existentes. Nenhum estoque instantâneo ou compra emergencial foi introduzido. Reposições cujo prazo de chegada ultrapassa o cutoff não são agendadas. O Smoke preserva seu comportamento oracle; a geração Portfolio não modifica o horizonte.

### Auditoria lógica incremental — 10.000 intenções

O baseline da subfase anterior gerava os 10.000 pedidos: 9.006 `confirmed`, 724 `completed` e 270 `cancelled`. Com a nova regra física, 3.867 intenções sem estoque local não foram convertidas; 6.133 pedidos foram emitidos. A geração foi interrompida no gate final ao identificar saldo parcial vencido. Entre os 6.133 pedidos emitidos, o estado no ponto de bloqueio foi:

| Status/resultado | Contagem |
|---|---:|
| `completed` (estimativa antes do bloqueio) | 5.036 |
| `cancelled` | 363 |
| `confirmed` abertos no ponto de bloqueio | 734 |
| Dos confirmados: parcialmente atendidos além de 14 dias | 704 |
| Dos confirmados: prazo de espera ainda aberto no cutoff (deadline posterior) | 30 pedidos / 46 linhas |
| Intenções físicas sem estoque, não convertidas em pedido | 3.867 |
| Pedidos sem expedição cancelados e reembolsados após prazo | 203 |

O diagnóstico anterior registra o caso parcial de `ORDER-KEY-0001` com 4 de 5 unidades e `ORDER-KEY-0002` sem fulfillment; a nova engine exige saldo completo ou tratamento permitido antes de conclusão. Exemplos que bloqueiam esta rodada incluem `ORDER-KEY-3007` (2/3 unidades, saldo 1, deadline 2024-03-01), `ORDER-KEY-3282` (1/2, saldo 1, deadline 2024-04-08) e `ORDER-KEY-3557` (1/2, saldo 1, deadline 2024-05-15). Os três expiraram sem reposição suficiente; mais sete exemplos determinísticos foram capturados na mensagem de diagnóstico do gerador.

Após reposições, foram resolvidas 745 linhas e atendidas 774 unidades de backorder. O máximo simultâneo foi 37 pedidos pendentes. O fluxo recebeu 75.315 unidades no total. Dezesseis solicitações de reposição, somando 136 unidades, teriam chegada além do cutoff e foram omitidas. Esses totais comprovam que os eventos de reposição agora retomam a fila, mas também comprovam que o abastecimento atual não satisfaz o prazo em todos os pedidos. Não houve gate final de reconciliação completa de estoque, pois a implementação parou intencionalmente no caso parcial não representável.

### Regressão e decisão

- Smoke: todas as 21 tabelas, agregados e digest seguem cobertos pelo oracle `36640f5474a02c02168cb50f983327b2c9f181bd5d8cdaca50ab5513bf23874a`.
- Testes após a alteração: **87 passed, 4 skipped**; os quatro skips são os testes de integração PostgreSQL que exigem `PROJECTBI_RUN_INTEGRATION=1`. `compileall` também passou.
- Nenhuma conexão, escrita ou teste PostgreSQL foi executado; não se aplicou migration e nenhum dado foi persistido.
- Diff sem erro de whitespace no checkpoint anterior; revisão final e estado Git permanecem nesta subfase. Não houve commit nem push.

**LIFECYCLE BLOCKED.** A retomada por reposição, FIFO e cancelamento/refund integral sem expedição estão implementados. A limitação é o tratamento de 704 pedidos parcialmente expedidos que excederam o prazo sem suporte do schema para cancelar/estornar somente a quantidade pendente. A conversão física de 6.133/10.000 intenções também altera o volume e requer análise de abastecimento em fase autorizada. A Fase 3E.2c e a Fase 3E.2 continuam abertas; não houve calibração anual, de recorrência, pagamentos ou margem.

### Subfase 3E.2c.2 — auditoria de abastecimento e proposta estrutural

Foi executado diagnóstico Portfolio não persistente para 10.000 intenções, com seed oficial e instrumentação opt-in. A variante balanceada preservou as quantidades centrais de bootstrap por SKU e redistribuiu deterministamente 52% às dez lojas e 48% aos quatro armazéns. O profile oficial não foi alterado. O total inicial diferiu em oito unidades por componentes auxiliares do bootstrap; a comparação controla o estoque central por SKU, mas não é perfeitamente idêntica em todo o estoque inicial.

Esta reprodução na árvore de trabalho atual difere do checkpoint histórico imediatamente acima (704 vs. 728 parciais vencidos; 30 vs. 32 pedidos ainda dentro do prazo). O checkpoint foi preservado, sem reescrita dos resultados anteriores. Duas execuções controle consecutivas no mesmo processo reproduziram os mesmos agregados; para esta subfase, comparação e percentuais abaixo usam somente controle e variante executados no mesmo processo/código. Investigar a divergência entre checkpoints antes de estabelecer qualquer baseline final.

| Métrica | Controle | Balanceamento de locais |
|---|---:|---:|
| Pedidos emitidos | 6.133 | 8.378 |
| Intenções físicas não convertidas | 3.867 | 1.622 |
| Unidades físicas perdidas | 8.962 | 4.480 |
| Pedidos estimados completos antes do bloqueio | 4.988 | 8.147 |
| Pedidos parciais vencidos | 728 | 5 |
| Unidades de backorder vencidas | 874 | 5 |
| Backorders ativos no cutoff | 32 pedidos | 0 |
| Unidades recebidas no horizonte | 75.426 | 79.142 |
| Estoque inicial | 11.949 | 11.941 |
| Disponível final | 64.301 | 62.406 |
| Disponível final sem demanda naquela combinação SKU/local | 46.570 | 17.796 |
| Disponível médio no horizonte | 45.595,71 | 43.296,38 |
| Lead time médio / máximo | 8,4 / 12 dias | 7,9 / 12 dias |

O balanceamento reduziu em cerca de 58% as intenções físicas recusadas e em 50% as unidades físicas perdidas, mas ainda bloqueou por cinco pedidos com atendimento parcial vencido. Os recebimentos aumentaram por reposições disparadas endogenamente após a mudança de saldo por local; isso não valida a política de compras. No controle, havia 46.570 unidades finais sem demanda na localização enquanto 6.740 pares SKU/local tiveram algum período sem disponibilidade. A variante teve 17.796 unidades sem demanda e 6.984 pares SKU/local com ruptura. O número de pares com ruptura, sozinho, não mede duração ou severidade.

Todas as perdas físicas ocorreram na loja de atendimento: controle — ST-PO-010 (1.566 unidades), ST-PO-008 (1.215), ST-PO-009 (1.177); balanceado — ST-PO-010 (1.122), ST-PO-008 (750), ST-PO-009 (732). O controle perdeu unidades em todas as 12 categorias, sem concentração em uma categoria (729–780 por categoria). No controle, as intenções físicas recusadas por ano foram 1.248, 1.101, 949 e 569 (2023–2026), com 2.858, 2.556, 2.239 e 1.309 unidades físicas perdidas. No balanceado foram 558, 476, 388 e 200 intenções, e 1.511, 1.343, 1.073 e 553 unidades perdidas. Backorders digitais vencidos concentraram-se no armazém LOC-PO-WH-013; o SKU repetido nos poucos vencimentos da variante foi SKU-NOT-00001.

**Causas.** A causa principal demonstrada é a localização incompatível entre estoque e atendimento: o bootstrap original concentra cada SKU em um local; venda física exige saldo imediato na loja, e o saldo de armazém não é transferido automaticamente. O estoque agregado não é insuficiente. A reposição também contribui para o saldo ocioso: responde à ruptura com alvo fixo de 7/10 unidades por família e não considera cobertura histórica por SKU/local. O lead time médio observado (7,9–8,4 dias) e máximo (12 dias) deixa pouca margem dentro da espera de 14 dias, mas não é causa única provada. O schema e a engine permitem movimentos de transferência; falta política causal que acione uma transferência elegível antes de perder a venda. Nenhuma compra retroativa, estoque instantâneo ou previsão com conhecimento de pedidos futuros foi usada.

**Política a avaliar em etapa autorizada.** Definir ponto de reposição por SKU/local usando demanda observada até a data da decisão, demanda esperada durante o lead time e estoque de segurança; considerar saldo disponível e inbound confirmado, cobertura por local, sazonalidade somente se sustentada pelos dados e limites de lote/cobertura. Quando houver excedente elegível em outro local, usar transferência real com movimentos pareados e prazo operacional; caso contrário, purchase order e goods receipt normais. O rateio 52/48 é somente experimento de sensibilidade, não parâmetro aprovado.

**Cancelamento parcial.** O schema registra quantidade original em `sales.sales_order_items.quantity`, atendimento em `logistics.fulfillment_items.fulfilled_quantity` e fluxo financeiro em pagamentos/refunds, mas não possui quantidade cancelada por item nem snapshot do desconto/valor líquido cancelado. O status de pedido cobre cancelamento integral. `logistics.return_items` exige fulfillment real e não pode representar unidade nunca expedida. Logo, o cenário 3 unidades, 2 expedidas, 1 cancelada não pode ser representado sem ambiguidade.

Proposta mínima para decisão, sem alteração nesta fase: tabela `sales.sales_order_item_cancellations` com identity PK, FK composta para pedido/item, quantidade positiva, timestamp, motivo controlado e snapshots BRL de desconto cancelado e valor líquido cancelado. A escrita deve bloquear o pedido/item e validar quantidade acumulada cancelada + fulfillment contra a quantidade original. O desconto deve ser rateado sobre `sales.applied_discounts` com regra determinística de centavos. Refund parcial ligado a cada pagamento capturado; em pagamentos divididos, alocação determinística por saldo ainda reembolsável e limite agregado ao capturado. Regras de frete/tributos e motivos ainda precisam de decisão de negócio. Não adicionar status nesta fase: pedido totalmente cancelado permanece `cancelled`; pedido com linhas entregues e saldo cancelado poderia terminar `completed` quando todas as quantidades estiverem entregues ou canceladas e os refunds correspondentes registrados, sujeito à aprovação dessa semântica.

A migration exigiria atualizar constraints/índices, `PostgreSQLTransactionSink` e lifecycle do registro de IDs, geração incremental, validações de quantidade/desconto/pagamento/refund e diagnósticos SQL. Preservar o smoke de 21 tabelas e digest `36640f5474a02c02168cb50f983327b2c9f181bd5d8cdaca50ab5513bf23874a`. Não usar returns para não expedidos nem criar status sem aprovação.

Para a meta futura de 120.000 pedidos registrados, manter métricas separadas de intenções tentadas e pedidos aceitos. Se a meta continuar sendo pedidos efetivos, gerar intenções determinísticas até atingi-la sob limite de tentativas explícito; controlar distribuição anual e participação de canal sobre pedidos aceitos e reportar recusas por motivo, sem deslocar silenciosamente cotas. Não alterar o alvo oficial nesta fase.

Ordem recomendada: aprovar cancelamento parcial, incluindo motivo, rateio de desconto/frete/tributos, reembolso dividido e semântica final; implementar migration, sink e validações; substituir o bootstrap e a reposição por cobertura baseada em demanda observada/lead time e transferência real; então repetir 10.000 pedidos antes de qualquer escala. A variante ainda falha lifecycle e não conclui 3E.2c.1. Suíte: **90 passed, 4 skipped** (integrações PostgreSQL não iniciadas). Nenhum PostgreSQL foi acessado, dado persistido ou migration criada; sem commit/push.

**ABASTECIMENTO DIAGNOSTICADO — DECISÃO ESTRUTURAL PENDENTE**

## Fase 3E.2c.3 — cancelamento parcial de pedidos (2026-10-07)

A migration `database/migrations/003_partial_item_cancellations.sql` foi aplicada depois do preflight de leitura confirmar o estado aprovado da database vazia: PostgreSQL 18.6, nove schemas, 40 tabelas antigas, sem dados e sem objetos inesperados. A alteração é aditiva: acrescenta contadores de quantidade atendida/cancelada em `sales.sales_order_items`, `sales.sales_order_item_cancellations`, referência opcional em `payments.refunds` e constraints, triggers e índices associados. Nenhuma tabela ou linha preexistente foi apagada ou recriada.

A validação estrutural após a migration confirmou 9 schemas, 41 tabelas, 41 PKs, 72 FKs, 85 CHECKs, 38 UNIQUEs e 154 índices físicos. Foram conferidos JSONB de `catalog.products.specifications`, coluna gerada de estoque, `source_fulfillment_item_id`, ausência de `unit_cost_snapshot`, moeda BRL nos pontos previstos e ausência de CHECK de domínio em `unit_of_measure` conforme pendência já registrada.

O profile lógico determinístico com 10.000 intenções passou pelas validações de ciclo de vida, estoque e finanças. Foram emitidos 6.133 pedidos; 5.740 terminaram `completed`, 363 `cancelled` e 30 permaneceram `confirmed` dentro da janela no cutoff. Houve 1.083 cancelamentos de item, dos quais 13 em pedidos parcialmente atendidos que concluíram após resolver as unidades restantes. Quantidades: 11.199 atendidas, 1.123 canceladas e 376 pendentes no cutoff. O cancelamento totalizou BRL 6.415.971,88 bruto, BRL 127.530,94 de desconto rateado e BRL 6.288.440,94 líquidos; o frete estornado foi BRL 2.905,50 apenas em pedidos totalmente cancelados sem fulfillment. Refunds ligados a cancelamentos somaram BRL 6.291.346,44 em 1.098 linhas. Não foram criados movimentos ou returns fictícios para unidades não expedidas.

O teste PostgreSQL full de 10.000 intenções passou: validações SQL e replay do ledger aprovaram, inclusive 19.071 movimentos no cenário da execução. Um fixture sob savepoint confirmou estorno de cancelamento distribuído entre duas capturas e limitado aos saldos reembolsáveis; a tentativa negativa excedendo a quantidade restante também foi rejeitada pela constraint esperada. O teste multibatch de 1.000 intenções passou depois de corrigir sua asserção: o alvo é de intenções, e vendas físicas sem estoque local suficiente podem ser recusadas. Ambos terminaram com `ROLLBACK` e verificação em conexão nova.

A suíte unitária terminou com 96 passed e 5 integrações ignoradas quando executada sem a flag de integração. O smoke incremental/full manteve o digest `36640f5474a02c02168cb50f983327b2c9f181bd5d8cdaca50ab5513bf23874a`. Após os rollbacks, uma conexão nova contou zero linhas nas 41 tabelas operacionais. Nenhum dado de negócio foi persistido.

**Resultado desta subfase: PARTIAL CANCELLATION READY.** O cancelamento parcial está representado e validado no schema, no gerador, no sink e nas regras financeiras. Isto não aprova calibração de abastecimento, execução Portfolio 120k ou avanço ao Power BI; esses escopos permanecem fora desta subfase. Sem commit e sem push.

## Fase 3E.2c.4 — abastecimento e transferências (2026-10-08)

### Baseline reproduzido e números históricos

O controle atual foi gerado em memória com seed `20261005`, 10.000 intenções e sem os overrides da política nova. Para comparar cenários, o profile não-smoke agora deriva o conteúdo SKU/quantidade de cada intenção por índice determinístico, sem que uma recusa de estoque altere os sorteios das intenções seguintes. Reproduziu 6.127 pedidos aceitos (5.678 `completed`, 419 `cancelled`, 30 `confirmed` no cutoff), 3.873 intenções físicas recusadas, 8.937 unidades físicas perdidas, 686 pedidos com backorder parcial vencido, 839 unidades vencidas, 252 cancelamentos integrais por timeout e 30 pedidos/46 linhas ainda dentro dos 14 dias. O estoque inicial controlado somou 11.949 unidades; disponibilidade média 45.510,77; 46.472 unidades finais estavam em pares SKU/local sem demanda observada. Lead time médio/máximo foi 8,4/12 dias.

O número histórico **728** do checkpoint de auditoria anterior descreve pedidos parciais que venceram naquela árvore; a reprodução de controle desta subfase encontrou 686 (diferença de 42) e 30 pedidos ainda dentro do prazo, contra 32 naquele checkpoint. O número **13** registrado no relatório da subfase 3E.2c.3 descreve outra classificação (“pedidos parcialmente atendidos que concluíram após resolver as unidades restantes”); não é a contagem de backorders vencidos e não foi reproduzido com essa definição no controle atual. Nesta execução, os 686 pedidos vencidos tinham ao menos uma unidade atendida, tiveram o saldo cancelado e foram classificados `completed`; o controle também teve 1.155 linhas de cancelamento de item. A série de SKU/quantidades por intenção foi isolada por índice nesta subfase para impedir que a aceitação alterasse as intenções seguintes. Os checkpoints anteriores não têm artefato/digest suficiente para atribuir exatamente a diferença de 728/32 para 686/30 apenas à migration 003; os números históricos foram preservados como histórico, sem misturá-los ao baseline atual.

### Política e experimento

O estoque inicial foi conservado por SKU em todas as variantes: cada total de SKU que era 9–15 unidades no controle permaneceu igual na alternativa distribuída; os SKUs especiais das fixtures e os cinco pedidos extras de bootstrap mantiveram a regra original. Para SKUs distribuídos, o rateio usa dois estágios: share de lojas/armazéns (maior resto) e rateio uniforme dentro de cada papel, com desempate por hash da seed/SKU. O share configurado de 65% resultou em 7.709 unidades nas lojas e 4.240 nos armazéns (64,5%/35,5% do total, por arredondamento e fixtures preservadas). É parâmetro experimental, não uma aprovação de capacidade física das lojas. Não há no modelo aprovado metadado de metragem/capacidade ou perfil de demanda por categoria; na ausência desses dados, as lojas e os armazéns recebem pesos iguais dentro de seu papel. O prior usa lojas abertas até a data da decisão, e o histórico observado passa a dominar gradualmente.

A previsão usa janela móvel de 90 dias e prior calculado sem acessar intenções futuras: alvo configurado de intenções × 2,1 itens × participação 52% física/48% digital, dividido por dias do horizonte, SKUs e locais ativos do papel. Usa 60 dias de força de prior. Demanda física recusada entra como observação não atendida, distinta das unidades expedidas; não produz pedidos fictícios nem é recontada como atendimento. A posição na reposição é `disponível + inbound confirmado − backorders`; disponível já exclui reservas, e inbound conta compras/transferências confirmadas em trânsito uma vez. O alvo de cobertura é lead time observado/decidido do fornecedor mais 14 dias de revisão e estoque de segurança. Transferência desconta reserva, backorder, demanda prevista durante o trânsito e safety do saldo doador; origem é limitada a armazéns, destino a loja e o trânsito é 2–5 dias, além de 8 horas até expedição.

As doze variantes (controle; shares 40%, 52% e 65%; transferência isolada; cobertura isolada; combinações; e segurança 2×) foram executadas no mesmo processo, mesma seed e mesmas 10.000 intenções. O digest de conteúdo completo das intenções (canal, loja, cliente, instante, SKU e quantidade) foi idêntico nas doze variantes: `d89efc2e75bef5123839ad2e1ba0000fc77073f871cc7aef451de84bf5547767`. Toda variante distribuída passou a asserção de conservação do mapa SKU→unidades iniciais. O experimento completo levou aproximadamente 2 min 05 s; a fila máxima foi 11.496 eventos, com máximos de 13 pedidos ativos, 6 backorders e 3 transferências simultâneas na candidata. A memória de processo não foi medida nesta rodada.

| Variante | Pedidos aceitos | Intenções físicas recusadas | Unidades físicas perdidas | Backorders parciais vencidos / no cutoff | Recebimentos aceitos | Transferências de política (itens/unidades) | Disponível médio | Saldo final sem demanda |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Controle atual | 6.127 | 3.873 | 8.937 | 686 / 30 | 75.212 | 0 / 0 | 45.510,77 | 46.472 |
| A — bootstrap 65% loja | 8.554 | 1.446 | 3.776 | 0 / 0 | 79.504 | 0 / 0 | 43.503,96 | 15.483 |
| B — bootstrap 52% + transferências | 7.893 | 2.107 | 5.300 | 5 / 0 | 75.333 | 2.352 / 13.616 | 40.463,58 | 19.883 |
| C — bootstrap 52% + cobertura, safety base | 7.814 | 2.186 | 5.521 | 0 / 8 | 31.543 | 0 / 0 | 15.217,13 | 7.606 |
| D — A + cobertura/safety base | 8.440 | 1.560 | 4.099 | 0 / 10 | 32.617 | 0 / 0 | 15.174,90 | 6.474 |
| D + transferências | 8.445 | 1.555 | 4.087 | 0 / 12 | 32.609 | 82 / 91 | 15.138,17 | 6.447 |
| C2 — A + cobertura, safety 2× | 8.531 | 1.469 | 3.844 | 0 / 5 | 41.480 | 0 / 0 | 20.378,88 | 8.246 |
| **Candidata — A + cobertura/safety 2× + transferências protegidas** | **8.529** | **1.471** | **3.850** | **0 / 3** | **41.434** | **63 / 71** | **20.327,21** | **8.243** |

A candidata foi escolhida como compromisso para a fixture, não para maximizar apenas pedidos aceitos. Contra o controle, aumentou pedidos aceitos em 39,2%, reduziu intenções físicas recusadas em 62,0%, unidades perdidas em 56,9%, disponibilidade média em 55,3%, saldo final sem demanda em 82,3% e dias acumulados sem disponibilidade em 52,4% (3.666.647,42 → 1.746.579,01). O estoque final total caiu de 64.323 para 24.485 unidades. Recebimentos caíram 44,9%; a candidata gerou 20.448 ordens de compra para 41.436 unidades ordenadas, distribuídas por SKU/local. A variante C2 sem transferências teve 2 pedidos aceitos a mais e 6 unidades físicas perdidas a menos, mas 2 pedidos adicionais no cutoff; transferências moveram 71 unidades em 63 itens e reduziram 46 unidades de procurement confirmado. O trânsito somou 243 dias, média aproximada de 3,86 dias por item. Esse ganho é pequeno frente ao efeito de bootstrap/cobertura; a transferência foi mantida como política conservadora elegível, não como alavanca principal de conversão.

O trade-off permanece explícito: a candidata teve 10.092 episódios sem estoque contra 7.204 no controle, embora a soma de dias de ruptura tenha caído. Em relação ao bootstrap 65% isolado, a candidata quase manteve conversão (8.529 vs. 8.554), mas reduziu disponibilidade média de 43.503,96 para 20.327,21 e reduziu o saldo ocioso de 15.483 para 8.243; aumentou os episódios de ruptura de 7.233 para 10.092 e os dias acumulados de 979.568,06 para 1.746.579,01. A leitura por loja mostra concentração de unidades perdidas em ST-PO-010 (771), ST-PO-008 (562) e ST-PO-009 (552); por ano foram 1.338 (2023), 1.127 (2024), 877 (2025) e 508 (2026). Este trade-off deve acompanhar qualquer futura calibração; não foi ocultado pelo total de pedidos aceitos.

### Lifecycle, validação e banco

Na candidata: 8.292 pedidos `completed`, 234 `cancelled`, 3 `confirmed` no cutoff; 105 unidades de backorder foram atendidas; nenhum backorder parcial venceu nem gerou linha de cancelamento de saldo. O prazo de 14 dias permaneceu em vigor. O controle atual teve 1.155 linhas de cancelamento, incluindo 686 pedidos com atendimento parcial cujo saldo pendente foi cancelado. Um savepoint do runner integrou refund de cancelamento de BRL 90 em duas capturas e rejeição de quantidade acima do elegível.

O smoke foi verificado pela suíte e manteve o digest histórico `36640f5474a02c02168cb50f983327b2c9f181bd5d8cdaca50ab5513bf23874a`. A suíte unitária terminou com **113 passed, 6 skipped** sem a flag de integração; os skips são as fixtures PostgreSQL. As validações de transações em memória passaram nas 12 variantes, incluindo ledger, lifecycle, custo e cutoff.

A integração PostgreSQL da candidata foi executada em 10.000 intenções no target `projeto_bi`, PostgreSQL 18, 9 schemas e 41 tabelas. O ensaio executou `BEGIN`, carga, `ANALYZE` das 41 tabelas e validações SQL nomeadas, incluindo balanço do ledger, replay de custo médio, posição final, movimentos pareados de transferência, resolução/cancelamento de itens e refunds; fez `ROLLBACK` e consultou uma conexão nova. O teste passou em 150,50 s, confirmou zero linhas nas 41 tabelas e validou IDs transitórios zerados. O primeiro ensaio final falhou apenas na métrica de ciclo de vida de IDs: um item de recebimento com zero unidades aceitas não gera movimento e, portanto, sua referência não era liberada. O sink foi corrigido para liberar essa referência sem alterar o schema; o novo ensaio passou. Nenhuma migration, commit, push ou carga persistente foi executada.

**Resultado da Fase 3E.2c.4: SUPPLY POLICY READY para esta subfase experimental.** Conservação do bootstrap, causalidade, lifecycle, transferências, smoke, comparações reproduzíveis, suíte e integração PostgreSQL com rollback passaram. A candidata e seus trade-offs não aprovam a calibração definitiva do profile. A Fase 3E.2 permanece aberta; não executar 120.000 intenções, carga persistente nem Power BI.

### Revalidação nesta retomada

A suíte unitária foi repetida na árvore atual: **113 passed, 6 skipped** em 24,49 s; os seis skips são as fixtures PostgreSQL desabilitadas nessa execução. A integração da política com transferências foi então executada separadamente no PostgreSQL 18.6, com 10.000 intenções. O teste concluiu em 504,78 s e passou; inclui o guard de database/schema vazio, `BEGIN`, carga da candidata, `ANALYZE`, validações SQL e fixtures negativas em savepoint, `ROLLBACK` e contagem por conexão nova. As asserções confirmaram 41 tabelas sem linhas e zero IDs transacionais retidos. Nenhum dado permaneceu persistido.

Também foi medido o crescimento de memória em 25.000 intenções, com o sink descartável e sem conexão ao banco. O master ocupou 65,9 MiB de heap corrente e 69,9 MiB de pico. Bootstrap 65% levou 95,93 s, teve delta de pico de 44,2 MiB, delta corrente de 5,0 MiB e 22.742 pedidos aceitos; terminou com 32 pedidos e 16 backorders ativos, além de 12 transferências fixas em trânsito. Cobertura com safety 3 levou 107,06 s, teve delta de pico de 34,1 MiB, delta corrente de 4,7 MiB e 22.351 pedidos aceitos; terminou com 92 pedidos e 78 backorders ativos, sem transferência ativa. Ambas mantiveram lote máximo de 5.000 linhas e fila máxima de 11.496 eventos. São medições comparativas de memória/escala, não uma nova calibração nem autorização para executar a meta Portfolio.

## Marco M1 — decisão técnica do profile (2026-10-08)

A expansão das medições para sete variantes confirmou que o universo de intenções foi idêntico em todos os cenários (`d89efc2e75bef5123839ad2e1ba0000fc77073f871cc7aef451de84bf5547767`) e que o rateio inicial conserva o total SKU→unidades do controle. Para a escolha de segurança, bootstrap 65% sem cobertura aceitou 8.554 pedidos, perdeu 3.776 unidades e ordenou 79.506 unidades. Cobertura safety 2 aceitou 8.531, perdeu 3.844 e ordenou 41.482; safety 3 aceitou 8.550, perdeu 3.788 e ordenou 50.159; safety 4 aceitou 8.551, perdeu 3.782 e ordenou 58.450.

Safety 3 foi selecionado: sobre safety 2, adiciona 8.677 unidades ordenadas, mas melhora atendimento em 19 pedidos, reduz 56 unidades perdidas, reduz três pedidos ainda no prazo no cutoff, 326.729,73 dias de ruptura e 1.103 episódios. Safety 4 exige outras 8.291 unidades para um pedido aceito a mais e seis unidades perdidas a menos que safety 3. Em comparação ao bootstrap 65% sem cobertura, safety 3 reduz compras em 29.347 unidades e estoque final sem demanda em 5.565 unidades, ao custo de quatro pedidos aceitos a menos, 12 unidades perdidas adicionais e 432.753,40 dias adicionais de ruptura. Esses trade-offs foram registrados, sem maximizar apenas conversão.

Transferências foram mantidas disponíveis, mas desligadas no profile: a safety 2, a variante com elas movimentou 71 unidades em 63 itens e aceitou dois pedidos a menos, perdeu seis unidades a mais, acumulou 75.527,82 dias adicionais de ruptura e economizou 46 unidades de compra contra a mesma variante sem transferências. A configuração oficial M1 agora é bootstrap 65%, cobertura ligada, segurança 3×, transferências automáticas desligadas. As transferências operacionais fixas já previstas (12) permanecem independentes dessa flag. A configuração não altera as faixas de negócio e ainda precisará passar por calibração M2 e integração M4.

**Gate M1: PASS.** Matriz causal/determinística, conservação, memória incremental, fila e perfil foram verificados. A homologação do perfil não equivale ao gate de volume aceito 120k nem à persistência do dataset.

### Revalidação da Fase 3E.2c.4 na árvore atual (2026-10-09)

A suíte em memória foi repetida com o código atual: **116 passed, 6 skipped** em 22,60 s. Os seis skips são testes de integração PostgreSQL, desativados nessa execução. O smoke preservou o digest histórico `36640f5474a02c02168cb50f983327b2c9f181bd5d8cdaca50ab5513bf23874a`.

A matriz foi reproduzida com 10.000 intenções, seed `20261005`, sink de coleta em memória e 14 variantes. Todas compartilharam o digest de intenção `1c530bfda3d81c660cb194e77c4f5ed0f76d19630faf43686983515a8f87d217`; a soma inicial por SKU também coincidiu exatamente em todas as variantes, totalizando 11.949 unidades. O baseline desta execução foi 6.114 pedidos aceitos (5.622 completed, 463 cancelled, 29 confirmed no cutoff), 3.886 intenções físicas recusadas, 9.033 unidades físicas perdidas e 786 pedidos/993 unidades de backorder parcial vencidos. O resultado difere dos checkpoints anteriores (6.127 nesta subfase e 6.133 na subfase 3E.2c.3); a série de intenção atual tem digest próprio, e os números históricos foram preservados como reproduções de árvores anteriores, não atribuídos apenas à migration 003.

| Variante atual | Aceitos | Unidades físicas perdidas | Backorders parciais vencidos | Compras (unidades) | Saldo final sem demanda | Dias sem estoque | Episódios |
|---|---:|---:|---:|---:|---:|---:|---:|
| Controle | 6.114 | 9.033 | 786 / 993 | 75.055 | 46.279 | 3.678.330,88 | 7.212 |
| Bootstrap 65% lojas | 8.463 | 4.135 | 0 / 0 | 80.622 | 16.275 | 1.004.550,69 | 7.291 |
| Bootstrap 65% + cobertura, safety 2× | 8.439 | 4.200 | 0 / 0 | 41.942 | 8.483 | 1.816.725,17 | 10.278 |
| **Perfil atual: bootstrap 65% + cobertura, safety 3×** | **8.460** | **4.145** | **0 / 0** | **50.662** | **10.254** | **1.450.966,29** | **9.066** |
| Bootstrap 65% + cobertura, safety 4× | 8.463 | 4.136 | 0 / 0 | 59.229 | 11.969 | 1.246.530,94 | 8.365 |
| Bootstrap 65% + transferências, sem cobertura | 8.472 | 4.112 | 67 / 73 | 78.134 | 15.211 | 1.715.530,15 | 9.817 |
| Bootstrap 65% + cobertura, safety 2× + transferências | 8.439 | 4.202 | 0 / 0 | 41.890 | 8.469 | 1.823.384,65 | 10.305 |

O baseline reproduzido pela variante de controle (sem overrides) confirma o ganho de disponibilidade em relação à concentração atual. O bootstrap distribuído conserva 11.949 unidades e reduz unidades perdidas em 54,2%; por si só, porém, ordena 5.567 unidades a mais que o controle e mantém maior ruptura em duração do que o perfil com cobertura. O perfil atual safety 3, frente ao controle, aceita 2.346 pedidos a mais, perde 4.888 unidades físicas a menos, ordena 24.393 unidades a menos e reduz o saldo sem demanda em 36.025 unidades; os dias acumulados sem estoque caem 60,6%. Ele ainda apresenta 9.066 episódios, 1.854 acima do controle: a política reduz a duração total, mas fragmenta a ruptura em mais episódios. Frente ao safety 2, safety 3 ordena 8.720 unidades a mais e termina com 1.771 unidades adicionais sem demanda, para 21 pedidos a mais, 55 unidades perdidas a menos e 365.758,88 dias de ruptura a menos. Safety 4 reduz outros 204.435,35 dias e 701 episódios em comparação com safety 3, mas pede mais 8.567 unidades para apenas três pedidos aceitos adicionais. Esses trade-offs mantêm safety 3 como compromisso experimental; não são aprovação de calibração comercial.

As transferências são eventos físicos pareados com trânsito e saldo indisponível até `transfer_in`. Sem cobertura, a variante de transferências movimentou 13.263 unidades em 2.318 itens, teve até 27 transferências simultâneas e 8.744 dias-item em trânsito; portanto esse modo não foi selecionado para ativação automática. Com bootstrap/cobertura/safety 2×, as transferências moveram 58 unidades em 44 itens, mas não aumentaram pedidos aceitos e reduziram compras em apenas 52 unidades, enquanto aumentaram dias de ruptura em 6.659,48 e 27 episódios. O profile mantém a flag automática desligada; as 12 transferências estruturais preexistentes permanecem. O teste de determinismo por batch size cobre a variante combinada.

A medição incremental com sink descartável em 25.000 intenções comparou bootstrap 65% e o perfil safety 3, ambos com digest `0128e6ec0f0baf6fda5ac8305497a7afeaece4cb37fb013c2ffaea6429c64410`. A geração da master levou 34,47 s e reteve 65,94 MiB de heap Python corrente (pico 69,90 MiB). Bootstrap 65% levou 92,40 s, pico adicional 42,91 MiB, estado corrente adicional 5,02 MiB, aceitou 22.666 pedidos e terminou sem pedidos/transferências dinâmicos ativos (12 transferências estruturais estavam em trânsito no máximo). O perfil safety 3 levou 99,72 s, pico adicional 32,48 MiB, corrente adicional 4,73 MiB, aceitou 22.293 pedidos e terminou com zero estados ativos. Ambos respeitaram lote máximo de 5.000 e fila máxima de 11.496; backorders ativos máximos foram 23 e 81, respectivamente. Estas medições cobrem heap Python e a fixture de 25.000 intenções, não a memória total do processo nem a meta de 120.000 pedidos aceitos.

O teste PostgreSQL atual `test_postgresql_portfolio_supply_policy_with_transfers_rolls_back` passou em **585,65 s**. O runner verificou o servidor PostgreSQL 18, alvo/schema vazio, iniciou transação, carregou a fixture de 10.000 intenções com transferências, executou `ANALYZE`, validações SQL e casos negativos em savepoint, fez `ROLLBACK` e confirmou por conexão nova zero linhas nas 41 tabelas. Também confirmou transferências/itens/movimentos existentes na fixture, refund dividido, bloqueio de cancelamento acima do saldo elegível, limite de batch e zero IDs transacionais retidos. Não houve migration, COMMIT, carga persistente ou push.

**Revalidação: SUPPLY POLICY READY permanece válido para a subfase experimental 3E.2c.4.** A configuração escolhida continua com transferências automáticas desligadas devido ao resultado comparativo atual. A Fase 3E.2 permanece aberta; não executar calibração completa de 120.000 pedidos, persistência ou Power BI.

## M2 — execução descartável Portfolio 120k (2026-10-09)

O runner `benchmark_accepted_orders.py --orders 120000 --no-tracemalloc` concluiu em memória, sem conexão PostgreSQL. Gerou exatamente 120.000 pedidos aceitos. Planejou 214.604 intenções dentro do cap de 230.000, processou 176.292 e pulou 38.312 depois que suas quotas já estavam preenchidas. O digest das intenções foi `06774f74543a87de79c756e91cc1c2377ee1081898da798ddfd786d31bcfef6a`. Encaminhou 4.350.830 linhas em lotes descartados (batch máximo 5.000), com fila máxima de 11.496 eventos. Revalidação final: master 1,65 s, transações 105,58 s. Este ensaio não mediu heap.

| Período | Pedidos aceitos | Participação anual | Físico | E-commerce | Marketplaces |
|---|---:|---:|---:|---:|---:|
| 2023 | 24.000 | 20% | 54% | 29% | 17% |
| 2024 | 30.000 | 25% | 53% | 29% | 18% |
| 2025 | 36.000 | 30% | 52% | 29% | 19% |
| Jan–Set/2026 | 30.000 | 25% | 50% | 31% | 19% |

Os meses de janeiro tiveram média de 2.385,25 pedidos; dezembro, 2.771,33; novembro de 2023–2025, 3.373,33 versus média de 2.616,19 nos demais meses. Não há novembro de 2026. O mix físico/e-commerce/marketplace total ficou em 52,15/29,50/18,35%; vendas físicas anônimas foram 31,69%, sem clientes anônimos em canais digitais.

Estados: 116.305 `completed` (96,92%), 3.265 `cancelled` (2,72%) e 430 `confirmed` no cutoff (0,36%). Recorrência PF foi 42/38/16/4% nas faixas 1, 2–4, 5–10 e 11+; PJ, 25/45/25/5%. A frequência média PJ foi 4,0779 pedidos, acima de PF em 3,2446. Cartão/instantâneo/dinheiro/transferência foram 48,08/42,96/8,19/0,76%. Incidência de desconto: 38,74%; Black Friday: 54,69% versus 37,27% nos demais meses. Pedidos completed com devolução: 5,95%; ticket médio PJ/PF: 1,6944×; participação de receita de produto completed PJ: 19,12%.

Revalidação após regra aprovada pelo usuário: preservar o ledger original de fulfillment; deduzir do COGS analítico somente os custos históricos de retornos `sellable` reintegrados; preservar `non-sellable` como perda identificada, já incluída no COGS analítico, sem dedução adicional. No ensaio descartável, receita líquida de produto completed BRL 922.588.975,44, COGS original completed BRL 725.466.564,62, reversão sellable BRL 8.010.914,36, COGS analítico BRL 717.455.650,26 e perda non-sellable identificada BRL 12.296.704,23. A identidade `COGS original − reversão sellable = COGS analítico` fecha ao centavo; margem 22,23% está na banda 8–28%. Esses agregados não são ainda a auditoria lógica completa M3.

O estado e as contagens do perfil foram exercitados em streaming com agregados por pedido/item/fulfillment, sem guardar o conjunto completo de 4,35 milhões de linhas. Esta seção registra a calibração comercial/financeira M2; a auditoria lógica mais ampla M3 tem resultados parciais na seção seguinte. Nenhuma linha foi persistida e nenhum comando PostgreSQL foi executado nesta etapa.

## M3 — replay de estoque e classificação dos 120k (2026-10-09)

Reexecução final com `benchmark_accepted_orders.py --orders 120000 --stock-audit --no-tracemalloc`: exatamente 120.000 aceitos; comparação com plano retornou **PASS**, 0 divergências em todas as células mensais/canais; classificador de bandas retornou **0 critical fails, 0 distributional fails, 0 warnings**. Gerou 4.350.830 linhas para o sink descartável; lote máximo 5.000; fila máxima 11.496; duração 113,19 s e master 1,61 s.

O replay ordenado de 675.382 eventos reconstruiu quantidade física, reservas e custo médio ponderado desde o início do horizonte. Comparou o resultado às 13.837 posições finais (1.000 SKUs) e encontrou **0 divergências**. Abertura: 11.949 unidades; encerramento: 10.089 físicas e disponíveis; unidades disponíveis finais sem demanda: zero. A auditoria temporal registrou 7.342.024,68 dias-item sem estoque e 166.369 episódios. Os agregados financeiros do mesmo run permaneceram: receita BRL 922.588.975,44; COGS fulfillment original completed BRL 725.466.564,62; reversão `sellable` BRL 8.010.914,36; COGS analítico BRL 717.455.650,26; perda `non-sellable` incluída BRL 12.296.704,23; margem 22,23%.

Execução final com replay e auditor lógico habilitado, sob tracemalloc: 662,81 s (master 31,24 s), pico de heap Python 923,64 MiB e heap corrente 515,98 MiB. O working set observado em uma amostra chegou a pelo menos 2,35 GiB; não é um medidor de pico do processo. Sem tracemalloc, a mesma versão durou 113,19 s. A instrumentação de heap multiplica a duração e o sink agregador continua retendo índices por entidade.

**Auditoria lógica streaming:** nove gates agregados passaram sem divergências em 120.000 pedidos: totais de itens/descontos; fulfillment e cancelamentos; parcelas; conciliação de pagamentos/refunds; devoluções versus fulfillment original; lifecycle de eventos logísticos; vínculos e valores de refunds associados a cancelamentos; identidade entre COGS original, reversões `sellable` e COGS analítico com perda `non-sellable` preservada sem dupla contagem; pares de movimentos de transferência. O sink reteve agregados/índices de 120.000 pedidos, 241.637 itens, 237.742 fulfillments, 127.380 pagamentos e 7.129 return items, sem materializar todas as linhas.

**Contrato com SQL em fixture reduzida:** 300 pedidos do profile smoke foram gerados duas vezes com a mesma seed, uma vez no sink PostgreSQL dentro de transação e outra no sink descartável. As contagens coincidiram; os nove gates lógicos do sink passaram; os 39 checks SQL passaram com zero; cinco métricas financeiras do relatório streaming coincidiram com agregados de `11_cost_and_margin.sql`. A fixture usou PostgreSQL major 18, executou `ROLLBACK` e confirmou por nova conexão zero linhas nas 41 tabelas. Duração: 2,55 s.

O teste de determinismo entre batch sizes 73 e 127 passou comparando todos os registros coletados e contagens. **Gate M3: PASS.** A suíte registrada anteriormente passou 117 testes e 6 integrações PostgreSQL foram ignoradas naquela execução; nesta etapa foram executados o teste de determinismo, a fixture reduzida e o benchmark de 120k com e sem tracemalloc. Nenhum dado de negócio permaneceu persistido.

## M4 — fixtures PostgreSQL Portfolio rollback-only (2026-10-09)

As fixtures de escala foram executadas com `run_portfolio_rollback_fixture.py`, usando o profile Portfolio, PostgreSQL major 18, sink incremental oficial, uma transação e rollback explícito por execução. Não houve commit de dados.

| Fixture | Pedidos aceitos | Linhas transacionais temporárias | Invariantes SQL | Duração | Resultado |
|---|---:|---:|---:|---:|---|
| Portfolio 10k | 10.000 | 341.396 | 39, zero falhas | 466,99 s | PASS |
| Portfolio 50k | 50.000 | 1.454.848 | 39, zero falhas | 8.597,54 s | PASS |

A fixture 10k testou por savepoint a rejeição de cancelamento acima da quantidade elegível e refund dividido entre pagamentos. Os controles foram revertidos no savepoint e não alteraram a fixture. No lote de 50k foram observados 53.082 pagamentos, 81.993 parcelas, 3.022 refunds, 2.992 returns, 163.833 movimentos de estoque e 217.220 eventos logísticos. Não houve cancelamentos parciais gerados nesse lote, então essa contagem de cenário não foi usada como evidência do controle negativo, que foi exercitado separadamente em 10k.

Conciliação SQL de margem na fixture 50k: receita líquida de fulfillments completed BRL 385.445.464,80; COGS original de fulfillment BRL 302.895.054,13; reversão de custo histórico das devoluções `sellable` reintegradas BRL 3.313.558,21; COGS analítico BRL 299.581.495,92; perda `non-sellable` identificada BRL 5.076.322,25. A relação `COGS original − reversão sellable = COGS analítico` fecha ao centavo. As perdas `non-sellable` permanecem contidas no COGS analítico e não são deduzidas novamente. Os movimentos originais de fulfillment e retorno não foram alterados.

Os dois runners verificaram o rollback em conexão nova e confirmaram 41 tabelas vazias. Uma conferência independente adicional após o ensaio 50k também retornou 41 tabelas, zero tabelas não vazias e zero linhas. **Gate M4: PASS.** M5 segue aguardando autorização explícita para o primeiro `COMMIT` permanente do Portfolio; nenhuma persistência, baselines dependentes dos dados ou construção Power BI foi iniciada.

## M5 — preflight sem carga permanente (2026-10-09)

A conexão de preflight confirmou PostgreSQL 18, database `projeto_bi`, nove schemas, 41 tabelas, guard estrutural aprovado e zero linhas. `full --profile portfolio --plan` confirmou a meta de 120.000 pedidos aceitos, 219.009 linhas mestre estimadas e 2.200.000 linhas transacionais estimadas, com `database_connected=false`, `generated=false` e `persistent_write=false`.

Os 13 SQLs oficiais em `BASELINE_QUERIES` foram executados em transação rollback-only com a fixture smoke de 300 pedidos, junto com `collect_portfolio_metrics` e `validate_baseline_results`. As consultas retornaram entre 1 e 161 linhas; o controle cobriu exatamente 41 tabelas, os cinco critérios de reconciliação dos baselines passaram e o YTD retornou 2025 e 2026. Os 39 invariantes SQL passaram; rollback e nova conexão confirmaram 41 tabelas vazias. O teste de integração `test_postgresql_smoke_baselines_and_portfolio_metrics_reconcile_roll_back` passou. A suíte padrão ficou em 117 passed e 7 skips condicionais de integração; o teste novo foi executado separadamente com PostgreSQL autorizado.

O preflight descobriu e corrigiu a ambiguidade de `sales_order_id` no cálculo pré-COMMIT de perda de retorno em `collect_portfolio_metrics`; também corrigiu o rótulo do controle de baseline para 41 tabelas. Nenhum baseline definitivo foi materializado, nenhum dado Portfolio foi gerado/persistido nesta checagem e nenhum `--commit` foi executado. A autorização controlada para uma carga definitiva foi concedida posteriormente; ela permanece não consumida.

## M5 — diagnóstico final de desempenho e capacidade (2026-10-09)

### Reproduções e causa

As evidências M4 anteriores registravam 466,99 s em 10k (341.396 linhas transacionais) e 8.597,54 s em 50k (1.454.848 linhas). O tempo cresceu 18,4× para 5× pedidos, enquanto as validações nomeadas e `ANALYZE` permaneciam na casa de segundos. Não executei nova fixture 50k nem carga 120k nesta etapa.

Instrumentei o runner 10k existente sem mudar arquivos do projeto: medi geração, `consume`, `_write_stock`, `_many`, chamadas Psycopg por tabela/operação, `ANALYZE`, validações, processo Python/backend PostgreSQL, WAL e estatísticas de tabela antes/depois. A primeira execução do adaptador parou na verificação final por não suportar o context manager; seu `ROLLBACK` foi seguido por conferência em conexão nova (41 tabelas, 0 linhas). A execução instrumentada válida anterior à correção fechou em 374,08 s, com 341.396 linhas, 39 invariantes sem falha e confirmação de rollback.

| Componente 10k | Antes do batch write | Depois do batch write |
|---|---:|---:|
| Duração total | 374,08 s (466,99 s no log histórico M4) | 131,77 s |
| Geração transacional, incluindo sink | 351,28 s | 109,53 s |
| Python fora do `consume` | 5,93 s | 5,79 s |
| `consume` do sink | 345,34 s | 103,74 s |
| `_write_stock` (sobreposto a `consume`) | 176,99 s | 39,51 s |
| `_many` (sobreposto a `consume`) | 167,42 s | 94,74 s |
| `ANALYZE` de 41 tabelas | 1,77 s | 1,83 s |
| Validações SQL (39 invariantes) | 1,51 s | 1,45 s |
| Flushes / batch máximo | 1.412 / 5.000 | 1.412 / 5.000 |
| Round trips aproximados do sink | 155.527 | 53.024 |

Antes, o loop de estoque fazia 76.565 `UPDATE inventory.stock_positions` individuais (120,35 s) e 41.968 `INSERT inventory.stock_movements` individuais (40,78 s). A carga do PostgreSQL permaneceu CPU-bound em um backend serial: amostras de 74–102% de um núcleo; Python oscilou entre 0–34%; não apareceram wait events nem blockers. O throughput de I/O observado no processo PostgreSQL ficou abaixo de 1 MiB/s. Os tempos de validação e `ANALYZE` não explicam a lentidão não linear.

Também foi medido o trigger da migration 003: 20.205 `fulfillment_items` provocaram 20.206 updates contabilizados em `sales_order_items` (incluindo um controle negativo revertido por savepoint). O `executemany` de fulfillment items levou 32,40 s antes e 9,84 s depois do batch write. Esse trabalho é consequência da integridade linha a linha aprovada; não alterei nem desabilitei o trigger. A medição da fixture 10k não gerou cancelamentos parciais de negócio; portanto não atribuo à trigger de cancelamento a lentidão observada.

### Correção verificada

O sink agora calcula todos os movimentos na ordem causal original, envia `stock_movements` em lotes e persiste o estado final de cada posição uma vez por lote. O batch de movimentos mantém a ordenação das linhas, identities e timestamps. Para posição inexistente, o `INSERT ... RETURNING` entrega o estado inicial e evita um `SELECT ... FOR UPDATE` redundante; em conflito, o caminho continua fazendo o `SELECT ... FOR UPDATE`. A migration, constraints, dados, seed, regras comerciais e ordem do replay não foram alterados.

No 10k instrumentado após batch write, o número de chamadas client-side a `UPDATE stock_positions` caiu de 76.565 para 1.394 lotes; os 69.491 registros efetivamente atualizados foram agrupados. Os 41.968 movimentos passaram a 1.392 lotes. O tempo total caiu 64,8% contra o probe anterior sob a mesma instrumentação (374,08 → 131,77 s); contra o histórico 10k M4, 71,8%, com ressalva de variação/caches entre execuções. Custo observado por mil pedidos: 37,41 s no probe pré-correção e 13,18 s pós-correção. A otimização adicional do `RETURNING` foi validada no smoke de 300; não foi medida em novo 10k.

O WAL emitido pelo probe pós-correção foi 323.406.408 bytes, incluindo carga mestre e 10k. As estatísticas de tabela da execução rollback-only contabilizaram 69.491 updates em posições e 20.206 updates em itens; elas contam operações tentadas, mesmo revertidas. O sink terminou com zero IDs transacionais.

### Capacidade observada

- Windows: 15,87 GiB de RAM visível; livre variou 7,36–8,16 GiB no ensaio; Python ficou em aproximadamente 155 MiB de working set privado e o backend em cerca de 20 MiB privado. O pagefile tem 26 GiB alocados; uso observado durante o ensaio ~292 MiB, abaixo do pico histórico 2,5 GiB. Não houve pressão de memória.
- Volume D: 385,39 GiB livres de 476,94 GiB.
- PostgreSQL 18.6: database `projeto_bi` em 332 MB; diretório WAL com 37 arquivos / 620.756.992 bytes depois dos ensaios rollback-only; nenhuma sessão ativa ao fim. `max_wal_size=1 GiB` é um limite brando; extrapolando linearmente o WAL do 10k, uma transação 120k poderia produzir aproximadamente 3,9 GB e acionar checkpoints. O disco tem ampla margem, mas os checkpoints podem variar o tempo.
- `track_io_timing=off` e extensão `pg_stat_statements` ausente; não alterei configurações do servidor. A telemetria usada foi tempo de chamadas no cliente, contadores PostgreSQL/WAL/tabelas, WMI por processo e sessões/waits somente leitura. A taxa baixa de I/O não é uma medição direta de latência física do volume.

Uma projeção puramente linear de 10k otimizado resulta em aproximadamente 26 minutos para 120k, antes de validações posteriores ao COMMIT e baselines. Como os tempos M4 antigos cresceram de forma não linear, essa projeção não é garantia; o 50k/120k pós-correção não foi executado por limite. RAM e armazenamento atuais suportam a escala estimada; planeje janela de pelo menos uma hora e acompanhe o progresso da transação única.

### Validação e estado

O smoke de 300 pedidos passou em PostgreSQL 18.6, executou os 39 invariantes e terminou em `ROLLBACK`; a saída mostrou zero linhas restantes nas 41 tabelas. Uma consulta de conferência em conexão nova também encontrou 41 tabelas vazias e zero linhas. O digest de geração foi coberto pelo teste de regressão. A suíte completa passou: 117 testes e 7 integrações condicionais ignoradas sem a flag PostgreSQL. Após a alteração final de `INSERT ... RETURNING`, 5 testes direcionados e o smoke de 300 foram repetidos e passaram. `git diff --check` passou.

Não executei migration, `--commit`, fixture acima de 10k, carga 120k, Power BI, reset ou limpeza do banco. A autorização controlada do usuário para um único `COMMIT` continua não consumida. **M5 PERFORMANCE READY**; o dataset persistido e os baselines finais seguem pendentes.
