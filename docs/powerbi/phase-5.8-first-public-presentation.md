# Fase 5.8 — Preparação da primeira apresentação pública

**Data:** 2026-10-15
**Resultado:** **PASS — materiais de apresentação preparados; publicação não realizada**
**Commit de entrada:** `563774aafe3beb944bfa69e7f5b08ad97d335cd1` (`main`, sincronizada com `origin/main`)

## Objetivo e limites

Preparar materiais revisáveis para apresentar publicamente o ProjetoBI sem publicar, enviar alterações, criar tags ou Releases, alterar a visibilidade do repositório ou iniciar um ramo de visuais HTML/personalizados. Não houve refresh, acesso ao PostgreSQL nem mudança em dashboards, modelo ou dados.

O escopo incluiu uma página inicial pública para o repositório, galeria das cinco páginas, guia curto do PBIX, minuta de GitHub Release `v0.1-demo`, resumo para LinkedIn, roteiro opcional de vídeo, relatório desta fase e atualização do plano mestre. Nenhum texto foi publicado externamente.

## Estado inicial e preservação

No início, `main` estava no commit `563774a`, igual a `origin/main`, com staging vazio e 104 caminhos locais modificados ou não rastreados preexistentes. Esses caminhos foram preservados e excluídos do staging. A remoção temporária do README durante uma edição interrompida foi identificada e o README foi recriado com o conteúdo de apresentação; nenhuma outra alteração preexistente foi substituída deliberadamente.

## Conteúdo preparado

- `README.md`: propósito, estado de desenvolvimento, dados sintéticos, arquitetura, escopo correto das 41 tabelas operacionais versus 10 tabelas semânticas, cinco páginas, participação assistida por IA, limitações e links de documentação.
- `docs/portfolio/images/`: galeria com cinco imagens das páginas Visão Executiva, Análise Comercial, Produtos e Categorias, Custos e Margens e Devoluções.
- `docs/portfolio/PBIX_DEMO_GUIDE.md`: abertura e navegação, versão Desktop observada, período dos dados, aviso para não atualizar e limites de homologação.
- `docs/portfolio/GITHUB_RELEASE_DRAFT.md`: minuta `v0.1-demo`, arquivo candidato, tamanho e hash, com pendência offline declarada.
- `docs/portfolio/LINKEDIN_BRIEF.md`: resumo curto e roteiro opcional de 60–90 segundos. São rascunhos, não publicações.
- `docs/portfolio/security-scan.json`: resumo estruturado do escopo e achados de segurança desta preparação.

## Proveniência visual

As cinco imagens têm 2050 × 1175 pixels e foram renderizadas a partir das cinco páginas do PDF exportado nativamente pelo Power BI na Fase 5.7.2. Não são capturas atuais do Desktop nem evidência de uma nova validação visual nesta fase. A fonte preservada é `docs/powerbi/evidence/phase-5.7.2/pbix-exportado-powerbi.pdf` (467.549 bytes). A página Comercial mostra barras de rolagem horizontais e a visualização de Custos tem eixo denso, limitações também descritas nos registros de validação. A galeria mantém essa proveniência visível.

## Artefato demonstrativo e licença

O PBIX candidato está fora do Git, em `D:\Codex\ProjetoBI-Distribution\Fase-5.7.2\ProjetoBI-InfoTech-Demo.pbix`, com 38.910.666 bytes e SHA-256 `398EB0B3866810F2ABD787AC71FAE4ED9CD8327A84589BF43567F7CA85A399D2`, conforme a Fase 5.7.2.1. A abertura, renderização de cinco páginas, filtros e persistência foram validados no Desktop 2.158.1304.0. O teste offline sem PostgreSQL permanece **NOT TESTED**, portanto a homologação do PBIX segue **PARTIAL — OFFLINE VALIDATION PENDING**. O guia não recomenda refresh ou conexão à origem.

Não existe arquivo LICENSE e nenhuma licença foi presumida ou criada. As permissões de reutilização não foram concedidas por inferência.

## Exame de segurança e privacidade

Uma busca direcionada por padrões de alta confiança foi feita na árvore Git e no histórico alcançável de 65 commits. Nenhuma ocorrência desses padrões foi encontrada. `.env` permanece ignorado e não foi lido; `.env.example` contém somente nomes de variáveis e valores vazios. A triagem de nomes de entradas de arquivos ZIP rastreados não encontrou nomes suspeitos. Isso é uma revisão proporcional, não prova de ausência de todo dado sensível.

**Achado informativo de baixa severidade:** 12 documentos históricos rastreados contêm caminhos absolutos locais, incluindo o perfil Windows do usuário e `D:\Codex\ProjetoBI`. Não foi identificado valor de credencial associado nos padrões pesquisados. Não se reescreveu o histórico. O repositório continua privado; nenhum push ou alteração de visibilidade ocorreu. Antes de futura exposição pública, o responsável deverá revisar e decidir se autoriza uma limpeza separada do histórico.

O PBIX não foi inspecionado exaustivamente por dentro. A pendência offline e esse limite estão declarados, sem afirmar ausência absoluta de metadados sensíveis incorporados.

## Status dos gates

| Gate | Resultado | Evidência/limite |
|---|---|---|
| Materiais de apresentação | PASS | README, galeria, guia, minuta de Release e resumo/roteiro preparados. |
| Dados e afirmações do projeto | PASS documental | Números e cinco páginas reconciliados com os relatórios de fase; 41 tabelas operacionais não foram confundidas com 10 tabelas semânticas. |
| PBIX demonstrativo | PARTIAL | Desktop reabriu e cinco páginas/filtros persistiram; isolamento sem PostgreSQL ainda não testado. |
| Exame direcionado de segurança | PASS com achado | Nenhum padrão de segredo de alta confiança encontrado; caminhos absolutos históricos requerem decisão antes da publicação. |
| Licença e reutilização | PENDENTE | Não existe LICENSE; nenhuma permissão foi inferida. |
| Publicação | NÃO EXECUTADA | Sem push, tag, Release, upload de PBIX ou alteração de visibilidade. |

## Verificações desta fase

- Revisão de `git status`, branch, HEAD, staging e diff antes da edição.
- Conferência do tamanho e hash SHA-256 do PBIX externo com os metadados da Fase 5.7.2.1.
- Conferência das cinco imagens rasterizadas da exportação PDF e de suas dimensões.
- Revisão de caminhos Markdown planejados, `git diff --check`, escopo do staging e nomes/conteúdo a serem commitados.
- Nenhum teste de banco, refresh ou operação no Desktop foi realizado nesta fase.

## Git e próximo passo

O commit local autorizado é `docs: prepara primeira apresentacao publica do ProjetoBI`. Somente os materiais desta fase, as cinco imagens da galeria e a atualização deste plano mestre devem ser incluídos. As 104 entradas locais preexistentes não pertencem ao commit. Nenhum push, merge, rebase, tag ou Release foi executado.

A preparação documental está concluída, mas isso **não equivale a autorização ou prontidão automática para publicar**. Antes de publicar, decidir sobre a exposição dos caminhos históricos e licença, além de concluir ou aceitar explicitamente a pendência de teste do PBIX isolado.
