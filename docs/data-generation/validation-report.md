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
