# Implementação do gerador — Fases 3B a 3D

## Escopo entregue

A implementação atual cobre o ecossistema transacional e a política experimental de abastecimento da Fase 3E. O Portfolio foi auditado em modo descartável para 120.000 pedidos e validado em fixtures PostgreSQL rollback-only de 10.000 e 50.000 pedidos. M0–M4 passaram e M6 documental concluiu a preparação analítica sem criar modelo Power BI; a estrutura contém 9 schemas e 41 tabelas (migrations 001–003) e permanece sem dados operacionais persistidos. M5 está `PERFORMANCE READY`; a autorização controlada para uma única persistência foi concedida, mas o dataset ainda não foi carregado. As seções históricas preservam os gates e resultados de cada fase; o status integrado está em `docs/PROJECT_COMPLETION_PLAN.md`.

O banco operacional continua sendo a fonte de verdade para tipos, constraints e relações. O gerador usa chaves lógicas para resolver os IDs identity retornados pelo PostgreSQL; não pressupõe IDs técnicos fixos. A ordem de dependências está em [dependency-order.md](dependency-order.md).

## Ambiente local

Requer Python 3.11 ou superior. O ambiente validado nesta fase é Python 3.13.15, instalado em `data-generator/.venv/`, ignorado pelo Git. No PowerShell, a partir da raiz do projeto:

```powershell
py -3.13 -m venv .\data-generator\.venv
Set-Location .\data-generator
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
Set-Location ..
```

As dependências de execução são `psycopg[binary]` e Faker; pytest é dependência de desenvolvimento. Não há ORM, Pandas ou NumPy. A configuração não contém credenciais. Para integração local, o pacote carrega o `.env` da raiz como fallback para variáveis de processo `POSTGRES_*`, sem imprimir valores. O arquivo `.env` real permanece ignorado e fora do Git.

## Configuração e reprodutibilidade

- `config/generator.toml` contém versão de configuração, versão do gerador, seed raiz `20261005`, janela comercial, janela de bootstrap e `America/Sao_Paulo`.
- Os arquivos `config/profiles/{smoke,portfolio,large}.toml` descrevem volumes; os perfis maiores incluem dez endereços inteiramente fictícios.
- Dez sub-seeds de domínio são derivados por SHA-256 de forma estável. Cada domínio recebe seu próprio `random.Random` e instância Faker, sem compartilhar estado aleatório; intenções de venda usam um sub-seed independente nos profiles maiores.
- Datas e timestamps são explícitos e os valores monetários são `Decimal`. CPF/CNPJ passam por checksum e são gerados deterministicamente; contatos de e-mail usam `example.com`.

## Dados mestres e segurança da carga

O profile smoke implementa as 19 tabelas mestre, na ordem de dependências declarada: lojas, pessoas/funções/atribuições, clientes/perfis/contatos/endereços, categorias/marcas/produtos/fornecedores/preços, locais de estoque, meios de pagamento, transportadoras e canais. Validadores Python verificam volumes, chaves únicas, referências, árvore de categorias, vigências não sobrepostas, perfis PF/PJ, documentos fiscais, endereços, unidade `unit`, objeto JSONB e especificações por família.

`--dry-run` não abre conexão. `--load-smoke` é restrito ao profile smoke e verifica database `projeto_bi`, PostgreSQL major 18, 9 schemas, 41 tabelas, estrutura aprovada e zero linhas em todas as tabelas antes de inserir. A escrita é parametrizada e ocorre em uma única transação; validações SQL conferem contagens, relações financeiras e movimentos do ledger. O comando executa `ROLLBACK` explícito e abre nova conexão para verificar que as 41 tabelas continuam vazias. O guard interrompe a carga se encontrar dados ou estrutura inesperados.

As validações SQL de escala usam nomes estáveis, registram início/fim, duração, resultado e linhas retornadas e definem `statement_timeout` local de 120 segundos dentro da transação. As verificações antes agrupadas em bundles escalares foram separadas por regra para isolar tempos e falhas sem retirar condições. Para diagnóstico pontual, `PROJECTBI_EXPLAIN_VALIDATION` e `PROJECTBI_EXPLAIN_ANALYZE_VALIDATION` selecionam pelo nome uma consulta para exibir `EXPLAIN` ou `EXPLAIN ANALYZE, BUFFERS`; essas opções são locais ao processo e não alteram configuração global do servidor.

No profile Portfolio, as tabelas mestre são analisadas depois da carga mestre e antes da validação mestre; após inserir as transações, `ANALYZE` é executado nas 41 tabelas operacionais antes das validações pré-COMMIT. Isso atualiza estatísticas do planner dentro da própria transação. A operação não altera schema nem índices e não usa `VACUUM` ou configurações globais.

## Comandos

Na raiz do projeto:

```powershell
.\data-generator\.venv\Scripts\python.exe -m projectbi_generator.cli master --profile smoke --dry-run
.\data-generator\.venv\Scripts\python.exe -m pytest .\data-generator
$env:PROJECTBI_RUN_INTEGRATION = '1'
.\data-generator\.venv\Scripts\python.exe -m pytest .\data-generator
```

