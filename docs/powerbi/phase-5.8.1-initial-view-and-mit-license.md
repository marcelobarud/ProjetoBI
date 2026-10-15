# Fase 5.8.1 — Estado inicial dos dashboards e licença MIT

**Data:** 2026-10-15
**Resultado:** **PASS — validação visual e persistência confirmadas pelo usuário; teste offline sem PostgreSQL permanece pendente**
**HEAD de entrada:** `26f22102c9cb3a427f41242b6300bd70eef7c1cd` (`main`, sincronizada com `origin/main`)

## Objetivo e limites

Preparar a abertura das cinco páginas em `FitToPage`, iniciar o relatório na Visão Executiva, manter o painel recolhível de filtros fechado e formalizar a licença MIT. Preservar bookmarks, navegação, filtros, modelo semântico e medidas. A tarefa não alterou DAX, relações, PostgreSQL nem dados; nenhum refresh, publicação, upload, push, tag ou Release foi realizado.

## Estado inicial e preservação

No preflight, `main` estava no commit `26f2210`, igual a `origin/main`, staging vazio e 108 caminhos modificados ou não rastreados na worktree. Esses caminhos continham alterações locais preexistentes; foram preservados e não foram usados como fonte do candidato. Um snapshot externo de proteção dos arquivos PBIR/TMDL e do PBIX foi criado antes de qualquer tentativa de salvamento no Desktop:

- Arquivo externo: `ProjetoBI-Phase5.8.1-preflight-20261015-112150.zip`
- Tamanho: 38.371.211 bytes
- SHA-256: `E6F2A8E3093978981E459197F318A5E67AD98ECACB8EF7D88BB07846AFFBEBC2`
- PBIX de entrada preservado separadamente dentro do snapshot.

O candidato usado na validação estática foi extraído exclusivamente do HEAD versionado e recebeu apenas as alterações previstas nesta fase. Não incorporou os outros arquivos PBIR/TMDL modificados localmente nem o cache ignorado.

## Estado versionado original e alterações propostas

| Página | Opção no HEAD | Candidato | Canvas |
|---|---|---|---|
| Visão Executiva | `FitToWidth` | `FitToPage` | 1920 × 1080 |
| Análise Comercial | `FitToWidth` | `FitToPage` | 1920 × 1080 |
| Produtos e Categorias | `FitToWidth` | `FitToPage` | 1920 × 1080 |
| Custos e Margens | `FitToWidth` | `FitToPage` | 1920 × 1080 |
| Devoluções | `FitToWidth` | `FitToPage` | 1920 × 1080 |

Também foi corrigido o metadado `activePageName`: o HEAD selecionava Produtos e Categorias; o candidato seleciona Visão Executiva. O README e os documentos de distribuição agora deixam claro que esse candidato PBIR ainda não foi validado em runtime.

## Painel de filtros, bookmarks e preservação de seleção

A inspeção estática do HEAD mostrou que os grupos “Painel de filtros” das cinco páginas já estão com `isHidden=true`. Os cinco pares de botões já apontam para os bookmarks Filtros/Fechar filtros da própria página. Os bookmarks mantêm estados opostos (`isHidden=false` ao abrir e `true` ao fechar), `applyOnlyToTargetVisuals=true`, `suppressData=true` e a propriedade `visualContainers` requerida nas seções. A alteração desses componentes não era necessária e foi evitada.

Esse estado confirma a configuração declarada no PBIR, não a operação na interface. A Fase 5.6A.2 e a Fase 5.7.2.1 registraram cenários funcionais anteriores de abrir/fechar, preservação/sincronização de filtros e navegação; esses registros continuam históricos e não substituem uma regressão desta versão.

## Validação do candidato PBIR

O candidato limpo derivado do HEAD foi validado estaticamente:

- 117 arquivos JSON parseáveis;
- cinco páginas 1920 × 1080, todas com `FitToPage`;
- Visão Executiva como página ativa;
- cinco grupos de filtros ocultos no estado inicial;
- dez bookmarks com `visualContainers` presentes;
- modelo com dez tabelas, 55 medidas e 21 relacionamentos.

**Controle direto do Desktop pelo Codex: não disponível.** Nenhuma captura foi obtida nesta sessão. Posteriormente, o usuário confirmou que validou o PBIP no Desktop e que o PBIX corrigido foi salvo e reaberto; as confirmações manuais e a inspeção estática do arquivo são registradas separadamente abaixo.

## Atualização de validação e PBIX — 2026-10-15

O usuário confirmou que validou o PBIP no Desktop e que estava correto. Relatou que a versão PBIX anterior tinha um bookmark aberto e algumas páginas em `FitToWidth`, corrigiu os problemas e salvou a nova versão no caminho abaixo. Após selecionar Visão Executiva como página inicial e salvar/reabrir, o usuário confirmou que essa página abre primeiro e que Devoluções inicia com o painel fechado. Estas são confirmações manuais fornecidas pelo usuário; não houve controle direto da janela do Desktop nesta sessão nem screenshots novos.

