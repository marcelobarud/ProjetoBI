# Implementação do gerador — Fase 3B

## Escopo entregue

A Fase 3B implementa o pacote Python em `data-generator/` para configuração determinística, geração e validação de dados mestres e um smoke transacional exclusivamente reversível. O profile `smoke` pode ser gerado em memória; `portfolio` e `large` têm configurações e endereços fictícios preparados, mas não podem ser executados nesta fase. A engine de compras, vendas, estoque, pagamentos, logística, devoluções e cargas persistentes permanece para fases posteriores.

O banco operacional continua sendo a fonte de verdade para tipos, constraints e relações. O gerador usa chaves lógicas para resolver os IDs identity retornados pelo PostgreSQL; não pressupõe IDs técnicos fixos. A ordem de dependências está em [dependency-order.md](dependency-order.md).

## Ambiente local

Requer Python 3.11 ou superior. O ambiente validado nesta fase é Python 3.13.15, instalado no `.venv/` ignorado pelo Git. No PowerShell, a partir da raiz do projeto:

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e .\data-generator[dev]
```

As dependências de execução são `psycopg[binary]` e Faker; pytest é dependência de desenvolvimento. Não há ORM, Pandas ou NumPy. A configuração não contém credenciais. Para integração local, `data-generator/.env` não é usado: o pacote carrega o `.env` da raiz como fallback para variáveis de processo `POSTGRES_*`, sem imprimir valores. O arquivo `.env` real permanece ignorado e fora do Git.

## Configuração e reprodutibilidade

- `config/generator.toml` contém versão de configuração, versão do gerador, seed raiz `20261005`, janela comercial, janela de bootstrap e `America/Sao_Paulo`.
- Os arquivos `config/profiles/{smoke,portfolio,large}.toml` descrevem volumes; os perfis maiores incluem dez endereços inteiramente fictícios.
- Nove sub-seeds de domínio são derivados por SHA-256 de forma estável. Cada domínio recebe seu próprio `random.Random` e instância Faker, sem compartilhar estado aleatório.
- Datas e timestamps são explícitos e os valores monetários são `Decimal`. CPF/CNPJ passam por checksum e são gerados deterministicamente; contatos de e-mail usam `example.com`.

## Dados mestres e segurança da carga

O profile smoke implementa as 19 tabelas mestre, na ordem de dependências declarada: lojas, pessoas/funções/atribuições, clientes/perfis/contatos/endereços, categorias/marcas/produtos/fornecedores/preços, locais de estoque, meios de pagamento, transportadoras e canais. Validadores Python verificam volumes, chaves únicas, referências, árvore de categorias, vigências não sobrepostas, perfis PF/PJ, documentos fiscais, endereços, unidade `unit`, objeto JSONB e especificações por família.

`--dry-run` não abre conexão. `--load-smoke` é restrito ao profile smoke e verifica database `projeto_bi`, PostgreSQL major 18, 9 schemas, 40 tabelas, estrutura aprovada e zero linhas em todas as tabelas antes de inserir. A escrita é parametrizada e ocorre em uma única transação; validações SQL conferem contagens e relações. O comando executa `ROLLBACK` explícito e abre nova conexão para verificar que as 40 tabelas continuam vazias. O guard interrompe a carga se encontrar dados ou estrutura inesperados.

## Comandos

Na raiz do projeto:

```powershell
.\.venv\Scripts\python.exe -m projectbi_generator.cli master --profile smoke --dry-run
.\.venv\Scripts\python.exe -m pytest -m "not integration" .\data-generator
$env:PROJECTBI_RUN_INTEGRATION = '1'
.\.venv\Scripts\python.exe -m pytest -m integration .\data-generator
```

O teste de integração requer a database local aprovada, `.env` configurado e vazia. Ele só executa o smoke com rollback. Para verificar novamente o conjunto completo de testes, use `python -m pytest` com `PROJECTBI_RUN_INTEGRATION=1` definido e diretório atual `data-generator`.

## Limites desta fase

Não existe geração nem persistência de fatos transacionais, algoritmo de estado de estoque, rotina de reset, carga portfolio/large ou integração com Power BI. O teste PostgreSQL desta fase não deixa linhas de negócio persistidas. O próximo escopo recomendado é a Fase 3C, para engine operacional de compras, recebimentos, vendas e estoque, com autorização específica.