Os testes de integração requerem a database local aprovada, `.env` configurado e vazia. Eles executam somente cargas smoke com rollback. Para verificar novamente o conjunto completo, use `python -m pytest` com `PROJECTBI_RUN_INTEGRATION=1` definido e diretório atual `data-generator`.

## Núcleo transacional — Fases 3C e 3D

A Fase 3C acrescenta uma engine determinística orientada a eventos para compras, recebimentos, reposição, pedidos de venda, descontos, reservas, cancelamentos, fulfillment, movimentos e posições de estoque. Eventos usam instante, prioridade e chave lógica estável para preservar causalidade e reprodutibilidade. Quantias monetárias usam `Decimal`; rateios de desconto preservam centavos, e custo de estoque usa média móvel com escala de oito casas.

O profile smoke gera 300 pedidos e 630 linhas, cobre os quatro canais existentes, pedidos físicos anônimos, pedidos cancelados, descontos e fulfillment dividido. O fluxo inclui recebimentos parciais e quantidades rejeitadas, reabastecimento durante a janela comercial e reserva/liberação/consumo do estoque. O custo realizado é calculado pelos movimentos de saída; a posição final reconcilia unidades recebidas, unidades expedidas e saldo. Preços e fornecedores são validados contra as dimensões mestre e suas vigências/associações.

A Fase 3D amplia a engine sem alterar os registros-base da Fase 3C. Os pagamentos conciliam exatamente com o total dos pedidos; recusas e falhas têm retry bem-sucedido, pagamentos divididos e parcelamento cobrem meios elegíveis. Eventos registram a sequência de despacho/entrega e preparação/liberação/retirada. Transferências criam movimentos pareados com o mesmo custo médio; devoluções referenciam itens de fulfillment, preservam o custo histórico e só reintegram ao estoque itens classificados como vendáveis. Refunds ficam limitados às capturas correspondentes.

O smoke `full` valida em memória a reconciliação financeira e física, cutoff e referências. A integração persiste temporariamente as 21 tabelas transacionais, valida também no PostgreSQL e faz `ROLLBACK` explícito; a conexão posterior confirmou zero linhas nas 40 tabelas. Não requer migration. O escopo não inclui persistência permanente, execução dos perfis `portfolio`/`large` nem Power BI.

## Limites da Fase 3B

Rotina de reset, carga portfolio/large, persistência permanente e integração com Power BI continuam fora do escopo. Nenhuma linha de negócio smoke permanece persistida.

## Fase 3E.1 — refatoração de escala (em andamento)

Os profiles declaram alvo de pedidos, lote e estimativas. A master engine lê os volumes para os três profiles e passou pelas validações de portfolio e large. `full --profile portfolio --plan` e `full --profile large --plan` validam configuração sem gerar dados ou conectar ao banco.

A engine transacional recebe o alvo configurado. Foram adicionados lookups indexados por SKU/chaves lógicas, contadores incrementais por pedido, replay cronológico de custo após devolução vendável, testes de profiles e helper de lotes usado por escritas sem retorno no repositório. O smoke preserva os resultados agregados da Fase 3D.

O gate de escala da Fase 3E.1 **ainda não foi concluído**. A subfase 3E.1a implementou streaming de geração para o núcleo 3C, mas a extensão 3D continua no caminho legado, e a integração de persistência multibatch, os inserts com `RETURNING` e o ciclo de vida dos mapas de IDs ainda não foram validados nesse caminho. Os benchmarks legados e incremental estão em `scalability-review.md` e `validation-report.md`. Não executar portfolio integral nem carga persistente até concluir os gates restantes.

### Subfase 3E.1a — streaming do núcleo 3C

O caminho incremental do núcleo 3C reutiliza a engine causal e envia registros completos por `TransactionBatchEmitter` a um `TransactionSink`; não cria `TransactionData` nem retém listas com o histórico. O caminho legado permanece disponível para smoke e para a extensão 3D, que não foi refatorada. O estado mutável fica restrito a pedidos/compras/reservas/fulfillments ativos e é removido ao completar os eventos correspondentes. Posições finais permanecem em memória por produto/local. O teste smoke comparou as saídas 3C do novo caminho ao legado e confirmou digest independente do tamanho do lote.

O benchmark `incremental_3c_sink` mediu 1.000, 5.000 e 10.000 pedidos com `CountingDiscardingSink`; o pico total foi 71,8 MiB em todos os tamanhos (master: 65,9 MiB; transação acima da master: 5,9 MiB). Veja a tabela em `validation-report.md`. Isso valida descarte do histórico no caminho 3C, não valida inserção PostgreSQL multibatch nem a extensão 3D. A Fase 3E.1 continua em andamento.

### Subfase 3E.1b — incremental completion

