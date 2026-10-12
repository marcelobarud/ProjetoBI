# Auditoria da working tree Power BI

**Data:** 2026-10-12.
**Branch/HEAD observado:** main, a7899e2 (origin/main), commit feat(powerbi): implementa medidas DAX financeiras.
**Classificação:** AUDIT PASS — CLEANUP PLAN READY.
**Resultado desta fase:** somente documentos novos e resumos atuais foram versionados. As 15 alterações PBIP preexistentes foram preservadas fora do commit.

## 1. Inventário inicial

Na entrada havia 15 arquivos rastreados modificados, nenhum arquivo não rastreado e nenhuma mudança staged. HEAD era a7899e2, branch main acompanhando origin/main. Nenhum remoto foi alterado. O diff inicial era 66 linhas adicionadas, sem remoções: 14 em report.json, 39 em diagramLayout.json e uma linha em branco final em cada um dos 13 TMDLs.

| Arquivo | Estado e diferença inicial | Origem provável / classe | Risco e recomendação |
|---|---|---|---|
| powerbi/ProjetoBI.Report/definition/report.json | Modified; painel outspacePane colapsado, queryLimitOption=None e limites customizados já existentes | F — origem não determinada; o painel é estado de UI, limite de consulta pode afetar a simulação | Médio: preservar. Usuário deve decidir se a opção None é intencional antes de release. |
| powerbi/ProjetoBI.SemanticModel/definition/cultures/pt-BR.tmdl | Modified; somente linha em branco ao fim | C — normalização textual provável | Baixo conteúdo, mas preexistente; não editar sem aprovação. |
| powerbi/ProjetoBI.SemanticModel/definition/database.tmdl | Modified; somente linha em branco ao fim | C — normalização textual provável | Baixo conteúdo, mas preexistente; não editar sem aprovação. |
| powerbi/ProjetoBI.SemanticModel/definition/model.tmdl | Modified; somente linha em branco ao fim | C — normalização textual provável | Baixo conteúdo, mas preexistente; não editar sem aprovação. |
| powerbi/ProjetoBI.SemanticModel/definition/relationships.tmdl | Modified; somente linha em branco ao fim | C — nova diferença após ciclo Desktop; provável serialização ao salvar, evidência temporal | Baixo conteúdo, origem provável Desktop; manter até aprovação. |
| powerbi/ProjetoBI.SemanticModel/definition/tables/DimCalendario.tmdl | Modified; somente linha em branco ao fim | C — normalização textual preexistente | Baixo conteúdo, mas preexistente; não editar sem aprovação. |
| powerbi/ProjetoBI.SemanticModel/definition/tables/DimCanal.tmdl | Modified; somente linha em branco ao fim | C — normalização textual preexistente | Baixo conteúdo, mas preexistente; não editar sem aprovação. |
| powerbi/ProjetoBI.SemanticModel/definition/tables/DimCliente.tmdl | Modified; somente linha em branco ao fim | C — normalização textual preexistente | Baixo conteúdo, mas preexistente; não editar sem aprovação. |
| powerbi/ProjetoBI.SemanticModel/definition/tables/DimLoja.tmdl | Modified; somente linha em branco ao fim | C — normalização textual preexistente | Baixo conteúdo, mas preexistente; não editar sem aprovação. |
| powerbi/ProjetoBI.SemanticModel/definition/tables/DimProduto.tmdl | Modified; somente linha em branco ao fim | C — normalização textual preexistente | Baixo conteúdo, mas preexistente; não editar sem aprovação. |
| powerbi/ProjetoBI.SemanticModel/definition/tables/FatoCustoFulfillment.tmdl | Modified; somente linha em branco ao fim | C — nova diferença após ciclo Desktop; provável serialização ao salvar, evidência temporal | Baixo conteúdo, origem provável Desktop; manter até aprovação. |
| powerbi/ProjetoBI.SemanticModel/definition/tables/FatoDevolucoes.tmdl | Modified; somente linha em branco ao fim | C — nova diferença após ciclo Desktop; provável serialização ao salvar, evidência temporal | Baixo conteúdo, origem provável Desktop; manter até aprovação. |
| powerbi/ProjetoBI.SemanticModel/definition/tables/FatoItensPedido.tmdl | Modified; somente linha em branco ao fim | C — normalização textual preexistente | Baixo conteúdo, mas preexistente; não editar sem aprovação. |
| powerbi/ProjetoBI.SemanticModel/definition/tables/FatoPedidos.tmdl | Modified; somente linha em branco ao fim | C — normalização textual preexistente | Baixo conteúdo, mas preexistente; não editar sem aprovação. |
| powerbi/ProjetoBI.SemanticModel/diagramLayout.json | Modified; adiciona nodes _Medidas, FatoCustoFulfillment e FatoDevolucoes com lineage tags e coordenadas | E — mudança de layout; provável escrita/geração pelo Desktop, não é relacionamento | Médio: preservar; layout útil. Versionar se mantiver o diagrama atualizado. |

