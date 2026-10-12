# Projeto Power BI

O projeto inicial é gerado e aberto pelo Power BI Desktop em [`ProjetoBI.pbip`](ProjetoBI.pbip). Ele contém um relatório em branco e um modelo semântico vazio; ainda não há conexão a fontes, tabelas importadas, Power Query, medidas DAX ou páginas analíticas.

## Fluxo de trabalho

1. Abra `ProjetoBI.pbip` no Power BI Desktop para trabalhar no projeto.
2. Use o Desktop para criar ou alterar o relatório e o modelo semântico. Salve pelo próprio Desktop para que as definições PBIR e TMDL permaneçam consistentes.
3. Abra o repositório no VS Code/Codex para revisar diferenças textuais e documentação. As definições ficam em `ProjetoBI.Report/definition/` (PBIR) e `ProjetoBI.SemanticModel/definition/` (TMDL).
4. Se uma definição textual for alterada externamente, revise o diff e reabra/atualize o projeto no Desktop para validar antes de commit.
5. Versione o `.pbip`, as pastas `.Report` e `.SemanticModel` e seus arquivos de definição. A pasta `.pbi/` guarda cache e estado local do Desktop e é ignorada pelo Git.

Não coloque senhas, tokens ou connection strings com credenciais nas definições do projeto. A conexão PostgreSQL e a seleção de tabelas devem usar acesso somente leitura e ser feitas apenas na fase correspondente; o projeto inicial ainda não está conectado ao banco.
