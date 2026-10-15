# Fase 5.8.1 — Estado inicial dos dashboards e licença MIT

**Data:** 2026-10-15
**Resultado:** **PARTIAL — PBIR preparado estaticamente; validação no Desktop e novo PBIX pendentes**
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

**Validação no Power BI Desktop: não executada.** A sessão atual não expôs um aplicativo Windows controlável para o Desktop. Nenhuma página foi aberta, salva ou reaberta pelo Desktop nesta fase; nenhum screenshot novo foi capturado. Por isso não se afirma que o Desktop reconheceu ou persistiu essas mudanças, nem que a composição inteira foi vista no viewport.

## PBIX demonstrativo

O PBIX externo não foi alterado, exportado ou substituído. A cópia existente continua identificada pela homologação anterior:

- Caminho: `D:\Codex\ProjetoBI-Distribution\Fase-5.7.2\ProjetoBI-InfoTech-Demo.pbix`
- Tamanho: 38.910.666 bytes
- SHA-256: `398EB0B3866810F2ABD787AC71FAE4ED9CD8327A84589BF43567F7CA85A399D2`
- Estado anterior: Visão Executiva, filtros fechados, Canal/Loja Todos e período 04/01/2026–30/09/2026; a versão anterior não continha o enquadramento desta fase comprovado.

**G3 — novo PBIX: PENDENTE.** Sem operação nativa no Desktop, não foi possível salvar a versão corrigida, fechar e reabrir, confirmar dados/modelo e produzir novo tamanho/hash. Não foi editado o contêiner binário. A validação isolada sem PostgreSQL permanece pendente, sem promoção de status.

## Licença MIT

O usuário confirmou expressamente o titular **Marcelo Vinicius Moreira Barud Torres**. Foi criado `LICENSE` com o texto integral da licença MIT, ano 2026, e o README agora identifica a licença e resume permissões/condições sem ampliar seu alcance. Bibliotecas, marcas e outros materiais de terceiros permanecem sujeitos a suas licenças e termos próprios. O texto adotado corresponde à referência da [Open Source Initiative — MIT License](https://opensource.org/license/mit).

## Documentação e evidências

Foram atualizados `README.md`, `docs/portfolio/PBIX_DEMO_GUIDE.md`, `docs/portfolio/GITHUB_RELEASE_DRAFT.md`, `docs/PROJECT_COMPLETION_PLAN.md` e `docs/powerbi/INFOTECH_DESIGN_SYSTEM.md`. A minuta da Release agora usa “ProjetoBI InfoTech” no título e avisa que o PBIX associado ao hash registrado é a versão anterior, ainda não substituída.

As evidências estáticas estão em `docs/powerbi/evidence/phase-5.8.1/`, com resumo estruturado e limitações de captura. Não há screenshots do Desktop nesta fase, pois nenhuma janela nativa ficou disponível para controle.

## Gates

| Gate | Estado | Evidência e limite |
|---|---|---|
| G1 — PBIR | **PARTIAL** | Configuração estática `FitToPage` nas cinco páginas e Visão Executiva ativa; falta reconhecer/salvar/reabrir no Desktop. |
| G2 — interatividade | **PARTIAL** | Grupos e bookmarks existentes estão estruturalmente coerentes; não reexercitados em runtime nesta fase. |
| G3 — PBIX | **PENDENTE** | Artefato não atualizado nem reaberto. PBIX anterior e hash preservados. |
| G4 — licenciamento | **PASS** | Texto MIT integral, ano e titular confirmados; README atualizado com ressalva de terceiros. |
| G5 — integridade | **PASS estático** | Dez tabelas, 55 medidas e 21 relações verificadas; nenhuma definição semântica alterada, nenhum refresh ou acesso ao PostgreSQL. |
| G6 — Git | **PASS após commit parcial** | Somente alterações desta fase serão commitadas; alterações locais anteriores ficam fora; sem push. |

## Resultado e continuação necessária

O pacote documental, a licença e a configuração PBIR estática estão preparados. A fase permanece **PARTIAL** até validação visual/funcional do PBIP no Desktop, salvamento/reabertura e geração de um novo PBIX pelo Desktop. O artefato anterior não deve ser divulgado como se incluísse o novo estado. A exportação PDF, hash e tamanho finais só poderão ser registrados após essa etapa; não se executa refresh nem teste no PostgreSQL.

Commit local desta entrega parcial: `fix(powerbi): prepara abertura parcial e adiciona licenca MIT`. Nenhum push, merge, rebase, tag, Release ou alteração de visibilidade foi realizado.
