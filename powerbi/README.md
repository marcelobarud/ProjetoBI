# Projeto Power BI

O projeto oficial PBIP é aberto pelo Power BI Desktop em [`ProjetoBI.pbip`](ProjetoBI.pbip), com relatório PBIR e modelo semântico TMDL. O checkpoint inicial da Fase 4.1 era vazio. Na Fase 4.2 foi criada e validada a role PostgreSQL `projetobi_pbi_ro`, mas a conexão pelo Desktop e a importação controlada das sete tabelas ainda aguardam validação interativa. Consulte [`phase-4.2-connection-and-model-foundation.md`](../docs/powerbi/phase-4.2-connection-and-model-foundation.md) para o estado atual, contagens e arquitetura proposta.

## Fluxo de trabalho

1. Abra `ProjetoBI.pbip` no Power BI Desktop para trabalhar no projeto. Para a continuação da Fase 4.2, use `projeto_bi`, a role `projetobi_pbi_ro` e modo Import; importe somente `sales.sales_orders`, `sales.sales_order_items`, `catalog.products`, `catalog.categories`, `crm.customers`, `core.stores` e `sales.sales_channels`.
2. Use o Desktop para criar ou alterar o relatório e o modelo semântico. Salve pelo próprio Desktop para que as definições PBIR e TMDL permaneçam consistentes.
3. Abra o repositório no VS Code/Codex para revisar diferenças textuais e documentação. As definições ficam em `ProjetoBI.Report/definition/` (PBIR) e `ProjetoBI.SemanticModel/definition/` (TMDL).
4. Se uma definição textual for alterada externamente, revise o diff e reabra/atualize o projeto no Desktop para validar antes de commit.
5. Versione o `.pbip`, as pastas `.Report` e `.SemanticModel` e seus arquivos de definição. A pasta `.pbi/` guarda cache e estado local do Desktop e é ignorada pelo Git.

Não coloque senhas, tokens ou connection strings com credenciais nas definições do projeto. A senha read-only está guardada no Windows Credential Manager local. O Power BI ainda precisa autenticar e fazer o primeiro refresh; não considerar a importação concluída até reconciliar contagens e tipos e reabrir o PBIP.
