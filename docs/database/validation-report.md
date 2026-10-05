# Relatório de validação PostgreSQL — Fase 2B.1

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