A extensão 3D agora usa o mesmo event loop cronológico, emitter e sink do núcleo 3C no caminho incremental. Pagamentos/parcelas são derivados ao criar o pedido, eventos logísticos ao criar cada fulfillment, transferências após a demanda 3C se estabilizar, e devoluções/refunds são agendados no marco de elegibilidade/recebimento. Retornos vendáveis atualizam posição e custo médio dentro do evento, antes de qualquer fulfillment posterior; esse caminho não chama `_replay_extended_stock` nem `extend_transactions`.

O smoke incremental compara todas as 21 tabelas lógicas ao oracle legado por registros e digest canônico e executa os validadores transacionais e 3D completos sobre `CollectingSink`. A saída preserva 314 pagamentos, 587 parcelas, 590 eventos logísticos, 2 transferências, 8 devoluções, 6 refunds, saldo 222 e custo realizado BRL 369830.61051434. O benchmark full com `CountingDiscardingSink` em 1k/5k/10k registrou picos de 73,8/74,3/75,1 MiB e fila máxima 1.007 em todos os tamanhos (vs. 2.209/10.873/21.903 no baseline legado 3D); consulte `validation-report.md`.

Para manter duas regras globais específicas do oracle smoke, o runner faz uma prévia full incremental com sink descartável e retém apenas o índice do pedido com método de cartão e até oito chaves mínimas de return elegíveis. Nenhuma linha histórica fica retida; a geração de saída percorre novamente todo o fluxo causal. Profiles portfolio/large não usam essa prévia.

A subfase 3E.1b conclui o caminho incremental de geração full. Persistência PostgreSQL em lotes, `RETURNING`, lifecycle de IDs e validação multibatch com ROLLBACK permanecem para 3E.1c; por isso a Fase 3E.1 segue aberta.

A continuação anterior adicionou o contrato `TransactionSink`, `TransactionBatchEmitter` e sinks de coleta e contagem/descarte, além de digest lógico sem IDs técnicos. Naquele momento, o contrato ainda não participava da geração. A integração ao event loop 3C e o resultado de benchmark da subfase atual estão descritos em **Subfase 3E.1a** acima.

## Subfase 3E.1c — PostgreSQL incremental sink

`PostgreSQLTransactionSink` implementa o mesmo protocolo `TransactionSink` e recebe a conexão já aberta pelo runner. Não abre conexões, não faz commit e não faz rollback. O runner valida database `projeto_bi`, PostgreSQL major 18, os nove schemas, 40 tabelas, os guards da migration 002 e zero linhas antes de iniciar uma única transação. Tanto smoke quanto fixture multibatch terminam em `ROLLBACK`; uma conexão nova confirma as 40 tabelas vazias.

Os inserts usam `executemany` com parâmetros Psycopg 3 e lotes limitados. Para identities, `executemany(..., returning=True)` é consumido com `fetchone()`/`nextset()` por entrada, preservando a ordem de associação entre chave lógica e ID retornado. O fluxo completo validou pais e filhos com identities. O sink organiza compras/recebimentos, vendas/itens, pagamentos/parcelas, logística, transferências, devoluções/refunds e ledger em ordem FK-safe. Updates causais de estado (compras, pedidos, devoluções e itens) são eventos explícitos do batch. O estoque segue a ordem causal, `SELECT ... FOR UPDATE` e locks de duas locations de transferência em ordem numérica determinística. `stock_positions` representa posição corrente; o ledger permanece em `stock_movements` e não se grava `available_quantity`.

IDs mestre são mantidos durante a execução. O `TransientTransactionIdRegistry` retém apenas IDs transacionais com referências abertas e recebe release hints da engine: purchase orders/itens até o recebimento; receipt items até seu movimento; pedido e seus itens, pagamentos e referências de fulfillment até o fechamento causal de pagamentos/fulfillments/devoluções; transfer item até o movimento de entrada; return e return item até decisão/recebimento/refund final. IDs de parcelas, reservas e refunds são descartados após o insert. No smoke, pico de 28 IDs e final zero. Na fixture portfolio de 1.000 pedidos, pico de 626 e final zero; os picos por entidade estão em `validation-report.md`.

O smoke inseriu 4.837 linhas relacionais em 484 flushes (2.743 com `RETURNING` e 2.094 sem), recebeu 5.725 operações do emitter incluindo 923 updates e limitou o maior batch a 36 linhas. As validações SQL conferiram contagens das 21 tabelas transacionais, custo realizado e invariantes financeiras/estoque. A regressão de geração manteve o digest lógico `36640f5474a02c02168cb50f983327b2c9f181bd5d8cdaca50ab5513bf23874a` e os valores smoke descritos em `validation-report.md`.

A integração multibatch usou o profile portfolio real para 219.009 linhas mestre e override interno para 1.000 pedidos (não é um quarto profile). Inseriu 18.720 linhas transacionais em 1.128 flushes; batch máximo 1.006; 4.827 updates; pico de 626 IDs; final zero; duração 64,33 s. Não houve commit e todas as linhas foram revertidas. Uma verificação in-memory de lifecycle com 5.000 pedidos também passou, sem conexão ao banco, com pico de 82 IDs para janela ativa de 41 pedidos.

