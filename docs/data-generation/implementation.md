# Implementação do gerador — Fases 3B a 3D

## Escopo entregue

A Fase 3B implementa o pacote Python em `data-generator/` para configuração determinística, geração e validação de dados mestres. As Fases 3C e 3D completam o fluxo de compras e recebimentos, vendas, estoque, pagamentos, parcelas, logística, transferências, devoluções e refunds no profile `smoke`. A carga no PostgreSQL é exclusivamente rollback-only. Os profiles `portfolio` e `large` têm configurações preparadas, mas não foram gerados ou carregados.

O banco operacional continua sendo a fonte de verdade para tipos, constraints e relações. O gerador usa chaves lógicas para resolver os IDs identity retornados pelo PostgreSQL; não pressupõe IDs técnicos fixos. A ordem de dependências está em [dependency-order.md](dependency-order.md).

## Ambiente local

Requer Python 3.11 ou superior. O ambiente validado nesta fase é Python 3.13.15, instalado em `data-generator/.venv/`, ignorado pelo Git. No PowerShell, a partir da raiz do projeto:

```powershell
py -3.13 -m venv .\data-generator\.venv
Set-Location .\data-generator
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
Set-Location ..
```

As dependências de execução são `psycopg[binary]` e Faker; pytest é dependência de desenvolvimento. Não há ORM, Pandas ou NumPy. A configuração não contém credenciais. Para integração local, o pacote carrega o `.env` da raiz como fallback para variáveis de processo `POSTGRES_*`, sem imprimir valores. O arquivo `.env` real permanece ignorado e fora do Git.

## Configuração e reprodutibilidade

- `config/generator.toml` contém versão de configuração, versão do gerador, seed raiz `20261005`, janela comercial, janela de bootstrap e `America/Sao_Paulo`.
- Os arquivos `config/profiles/{smoke,portfolio,large}.toml` descrevem volumes; os perfis maiores incluem dez endereços inteiramente fictícios.
- Nove sub-seeds de domínio são derivados por SHA-256 de forma estável. Cada domínio recebe seu próprio `random.Random` e instância Faker, sem compartilhar estado aleatório.
- Datas e timestamps são explícitos e os valores monetários são `Decimal`. CPF/CNPJ passam por checksum e são gerados deterministicamente; contatos de e-mail usam `example.com`.

## Dados mestres e segurança da carga

O profile smoke implementa as 19 tabelas mestre, na ordem de dependências declarada: lojas, pessoas/funções/atribuições, clientes/perfis/contatos/endereços, categorias/marcas/produtos/fornecedores/preços, locais de estoque, meios de pagamento, transportadoras e canais. Validadores Python verificam volumes, chaves únicas, referências, árvore de categorias, vigências não sobrepostas, perfis PF/PJ, documentos fiscais, endereços, unidade `unit`, objeto JSONB e especificações por família.

`--dry-run` não abre conexão. `--load-smoke` é restrito ao profile smoke e verifica database `projeto_bi`, PostgreSQL major 18, 9 schemas, 40 tabelas, estrutura aprovada e zero linhas em todas as tabelas antes de inserir. A escrita é parametrizada e ocorre em uma única transação; validações SQL conferem contagens, relações financeiras e movimentos do ledger. O comando executa `ROLLBACK` explícito e abre nova conexão para verificar que as 40 tabelas continuam vazias. O guard interrompe a carga se encontrar dados ou estrutura inesperados.

## Comandos

Na raiz do projeto:

```powershell
.\data-generator\.venv\Scripts\python.exe -m projectbi_generator.cli master --profile smoke --dry-run
.\data-generator\.venv\Scripts\python.exe -m pytest .\data-generator
$env:PROJECTBI_RUN_INTEGRATION = '1'
.\data-generator\.venv\Scripts\python.exe -m pytest .\data-generator
```

Os testes de integração requerem a database local aprovada, `.env` configurado e vazia. Eles executam somente cargas smoke com rollback. Para verificar novamente o conjunto completo, use `python -m pytest` com `PROJECTBI_RUN_INTEGRATION=1` definido e diretório atual `data-generator`.

## Núcleo transacional — Fases 3C e 3D

A Fase 3C acrescenta uma engine determinística orientada a eventos para compras, recebimentos, reposição, pedidos de venda, descontos, reservas, cancelamentos, fulfillment, movimentos e posições de estoque. Eventos usam instante, prioridade e chave lógica estável para preservar causalidade e reprodutibilidade. Quantias monetárias usam `Decimal`; rateios de desconto preservam centavos, e custo de estoque usa média móvel com escala de oito casas.

O profile smoke gera 300 pedidos e 630 linhas, cobre os quatro canais existentes, pedidos físicos anônimos, pedidos cancelados, descontos e fulfillment dividido. O fluxo inclui recebimentos parciais e quantidades rejeitadas, reabastecimento durante a janela comercial e reserva/liberação/consumo do estoque. O custo realizado é calculado pelos movimentos de saída; a posição final reconcilia unidades recebidas, unidades expedidas e saldo. Preços e fornecedores são validados contra as dimensões mestre e suas vigências/associações.

A Fase 3D amplia a engine sem alterar os registros-base da Fase 3C. Os pagamentos conciliam exatamente com o total dos pedidos; recusas e falhas têm retry bem-sucedido, pagamentos divididos e parcelamento cobrem meios elegíveis. Eventos registram a sequência de despacho/entrega e preparação/liberação/retirada. Transferências criam movimentos pareados com o mesmo custo médio; devoluções referenciam itens de fulfillment, preservam o custo histórico e só reintegram ao estoque itens classificados como vendáveis. Refunds ficam limitados às capturas correspondentes.

O smoke `full` valida em memória a reconciliação financeira e física, cutoff e referências. A integração persiste temporariamente as 21 tabelas transacionais, valida também no PostgreSQL e faz `ROLLBACK` explícito; a conexão posterior confirmou zero linhas nas 40 tabelas. Não requer migration. O escopo não inclui persistência permanente, execução dos perfis `portfolio`/`large` nem Power BI.

## Limites da Fase 3B

Rotina de reset, carga portfolio/large, persistência permanente e integração com Power BI continuam fora do escopo. Nenhuma linha de negócio smoke permanece persistida. O próximo escopo recomendado é planejar a Fase 3E.
