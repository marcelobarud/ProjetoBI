# Fase 4.6.2 — estabilização do PBIP e serialização TMDL

**Resultado: PARTIAL — limite de consultas pendente.** Esta fase estabilizou os artefatos TMDL e registrou o comportamento de persistência da simulação de limite de consultas. Não iniciou dashboards, publicação ou a Fase 5.

## Estado inicial e snapshot

- Repositório `D:\Codex\ProjetoBI`, branch `main`, HEAD inicial `44228184135c1bce6542981bb8e6b809e149594c`.
- Antes das alterações desta fase, havia 15 caminhos rastreados modificados: 14 TMDLs e `powerbi/ProjetoBI.Report/definition/report.json`; não havia staging nem arquivos não rastreados.
- A auditoria dos diffs confirmou que cada um dos 14 TMDLs continha somente uma linha vazia final adicional. Não havia mudança semântica, de metadados ou de formatação DAX.
- O manifesto de `POWERBI_WORKTREE_REGULARIZATION.md` declara 15 caminhos, mas enumera 16. A lista inclui `_Medidas.tmdl` além dos 15 nomes esperados; esta fase registra a discrepância sem alterar o documento histórico.
- Snapshot externo ao Git: `C:\Users\D2\AppData\Local\Temp\ProjetoBI-phase-4.6.2-snapshot-20261012-204105`. O manifesto preserva branch, HEAD, status e SHA-256 dos 15 arquivos. Todos os 15 hashes das cópias foram comparados com os arquivos de origem. SHA-256 original de `report.json`: `89B99889C1555BFFDD00D4675E423E3159FACB84D8D320DA8E19BF6E9CA60E40`.

## Serialização do Desktop

O Power BI Desktop `2.158.1177.0 (26.09)+a10b99dd55051d4b25e9e28c4a1747d23f7a4f1f` abriu o PBIP sem erro. Depois de salvar, fechar e reabrir, o modelo exibiu 10 tabelas, 55 medidas, 11 Display Folders e 21 relações. A verificação do TMDL confirmou 2 relações inativas e nenhuma configuração bidirecional; esta subfase não repetiu as consultas de regressão DAX da Fase 4.6.1.

Os SHA-256 dos 14 TMDLs continuaram idênticos aos do snapshot após o ciclo do Desktop (14/14). Assim, a linha vazia final pré-existente não se acumulou e a serialização do Desktop foi aceita.

## Regra Git de whitespace

Foi adicionada uma regra estrita e limitada ao modelo:

```gitattributes
powerbi/ProjetoBI.SemanticModel/definition/*.tmdl whitespace=-blank-at-eof
powerbi/ProjetoBI.SemanticModel/definition/tables/*.tmdl whitespace=-blank-at-eof
powerbi/ProjetoBI.SemanticModel/definition/cultures/*.tmdl whitespace=-blank-at-eof
```

`git check-attr` confirmou a regra nos TMDLs do modelo e ausência de regra em `report.json` e `powerbi/README.md`. `git diff --check` não sinalizou a linha vazia final dos TMDLs. Em repositório descartável, a mesma regra suprimiu o aviso de linha vazia final para TMDL, mas continuou detectando espaço em branco ao fim da linha. Nenhuma configuração global do Git ou regra `text`/`eol` foi alterada.

## Limite de consultas: tentativa única não persistente

O `report.json` original continha `settings.queryLimitOption: None`, com `customMemoryLimit: 1048576`, `customTimeoutLimit: 225` e painel lateral recolhido. Foi feita uma única alteração controlada de `None` para `Auto` e o JSON continuou válido.

Na primeira abertura, **File > Options > Current file > Report settings** mostrou **Auto (recommended)**, com 1 GB e 225 segundos. Após salvar, o Desktop omitiu `queryLimitOption` da serialização. Depois de fechar e reabrir, a mesma tela mostrou **No query limits**. Portanto, o gate de persistência não passou. Não foi feita uma segunda tentativa nesta fase.

Ao encerrar a tentativa, `report.json` foi restaurado byte a byte do snapshot: voltou a `None`, manteve os limites personalizados e o painel recolhido, e recuperou seu hash original. Esse diff preexistente fica fora dos commits da Fase 4.6.2 para preservar o estado que o usuário já tinha antes da tentativa.

## Referências de dados

As validações SQL × DAX e as oito regressões foram executadas na Fase 4.6.1. Os baselines permanecem registrados em `POWERBI_WORKTREE_REGULARIZATION.md`; não foram executados novamente aqui porque as definições TMDL permaneceram estáveis. A documentação Microsoft posiciona a escolha de limites em **Current file > Report settings** e recomenda **Auto** para novos relatórios: <https://learn.microsoft.com/en-us/power-bi/create-reports/desktop-set-visual-query-limits>. A persistência do PBIR foi inspecionada contra o schema oficial 3.3.0, que admite `Auto` como valor de `queryLimitOption`, sem declarar um valor default: <https://developer.microsoft.com/json-schemas/fabric/item/report/3.3.0/schema.json>.

## Commits e estado final

O commit de serialização contém somente `.gitattributes` e os 14 TMDLs, sem alterações analíticas. O commit de documentação contém este registro, `powerbi/README.md` e `docs/PROJECT_COMPLETION_PLAN.md`. `report.json` permanece fora de ambos e deve continuar como a única alteração rastreada residual desta fase.

**Gate final:** serialização TMDL PASS; abertura e inventário do modelo PASS; configuração `Auto` persistente PENDENTE. Retomar apenas numa fase autorizada, sem iniciar dashboards ou publicação enquanto esse requisito permanecer pendente.
