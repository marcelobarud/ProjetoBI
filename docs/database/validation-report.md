# Relatório de validação PostgreSQL — Fases 2B.1 e 2B.2

**Data:** 2026-10-05

**Database:** `projeto_bi`

**Servidor:** PostgreSQL 18.6

**Cliente:** `psql` PostgreSQL 18.6 (`D:\PostGre\pgAdmin 4\runtime\psql.exe`)

## Execução

- O teste de conectividade confirmou a versão real do servidor como PostgreSQL 18.6.
- A database `projeto_bi` não existia. Ela foi criada vazia após a verificação de ausência.
- `database/migrations/001_initial_schema.sql` foi aplicada e terminou com `COMMIT`.
- `scripts/Invoke-DatabaseValidation.ps1` e `database/tests/001_structure.sql` concluíram sem erro.
- `scripts/Invoke-SmokeTest.ps1` executou `database/tests/002_smoke_rollback.sql`; a transação terminou em `ROLLBACK`.

## Estrutura confirmada

| Verificação | Resultado |
| --- | ---: |
| Schemas | 9 |
| Tabelas | 40 |
| Primary keys | 40 |
| Foreign keys | 70 |
| CHECK constraints | 75 |
| UNIQUE constraints | 37 |
| Índices físicos totais | 148 |

Os 148 índices físicos incluem índices criados para as 40 PKs e 37 constraints UNIQUE, além dos índices declarados diretamente pela migration (64 índices comuns e 7 índices únicos).

Também foram confirmados:

- `catalog.products.specifications` como `JSONB`, anulável e sujeito ao CHECK de objeto JSON.
- `inventory.stock_positions.available_quantity` como `BIGINT GENERATED ALWAYS`.
- `after_sales.return_items.source_fulfillment_item_id` como `BIGINT`.
- Ausência da coluna `unit_cost_snapshot`.
- CHECK de moeda BRL em `sales.sales_orders`, `procurement.purchase_orders` e `payments.payments`.
- `catalog.products.unit_of_measure` permanece sem CHECK de domínio, conforme decisão registrada; a definição do vocabulário segue como pendência.

## Dados persistidos

Após o smoke test, foram contadas as linhas em todas as 40 tabelas dos nove schemas operacionais. O resultado foi zero em todas: nenhum registro de smoke permaneceu e não há dados de negócio persistidos. Nenhum dado sintético foi gerado.

## Fase 2B.2 — endereço estruturado de lojas

**Validação concluída:** 2026-10-05
**Database:** `projeto_bi`
**Servidor:** PostgreSQL 18.6

`database/migrations/002_add_store_address.sql` já havia sido aplicada e concluído com `COMMIT` antes desta retomada. A retomada confirmou as oito colunas no banco e **não reaplicou nem reverteu** a migration. `database/migrations/001_initial_schema.sql` permaneceu inalterada; a mudança continua isolada na migration incremental 002.

### Correção e smoke test

Na primeira tentativa do teste, um `store_code` temporário excedeu `VARCHAR(30)`, impedindo que o caso chegasse ao `NOT NULL` pretendido. O teste foi corrigido para usar token curto com sufixos distintos. As exceções esperadas agora verificam também o nome do CHECK ou da coluna, garantindo que cada cenário falhe pela regra-alvo.

O teste transacional foi executado com sucesso:

- Inserção válida: passou com código/nome/status válidos, CEP de oito dígitos, endereço preenchido, UF `SP`, país `BR` e timestamps.
- CEP com letras e CEP com sete dígitos: rejeitados por `ck_stores_postal_code`.
- UF `XX`: rejeitada por `ck_stores_state_code`.
- País `AR`: rejeitado por `ck_stores_country_code`.
- Campos obrigatórios nulos: `postal_code`, `street`, `street_number`, `district`, `city`, `state_code` e `country_code` foram rejeitados individualmente pela nulabilidade da coluna correspondente.
- A transação terminou em `ROLLBACK`. Uma consulta posterior confirmou `COUNT(*) = 0` em `core.stores`.

### Estrutura atual confirmada

`database/tests/001_structure.sql` passou contra o banco real. A validação conferiu os tipos e comprimentos aprovados (`VARCHAR(8)`, `VARCHAR(180)`, `VARCHAR(30)`, `VARCHAR(100)`, `VARCHAR(100)`, `VARCHAR(120)`, `CHAR(2)`, `CHAR(2)`), nulabilidade correta, três CHECKs de endereço e o índice `idx_stores_state_city` sobre `(state_code, city)`. Também confirmou as colunas críticas pré-existentes e ausência de tabelas extras.

| Verificação | Resultado real |
| --- | ---: |
| Versão do servidor | PostgreSQL 18.6 |
| Schemas operacionais | 9 |
| Tabelas | 40 |
| Primary keys | 40 |
| Foreign keys | 70 |
| CHECK constraints | 78 |
| UNIQUE constraints | 37 |
| Índices físicos totais | 149 |
| Colunas de endereço em `core.stores` | 8 |
| Linhas em `core.stores` após rollback | 0 |
| Linhas em todas as 40 tabelas operacionais | 0 |

As PKs e FKs mantiveram as contagens validadas na Fase 2B.1. O schema está **READY FOR GENERATOR** para a futura implementação, sujeita à autorização da fase. `catalog.products.discontinued_at` permanece uma melhoria **OPTIONAL**, fora do gate. Nenhum dado sintético foi gerado e a Fase 3B e o Power BI não foram iniciados.

## Fase 3E.2c.3 — cancelamento parcial (2026-10-07)

A migration incremental 003 foi aplicada após confirmar que a estrutura aprovada anterior estava intacta e vazia. A validação após a migration confirmou:

| Verificação | Resultado |
| --- | ---: |
| Versão PostgreSQL | 18.6 |
| Schemas | 9 |
| Tabelas | 41 |
| Primary keys | 41 |
| Foreign keys | 72 |
| CHECK constraints | 85 |
| UNIQUE constraints | 38 |
| Índices físicos | 154 |
| Linhas em todas as tabelas depois dos rollbacks | 0 |

`database/tests/001_structure.sql` passou. Foram reconfirmados specifications JSONB, coluna gerada `available_quantity`, `source_fulfillment_item_id`, ausência de `unit_cost_snapshot`, os CHECKs de BRL previstos e a pendência de domínio de `unit_of_measure` sem CHECK.

O rollback full PostgreSQL de 10.000 intenções passou nas validações relacionais, financeiras e replay de estoque. A fixture de cancelamento com duas capturas confirmou refund de BRL 90,00 dividido em duas linhas dentro dos saldos disponíveis; o controle negativo de quantidade excedente foi rejeitado. A integração multibatch de 1.000 intenções também passou. Smoke permaneceu sem diferenças de digest. Verificação em conexão nova depois das integrações encontrou zero registros nas 41 tabelas; nenhum dado de negócio foi persistido.

O estado estrutural é **READY FOR PARTIAL CANCELLATION**. Esta conclusão não valida a calibração do abastecimento, a escala Portfolio 120k ou uma fase de Power BI.
