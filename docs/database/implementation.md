# Implementação PostgreSQL

## Escopo e estado

O modelo aprovado é PostgreSQL 18, database `projeto_bi`, nove schemas e quarenta tabelas. O schema é criado pela migration `database/migrations/001_initial_schema.sql`; a criação da database fica separada nos scripts PowerShell. Esta versão não cria dados, seeds, triggers, procedures ou estruturas analíticas.

Na Fase 2B.1, a migration inicial foi aplicada e validada no servidor PostgreSQL 18.6. A database `projeto_bi` estava ausente e foi criada vazia antes da aplicação. O smoke test foi executado em transação com `ROLLBACK`; após a execução, as 40 tabelas continuaram sem linhas. O relatório detalhado está em `docs/database/validation-report.md`.

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

O teste de conexão exige PostgreSQL 18 e testa a database administrativa `postgres`. O bootstrap cria `projeto_bi` somente se ausente. Se ela existir e contiver objetos que não correspondam ao esquema integral esperado ou estiver parcialmente criada, o script para sem apagar ou recriar nada. A migration roda dentro de transação e aborta no primeiro erro.

Para reproduzir em ambiente descartável, use uma database vazia e execute o mesmo fluxo. Não use `DROP DATABASE` para reiniciar uma base existente. Uma execução repetida sobre uma base que já contém o esquema é recusada; a validação estrutural pode ser executada quantas vezes necessário.

## Validações

- `Test-SchemaDefinition.ps1` compara a lista `CREATE TABLE` da migration com os cabeçalhos do dicionário e verifica schemas e contagem esperada sem conexão.
- `database/tests/001_structure.sql` confere database, schemas, quarenta tabelas, ausência de tabelas extras nos schemas aprovados, PKs, FKs, constraints, índices e colunas críticas.
- `database/tests/002_smoke_rollback.sql` é um smoke test mínimo em transação que termina em `ROLLBACK`; execute por `Invoke-SmokeTest.ps1` apenas em `projeto_bi` depois da migration.

Conexão, aplicação e validação estrutural da Fase 2B.1 concluídas. O cliente e o servidor reportaram PostgreSQL 18.6. A migration terminou com `COMMIT`; a validação confirmou os objetos esperados. Depois do smoke test com `ROLLBACK`, uma contagem exata nas 40 tabelas confirmou zero linhas persistidas. A database permanece pronta para uma fase futura de geração de dados, que não foi iniciada.

## Pendência de domínio

`catalog.products.unit_of_measure` permanece `NOT NULL`, sem CHECK de domínio nesta versão, conforme decisão do usuário. O vocabulário pode ser definido em migração futura.

## Erros comuns

- **Variável ausente:** configure `POSTGRES_HOST`, `POSTGRES_PORT`, `POSTGRES_DB`, `POSTGRES_USER` e `POSTGRES_PASSWORD` no processo PowerShell atual ou no arquivo local `.env`.
- **Versão diferente:** a automação exige PostgreSQL 18 e para antes de criar ou aplicar objetos.
- **`psql` ausente:** configure `POSTGRES_PSQL_PATH`, adicione o cliente PostgreSQL 18 ao `PATH` ou disponibilize-o em `C:\Program Files\PostgreSQL\18\`; nenhum cliente é instalado automaticamente.
- **Database existente com objetos inesperados:** não remova objetos; revise-os manualmente antes de autorizar qualquer procedimento.
- **Falha de permissão:** solicite ao administrador a permissão necessária fora dos arquivos versionados; não embuta credenciais em scripts.
