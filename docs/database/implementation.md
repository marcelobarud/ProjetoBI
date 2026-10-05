# Implementação PostgreSQL

## Escopo e estado

O modelo aprovado é PostgreSQL 18, database `projeto_bi`, nove schemas e quarenta tabelas. O schema é criado pela migration `database/migrations/001_initial_schema.sql`; a criação da database fica separada nos scripts PowerShell. Esta versão não cria dados, seeds, triggers, procedures ou estruturas analíticas.

Os arquivos da Fase 2B foram preparados localmente. A instância alvo ainda não foi acessada nem validada. A conexão depende da configuração segura das variáveis indicadas abaixo.

## Configuração local

Defina no ambiente local, sem salvar credenciais no repositório:

```powershell
$env:POSTGRES_HOST = 'host-do-servidor'
$env:POSTGRES_PORT = '5432'
$env:POSTGRES_DB = 'projeto_bi'
$env:POSTGRES_USER = 'usuario'
$env:POSTGRES_PASSWORD = 'senha-local'
```

Use um gerenciador local de segredos ou configure essas variáveis fora do Git. `.env.example` contém somente os nomes, sem valores reais. Nunca use senha em argumento de comando, script versionado, log ou connection string commitada.

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

A conexão e aplicação continuam pendentes nesta cópia porque não há `POSTGRES_*` configuradas e `psql` não está instalado/disponível no PATH. Configure as cinco variáveis e disponibilize `psql` antes de aplicar. A validação SQL informa erro se a base alvo não for `projeto_bi`.

## Pendência de domínio

`catalog.products.unit_of_measure` permanece `NOT NULL`, sem CHECK de domínio nesta versão, conforme decisão do usuário. O vocabulário pode ser definido em migração futura.

## Erros comuns

- **Variável ausente:** configure `POSTGRES_HOST`, `POSTGRES_PORT`, `POSTGRES_DB`, `POSTGRES_USER` e `POSTGRES_PASSWORD` no processo PowerShell atual.
- **Versão diferente:** a automação exige PostgreSQL 18 e para antes de criar ou aplicar objetos.
- **`psql` ausente:** instale ou adicione o cliente PostgreSQL 18 ao `PATH`; nenhum cliente foi instalado nesta fase.
- **Database existente com objetos inesperados:** não remova objetos; revise-os manualmente antes de autorizar qualquer procedimento.
- **Falha de permissão:** solicite ao administrador a permissão necessária fora dos arquivos versionados; não embuta credenciais em scripts.
