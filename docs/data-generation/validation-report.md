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

**Fase 3D validada.** Recomenda-se planejar a Fase 3E antes de executar perfis maiores, persistir dados ou iniciar Power BI.
