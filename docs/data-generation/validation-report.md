# Relatório de validação do gerador — Fase 3B

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

**Fase 3B validada.** Fundação determinística e geração de dados mestres smoke concluídas. O banco segue sem dados de negócio persistidos. A engine transacional continua fora do escopo e é o trabalho recomendado para a Fase 3C.
