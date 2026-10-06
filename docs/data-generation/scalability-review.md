# Auditoria de escalabilidade do gerador

## Estado auditado

Base `ae8dc2f` (`feat: completa ecossistema transacional sintetico`), sem mudanças locais. A suíte inicial PostgreSQL habilitada passou com 56 testes; a integração smoke terminou em `ROLLBACK`.

## Achados

| Severidade | Área | Evidência e impacto |
|---|---|---|
| BLOCKER | Profile / CLI | `cli.py`, `generators/master.py`, `generators/transactions.py`, `generators/completion.py` e `validation/transactions.py` rejeitam profile diferente de `smoke`. A master também fixa papéis/categorias e contagens incompatíveis com os TOMLs maiores. |
| BLOCKER | Memória da engine | `TransactionData` armazena listas para pedidos, itens, eventos, movimentos, pagamentos, fulfillments, devoluções e trace até o horizonte inteiro. `generate_transactions` e `extend_transactions` retornam o histórico completo. Não há consumidor incremental nem mecanismo para liberar registros. |
| BLOCKER | Persistência e IDs | `load_transaction_data` insere linha a linha com `RETURNING` e mantém mapas de IDs para cada relação transacional; dependências retardadas (movimentos, devoluções e pagamentos) exigem histórico global. Não existe contrato de escrita por lote/consumidor. |
| HIGH | Buscas quadráticas | A persistência usa `next(...)` sobre compras, recebimentos, pedidos, produtos, fulfillments, pagamentos e devoluções dentro de loops de filhos. A extensão busca fulfillment por item repetidamente; o fulfillment reconta itens e movimentos anteriores. Cresce com o histórico. |
| HIGH | Eventos futuros | `EventQueue` guarda heap completo e conjunto de chaves; `extend_transactions` ainda drena a fila para outra lista `queued_events`. Históricos de estado/trace e ordenações completas também são materializados. |
| HIGH | Validação | Validadores criam mapas e listas duplicados sobre todas as tabelas e alguns filtram `stock_movements` para cada receipt/fulfillment. Isso é apropriado ao smoke, mas excede a estratégia de memória incremental planejada. |
| MEDIUM | Volumes mestre | O carregador confere 19 volumes, mas geradores fixam 5 funções e 15 categorias; locais extras, contatos/endereço, vínculos fornecedor e preços não são derivados integralmente dos volumes do profile. |
| MEDIUM | Batching mestre | `repositories/master_data.py` usa `executemany` para parte das dimensões, porém constrói listas completas de valores e resultados; lotes não são uma abstração compartilhada e algumas tabelas fazem inserts individuais. |
| LOW | Configuração de escala | Os perfis não declaram total de pedidos nem limites de lote. A quantidade de pedidos está como constante global `ORDER_COUNT = 300`. |

## Direção de refatoração

Manter uma única engine determinística, trocar constantes por configuração do profile, substituir buscas repetidas por índices criados uma vez e definir consumidor de lotes na fronteira da persistência. O loop de eventos precisa entregar fatos causalmente completos em janela temporal limitada; eventos futuros devem permanecer em fila mínima, e agregados necessários para validação/retorno devem substituir referências ao histórico inteiro. O smoke deve preservar seed e saída atuais.

O gate desta fase inclui demonstração de limite de memória e benchmark acima do smoke. Até esses itens e os validadores/repositórios estarem integrados ao fluxo incremental, a capacidade de persistir portfolio permanece bloqueada.

## Resultado parcial da Fase 3E.1

### Corrigido nesta retomada

- Profiles passaram a declarar `sales_orders`, `estimated_order_items`, `estimated_transaction_rows`, `batch_size`, mistura PF/PJ, multiperíodos de preço, transferências, devoluções e split payments.
- Master generation agora aceita smoke/portfolio/large conforme volumes; os perfis maiores foram gerados e validados, inclusive períodos de preço com vigências não sobrepostas.
- CLI oferece `full --profile {smoke,portfolio,large} --plan`, que apenas carrega/valida configuração e informa volumes, sem gerar nem conectar.
- A engine usa `config.sales_order_target`; buscas por SKU e item em fulfillment/repository/conclusão foram substituídas por mapas, contadores por pedido e agregados de custo. O repository agrupa em batches parte dos inserts sem retorno.
- O replay de custo atualiza movimentos de fulfillments posteriores a reentrada sellable, preservando a ordem temporal para profiles maiores. Smoke e agregados financeiros originais continuam iguais.
- Validadores transacionais não constroem listas auxiliares de chaves e usam índices para movimentos de receipt/fulfillment; checks de cronologia percorrem pares adjacentes.