- PBIX: `D:\Codex\ProjetoBI-Distribution\Fase-5.7.2\ProjetoBI-InfoTech-Demo.pbix`
- Tamanho verificado após a última gravação: **38.911.257 bytes**
- SHA-256 verificado: `B114FE56897C8376E6FF896ABF4FDF478D8203498925BF255B6E8A8D1CDB8E6B`
- Versão Desktop instalada no ambiente: **2.158.1304.0** (versão que salvou este arquivo não foi capturada diretamente)

O pacote foi aberto somente para leitura como arquivo ZIP/PBIR: 127 entradas, incluindo modelo e definições do relatório. A inspeção confirmou cinco páginas em canvas 1920 × 1080 com `FitToPage`, Visão Executiva ativa, todos os cinco grupos de filtros com `isHidden=true` e dez bookmarks com `visualContainers`, dados suprimidos e estados de abertura/fechamento opostos. O usuário também confirmou que Devoluções inicia com o painel fechado após salvar/reabrir.

A homologação anterior registrada para o PBIX antigo permanece histórica em `docs/powerbi/phase-5.7.2.1-public-pbix-closure.md`; o hash novo acima substitui o hash antigo somente para o artefato atual. O PBIX anterior permanece dentro do snapshot externo de preflight indicado no início deste relatório; não há cópia separada dele na pasta de distribuição.

**G3 — PBIX: PASS por validação manual do usuário e inspeção estrutural.** O usuário confirmou a correção, o salvamento e a reabertura, inclusive o painel fechado em Devoluções. Tamanho/hash e estrutura PBIR foram verificados localmente. A validação isolada sem PostgreSQL continua pendente. Nenhum refresh, alteração no PostgreSQL, DAX, Power Query ou relacionamentos foi realizado; não houve edição direta do contêiner binário.

## Licença MIT

O usuário confirmou expressamente o titular **Marcelo Vinicius Moreira Barud Torres**. Foi criado `LICENSE` com o texto integral da licença MIT, ano 2026, e o README agora identifica a licença e resume permissões/condições sem ampliar seu alcance. Bibliotecas, marcas e outros materiais de terceiros permanecem sujeitos a suas licenças e termos próprios. O texto adotado corresponde à referência da [Open Source Initiative — MIT License](https://opensource.org/license/mit).

## Documentação e evidências

Foram atualizados `README.md`, `docs/portfolio/PBIX_DEMO_GUIDE.md`, `docs/portfolio/GITHUB_RELEASE_DRAFT.md`, `docs/PROJECT_COMPLETION_PLAN.md` e `docs/powerbi/INFOTECH_DESIGN_SYSTEM.md`. A minuta da Release agora usa “ProjetoBI InfoTech” no título e avisa que o PBIX associado ao hash registrado é a versão anterior, ainda não substituída.

As evidências estáticas estão em `docs/powerbi/evidence/phase-5.8.1/`, com resumo estruturado e limitações de captura. Não há screenshots do Desktop nesta fase, pois nenhuma janela nativa ficou disponível para controle.

## Gates

| Gate | Estado | Evidência e limite |
|---|---|---|
| G1 — PBIR | **PASS por relato do usuário e inspeção estática** | O usuário confirmou validação correta do PBIP; PBIX confirma cinco páginas `FitToPage`, canvas Full HD e Visão Executiva ativa. |
| G2 — interatividade | **PASS por relato do usuário; estrutura verificada** | O usuário validou o PBIP e corrigiu o bookmark que estava aberto. Os dez bookmarks mantêm estado abrir/fechar e supressão de dados; Devoluções foi confirmada fechada após reabrir. |
| G3 — PBIX | **PASS por relato do usuário e inspeção estrutural** | PBIX corrigido, salvo e reaberto segundo o usuário; tamanho/hash e pacote verificados. A verificação offline sem PostgreSQL permanece pendente. |
| G4 — licenciamento | **PASS** | Texto MIT integral, ano e titular confirmados; README atualizado com ressalva de terceiros. |
| G5 — integridade | **PASS estático** | Dez tabelas, 55 medidas e 21 relações verificadas; nenhuma definição semântica alterada, nenhum refresh ou acesso ao PostgreSQL. |
| G6 — Git | **PASS após commit parcial** | Somente alterações desta fase serão commitadas; alterações locais anteriores ficam fora; sem push. |

## Resultado e continuação necessária

O PBIP e o novo PBIX foram validados manualmente pelo usuário; a estrutura, as cinco páginas, os bookmarks, o tamanho e o hash foram conferidos localmente. O usuário confirmou que, após salvar e reabrir, o PBIX inicia em Visão Executiva; a inspeção do pacote agora também confirma essa página ativa e `FitToPage` nas cinco páginas. A Fase 5.8.1 está **PASS** para apresentação e persistência. A validação offline sem PostgreSQL permanece pendente e deve continuar identificada como tal em materiais de distribuição. O PBIX anterior não deve ser divulgado como se incluísse o novo estado. Não houve refresh nem teste no PostgreSQL.

Commit local desta entrega parcial: `fix(powerbi): prepara abertura parcial e adiciona licenca MIT`. Nenhum push, merge, rebase, tag, Release ou alteração de visibilidade foi realizado.
