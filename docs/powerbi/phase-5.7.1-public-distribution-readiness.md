# Fase 5.7.1 — Regularização do PBIR e preparação para distribuição pública

**Data:** 2026-10-15 (America/Sao_Paulo)

**Checkpoint de entrada:** `e0654b1`

**Resultado:** `PARTIAL — candidato PBIR estático preparado; abertura isolada no Desktop e validação de dados distribuíveis pendentes`

**Design System:** InfoTech v0.3

## 1. Escopo e preservação

O objetivo foi regularizar seletivamente as diferenças estruturais entre o PBIR versionado e o workspace, preparar a rota de distribuição pública e preservar as alterações que já existiam localmente. Não houve atualização de dados, conexão ao PostgreSQL, alteração do modelo semântico/DAX/Power Query, criação de PBIX, publicação, Release, push, merge, rebase ou tag.

Antes das alterações, foi criado um snapshot externo das 105 entradas rastreadas ou não rastreadas que já estavam modificadas, sem ler nem incluir cache ignorado. O snapshot fica fora do repositório em `%TEMP%` como `ProjetoBI-Phase5.7.1-preflight-20261015-082407.zip` (SHA-256 `AE9E78BF908B7A15466C0E329725A51656EA2BF9981F974888151A929C051C47`). As mudanças legadas em PBIR, TMDL e evidências permanecem na working tree e não foram selecionadas para este commit.

## 2. Estado de entrada e decisão dos 20 diffs

O ponto de partida continha 93 arquivos PBIR JSON modificados: 20 diferenças de conteúdo/estrutura e 73 diferenças equivalentes após normalização canônica da ordem das propriedades. Os 73 casos são serialização e ficaram fora do commit. A tabela `evidence/phase-5.7.1/pbir-diff-disposition.csv` examina os 20 casos um a um.

Decisões aplicadas:

- As 12 definições locais de slicers sincronizados refletem seleções transitórias de teste (período, Canal e Loja) e foram excluídas para não persistir escolhas temporárias como padrão.
- Os quatro estados `isHidden` dos painéis por bookmark foram excluídos; o estado local diferia do estado base de cada página e não havia motivo para uniformizá-los sem teste no candidato.
- A textbox “InfoTech” executiva tem diferença local de schema/serialização e removeu `bold`; essa alteração visual não foi promovida sem homologação equivalente no candidato.
- A seleção de página ativa (Devoluções vs. Produtos) e opções globais de report (`queryLimitOption` e painel recolhido) foram tratadas como estado transitório/configuração não aprovada e ficaram fora.
- Na definição da página Devoluções, o archive de entrada continha 30 `visualInteractions` cujos source/target IDs pertencem à página Custos e Margens, não aos 18 visuais de Devoluções. A cópia local não tinha esse array. A correção é remover essas 30 referências inválidas, preservando a interação nativa padrão da página. Nenhuma outra definição PBIR foi incorporada.

Um candidato isolado foi montado fora do workspace a partir de `HEAD e0654b1` e somente da definição local corrigida de Devoluções (`f5502600000000000001/page.json`). A validação registrada foi feita sobre esse candidato, não sobre o projeto aberto no Desktop.

## 3. Validação técnica do candidato

O manifesto em `evidence/phase-5.7.1/candidate-validation.json` registra o archive temporário e os resultados. Foram conferidos:

- 117 arquivos JSON do relatório parseiam; cinco páginas mantêm canvas 1920×1080 e `FitToWidth`.
- Cada página preserva os grupos sincronizados `InfoTech.PeriodoComercial`, `InfoTech.Canal` e `InfoTech.Loja`.
- A página Devoluções tem 18 visuais, zero entradas `visualInteractions` externas e nenhuma referência inválida nas cinco páginas.
- Os dez bookmarks estão estruturalmente completos, cada seção tem `visualContainers` e os destinos correspondem a visuais existentes.
- As definições do modelo permanecem em 10 tabelas, 55 medidas, 11 pastas de exibição e 21 relacionamentos; os dois gráficos de linha aprovados mantêm precisão de rótulo `1L`.
- O recurso SVG fonte e o recurso registrado coincidem no candidato.

**Verificação visual manual:** com o Power BI Desktop aberto pelo usuário, observei a página Devoluções renderizada, com quatro cartões e os gráficos de tendência/categorias/produtos visíveis, sem modal de erro. A imagem mostrava a página do workspace em escala 47%. Não foi executado refresh nem save. A janela aberta representa o projeto de trabalho, não o candidato limpo; não usei essa observação como prova de abertura do candidato.

O candidato temporário não foi aberto, salvo e reaberto isoladamente no Desktop nesta execução. Assim, não há validação de bookmarks/interações do candidato em runtime. Os cenários das fases anteriores servem como evidência histórica do workspace e não substituem esse teste.

## 4. Plano para distribuição e dados

### GitHub público — código-fonte PBIP

