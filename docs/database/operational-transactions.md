# Regras transacionais operacionais

Este documento orienta a futura camada operacional. A migration inicial cria as estruturas e constraints locais, mas não inclui triggers, procedures ou lógica de aplicação.

## Estoque, locking e atomicidade

Cada alteração de saldo ou custo de um produto em um local deve ocorrer dentro de uma transação. Para posição existente, localizar `inventory.stock_positions` por `(product_id, stock_location_id)` e bloquear a linha com row-level lock (`SELECT ... FOR UPDATE`) antes de calcular qualquer novo valor. A aplicação deve serializar também a criação concorrente da primeira posição, protegida por `UNIQUE (product_id, stock_location_id)`. O usuário do banco precisa de privilégios para ler/escrever as tabelas e usar as sequences identity correspondentes.

Atualizar atomicamente a posição e o ledger, incluindo a reserva e a origem operacional quando aplicáveis. Uma falha em qualquer etapa deve reverter a transação inteira. A posição mantém `on_hand_quantity`, `reserved_quantity`, `available_quantity` calculada e `average_unit_cost`; os movimentos formam o histórico para conciliação. Correções históricas geram movimentos compensatórios, não edição dos movimentos existentes.

## Custo médio móvel

`goods_receipt_items.unit_acquisition_cost` é considerado custo de aquisição já elegível na V1. Não há rateio adicional de frete de compra, impostos ou custos acessórios.

Para uma entrada elegível, calcular com aritmética decimal:

```text
novo_custo_medio =
  (quantidade_anterior * custo_medio_anterior
   + quantidade_entrada * custo_unitario_entrada)
  / (quantidade_anterior + quantidade_entrada)
```

Persistir custos unitários em `NUMERIC(20,8)`, aplicando arredondamento compatível com oito casas decimais. Não usar ponto flutuante. A camada Python futura deve usar `Decimal`. Uma saída usa o custo médio vigente e reduz a quantidade física sem recalcular a média.

## Movimentos e atendimento

Recebimento aceito, atendimento físico, retorno vendável e transferências atualizam posição e movimento na mesma transação. Movimento `fulfillment` tem quantidade negativa e referencia o `fulfillment_item`; `unit_cost` é o custo médio vigente no local. O custo realizado é `ABS(quantity_delta) * unit_cost`, podendo variar entre movimentos da mesma linha comercial.

Confirmação de atendimento deve respeitar o limite acumulado da quantidade vendida e reservas disponíveis. Mudanças de atendimento, reserva, posição, movimento e estado operacional correspondente devem ser atômicas.

## Transferências

`transfer_out` reduz o saldo da origem pelo custo médio vigente e registra esse custo. `transfer_in` usa o mesmo `unit_cost` da saída e recalcula a média própria do destino como entrada elegível. Os dois movimentos referenciam o mesmo `stock_transfer_item_id`. Atualizações dos locais devem ocorrer em ordem determinística de `stock_location_id` para reduzir deadlocks; o estado em trânsito não aumenta o saldo do destino antes do recebimento.

## Devoluções e custo do retorno

Antes de confirmar recebimento físico, `return_items.source_fulfillment_item_id` deve identificar a linha de atendimento do mesmo pedido e item. A quantidade devolvida acumulada não pode superar `fulfilled_quantity` dessa origem, abatendo devoluções anteriores; bloquear a linha de atendimento durante essa validação.

Para destino `sellable`, calcular o custo unitário histórico ponderado apenas sobre os movimentos `fulfillment` ligados à origem:

```text
custo_retorno =
  SUM(ABS(quantity_delta) * unit_cost)
  / SUM(ABS(quantity_delta))
```

Persistir o custo efetivamente utilizado em `inventory.stock_movements.unit_cost` do movimento `customer_return`. A entrada vendável atualiza normalmente o custo médio do local. `quarantine`, `repair` e `discard` não aumentam o saldo vendável. Aprovação comercial, recebimento físico, retorno ao estoque e reembolso são etapas distintas.

## Limites agregados

Validar dentro de transações serializadas nos registros-pai relevantes:

- recebimento acumulado por item não supera quantidade comprada;
- atendimento acumulado não supera quantidade vendida ou reservada;
- reservas ativas não excedem disponibilidade;
- devoluções recebidas não excedem a quantidade efetivamente atendida da origem física;
- reembolsos concluídos não excedem o valor elegível;
- parcelas conciliam com o pagamento;
- rateio de desconto concilia com o cabeçalho e não torna item líquido negativo;
- alterações de vigência não criam sobreposição de preços no mesmo SKU/canal nem lotações incompatíveis.

Os invariantes entre linhas/tabelas são responsabilidade transacional da camada operacional. A V1 não usa triggers complexos nem `btree_gist`.