Os três testes PostgreSQL anteriores agora cobrem master smoke, núcleo 3C incremental e full 3C+3D incremental; foi adicionado o multibatch rollback portfolio. Com `PROJECTBI_RUN_INTEGRATION=1`, todos executam sem skip. `full --load-smoke` e `transactions --load-smoke` usam o novo sink; o repository legado permanece para oracle e comparação. Este sink é o caminho oficial da persistência incremental na Fase 3E.2. Nenhuma migration/schema foi alterada.

**Fase 3E.1 concluída.** Portfolio completo e profile large não foram executados nem persistidos. Nenhuma linha de negócio permaneceu no banco. Power BI e Fase 3E.2 não foram iniciados.

### Fase 3E.2c.1 — lifecycle de estoque/backorders (em andamento)

O profile Portfolio declara espera máxima de estoque de 14 dias corridos no fuso configurado. Vendas físicas sem disponibilidade local suficiente não viram pedidos; intenções são contabilizadas como não convertidas. Pedidos digitais mantêm os saldos pendentes em uma fila FIFO indexada por SKU/local e recebem fulfillment incremental após `goods_receipt`, `transfer_in` ou retorno vendável, usando o custo vigente no instante causal. Retornos não vendáveis não aumentam o estoque disponível. A conclusão do pedido aguarda o saldo atendido e o encerramento de todos os fulfillments.

Pedidos sem qualquer unidade expedida podem expirar e ser cancelados após 14 dias, com refund do valor capturado ligado ao pedido/pagamento e sem devolução fictícia. O validador financeiro aceita a captura integralmente reembolsada para esse cancelamento; refunds continuam limitados ao valor capturado. O modelo atual só oferece cancelamento do pedido inteiro, sem quantidade cancelada por item. Portanto pedidos parcialmente expedidos que excedem o prazo bloqueiam o lifecycle: não são cancelados nem marcados como concluídos artificialmente. Não foi criada migration.

Na auditoria incremental de 10.000 intenções, a execução parou no primeiro gate final porque 704 pedidos parcialmente atendidos ultrapassaram os 14 dias. Foram convertidas em pedidos 6.133 intenções; 3.867 intenções físicas foram recusadas por falta de estoque local. Entre os pedidos emitidos, o diagnóstico antes do bloqueio estimou 5.036 concluídos, 363 cancelados e 734 confirmados abertos (704 parciais expirados e 30 ainda dentro do prazo no cutoff, com deadlines posteriores ao horizonte). O fluxo atendeu 774 unidades em 745 linhas de backorder após reposição, recebeu 75.315 unidades e registrou 16 solicitações de reposição fora do cutoff, somando 136 unidades. Esses dados mostram a retomada causal, mas não passam o gate: reposição atual não resolve saldo parcial dentro do prazo e a baixa conversão física também exige revisão posterior de abastecimento/perfil.

O smoke mantém o digest aprovado. Testes determinísticos cobrem FIFO, atendimento parcial da fila, remoção, reconciliação do refund de cancelamento sem expedição e a regressão existente. Não foi executada integração PostgreSQL porque a geração é bloqueada por cancelamentos parciais sem representação no schema. A Fase 3E.2c.1 e a 3E.2 geral permanecem abertas; não iniciar as calibrações seguintes até decisão estrutural sobre o saldo parcialmente atendido.

### Subfase 3E.2c.2 — auditoria de abastecimento

O event loop recebeu instrumentação de auditoria ativada apenas por override em memória (`stock_audit`). Ela agrega demanda, atendimento, perda física, recebimentos, lead time, backorders, saldo final e intervalos sem disponibilidade por ano/canal, loja, local, SKU e categoria. A configuração Portfolio versionada permanece desligada. O helper `_location_balanced_bootstrap_plan` distribui deterministicamente o total inteiro entre lojas e armazéns; testes verificam conservação e estabilidade. Um override por SKU viabiliza comparação diagnóstica sem alterar o TOML oficial.

No cenário de 10.000 intenções, o experimento manteve o estoque central por SKU e redistribuiu a localização inicial. As perdas físicas caíram de 8.962 para 4.480 unidades e os parciais vencidos de 728 para 5, mas o gate de lifecycle continua bloqueado. Os recebimentos e saldos também mudam por resposta causal das reposições; não constituem calibração ou baseline. Os resultados e limitações estão em `validation-report.md`. Nenhum schema, dado persistido ou profile oficial foi alterado; a decisão estrutural permanece pendente.

### Fase 3E.2c.3 — cancelamento parcial de pedidos (2026-10-07)

A migration incremental 003 registra cancelamentos por item e snapshots BRL de quantidade, desconto, valor líquido e frete aplicável. Contadores no item reconciliam unidades atendidas mais canceladas com a quantidade original. Triggers mantêm os contadores quando fulfillment ou cancelamento é inserido, alterado ou removido; constraints impedem excesso e refunds ligados a cancelamento não podem também referenciar devolução. Refunds por cancelamento são divididos deterministicamente entre capturas, limitados ao saldo ainda reembolsável. O vencimento de estoque após 14 dias cancela apenas a quantidade pendente; frete só é reembolsado no cancelamento total sem fulfillment. Unidades canceladas não geram returns nem movimentos de estoque.