### Ainda bloqueia a conclusão

- A estrutura `TransactionData` continua composta por listas de todo o histórico; `event_trace`, fila futura, state events, sales items, payments e demais entidades não são liberados por janela/lote.
- O benchmark de 5.000 pedidos ainda reteve **53.800 objetos/linhas transacionais** e atingiu **95,1 MiB** sob `tracemalloc`; o caminho de persistência não foi exercitado nessa escala.
- Os inserts transacionais que precisam obter IDs seguem majoritariamente um `execute(... RETURNING ...)` por linha. Mapas de IDs para pedidos, itens e operações também crescem com o dataset.
- A etapa 3D de conclusão deriva listas completas de candidatos a devolução e agendas pagamentos/eventos para todo o horizonte. Não há callback/iterator de fatos causais para flush e liberação.

Não rodar 120.000 pedidos até trocar a retenção integral por um desenho incremental demonstrável. A Fase 3E.1 não está concluída e não deve receber commit de conclusão.

## Continuação — contrato de consumo e instrumentação

O estado inicial desta continuação preservava o conjunto local não commitado sobre a base `ae8dc2f`; nenhuma alteração anterior foi descartada. Foi introduzido `TransactionBatchEmitter` com limite compartilhado por quantidade de linhas, protocolo `TransactionSink`, `CollectingSink` para fixtures pequenas e `CountingDiscardingSink` com contagem e SHA-256 lógico por tabela. O digest ignora IDs de banco porque o contrato recebe registros lógicos antes da resolução pelo repositório.

Também foram adicionados contadores de eventos inseridos, processados e máximo simultaneamente pendente em `EventQueue`, incluindo o maior tamanho observado nas filas 3C e 3D. Os contadores tornam visível a pressão e a emissão diária reduziu o acúmulo de intenções 3C; ainda não reduzem a retenção dos registros transacionais nem a agenda global 3D.

Correção nesta continuação: nos profiles `portfolio`/`large`, as intenções de venda agora são planejadas com sub-seed independente e inseridas cronologicamente na fila por dia comercial (buffer temporário de um dia); a fila não recebe antecipadamente uma entrada para cada pedido. O profile `smoke` continua consumindo o stream aleatório histórico e conserva os agregados de regressão. O plano de compras bootstrap ainda é enfileirado no início e sua quantidade acompanha os produtos mestre.

Os testes novos verificam limite do emitter, descarte via sink contador, retenção explícita via coletor, digest invariável para batch sizes diferentes e remoção de eventos processados. Um diagnóstico portfolio com override interno de 1.000 pedidos validou 2.100 itens/15.644 linhas materializadas, 77,9 MiB de pico (66,1 MiB após master), fila 3C máxima de 1.007 eventos e fila 3D máxima de 2.209. Outro diagnóstico com 5.000 pedidos validou 10.500 itens/53.511 linhas, 95,1 MiB, 1.007 eventos máximos em 3C e 10.873 em 3D. Com 10.000 pedidos: 21.000 itens/101.985 linhas, 119,8 MiB, 1.007 em 3C e 21.903 em 3D. Os picos cresceram 41,9 MiB de 1k para 10k, enquanto o pico da fila 3D ficou quase 10x; o custo fixo observado após a master foi 66,1 MiB. O benchmark identifica explicitamente `legacy_materialize_then_validate`; não é prova de streaming.

No estado anterior à subfase 3E.1a, o helper de sink ainda não estava ligado à engine. `TransactionData`, extensão 3D, candidatos a devolução e mapas de ID continuavam globais. A seção 3E.1a abaixo atualiza o resultado para o núcleo 3C; os gates de validação PostgreSQL e lifecycle de IDs ainda permanecem não demonstrados. Não executar integração pelo caminho legado como se ela validasse o sink novo.

## Fase 3E.1a — streaming do núcleo transacional 3C

A continuação implementa um caminho incremental separado para o núcleo 3C usando o mesmo event loop causal que o caminho legado. O modo legado continua retornando `TransactionData` para smoke e para a extensão 3D. O modo incremental publica linhas 3C pelo `TransactionBatchEmitter` ao serem causalmente completas e usa sinks, sem acumular as coleções históricas. Estados mutáveis ficam em mapas de registros ativos até a conclusão; posições finais ficam limitadas ao mapa produto/local. O trace não é retido nesse modo. A extensão 3D continua no caminho legado.

