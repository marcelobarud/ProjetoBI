# Fase 4.1 — projeto inicial PBIP/TMDL/PBIR

**Estado:** PASS — projeto inicial criado e reaberto no Power BI Desktop.

**Data:** 2026-10-12.

**Workspace:** `D:\Codex\ProjetoBI`.

## Verificações de entrada

- Branch `main`; HEAD de entrada `bdfd009db6986ed1d955a9698bba368a90b02379`, presente no histórico; worktree limpa antes das alterações desta fase.
- O estado da Fase 4.0 registra backup preservado e database PostgreSQL 18.6 com 9 schemas, 41 tabelas, 120.000 pedidos e 3.894.457 linhas. Nesta fase não houve conexão nem consulta ao banco, nem acesso ao arquivo de backup.
- Power BI Desktop instalado em `D:\Apps\Microsoft Power BI Desktop\bin\PBIDesktop.exe`; ProductVersion `2.158.1177.0 (26.09)` e FileVersion `2.158.1177.0`.
- Em **Opções > Recursos de visualização**, as opções **Power BI Project (.pbip)**, **TMDL** e **PBIR** já estavam habilitadas. Não foi necessário alterar configurações do Desktop.

## Estrutura criada pelo Desktop

```text
powerbi/
  ProjetoBI.pbip
  ProjetoBI.Report/
    definition.pbir
    definition/
      report.json
      version.json
      pages/
    StaticResources/
      SharedResources/BaseThemes/Fluent2-CY26SU09.json
  ProjetoBI.SemanticModel/
    definition.pbism
    definition/
      database.tmdl
      model.tmdl
      cultures/pt-BR.tmdl
    diagramLayout.json
  README.md
```

O modelo está em TMDL e contém zero tabelas, relações, medidas ou funções. O relatório está em PBIR e contém somente a página padrão vazia. `definition.pbir` referencia a pasta `.SemanticModel` correspondente. O Desktop também criou `.pbi/` com cache, editor settings e configurações locais; essa pasta não faz parte das definições versionáveis.

## Validação

- O próprio Desktop salvou `ProjetoBI.pbip` e criou as pastas `.Report` e `.SemanticModel`.
- O projeto foi reaberto pelo comando Abrir do Desktop; a barra de título passou a exibir `ProjetoBI` e o painel Dados informou que nenhum dado foi carregado.
- O `.gitignore` exclui `**/.pbi/`, mas mantém versionáveis `.pbip`, `.Report`, `.SemanticModel`, arquivos TMDL, PBIR, JSON de definição e recursos compartilhados do projeto.
- A instrução operacional para abrir e revisar o projeto usando Desktop, VS Code e Codex está em [`../../powerbi/README.md`](../../powerbi/README.md).

## Limites e continuidade

Não houve conexão PostgreSQL, criação de credenciais, importação das 41 tabelas, escrita no banco, geração de dados, migration ou alteração do backup. Não foram criados modelo estrela/dimensional, consultas Power Query, medidas DAX, páginas analíticas ou dashboards. A modelagem é uma fase posterior e exige escopo próprio.

## Fontes oficiais

- [Visão geral de Power BI Projects (PBIP)](https://learn.microsoft.com/en-us/power-bi/developer/projects/projects-overview).
- [Formato de projeto do modelo semântico e TMDL](https://learn.microsoft.com/en-us/power-bi/developer/projects/projects-dataset).
- [Formato de projeto de relatório](https://learn.microsoft.com/en-us/power-bi/developer/projects/projects-report).
- [Formato aprimorado PBIR](https://learn.microsoft.com/en-us/power-bi/developer/embedded/projects-enhanced-report-format).