A carga e os validadores usam o novo sink para persistir cancelamentos antes dos refunds e conservar as referências até o fechamento do pedido. O smoke de geração conserva o digest histórico. A validação Portfolio de 10.000 intenções passou em memória e no PostgreSQL sob transação com rollback; o teste incluiu pagamentos divididos, limite de quantidade e reconciliação de valores. A validação estrutural atual usa 41 tabelas nas migrations 001–003; `ANALYZE` roda nas tabelas operacionais dentro da transação de teste antes do replay/validações. A conexão nova confirmou todas vazias depois do rollback.

**Resultado: PARTIAL CANCELLATION READY.** A decisão e a implementação do cancelamento parcial da 3E.2c.3 estão validadas. Abastecimento/calibração do Portfolio, escala 120k e Power BI não foram iniciados por este resultado; a Fase 3E.2 global continua aberta. Nenhum commit ou push foi feito.

### Fase 3E.2c.4 — abastecimento e transferências (2026-10-08)

O gerador Portfolio oferece, por configuração de execução, três opções opt-in: distribuir o estoque de bootstrap por papel do local (`bootstrap_location_balance`), estimar reposição por SKU/local (`coverage_replenishment_enabled`) e acionar transferências de abastecimento (`supply_transfer_enabled`). Os defaults do perfil não ativam esses overrides; a carga Portfolio continua fora do escopo. O rateio primeiro separa o total inteiro de cada SKU entre lojas e armazéns e depois distribui cada parcela uniformemente dentro do papel, com desempate SHA-256 estável. SKU de fixtures especiais continua inalterado. O total de abertura é conservado exatamente por SKU e, portanto, globalmente.

A taxa de demanda usa somente unidades observadas até a decisão em janela móvel de 90 dias e um prior explícito de cold start. O prior divide o volume configurado de intenções, média determinística de 2,1 itens, participação comercial estimada (52% físico/48% digital), SKUs e locais operacionais ativos. A combinação usa shrinkage equivalente a 60 dias de prior; observações recentes ganham peso gradualmente. Demanda física recusada é uma observação de intenção perdida, separada das unidades efetivamente atendidas; não cria pedido de venda e não é contada novamente como fulfillment. Compras já decididas não são recalculadas. Para profiles não-smoke, os SKU/quantidades sorteados para cada intenção usam um sub-seed determinístico por índice; a indisponibilidade de uma intenção não desloca a sequência aleatória das intenções seguintes. O smoke preserva a sequência histórica.

Para reposição, `disponível = físico − reservado`; o inbound confirmado soma compras e transferências em trânsito; obrigações em backorder são subtraídas uma única vez. O alvo da variante candidata no experimento é `ceil(taxa diária × (lead time fornecedor + 14 dias de revisão) + segurança)`. Segurança base é 2 unidades para notebook, desktop e gráficos e 1 unidade nas demais famílias; o candidato de menor estoque dobrou esses valores. Assim, `quantidade = max(0, alvo − (disponível + inbound confirmado − backorders))`, limitada também à demanda explicitamente solicitada. Reservas já estão fora de disponível e não são subtraídas outra vez. A reposição antiga permanece disponível como controle.

Transferências de abastecimento seguem uma direção única armazém → loja. Uma transferência usa os registros existentes, agenda expedição após 8 horas e entrada 2–5 dias depois, determinística por seed/SKU/origem/destino. Até a entrada, o saldo não fica disponível no destino e a saída programada reduz a disponibilidade de origem. O excedente doador desconta reservas, saídas em trânsito, backorders, demanda esperada durante o trânsito e segurança; o multiplicador de segurança da variante de cobertura também protege o doador. Inbound já foi abatido da posição de estoque uma vez, antes de calcular a quantidade adicional a transferir. Requisições duplicadas no mesmo par ativo são bloqueadas. A mercadoria transferida conserva custo médio da origem e movimentos `transfer_out`/`transfer_in` pareados; a transferência não atende retroativamente a intenção física que a disparou. Se não houver excedente ou janela compatível, procurement segue pelo fornecedor.

Uma comparação da Fase 3E.2c.4 encontrou e corrigiu dois defeitos habilitados pela reposição mais rápida: o fulfillment consumia todas as reservas ativas de uma linha/local em vez da reserva associada a ele; e o evento de reserva FIFO despertada por devolução podia ser ordenado antes da entrada no replay quando os timestamps coincidiam. Cada item de fulfillment agora retém as chaves exatas das reservas que consome, e o ledger ordena a reserva despertada depois das entradas/devoluções e antes do fulfillment.

`max_stock_wait_days = 14` permanece no perfil Portfolio. A fila FIFO e o lifecycle de cancelamento/refund da migration 003 continuam ativos; a variante combinada com segurança dobrada encerrou 2 intenções digitais ainda em `confirmed` no cutoff e não teve backorder parcial vencido neste conjunto de 10 mil intenções. Nenhum saldo foi convertido em venda fictícia. Cenários com vencimento continuam cobertos pelos testes de cancelamento existentes e pela validação SQL/savepoint da integração.