Não foram encontrados arquivos não rastreados nem scripts TMDLScripts. _Medidas.tmdl não estava modificado na inspeção inicial; sua serialização funcional já pertence a commits anteriores. Não houve cache, PBIX/PBIT ou backup staged.

## 2. Evidência da causa

### Estado do Desktop e teste controlado

O processo local era Power BI Desktop versão 2.158.1177.0, com PBIDesktop.exe aberto sobre powerbi/ProjetoBI.pbip e motor msmdsrv local. Antes do ciclo de salvamento mais recente, foi preservada uma cópia temporária de comparação em C:\Users\D2\AppData\Local\Temp\ProjetoBI-pre-save-b7fd195824904017bbfa76896aabfcc5. A cópia não está no Git.

Os cenários B e C ocorreram no ciclo controlado documentado na Fase 4.5C: abrir, atualizar, o usuário salvar, fechar e reabrir. Comparar com o snapshot anterior ao salvamento mostrou que dez TMDLs já tinham as mesmas linhas em branco antes desse ciclo. Três TMDLs — relationships.tmdl, FatoCustoFulfillment.tmdl e FatoDevolucoes.tmdl — não estavam no snapshot e passaram a diferir apenas por uma linha em branco final. Seus mtimes são 19:00:07 e a instância reaberta iniciou às 19:00:12. A proximidade de horário e o conteúdo idêntico exceto EOF tornam a serialização do Desktop a origem provável dessas três mudanças, mas não provam isoladamente qual processo escreveu os bytes. Nenhuma alteração semântica foi observada nesses três arquivos.

O cenário A (abrir e fechar sem salvar) não foi executado separadamente nesta auditoria: demandaria outra intervenção manual no Desktop e não acrescentaria evidência necessária depois do cenário B/C já observado. Não foi executado refresh novo nesta Fase 4.6. O refresh completo e a reabertura sem erro foram validados na Fase 4.5C; o usuário reportou sem erros. Nenhum processo foi encerrado à força.

### Classificação arquivo a arquivo e causas

- report.json: conteúdo textual com estado de painel e configuração queryLimitOption=None. Não é whitespace nem mera quebra de linha. A alteração aparece no snapshot anterior ao último ciclo de salvamento e o mtime precede a instância atual. Portanto não se pode atribuir a origem à última gravação Desktop nem ao Codex. A opção deve ser revisada antes da publicação; não foi alterada.
- diagramLayout.json: adiciona três caixas posicionadas e seus lineage tags; não troca relações nem IDs de modelo. O layout já estava no snapshot pré-salvamento. O Desktop gerencia diagramas no PBIP, então autoria do Desktop é provável, mas a sessão que o criou não é identificável. O layout deixa novas tabelas visíveis e não deve ser descartado automaticamente.
- Dez TMDLs: só têm linha em branco final e estavam iguais ao snapshot pré-salvamento; mudanças existentes ao entrar. Não há mudança de declaração, expressão, lineage tag, chave, tipo ou relacionamento.
- Três TMDLs: mesma diferença de EOF, ausente no snapshot e com timestamp do processo de salvamento; autoria Desktop provável, conteúdo sem efeito semântico observado.
- Normalização CRLF/LF: não é a causa das alterações observadas. Arquivos estão no índice LF e no working tree CRLF devido à configuração autocrlf true. O diff Git mostra uma linha em branco adicional, não reescrita em massa de finais de linha.
- Codex: nenhum dos 15 arquivos foi editado pelo Codex nesta auditoria. Os relatórios e resumos próprios desta fase são novas alterações separadas e serão staged explicitamente.