O teste smoke incremental comparou as coleções 3C registro a registro com o resultado legado, além de validar digest invariável para batch sizes diferentes. Os resultados mantidos incluem 300 pedidos/630 itens, 49 compras, 50 recebimentos, 193 fulfillments/227 itens, 457 unidades recebidas, 238 expedidas, saldo final 219, custo realizado BRL 369830.61051434, 8 cancelamentos e 23 pedidos com fulfillment dividido.

O benchmark específico desta subfase executa somente o fluxo 3C incremental com `CountingDiscardingSink`, uma master compartilhada por 1k/5k/10k e batch size definido pelo profile portfolio. As métricas finais de execução estão registradas em `validation-report.md` e distinguem a retenção temporária de estado ativo do histórico legado materializado. Esse resultado não valida o caminho 3D, persistência PostgreSQL, integração do repository, lifecycle de IDs de banco, nem o portfolio completo.

**Fase 3E.1 continua aberta.** O streaming 3C avança um blocker de memória, mas não integra persistência nem validação PostgreSQL multibatch. A Fase 3D permanece legada; não executar o portfolio completo ou carga persistente neste escopo.

## Fase 3E.1b — incremental completion

A extensão 3D foi acoplada ao mesmo event loop e `TransactionBatchEmitter` do núcleo 3C. Pagamentos e parcelas são criados no pedido; eventos logísticos ao criar o fulfillment; transferências ao concluir a demanda 3C; elegibilidade de devolução no evento de fulfillment; customer return, recebimento e refund nos respectivos instantes causais. O caminho não chama `extend_transactions`, não materializa `TransactionData`, não conserva `event_trace` nem executa replay global de estoque. A validação smoke completa ainda usa os validadores existentes sobre `CollectingSink`.

### Benchmark incremental full

Profile base portfolio com override interno de pedidos, master gerada uma vez (219.009 linhas, baseline ~65,9 MiB). O pipeline 3C+3D usou `CountingDiscardingSink`, batch size 5.000 e nenhuma conexão. A master/validação levou 74,32 s sob `tracemalloc` nesta execução.

| Pedidos | Linhas emitidas | Pico | Acima da master | Max buffer | Flushes | Pedidos ativos pico | Pagamentos ativos pico | Transferências ativas pico | Elegibilidades de return pico | Eventos futuros pico | Duração transacional | Digest |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| 1.000 | 20.497 | 73,8 MiB | 7,9 MiB | 1.006 | 1.108 | 2 | 4 | 4 | 2 | 1.007 | 10,83 s | `e19641ab54f0be54744cd71a56ddd15476701c7f2bef92f204b4241f77d8b44a` |
| 5.000 | 73.631 | 74,3 MiB | 8,2 MiB | 1.021 | 1.389 | 5 | 8 | 4 | 4 | 1.007 | 35,16 s | `7bd1199247b275e2a044d82332152245e99275db83feebb38145c202e30ed8b9` |
| 10.000 | 141.640 | 75,1 MiB | 9,0 MiB | 1.055 | 1.388 | 7 | 13 | 4 | 7 | 1.007 | 61,99 s | `bf3133b679f2c7705e1e4ac914b75b83fdad139d8fc5ada53bb330594b47dfd5` |

Não restaram estados ativos. A fila futura máxima ficou em 1.007 nos três tamanhos; o baseline legado 3D era 2.209/10.873/21.903 em 1k/5k/10k. Os picos incrementais crescem 1,3 MiB de 1k para 10k, e max buffer permanece perto de mil linhas apesar do batch size 5.000 (flush diário). A elegibilidade de devolução cresce de 2 para 7 porque mantém somente os candidatos com futuro elegível dentro da janela; isso não acompanha o volume total de pedidos. Transferências são quatro por tamanho neste benchmark porque esse é o número de candidatos de rebalanceamento encontrado na master/ledger.

### Equivalência e limites

No smoke, os registros de todas as 21 tabelas transacionais, inclusive estoque final, foram comparados como multiconjunto de registros e por digest canônico ordenado; coincidiram integralmente com `extend_transactions` legado. As contagens e valores principais estão no relatório de validação.

Para manter o resultado smoke legado exato, seu runner obtém antes, por uma execução full incremental com sink descartável, o índice do pagamento de cartão de menor total e até o piso configurado de candidatos de return; só esses poucos valores são retidos. A execução de saída também percorre 3C+3D numa fila única. Profiles maiores e benchmarks dispensam a prévia e geram numa execução.