A matriz controlada e os números comparativos desta subfase estão em `validation-report.md`. Não houve alteração de schema, migration, README, carga persistente ou commit. O resultado é limitado à fixture causal de 10 mil intenções; não autoriza gerar 120 mil intenções, calibrar meta final ou iniciar Power BI.

Na integração final da candidata, o primeiro ensaio identificou uma referência transitória mantida para um item de recebimento totalmente rejeitado, que não produz movimento de estoque. O sink agora libera esse ID sem alterar os registros do banco. A repetição PostgreSQL concluiu com sucesso: `BEGIN`, carga de 10 mil intenções, `ANALYZE` e validações nomeadas, `ROLLBACK` e confirmação em nova conexão de zero linhas nas 41 tabelas. Nenhuma migration ou carga persistente foi executada.

### Marco M1 — homologação técnica do abastecimento (2026-10-08)

Após a matriz controlada e as medições incrementais, o profile Portfolio passa a selecionar bootstrap com participação-alvo de 65% para lojas, reposição por cobertura, multiplicador de segurança 3× e transferências automáticas da política desligadas. O bootstrap resultante fica em 64,5% de unidades nas lojas (diferença por arredondamento e fixtures preservadas). `coverage_safety_units=3` multiplica a segurança base por família (6 unidades em notebooks/desktops/gráficos e 3 nas demais). As 12 transferências estruturais já previstas no profile continuam sendo geradas; a flag desligada afeta somente novas transferências automáticas de abastecimento.

A seleção foi feita sobre a mesma seed e digest de intenções nas variantes. Em 10 mil intenções, safety 3 aceitou 8.550 pedidos, perdeu 3.788 unidades físicas, teve 2 pedidos digitais ainda dentro do prazo no cutoff e ordenou 50.159 unidades. Safety 2 aceitou 8.531, perdeu 3.844, teve 5 no cutoff e ordenou 41.482 unidades. O incremento de 8.677 unidades de compra para safety 3 reduziu em 326.729,73 os dias acumulados sem estoque e em 1.103 os episódios de ruptura; safety 3 foi escolhido como compromisso de atendimento e capital. Safety 4 custou mais 8.291 unidades de compra sobre safety 3 para apenas um pedido aceito adicional e seis unidades perdidas a menos, por isso não foi escolhido.

Na comparação isolada com safety 2, as transferências automáticas moveram 71 unidades em 63 itens, mas resultaram em dois pedidos aceitos a menos, seis unidades perdidas a mais, 75.527,82 dias acumulados de ruptura adicionais e apenas 46 unidades a menos de compra confirmada. Portanto permanecem desligadas por padrão; o mecanismo real continua disponível como override experimental. Bootstrap 65% isolado teve quatro pedidos aceitos a mais e 12 unidades perdidas a menos que safety 3, porém ordenou 29.347 unidades a mais, terminou com 5.565 unidades a mais sem demanda local e teve 432.753,40 dias adicionais sem estoque. O trade-off sustenta a escolha técnica, mas não substitui a calibração comercial de M2.

### M2 — benchmark descartável e regra de margem (2026-10-09)

O benchmark do profile Portfolio atingiu exatamente 120.000 pedidos aceitos, com 214.604 intenções planejadas, 176.292 processadas e 38.312 puladas após preenchimento de quotas. Encaminhou 4.350.830 linhas a sink descartável, batch máximo 5.000 e fila máxima 11.496. A reexecução final do gate M3 com classificador, replay de estoque e auditoria lógica cruzada durou 113,19 s (master 1,61 s), sem tracemalloc. Nenhuma conexão ou gravação PostgreSQL foi feita. Quotas anuais/canais, sazonalidade, recorrência PF/PJ, mix de pagamentos, descontos e estados permaneceram nos valores aprovados descritos em `validation-report.md`.

Regra aprovada para margem: os movimentos originais de fulfillment conservam o COGS integral; a receita analítica desconta todas as unidades recebidas em devolução; o COGS analítico deduz somente o custo dos retornos `sellable` reintegrados, pela movimentação histórica `customer_return`. Destinos `quarantine`, `repair` e `discard` mantêm seu custo no COGS analítico e são mostrados como perda pelo custo histórico ponderado da linha de fulfillment de origem. A perda é subconjunto do COGS mantido e não é deduzida novamente. No ensaio, receita líquida BRL 922.588.975,44, COGS original de fulfillments BRL 725.466.564,62, reversão sellable BRL 8.010.914,36, COGS analítico BRL 717.455.650,26, perda non-sellable identificada BRL 12.296.704,23 e margem bruta analítica 22,23%. A identidade `COGS original − reversão sellable = COGS analítico` fecha ao centavo; o resultado financeiro permanece dentro da banda 8–28%.