O PBIP/TMDL/PBIR versionado pode ser apresentado como código-fonte e arquitetura do projeto, acompanhado por instruções de configuração. A abertura local ainda depende de PostgreSQL e configuração local das credenciais. Não publicar credenciais, `.env`, cache `.pbi`, performance exports ou connection strings com segredos. Confirmar licença, README público e instruções de clone/abertura numa fase própria.

### PBIX offline — pacote sintético futuro

O PBIX futuro deve carregar um dataset de portfólio explicitamente sintético para funcionar offline no Power BI Desktop. Esta fase não criou nem aprovou um PBIX. Antes de uma distribuição, deve-se auditar o conteúdo real das tabelas importadas e dos metadados do modelo. Campos de nomes, `notes`, endereços, telefone, e-mail, referência externa e descrições livres merecem validação ou remoção/redação. Dados Faker podem parecer nomes reais; “sintético” por intenção do gerador não é prova de que cada registro seja seguro para redistribuição.

O PBIX incorpora dados consultáveis por seus destinatários. Identificadores de negócio, chaves e granularidade também devem ser avaliados por risco de ligação/reidentificação. Não presumir aprovação de privacidade sem examinar o extract efetivo. O modelo atual usa partições Import conectadas a `PostgreSQL.Database` em `127.0.0.1:5432`, database `projeto_bi`; metadados de conexão podem continuar presentes mesmo que a cópia abra offline. A futura cópia deve testar abertura sem rede, sem refresh, revisar metadados e realizar varredura de segredos.

### Portfólio LinkedIn

Uma fase posterior pode publicar capturas ou vídeo curto que mostrem páginas, KPIs e navegação, acompanhados por explicação do dataset sintético, escopo, limitações e instruções para encontrar o código-fonte e o PBIX. Inspecionar imagens para dados pessoais, caminho local, credenciais, nomes de contas e conteúdo incidental antes de publicar. Nenhuma publicação ou postagem foi feita.

### Sequência recomendada

1. Abrir no Desktop um clone/archive temporário limpo do candidato PBIR, navegar pelas cinco páginas e verificar filtros, bookmarks e interações sem refresh.
2. Se a abertura passar, salvar/fechar/reabrir o candidato e registrar versão do Desktop e resultado observável.
3. Em fase autorizada separadamente, definir contrato de dataset público, produzir cópia sintética e remover ou mascarar campos de risco conforme inspeção dos valores.
4. Gerar PBIX de distribuição sem reutilizar o `.pbi` local; testar abertura offline, visuais, filtros, metadados e ausência de segredos. Registrar SHA-256 e tamanho real.
5. Preparar README/licença e evidências do portfólio. Decidir de modo separado se/como um Release do GitHub será criado e publicar conteúdo LinkedIn somente após revisão.

Power BI Service, gateway, refresh agendado e distribuição operacional foram retirados da rota crítica desta modalidade pública Desktop/offline. Os registros históricos das fases anteriores permanecem intactos.

## 5. Gates

| Gate | Estado | Evidência e limite |
|---|---|---|
| A — Diferenças PBIR e integridade estrutural | **PASS estático** | Os 20 diffs foram classificados; só a correção de Devoluções compõe o candidato. 117 JSON válidos, estrutura do modelo, filtros sincronizados, bookmarks e interações válidos. Não equivale a compilação pelo Desktop. |
| B — Abertura/uso no Power BI Desktop | **PARTIAL** | O workspace aberto renderizou Devoluções sem erro e sem refresh. O candidato isolado ainda não foi aberto; runtime de interações/bookmarks e reabertura não estão validados para esse candidato. |
| C — Documentação e escopo de distribuição | **PASS documental** | PBIP público, PBIX sintético offline e portfólio LinkedIn estão separados; Service não é dependência da rota. Plano e limites estão registrados. |
| D — Segurança e adequação do conteúdo público | **PARTIAL** | Dependências e classes de campos de risco estão inventariadas. Nenhum dado de linha foi lido e nenhum PBIX foi produzido; logo privacidade do extract e remoção de metadados ainda não foram aprovadas. |

**Resultado geral: PARTIAL.** O checkpoint tecnicamente útil é o candidato PBIR estático com a correção isolada. Para fechar a Fase 5.7.1 sem ressalvas, falta abrir/testar/reabrir o candidato isolado e registrar a revisão dos dados e metadados do pacote que vier a ser distribuído. Essa pendência não autoriza gerar/publicar PBIX ou Release automaticamente.

## 6. Git e artefatos

Somente o arquivo `page.json` corrigido de Devoluções, este relatório, a linha correspondente no plano mestre e as evidências desta fase devem compor o commit local. Nenhum dos 73 JSONs equivalentes, os outros 19 diffs estruturais, `pt-BR.tmdl`, caches, ZIPs históricos ou `PowerBIPerformanceData.json` fazem parte da seleção. Não houve push, merge ou publicação.

Evidências de apoio: `evidence/phase-5.7.1/`. Pacote ZIP da fase: `evidence/archives/fase-5.7.1-evidencias.zip`.