**Fase 3E.1b concluída quanto ao caminho de geração incremental 3C+3D. A Fase 3E.1 geral continua aberta:** permanecem PostgreSQLTransactionSink, INSERT/RETURNING em lote, lifecycle de IDs técnicos e integração multibatch com ROLLBACK. O benchmark não representa carga no banco nem executa portfolio integral.

## Fase 3E.1c — PostgreSQL incremental sink

O caminho oficial para persistência é `TransactionBatchEmitter → PostgreSQLTransactionSink → PostgreSQL`, sem `TransactionData` nem repository transacional legado. O sink recebe a conexão/transaction do runner, não faz commit/rollback e não reconecta. Os 21 conjuntos relacionais são escritos em ordem FK-safe; estado mutable é enviado como evento de update separado. Inserts sem ID e inserts com identity usam `executemany` parametrizado em lotes. `RETURNING` usa Psycopg 3 `executemany(returning=True)` e avança pelos result sets com `nextset()` para preservar cada par chave lógica/ID. Movimentos seguem causalidade temporal e posições correntes são lock/update/upsert; transferências bloqueiam as duas locations em ordem determinística.

O registro mestre mantém os IDs das dimensões por toda a execução. O registry transacional separado usa release hints da engine e termina zerado. Relações de compras ficam até todos os recebimentos, IDs de receipt até os respectivos movimentos, pedidos/itens/pagamentos/fulfillments até a janela de retorno/refund fechar, transfer item até transfer-in e return/item até refund/recebimento final. IDs de parcelas, reservas/refunds e outros sem filhos futuros são soltos após o insert. No smoke: pico total 28. Na fixture 1k: pico 626, contra 16.323 linhas relacionais inseridas; não acompanha o histórico.

### Evidência PostgreSQL rollback-only

| Execução | Linhas inseridas | Updates | Flushes | Batch máximo | IDs transacionais pico/final | Duração | Rollback / nova conexão |
|---|---:|---:|---:|---:|---:|---:|---|
| Smoke full, 300 pedidos | 4.837 | 923 | 484 | 36 | 28 / 0 | ~3,5 s | explícito / 40 tabelas vazias |
| Portfolio master + override interno 1k | 18.720 | 4.827 | 1.128 | 1.006 | 626 / 0 | 64,33 s | explícito / 40 tabelas vazias |

A execução smoke confirmou 300/630 pedidos/itens, 314 pagamentos, 587 parcelas, 193/227 fulfillments/itens, 590 eventos, 2/2 transferências/itens, 8/8 devoluções/itens, 6 refunds e 284 movimentos. Validações SQL também conferiram as relações de pagamentos, descontos, cutoff, movimentos/posições, custo médio, pares de transferência, origem/quantidade de devoluções e limites de refunds. O digest de regressão full smoke segue `36640f5474a02c02168cb50f983327b2c9f181bd5d8cdaca50ab5513bf23874a`, com captured/refunds/net/custo de BRL 2.791.128,94 / 18.420,97 / 2.772.707,97 / 369830.61051434.

Na fixture de escala foram inseridas 18.720 linhas transacionais e 4.827 updates sobre a master portfolio completa (219.009 linhas), mas tudo em uma transação revertida; o override de 1.000 pedidos não é um novo profile. O sink registrou batch máximo de 1.006, pico de 626 IDs e zero ao final. Um teste in-memory adicional processou lifecycle de 5.000 pedidos com pico de 82 IDs para 41 pedidos ativos. A master portfolio teve nomes de marca duplicados em sua primeira tentativa de insert; a geração agora resolve colisões deterministicamente e o validador verifica a unicidade exigida por `uq_brands_name`. Nenhuma alteração estrutural foi feita.

`PROJECTBI_RUN_INTEGRATION=1` habilita os quatro testes PostgreSQL: master, core incremental, full incremental smoke e multibatch portfolio. A execução multibatch confirmou `ROLLBACK` e zero linhas numa conexão nova. Os planos portfolio (219.009 master, 120k orders, 264k items, 2.2M transacionais estimadas) e large (430.505, 240k, 528k, 4.4M) passaram sem conexão/escrita. Smoke dry-run e digest passaram. **Fase 3E.1 concluída; Fase 3E.2 ainda não iniciada.** Nenhum portfolio completo, carga persistente, large, baselines SQL ou Power BI foi executado.
