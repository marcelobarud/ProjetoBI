# Qualidade e validação futura — Fase 3A

Este plano será implementado junto ao gerador/carga nas fases futuras. Não há SQL ou validação executada neste documento. A migration atual mantém PK/FK/CHECK/UNIQUE ativos; a validação da geração deverá exercitar o schema real.

## 1. Integridade estrutural

- Garantir que todos os FKs resolvem, inclusive compostos que exigem pedido/item/fulfillment correspondentes.
- Não criar IDs lógicos duplicados: códigos de loja, funcionário, cliente, produto/SKU, fornecedor, pedido/compra, canal, carrier, pagamento e devolução devem obedecer às UNIQUEs e índices parciais.
- Endereço operacional de loja deve usar CEP de oito dígitos, UF brasileira e `country_code = 'BR'`; `city` é estruturada, região é derivada da UF e não se copia endereço do cliente para a loja.
- Confirmar perfil correto para cada `customer_type`; CPF/CNPJ, se presentes, têm dígitos/checksum válidos, unicidade e formato; não usar dados reais.
- Confirmar que `specifications` é nulo ou JSON object, com chave snake_case e template compatível com família/categoria.
- Confirmar valores de status, método, destino e tipo contra CHECKs existentes. `unit_of_measure` recebe apenas `unit` até nova decisão.
- Categorias formam árvore sem ciclo, não somente sem autorreferência direta.

## 2. Tempo e causalidade

Para cada relação, testar limites e ordenação, respeitando latência positiva:

- Cadastro de cliente e endereço <= pedido; loja aberta <= venda na loja; produto criado/disponível <= venda; preço aplicável cobre o instante de venda.
- Se `sales_orders.customer_address_id` for informado, o endereço pertence ao mesmo `customer_id`; snapshots do pedido representam o endereço escolhido. Pedido anônimo não referencia endereço cadastral de outro cliente.
- Funcionário contratado, lotado na função/local e não desligado na data de atuação <= atribuição a venda, compra, evento ou ajuste.
- Ordem de compra <= recebimento; quantidade recebida acumulada <= comprada.
- Pedido <= pagamento, reserva e fulfillment; fulfillment item e movimento seguem a sequência de atendimento.
- Evento `prepared` precede despacho; `delivered` ocorre depois de `dispatched`; `pickup_ready` precede `picked_up`.
- Atendimento/saída <= solicitação de devolução <= decisão/recebimento <= eventual reembolso.
- Nenhum evento comercial após 2026-09-30. Somente compras/recebimentos de bootstrap podem anteceder 2023, entre 2022-11-01 e 2022-12-31. Datas cadastrais permitidas antes do bootstrap devem ser explicitadas; não há dependência do relógio atual.
- Verificar timestamps `TIMESTAMPTZ` como instantes e dimensões diárias com calendário `America/Sao_Paulo`.

## 3. Reconciliação comercial e financeira

- Cabeçalho: `subtotal_amount` concilia com quantidade × preço dos itens; `discount_amount` concilia com alocações positivas em `applied_discounts`; `total_amount` concilia com subtotal − desconto + frete e nunca é negativo.
- Não reconstruir preço histórico a partir do preço atual. Desconto total por linha não supera valor elegível da linha.
- Cancelamento não entra como receita reconhecida; tentativa `declined`/`failed`/`cancelled` não é captura/valor recebido.
- Parcelas conciliam exatamente com a operação de pagamento, inclusive divisão de centavos; pagamentos aplicáveis reconciliam com o valor elegível do pedido, respeitando split/estado.
- Refund concluído <= valor capturado elegível e <= saldo reembolsável após outros refunds; relacionamentos pedido/pagamento/devolução apontam para a mesma operação comercial.
- Baseline futuro deve definir explicitamente receita bruta, desconto, líquida, frete, cancelamento e refund antes de comparar Power BI. Evitar duplicação de receita ao juntar itens a múltiplos pagamentos/fulfillments.

## 4. Estoque e custo

