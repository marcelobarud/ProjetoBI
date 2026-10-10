# Implementação PostgreSQL

## Escopo e estado

O modelo vigente é PostgreSQL 18, database `projeto_bi`, nove schemas e quarenta tabelas. `001_initial_schema.sql` cria o schema base; `002_add_store_address.sql` adiciona endereço geográfico operacional às lojas. A criação da database fica separada nos scripts PowerShell. As migrations não criam dados, seeds, triggers, procedures ou estruturas analíticas.

Na Fase 2B.1, a migration inicial foi aplicada e validada no servidor PostgreSQL 18.6. Na Fase 2B.2, a migration incremental de endereço de loja foi aplicada e validada. `core.stores` estava vazia antes da aplicação; os testes transacionais terminaram em `ROLLBACK` e a contagem de lojas permaneceu zero. O histórico e os totais estruturais estão em `docs/database/validation-report.md`.

## Configuração local

Configure os cinco valores de conexão em variáveis do processo PowerShell ou no arquivo local `.env`, na raiz do projeto. As variáveis já definidas no processo têm prioridade; `.env` preenche apenas as que estiverem ausentes ou vazias. O arquivo `.env` é ignorado pelo Git e não deve ser versionado.

Comece copiando `.env.example` para `.env` e preencha o arquivo localmente. O parser aceita linhas `NOME=VALOR`, ignora linhas vazias e comentários iniciados por `#`, e separa o valor pela primeira ocorrência de `=`. Valores podem ser colocados entre aspas simples ou duplas. Não imprima nem registre o conteúdo do arquivo.

```powershell
Copy-Item .env.example .env
```

`POSTGRES_DB` deve ser `projeto_bi`. `POSTGRES_PSQL_PATH` é opcional e pode apontar para `psql.exe`; sem ela, os scripts procuram `psql` no PATH e depois nos caminhos padrão do PostgreSQL 18. Nunca use senha em argumento de comando, script versionado, log ou connection string commitada. `.env.example` contém somente nomes com valores vazios.

## Conectividade e aplicação

No PowerShell, a partir da raiz do projeto:

```powershell
./scripts/Test-PostgresConnection.ps1
./scripts/Initialize-ProjectDatabase.ps1
./scripts/Test-SchemaDefinition.ps1
./scripts/Invoke-ProjectMigrations.ps1
./scripts/Invoke-DatabaseValidation.ps1
./scripts/Invoke-SmokeTest.ps1
```

O teste de conexão exige PostgreSQL 18 e testa a database administrativa `postgres`. O bootstrap cria `projeto_bi` somente se ausente. Em uma database vazia, `Invoke-ProjectMigrations.ps1` aplica em ordem `001` e `002`; nunca executa `001` sobre uma database estruturada. Se a base tiver somente o schema 001, o runner valida essa versão e orienta a aplicação incremental com `Invoke-StoreAddressMigration.ps1`. Esse script valida database/versão/estrutura, exige zero linhas em `core.stores` antes de adicionar colunas obrigatórias e aplica somente a migration 002. Schema parcial ou inesperado faz o fluxo parar sem remoção/recriação.

Para reproduzir em ambiente descartável, use uma database vazia e execute o mesmo fluxo. Não use `DROP DATABASE` para reiniciar uma base existente. Reexecutar os scripts reconhece a estrutura já aplicada e valida sem reaplicar migrations; não há framework externo de migrations nem tabela de controle adicional.

## Validações

- `Test-SchemaDefinition.ps1` compara a lista `CREATE TABLE` da migration com os cabeçalhos do dicionário e verifica schemas e contagem esperada sem conexão.
- `database/tests/001_structure.sql` confere database, schemas, quarenta tabelas, ausência de tabelas extras, PKs, FKs, constraints, índices e colunas críticas. Aceita o schema base 001 ou o schema atual 002 e rejeita estado parcial; quando 002 está aplicada, valida os oito campos, seus tipos/nulabilidade, três CHECKs e índice geográfico.
- `database/tests/002_smoke_rollback.sql` é um smoke test mínimo em transação que termina em `ROLLBACK`; execute por `Invoke-SmokeTest.ps1` apenas em `projeto_bi` depois da migration.
- `database/tests/003_store_address_rollback.sql` testa endereço válido, rejeições dos CHECKs e nulabilidade dentro de `BEGIN`/`ROLLBACK`; `Invoke-StoreAddressTest.ps1` exige zero lojas antes/depois do teste.

Conexão, migrations 001/002 e validações da Fase 2B.2 concluídas no PostgreSQL 18.6. A estrutura inicial mantinha 9 schemas e 40 tabelas; a evolução estrutural vigente é a seção de 3E.2c.3 e o relatório de validação. A database permanece sem dados de negócio sintéticos.

## Pendência de domínio

`catalog.products.unit_of_measure` permanece `NOT NULL`, sem CHECK de domínio nesta versão, conforme decisão do usuário. O vocabulário pode ser definido em migração futura.

## Erros comuns

- **Variável ausente:** configure `POSTGRES_HOST`, `POSTGRES_PORT`, `POSTGRES_DB`, `POSTGRES_USER` e `POSTGRES_PASSWORD` no processo PowerShell atual ou no arquivo local `.env`.
- **Versão diferente:** a automação exige PostgreSQL 18 e para antes de criar ou aplicar objetos.
- **`psql` ausente:** configure `POSTGRES_PSQL_PATH`, adicione o cliente PostgreSQL 18 ao `PATH` ou disponibilize-o em `C:\Program Files\PostgreSQL\18\`; nenhum cliente é instalado automaticamente.
- **Database existente com objetos inesperados:** não remova objetos; revise-os manualmente antes de autorizar qualquer procedimento.
- **Falha de permissão:** solicite ao administrador a permissão necessária fora dos arquivos versionados; não embuta credenciais em scripts.

## Fase 3E.2c.3 — cancelamento parcial de itens

A migration `003_partial_item_cancellations.sql` acrescenta a entidade `sales.sales_order_item_cancellations`, os contadores acumulados `fulfilled_quantity` e `cancelled_quantity` em `sales.sales_order_items`, e referência composta de refunds ao cancelamento. Os triggers sincronizam os contadores com fulfillment items e cancelamentos; a constraint da linha serializa o limite total contra a quantidade originalmente comprada. O sink insere cancelamentos antes de refunds e resolve suas identities técnicas por `INSERT ... RETURNING`; a referência do pedido fica retida até o fechamento do lifecycle e é liberada com as demais referências do pedido.

Ao exceder 14 dias desde `placed_at`, o gerador cancela somente o saldo não expedido, estorna o valor líquido das unidades com rateio determinístico de descontos e preserva o frete quando houve expedição. Sem expedição, cancelamento integral estorna o frete cobrado e conserva o status `cancelled`. O pedido parcialmente realizado pode terminar `completed` somente após fulfillment terminal, resolução de todas as unidades e refunds concluídos. Cancelar saldo não gera movimento de estoque ou devolução.
