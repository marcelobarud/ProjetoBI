# Backup lógico PostgreSQL — ProjetoBI

## Cópia de segurança da Fase 4.0

- Data/hora: 2026-10-10 10:28:21 -03:00.
- Origem: PostgreSQL 18.6, database `projeto_bi`.
- Ferramentas: `pg_dump` 18.6 e `pg_restore` 18.6.
- Formato: custom (`-Fc`), com schemas e dados completos.
- Arquivo: `D:\Backups\ProjetoBI\ProjetoBI_projeto_bi_20261010T102821-0300.backup`.
- Tamanho: 68.365.155 bytes (aprox. 65,2 MiB).
- SHA-256: `76C2AA25C02F8C70CA697E5AB5D5CBBD9BAFAA0A68EECE2E3018049B4CFA453D`.
- Resultado: `pg_dump` exit code 0; `pg_restore --list` exit code 0; catálogo contém 9 schemas e 41 entradas `TABLE DATA`.
- Verificação somente leitura antes e depois: PostgreSQL 18.6; 9 schemas; 41 tabelas; 3.894.457 linhas; 120.000 pedidos; tamanho lógico do banco 1.193.948.863 bytes. As contagens permaneceram iguais.
- `.env` não foi lido para saída, não foi incluído no backup como arquivo local e continua ignorado pelo Git. O backup está fora do repositório.

O catálogo do arquivo confirma que `pg_restore` consegue ler e enumerar o archive; isso **não** é uma restauração de teste e não comprova a recuperação integral dos dados. Nenhuma database de teste foi criada e nenhum restore foi executado. Uma cópia adicional em mídia física independente é recomendada, pois o arquivo atual e a instalação PostgreSQL estão na unidade D:.

## Procedimento de criação

1. Confirme que origem, versão do servidor e espaço de destino estão corretos e que não há outro processo de carga.
2. Use `pg_dump` da mesma versão principal ou compatível com o servidor, no formato custom (`-Fc`), sem filtros de schema/tabela. Passe credenciais por ambiente seguro ou prompt protegido; nunca coloque senha em argumentos, scripts versionados ou logs.
3. Use nome novo com timestamp. Confira que o destino não existe antes de iniciar; não sobrescreva backups anteriores.
4. Exija exit code zero, tamanho plausível, leitura por `pg_restore --list`, inventário esperado e hash SHA-256. Registre versão, momento, local, tamanho e hash.
5. Repita consultas somente leitura para confirmar que a origem não mudou durante o backup.

## Procedimento de restauração (futura, controlada)

1. Selecione uma instância e database de destino isoladas e aprovadas, nunca a origem de produção/estudo sem autorização expressa.
2. Confirme hash SHA-256 antes de restaurar e confira a versão de `pg_restore`.
3. Crie o destino vazio de forma deliberada e aprovada, restaure o formato custom usando `pg_restore`, e valide schemas, objetos, constraints e contagens em conexão read-only.
4. Preserve os logs de resultado e não remova a cópia de segurança até que a restauração tenha sido validada e uma política de retenção esteja definida.

## Retenção

Manter a cópia fora do Git. Guardar ao menos uma cópia em dispositivo independente da unidade D: antes de qualquer manutenção que possa afetar a instalação ou os dados dessa unidade.