- Para cada movimento, direção de `quantity_delta` corresponde a `movement_type`; movimentos `receipt`, `fulfillment`, `customer_return`, `transfer_in` e `transfer_out` têm custo unitário preenchido conforme CHECK.
- `on_hand_quantity >= 0`, `reserved_quantity >= 0`, `reserved_quantity <= on_hand_quantity` e `available_quantity = on_hand_quantity - reserved_quantity`.
- Saldo inicial zero ou inexistente até receber movimento `receipt`; saldo corrente por SKU/local concilia com soma de movimentos físicos e regra de reserva.
- Reserva ativa existe apenas com disponibilidade, e consumo/liberação atualiza estoque e reserva na mesma transação. Nunca reservar mais que saldo disponível.
- `stock_positions.average_unit_cost` após entradas acompanha média ponderada decimal; saídas usam a média vigente sem recalculá-la.
- Movimento `fulfillment` é negativo, vinculado ao `fulfillment_item`; custo realizado usa `SUM(ABS(quantity_delta) * unit_cost)` e não coluna de custo comercial.
- Transferência tem saída/entrada pareadas para o mesmo `stock_transfer_item`, custo de saída preservado na entrada e sem saldo no destino antes do recebimento.
- Para retorno `sellable`, custo usado é média ponderada das saídas `fulfillment` da origem indicada. Quarentena/reparo/descarte não aumentam saldo vendável.
- Ajustes são raros, têm motivo permitido e responsável; nunca compensam erro de geração sem trilha.

## 5. Compras, atendimento, devolução

- `accepted_quantity + rejected_quantity = quantity_received`; recebimentos acumulados não superam pedido comprado.
- `fulfilled_quantity <= quantity_allocated`; soma atendida por item não supera quantity vendida; atendimentos cancelados não geram saída física.
- `return_items` usa `source_fulfillment_item_id` do mesmo pedido/item; quantidades solicitadas/aprovadas/recebidas obedecem os CHECKs e cumulativamente não superam atendido dessa origem.
- Destino/condição do item retornado e `received_at` preenchidos quando recebido; só `sellable` pode gerar entrada de retorno disponível.
- Cada evento comercial gera movimentos/financeiro uma vez; operações parciais não duplicam entrada, saída ou reembolso.

## 6. Distribuições e adequação analítica

Calcular resultados por profile, ano/mês, canal, PF/PJ, categoria, loja, SKU, meio de pagamento e estado. Comparar com as bandas de [business-distributions.md](business-distributions.md): sazonalidade, crescimento comparável YTD, mix, anonimato, recorrência, long-tail, descontos, margem, devoluções e concentração por loja/vendedor. Medir unidades e pedidos separadamente.

Fora da banda, registrar a métrica e o seed/config envolvidos, localizar regra causal e ajustar distribuição/configuração com nova execução determinística; não editar registros gerados para forçar insight esperado. Registrar versão da configuração, raiz e sub-seeds, versão do gerador/schema e totais de controle.

## 7. SQL baselines para Power BI

Após carga aprovada, salvar consultas e resultados versionados sem credenciais para:

- pedidos distintos, unidades vendidas/atendidas, receita bruta, descontos, receita líquida, frete cobrado;
- custo realizado, lucro e margem bruta segundo regra de cancelamentos/refunds;
- ticket médio com denominador explícito;
- clientes identificados, clientes recorrentes e anônimos físicos;
- devoluções por solicitações, unidades e valor; refunds por estado;
- canal, categoria, loja, vendedor e período mensal/anual;
- estoque atual, disponível, custo médio, movimentos e cobertura de reposição.

Verificar que consultas não multiplicam fatos ao juntar relações 1:N. O baseline SQL e o modelo semântico deverão aplicar a mesma definição; DAX fica fora da Fase 3A.

## 8. Segurança e integridade da base

- Validar explicitamente `current_database() = 'projeto_bi'` antes de qualquer futura carga ou reset.
- Geração normal não apaga dados existentes. Reset exige comando separado, explícito, confirmação e ordem inversa das FKs; nunca usa `DROP DATABASE`.
- Nunca desabilitar FK/CHECK/UNIQUE, nunca imprimir `.env`, nunca colocar secrets na configuração/relatório e nunca usar dados externos de pessoas reais.
- Nesta Fase 3A nenhum comando de escrita PostgreSQL foi executado e nenhuma linha foi inserida.