Há evidência de serialização do Desktop como uma fonte de ruído, mas nem toda modificação acumulada vem do mesmo evento. A working tree contém mudanças de sessões/fases anteriores, alterações automáticas prováveis de EOF e ao menos uma configuração de relatório de intenção não identificada.

## 3. Regras Git e versionamento

- Não existe .gitattributes. git config informa core.autocrlf=true (configuração de sistema) e core.filemode=false (configuração local do repositório); core.eol e core.safecrlf não estão definidos.
- git ls-files --eol confirma i/lf e w/crlf para README, plano, PBIR, TMDL e diagrama. A configuração mantém o checkout CRLF e o índice LF. Não se recomenda mudar configuração global nem executar renormalização em massa: não explica o diff de uma linha em branco e poderia criar ruído extenso.
- .gitignore já ignora **/.pbi/, *.pbix, *.pbit, caches, temporários, logs, segredos e ambiente local, enquanto mantém PBIP, PBIR e TMDL versionáveis. git check-ignore confirmou regras para estado .pbi. Nenhuma política nova é necessária com a evidência atual.
- Os 13 baselines SQL oficiais estão rastreados e sem alteração. Não há TMDLScripts no workspace. .env é ignorado. Nenhuma credencial foi impressa, incluída ou staged.
- Definições PBIP/PBIR/TMDL e diagrama necessários ao projeto devem continuar versionados. Não usar .gitignore para ocultar arquivos já rastreados, não remover tracking e não trocar PBIP por arquivo binário.
- Referência Microsoft sobre diagramas PBIP: [projetos Power BI](https://learn.microsoft.com/en-us/power-bi/developer/projects/projects-report). Layouts são artifacts de projeto geridos pelo Desktop.

## 4. Regularização recomendada

### Recomendação imediata: conservadora

Preservar todos os 15 arquivos. Manter o commit desta auditoria restrito a dois relatórios e três resumos atuais. Não modificar report.json, diagramLayout.json ou TMDL preexistente sem a decisão do usuário. Antes de release, revisar a configuração queryLimitOption=None no Desktop. Isso mantém a rastreabilidade e não corre risco de perda.

### Regularização intermediária (aguarda aprovação do usuário)

1. Confirmar que o Desktop está fechado; obter backup fora da pasta de trabalho e hashes dos 15 arquivos; registrar git status e diffs integrais.
2. Abrir report.json com diff revisado. Confirmar no Desktop a intenção do limite de consulta. Só então decidir explicitamente se a propriedade None e o estado do painel devem permanecer.
3. Preservar diagramLayout.json se as três caixas adicionadas são desejadas; não remover nodes ou lineage tags por estética.
4. Comparar os 13 TMDLs contra HEAD. Somente depois de uma confirmação de equivalência do PBIP e do snapshot de segurança, normalizar a linha adicional de EOF nas 13 definições e validar o projeto em uma cópia de trabalho/abertura controlada. As três prováveis mudanças de salvamento ficam no mesmo grupo técnico; o histórico do snapshot identifica que as outras dez precediam o último ciclo.
5. Stage explícito apenas dos arquivos cuja intenção foi confirmada, revisar diff staged, abrir/salvar/reabrir se a fase autorizar e registrar novas serializações. Manter qualquer resíduo que não esteja explicado.

Nenhum comando de limpeza/descarte foi executado. Se aprovado, usar editor/alteração delimitada com backup e validação, não git reset --hard, git clean, stash, restore amplo, assume-unchanged ou renormalização. Os 13 arquivos TMDL seriam tocados somente após backup e confirmação da nova expectativa do usuário.

### Alternativas

| Alternativa | Benefícios | Risco / perda | Impacto PBIP | Complexidade / manutenção | Avaliação |
|---|---|---|---|---|---|
| Conservadora | Preserva toda a evidência e só melhora inspeção/staging | Mínimo; não remove ruído atual | Nenhum | Baixa; processo simples | Recomendada agora |
| Intermediária | Resolve linhas EOF comprovadas e decide o estado de report/layout | Médio se opção funcional ou layout for removido sem análise; exige backup e autorização | Mantém PBIP textual e valida cada serialização | Média; checkpoint antes/depois do Desktop | Recomendada somente após a decisão do usuário |
| Estrutural | Pode padronizar finais de linha e estabelecer política explícita para artefatos | Alto potencial de renormalização e conflitos; causa atual não justifica | Pode gerar diffs amplos em PBIR/TMDL; exige teste em cópia | Alta; manutenção de atributos e possíveis exceções Desktop | Não recomendada com a evidência atual |

## 5. Fluxo recomendado para as próximas fases

1. Registrar branch, HEAD, estado por arquivo e diff antes de abrir o PBIP.
2. Confirmar que não há edição concorrente; salvar e fechar o Desktop antes de editar TMDL externamente.
3. Fazer alteração delimitada e revisar somente os arquivos planejados.
4. Abrir o PBIP e validar a mudança no Desktop; atualizar somente quando o escopo da fase autorizar.
5. Salvar e fechar normalmente pelo Desktop.
6. Reexaminar status e diff; separar serialização do Desktop de mudanças funcionais e registrar cada arquivo novo.
7. Resolver o propósito de propriedades de relatório/layout antes de commit; não presumir que UI state é descartável.
8. Stage caminhos explícitos, revisar diff staged, rodar diff --cached --check e verificar segredos/caches/dados.
9. Commit local autorizado; registrar hash e alterações residuais ainda não resolvidas.

O protocolo concentra o esforço nos mecanismos observados: serialização após salvar, coexistência de edições entre processos e uma opção do PBIR de intenção incerta. Não se recomenda alterar configurações globais nem introduzir regras .gitattributes sem nova prova de necessidade.

## 6. Respostas e decisões

**Por que a working tree acumula alterações?** Porque o PBIP é um conjunto de arquivos editáveis; o Desktop serializa estado do modelo/diagrama e acrescentou três linhas em branco finais a TMDLs no ciclo observado. Outras alterações já estavam presentes antes do ciclo. report.json contém ainda uma configuração de consulta e painel cuja autoria e intenção não foram estabelecidas. Portanto não existe uma única causa nem um único save que explique todos os 15 arquivos.

**Quais arquivos precisam continuar versionados?** O projeto .pbip, definições PBIR e TMDL e o layout do diagrama quando atualizado/intencional. .pbi, PBIX/PBIT, credenciais, caches e arquivos locais não compartilháveis ficam ignorados. Os baselines SQL permanecem fonte oficial e não foram alterados.

**Quais alterações são seguras para regularização?** O conteúdo semanticamente neutro das 13 linhas em branco finais é candidata técnica a normalização, mediante confirmação e autorização por ser trabalho preexistente. Nenhuma alteração preexistente foi regularizada nesta fase. A diferença do diagrama não é mudança de relação, mas representa layout e foi preservada. A propriedade queryLimitOption=None requer decisão sobre publicação.

**O que depende do usuário?** Aprovação para alterar qualquer um dos 15 arquivos preexistentes; sobretudo confirmar o propósito do limite de consultas e se deseja manter o novo layout. Sem essa decisão, preservar o conteúdo atual.

## 7. Commit e estado posterior

O commit de Fase 4.6 contém exclusivamente relatórios e atualizações documentais desta fase. As 15 alterações anteriores permanecem fora do commit. Não houve push, merge, rebase, descarte de mudanças, alteração de configuração Git, alteração da base PostgreSQL nem limpeza da working tree.

### Atualização posterior — Fase 4.6.1

A autorização de regularização foi concedida numa fase separada. O resultado parcial, as mudanças seguras, as diferenças residuais e as verificações estão registrados em [POWERBI_WORKTREE_REGULARIZATION.md](POWERBI_WORKTREE_REGULARIZATION.md). Esta atualização não reescreve a classificação histórica nem o estado de entrada descrito acima.