M2 foi aprovado pelas quotas, bandas comerciais e reconciliação financeira documentadas. M3 segue em andamento: a auditoria de estoque reproduz quantidade, reservas e custo médio, mas o sink ainda não verifica de ponta a ponta todos os cruzamentos de pagamentos/refunds, parcelas, cancelamentos, devoluções e eventos logísticos. Nada foi commitado ou publicado.

### M3 — escala, replay de estoque e auditoria distributiva (2026-10-09)

A execução final de 120.000 aceitos comparou cada célula mensal/canal ao plano e obteve **PASS, zero divergências**. O classificador de bandas de Portfolio registrou **zero falhas críticas, zero falhas distribucionais e zero avisos**. O replay causal independente percorreu 675.382 eventos e reconciliou quantidade, reservas e custo médio final de todas as 13.837 posições (1.000 SKUs), sem divergências. O estado inicial foi 11.949 unidades e o final 10.089 físicas/disponíveis; nenhum saldo disponível final ficou sem demanda. Ruptura agregada: 7.342.024,68 dias-item e 166.369 episódios.

Sem tracemalloc, a geração e auditoria duraram 113,19 s (master 1,61 s), com máximo de 5.000 linhas por lote e fila de 11.496 eventos. Com tracemalloc, a mesma versão levou 663,10 s, registrou pico Python de 741,96 MiB e corrente de 325,95 MiB; o working set amostrado chegou a cerca de 1,69 GiB. O rastreamento de heap aumentou bastante a duração e mede alocações Python, não todo o processo.

O sink descartável agora executa nove gates lógicos em agregados por entidade, sem reter as 4,35 milhões de linhas: totais de itens/descontos; quantidades atendidas/canceladas; parcelas; pagamentos/refunds; devoluções contra fulfillment; eventos logísticos de fulfillments completos; vínculos e valores de refunds de cancelamento; identidade do COGS analítico sem dupla contagem da perda não vendável; pares de movimentos de transferência. Os nove passaram no benchmark final de 120k, com zero divergências. O sink reteve índices/agregados de 120.000 pedidos, 241.637 itens, 237.742 linhas de fulfillment, 127.380 pagamentos e 7.129 itens de devolução.

O auditor foi comparado com o PostgreSQL usando fixture reduzida de 300 pedidos: contagens iguais, nove gates lógicos e 39 checks SQL sem divergências; os cinco agregados financeiros também coincidiram com `11_cost_and_margin.sql`. `ROLLBACK` e nova conexão confirmaram 41 tabelas vazias. O teste de determinismo entre batch sizes passou. O M3 foi concluído. Naquele checkpoint, M4 estava planejado para executar as fixtures de 10k e 50k aceitos; o resultado final consta na seção M4 abaixo.

A medição final com tracemalloc, já incluindo o auditor, levou 662,81 s, com heap Python de pico 923,64 MiB e corrente 515,98 MiB. O working set observado em amostra chegou a pelo menos 2,35 GiB; não representa o pico medido do processo. Sem tracemalloc, a duração correspondente foi 113,19 s. Nenhum dado operacional permaneceu persistido.

M1 está aprovado apenas para habilitar essa configuração técnica reproduzível. O gate não homologa quotas anuais/canais nem volume aceito e não autoriza geração ou persistência do Portfolio completo. A configuração é coberta por teste unitário. A integração PostgreSQL pendente para a configuração homologada será exercitada como parte do M4, sem COMMIT.

### Revalidação da Fase 3E.2c.4 na árvore atual (2026-10-09)

A reexecução atual confirmou a suíte unitária (116 passed, 6 skips de integração), smoke inalterado e 14 variantes de abastecimento com o mesmo digest de intenções e conservação exata das 11.949 unidades iniciais por SKU. O baseline atual reproduziu 6.114 pedidos aceitos; o perfil versionado (bootstrap 65%, cobertura, safety 3× e transferências automáticas desligadas) aceitou 8.460, sem backorders parciais vencidos. A duração total dos episódios de falta caiu 60,6% frente ao controle, embora o número de episódios subisse de 7.212 para 9.066. A comparação safety 2×/3×/4× documenta o trade-off entre compras, rupturas e estoque ocioso em `validation-report.md`.

O digest das intenções atual é diferente dos checkpoints preservados porque esta árvore deriva SKU/quantidade de cada intenção por índice; por isso o controle reproduzido nesta revalidação (6.114) não deve ser misturado aos baselines históricos 6.127/6.133. A definição de 13 pedidos parcialmente atendidos e concluídos após resolução, também citada historicamente, não equivale a backorders parciais vencidos. A subfase atual não atribui a diferença histórica apenas à migration 003.

Transferências automáticas continuam disponíveis e causais, mas desligadas no profile. Sem cobertura, a combinação de bootstrap e transferências criou 2.318 itens/13.263 unidades transferidas sem benefício proporcional; com cobertura e safety 2×, transferiu 58 unidades em 44 itens, sem aumentar pedidos aceitos. A integração PostgreSQL atual, executada com transfers habilitados em fixture de 10.000 intenções, passou por `BEGIN`, carga, `ANALYZE`, validações SQL, savepoints negativos, `ROLLBACK` e confirmação em conexão nova de 41 tabelas vazias. Não foi criada migration, não houve COMMIT ou persistência e a configuração não homologa a calibração final do Portfolio.

