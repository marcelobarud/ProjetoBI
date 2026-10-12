# Regularização da working tree Power BI — Fase 4.6.1

**Data:** 2026-10-12
**Branch/HEAD de entrada:** `main`, `80e786509ae4245c063c0bec78b38a7626558de3`
**Estado:** PARTIAL — a simulação de limites de consulta continua em `None` e o Desktop recria as linhas em branco finais dos TMDLs.

## Estado inicial e cópia de segurança

A auditoria de entrada descrevia 15 arquivos rastreados modificados. O manifesto do snapshot, em `C:\Users\D2\AppData\Local\Temp\ProjetoBI-phase-4.6.1-snapshot-20261012-195525`, também guarda HEAD, branch, status, diffs e SHA-256. Há uma divergência no próprio manifesto: declara `ModifiedFiles=15`, mas sua lista de status contém `_Medidas.tmdl` além do conjunto `report.json` + 13 TMDLs + `diagramLayout.json` (16 caminhos). O snapshot contém esses arquivos e fica fora do Git.

`_Medidas.tmdl` apresentou uma linha em branco excedente no EOF e não pertence aos 13 arquivos aprovados para normalização. Foi preservado sem edição e fica fora do commit.

## TMDL e reserialização

Os 13 arquivos autorizados foram comparados com HEAD; cada diff era somente uma linha em branco no EOF. A normalização delimitada fez seus hashes de objeto Git voltarem aos blobs de HEAD, sem alterar conteúdo semântico. No ciclo de salvar/fechar do Desktop, as 13 linhas em branco reapareceram. O estado atual mostra uma inserção por arquivo e `git diff --check` aponta somente para esse EOF. O comportamento foi registrado sem novos ciclos de limpeza. Não foi alterada a formatação DAX nem usada configuração Git para ocultar as diferenças.

O arquivo adicional `_Medidas.tmdl` também permanece com uma linha em branco excedente no EOF. As declarações TMDL continuam intactas; nenhum dos 14 diffs contém mudança de fórmula, propriedade, relacionamento, coluna ou lineage tag.

## Relatório e limites de consulta

`report.json` contém `settings.queryLimitOption: "None"`, `customMemoryLimit: "1048576"` e `customTimeoutLimit: "225"`. A interface **Options > Current file > Report settings > Query-limit simulations**, conferida após reabrir o PBIP, mostrou **No query limits**. Embora a opção Auto tenha sido indicada como selecionada e salva na sessão anterior, ela não persistiu. O `report.json` continua serializando `None`; não foi feita edição manual do PBIR. A simulação de capacidade e seus limites customizados permanecem pendentes. O painel de filtros continua recolhido (`expanded=false`), como registrado no relatório.

## Diagrama e integridade do modelo

`diagramLayout.json` foi preservado para versionamento. O JSON é válido, contém um diagrama e 10 nós; nomes e lineage tags correspondem às definições TMDL, inclusive:

- `_Medidas`: `f7c8fdce-971a-4906-847e-1e8b96afaafc`;
- `FatoCustoFulfillment`: `5d333d48-a609-53b8-8544-c0a4c35d2792`;
- `FatoDevolucoes`: `0dab837c-3c08-513f-9e6e-0afec6e953fd`.

As coordenadas e as caixas preexistentes foram mantidas. O PBIP abriu no Power BI Desktop 2.158.1177.0 sem erro e o painel Dados mostrou as 10 tabelas. O inventário TMDL confirmou 55 medidas, todas em `_Medidas`, 11 Display Folders e 21 relações (19 ativas, 2 inativas). A inspeção estática do layout confirmou os nós e referências; a posição no canvas de Model View não foi verificada nesta fase.

## Regressão DAX

Uma consulta de leitura foi executada na DAX Query View do modelo Import local; não houve refresh, mudança no modelo, alteração PostgreSQL ou chamada ao serviço Power BI. Ela retornou sucesso e uma linha com os oito indicadores. Os totais e valores monetários coincidem com o baseline:

| Indicador | Esperado | DAX observado |
|---|---:|---:|
| Pedidos | 120.000 | 120.000 |
| Pedidos concluídos | 116.305 | 116.305 |
| Receita antes de devoluções | R$ 949.319.764,19 | R$ 949.319.764,19 |
| Receita após devoluções | R$ 922.588.975,45 | R$ 922.588.975,45 |
| COGS ajustado | R$ 717.455.650,26 | R$ 717.455.650,26 |
| Lucro bruto | R$ 205.133.325,19 | R$ 205.133.325,19 |
| Margem bruta | 22,23% | 0,22 como razão no grid DAX (arredondada a duas casas) |
| Receita YTD 2026 antes de devoluções | R$ 234.603.762,77 | R$ 234.603.762,77 |

A margem é armazenada como razão decimal. A expressão avaliada retornou aproximadamente `0,22`; seu formato percentual aprovado e sua precisão (`22,2345302886815%`, exibida como `22,23%`) estão registrados e já haviam sido reconciliados na Fase 4.5C. A consulta temporária foi descartada ao fechar o Desktop; não foi salva no PBIP.

## Documentação e fluxo futuro

`powerbi/README.md` documenta o protocolo: registrar status, fechar o Desktop antes de editar, limitar alterações, validar e salvar pelo Desktop, comparar antes/depois e fazer staging explícito. Também orienta não usar `git add -A`, `assume-unchanged`, `skip-worktree`, alterações globais de Git, `.gitattributes` sem evidência ou descarte de diffs desconhecidos.

## Git, escopo e pendências

Arquivos seguros para o checkpoint desta entrega: `diagramLayout.json`, README, este relatório e a referência da fase no plano/auditoria. Permanecem fora do commit:

- `report.json`, porque a opção Auto não persistiu e o arquivo mantém `None`;
- os 13 TMDLs aprovados e `_Medidas.tmdl`, porque o Desktop recriou diferenças apenas textuais de EOF.

O staging é explícito; as diferenças PBIR/TMDL serão registradas como residuais e não serão ocultadas. O backup e os artefatos de consulta não entram no Git. Nenhuma mudança PostgreSQL, refresh, dashboard, publicação, push, merge, rebase ou tag foi executada.

**Classificação:** `FASE 4.6.1 PARTIAL — DESKTOP SERIALIZATION PENDING`. O layout e as regressões essenciais foram preservados/verificados. Para concluir PASS, ainda é necessário obter a persistência de Auto pela interface e decidir o tratamento durável do EOF que o Desktop regenera; a regularização não continuará por tentativas repetidas.
