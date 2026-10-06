# Implementação do gerador — Fases 3B a 3D

## Escopo entregue

A Fase 3B implementa o pacote Python em `data-generator/` para configuração determinística, geração e validação de dados mestres. As Fases 3C e 3D completam o fluxo de compras e recebimentos, vendas, estoque, pagamentos, parcelas, logística, transferências, devoluções e refunds no profile `smoke`. A carga no PostgreSQL é exclusivamente rollback-only. Os profiles `portfolio` e `large` têm configurações preparadas, mas não foram gerados ou carregados.

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

`--dry-run` não abre conexão. `--load-smoke` é restrito ao profile smoke e verifica database `projeto_bi`, PostgreSQL major 18, 9 schemas, 40 tabelas, estrutura aprovada e zero linhas em todas as tabelas antes de inserir. A escrita é parametrizada e ocorre em uma única transação; validações SQL conferem contagens, relações financeiras e movimentos do ledger. O comando executa `ROLLBACK` explícito e abre nova conexão para verificar que as 40 tabelas continuam vazias. O guard interrompe a carga se encontrar dados ou estrutura inesperados.

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