### M4 — homologação PostgreSQL rollback-only (2026-10-09)

As fixtures Portfolio de 10.000 e 50.000 pedidos aceitos passaram no PostgreSQL 18 usando o sink incremental oficial, uma transação por fixture, `ANALYZE`, 39 invariantes SQL e `ROLLBACK` explícito. A fixture 10k levou 466,99 s e validou controles negativos para cancelamento acima do saldo elegível e refund dividido. A fixture 50k levou 8.597,54 s e inseriu temporariamente 1.454.848 linhas transacionais; os validadores financeiros preservaram o custo original de fulfillment, reverteram apenas o custo histórico de returns `sellable` reintegrados e identificaram perdas `non-sellable` dentro do COGS analítico sem dupla contagem.

Cada fixture verificou 41 tabelas vazias após rollback. Uma confirmação adicional em nova conexão, depois da fixture de 50k, encontrou zero linhas nas 41 tabelas. O M4 está concluído; o M5 permanece aguardando autorização explícita para a primeira carga permanente. Não executar um `COMMIT` por inferência deste resultado.

No preflight de M5, os 13 SQLs oficiais de baseline foram executados numa fixture smoke de 300 pedidos rollback-only junto com `collect_portfolio_metrics` e `validate_baseline_results`. Todos retornaram resultados; as 41 contagens de controle, margem/COGS, estornos e anos YTD reconciliaram. A execução encontrou uma junção ambígua de `sales_order_id` no agregador pré-COMMIT de perdas de devolução; a ligação foi explicitada pela chave do return item e a regressão foi coberta por teste de integração. `git diff --check` e a suíte unitária foram reexecutados; nenhum dado permaneceu persistido. Os 13 arquivos SQL ainda serão materializados e executados após a carga M5 autorizada.

### M5 — batching do writer de estoque

O diagnóstico instrumentado identificou chamadas por evento em `_write_stock` como a principal causa da duração PostgreSQL: 76.565 updates individuais de `stock_positions` e 41.968 inserts individuais de `stock_movements` em 10k. A saída causal passou a ser calculada em memória na ordem original, com movimentos inseridos em lotes e cada posição persistida uma vez por lote. A criação inicial de posição aproveita `INSERT ... RETURNING` para evitar uma busca redundante; conflitos mantêm `SELECT ... FOR UPDATE`.

Após a correção, a fixture Portfolio 10k passou 39 invariantes e terminou em `ROLLBACK`, com 41 tabelas vazias conferidas por conexão nova. O tempo instrumentado caiu de 374,08 s para 131,77 s (−64,8%); `ANALYZE` e validações SQL permaneceram ~1,8 s e ~1,5 s. Smoke PostgreSQL de 300, regressão de digest e suíte completa (117 passed, 7 skips condicionais) passaram. Nenhuma migration, regra de negócio ou dado persistente foi alterado. A correção e os limites de capacidade estão detalhados em `validation-report.md`; a fixture 50k não foi repetida após o batching.

### M5 — correção do lifecycle de IDs (2026-10-09)

A primeira carga definitiva abortou antes do `COMMIT` por uma reserva ainda referenciar um pedido cujo ID transitório já havia sido liberado. A reprodução completa pelo sink PostgreSQL encontrou também fronteiras de lote para descontos/itens, movimentos/itens de fulfillment e timestamps de parcelas, fulfillments e devoluções. As correções mantêm o ID do pedido até a publicação das reservas, publicam cada dependência antes do seu consumidor e conservam timestamps até o fechamento do registro pai. Nenhuma regra comercial ou estrutura do banco mudou.

O script `data-generator/scripts/validate_120k_id_lifecycle.py` executa o gerador e o sink PostgreSQL oficiais com adaptador em memória que atribui identidades e estados de posição sem persistir linhas. No seed `20261005`, os 120.000 pedidos aceitos geraram 4.673.957 linhas através de 1.546 flushes; o sink resolveu 4.900.758 referências de IDs, liberou 120.000 IDs de pedido e terminou com zero IDs, movimentos, estados ou grupos de referência pendentes. Pico de 11.614 IDs transitórios, lote máximo 5.000 e 95,07 s; working set de pico 228 MiB. Esse ensaio confirma lifecycle e limites de memória do processo, mas não mede escrita, WAL ou duração PostgreSQL.

A regressão histórica de digest, o smoke PostgreSQL com 13 baselines e 39 invariantes, a fixture PostgreSQL de 10.000 pedidos com 39 invariantes/`ROLLBACK` e a suíte unitária (119 passed, 7 integrações ignoradas por padrão) passaram. Na fixture 10k, o seed não gerou cancelamentos naturais; os controles negativos de limite e refund dividido foram exercitados dentro da transação. O banco ficou vazio após a conferência em conexão nova. O checkpoint de correção foi preparado localmente; a segunda e última tentativa de `--commit` foi autorizada e ainda não começou.
