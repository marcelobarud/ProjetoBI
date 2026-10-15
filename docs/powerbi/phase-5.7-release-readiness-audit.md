# Fase 5.7 — Auditoria de prontidão, integridade Git e entrega

**Data:** 2026-10-14 (America/Sao_Paulo)
**Classificação da auditoria:** `FASE 5.7 PASS — RELEASE READINESS AUDIT COMPLETED`
**Commit remoto analisado:** `e91ce059dd44ee34a9d7c3e9134338f441efc6b6` — `docs(powerbi): consolida InfoTech Design System v0.3`
**Design System vigente:** InfoTech v0.3.

> PASS descreve a conclusão da auditoria e a documentação das modalidades. Não significa GO para reproduzir o PBIP nem autorização para publicação. E2 é NO-GO até regularização seletiva.

## 1. Objetivo e escopo

Comparar o workspace, o HEAD e `origin/main`; verificar a inclusão dos commits enviados pelo usuário; examinar estaticamente o PBIP versionado, o modelo, os recursos, dependências e a segurança; classificar riscos e registrar um plano de regularização.

Foram usados `git fetch origin`, `git archive origin/main` extraído em `%TEMP%`, inspeção de Git/arquivos e verificações estáticas. Não houve edição de PBIR, TMDL semântico, DAX, Power Query, dados ou PostgreSQL. O Desktop não foi aberto, não houve refresh, consulta SQL, reconciliação adicional ou publicação.

## 2. Estado Git inicial

- Branch: `main`; HEAD: `e91ce059dd44ee34a9d7c3e9134338f441efc6b6`.
- Upstream: `origin/main`; staging vazio.
- Working tree: 94 arquivos rastreados modificados e 11 não rastreados (105 entradas); diff inicial: 1.665 inserções e 428 remoções. Não havia operação Git em andamento.
- Além desses caminhos, 4 arquivos ignorados nos diretórios `.pbi/` totalizavam 38.803.965 bytes. Um `.env` local ignorado existe; seu conteúdo não foi lido.
- Snapshot externo dos documentos e do estado inicial: `%TEMP%\ProjetoBI-Phase5.7-preflight-20261014-214619.zip`, SHA-256 `1E85C44EBDB064C1DD83BB3B953C525C54D706D42536472C71A05296012A6785`.
- As alterações PBIR/TMDL e evidências existentes foram preservadas. Inventário caminho a caminho: `evidence/phase-5.7/local-change-inventory.csv`.

## 3. Sincronização local/remota

Depois do fetch, `HEAD` e `origin/main` apontaram para o mesmo SHA (`e91ce05`): 0 commits somente locais e 0 somente remotos. `git ls-remote` confirmou que a única branch remota é `main`; não havia tags remotas. Não existe commit remoto posterior a `e91ce05`.

O archive de `origin/main` foi criado fora do workspace e tem SHA-256 `2508DE5F58E883844086F25A1A79B92AD642DE91B9C10EA426B734DCBF02E952`. Manifesto sem URLs ou credenciais: `evidence/phase-5.7/git-manifest.json`.

## 4. Histórico recente e push informado

O reflog local da referência remota registra `origin/main` em `6e470d3` às 20:49, atualização por push para `588f398` às 21:34 e outra atualização por push para `e91ce05` às 21:41 (horário local). O histórico confirma 19 commits de `6e470d3` até `588f398`, seguidos por mais 1 commit (`e91ce05`), totalizando 20 desde aquele tip remoto. Isso confirma os aproximadamente 19 commits reportados e o push posterior da Fase 5.6C. A branch remota observada é somente `main`; nenhum push foi feito nesta auditoria.

## 5. Paridade entre workspace, HEAD e remoto

HEAD e remoto são idênticos; portanto, para arquivos rastreados, o estado B (HEAD) e C (origin/main) coincide. O estado A contém diferenças locais relevantes:

- 94 rastreados modificados: 89 arquivos sob páginas/visuais, 3 bookmarks, 1 `report.json` e 1 `pt-BR.tmdl`.
- Nos 93 JSON PBIR modificados, 20 têm diferença estrutural/de valor após normalização da ordem das propriedades; 73 são equivalentes após essa normalização e diferem em serialização/ordem/fim de linha.
- As diferenças estruturais incluem 12 definições de filtros sincronizados em quatro páginas; 4 estados `isHidden` de controles; duas propriedades visuais no gráfico temporal executivo; a página Devoluções; página ativa; e configuração de relatório.
- O TMDL local adiciona 738 linhas de `linguisticMetadata` em `pt-BR.tmdl`. Os 10 arquivos TMDL das tabelas, medidas e relações não têm diff local versus remoto.
- O workspace está atualmente com Devoluções como página ativa; `origin/main` está com Produtos e Categorias. `queryLimitOption=None` está no PBIR local, mas ausente no remoto. A configuração local também registra o estado recolhido do painel externo.

A existência das cinco páginas em ambos os estados não comprova equivalência: valores de filtro, estados de controles, propriedades visuais e interações persistidas diferem. O registro manual das fases anteriores confirma validação no Desktop do workspace à época, mas não demonstra que o archive remoto foi aberto em outra máquina. A matriz e os 20 caminhos divergentes estão em `evidence/phase-5.7/pbir-comparison.json`.

## 6. Inventário das alterações locais

A classificação detalhada inclui os 94 modificados, 11 não rastreados e 4 arquivos de cache ignorados:

- **A/B — Essencial/funcional:** definições PBIR de páginas, visuais, bookmarks e configuração. O diff pode afetar estado, aparência, filtros/interações ou serialização; não foi incorporado.
- **C — Semântico/metadata:** o arquivo TMDL de cultura contém metadados linguísticos gerados; não altera as medidas/relacionamentos contados.
- **D/F — Documental/histórico:** 9 ZIPs e um README de evidências estão não rastreados. `phase-5.6a.zip` e `archives/fase-5.6a-evidencias.zip` têm SHA-256 idêntico (`DF659B3B1552ED0EBE4A515F6BA25050FE4EAFF2AB542C10AC116C5227231424`); nenhuma cópia foi removida.
- **E — Transitório:** `PowerBIPerformanceData.json` é compatível com exportação Performance Analyzer pelo nome e pelas chaves de topo `version/events/sessionId`; não foi tratado como dependência de produto. Os 4 arquivos `.pbi/` são estado/cache local ignorado.
- **G — Não identificado:** nenhum caminho permaneceu sem categoria no inventário; origem provável está marcada como provável quando não há prova direta.

Recomendação: não adicionar nenhum desses caminhos automaticamente. A seleção de estado PBIR e a decisão sobre TMDL precisam de revisão própria; organizar/remover ZIPs exige conferir finalidade e duplicidade.

## 7. Integridade do PBIP versionado

O `git archive origin/main` contém `ProjetoBI.pbip`, `.Report/definition.pbir`, `.SemanticModel/definition.pbism`, as definições de páginas/visuais/bookmarks e estruturas TMDL esperadas. As cinco páginas existem em ordem, com nomes confirmados, canvas 1920 × 1080 e `FitToWidth`; contêm 17, 22, 19, 22 e 18 visuais, respectivamente.

Os 117 JSONs sob a definição do relatório foram analisados; todos parsearam. `pageOrder` aponta para as cinco pastas existentes. Recursos principais existem e não foram encontrados caminhos absolutos de filesystem nas definições inspecionadas.

**Anomalia material:** a página remota Devoluções contém 30 entradas `visualInteractions`; source/target usam IDs `e510...`, `e520...`, `e300...`, `e400...` da página Custos e Margens, não IDs entre os 18 visuais da própria página Devoluções. Todas as 30 referências falham na validação estática de IDs da página. O array não existe na cópia local atual. A consequência em runtime não foi testada; não afirmo que o Desktop necessariamente falhará, mas a referência é incoerente e impede atestar paridade funcional do artefato remoto.

O inventário separado por estado está em `evidence/phase-5.7/versioned-pbip-inventory.json`; a lista de definições divergentes está em `evidence/phase-5.7/pbir-comparison.json`.

## 8. Integridade do modelo semântico

A versão remota contém:

- 10 tabelas, 55 medidas, 11 nomes únicos de Display Folder e 21 relacionamentos.
- 10 partições Import; nenhuma DirectQuery.
- As medidas e definições TMDL das tabelas/relacionamentos coincidem com o workspace. O diff semântico TMDL está limitado à cultura pt-BR gerada localmente.
- `DimCalendario.DataFinal` permanece `2026-09-30`, sem extrapolação baseada na data atual.
- A inspeção pontual das definições remotas confirma Receita Analítica após devoluções = receita de produtos antes das devoluções menos valor comercial devolvido pela coorte do pedido; COGS ajustado = COGS original concluído menos a reversão sellable; custo original não é removido para destinos non-sellable, e a perda é exposta separadamente sem subtração duplicada. Lucro bruto = receita analítica menos COGS ajustado; margem divide lucro pela receita. `docs/database/operational-transactions.md` mantém aprovação comercial, recebimento físico, retorno ao estoque e refund como etapas distintas. Esses TMDLs de tabela coincidem com o workspace e as auditorias anteriores; nenhuma reconciliação SQL × DAX foi repetida.

A contagem/inspeção de TMDL foi estática; não havia parser TMDL/Tabular Editor disponível e nenhum Desktop foi aberto. Portanto, não declaro compilação semântica nesta auditoria.

## 9. Recursos InfoTech

O tema `powerbi/themes/infotech-light.json`, o monograma fonte e o SVG registrado estão versionados. Os dois SVGs têm SHA-256 idêntico: `D762678E082E5713C28128C81F3E84A3038A89941D40BC0E3A92FAF77A18A542`. O `report.json` do remoto aponta para o tema registrado e base theme compartilhado incluídos no pacote. Design System v0.3 está documentado no commit analisado e não foi alterado nesta fase.

## 10. Segurança

O `.gitignore` exclui `.env`, diretórios `.pbi/`, segredos e PBIX/PBIT. O único arquivo `.env` versionado é o exemplo com valores vazios. Uma heurística inicial encontrou somente um campo de configuração `password` e seu encaminhamento como argumento de conexão em `database.py`; não era valor literal.

Foram pesquisados padrões de alta confiança para chave privada, tokens conhecidos, URI de conexão com userinfo e atribuições literais de credenciais nos arquivos rastreados e nos 61 commits alcançáveis; nenhum candidato encontrado. Os valores de `.env` local, Windows Credential Manager e conteúdo interno dos ZIPs não foram acessados. O limite está detalhado em `evidence/phase-5.7/security-scan-summary.md`; não se declara certificação absoluta de segurança.

## 11. Dependências do ambiente

As 8 tabelas externas usam `PostgreSQL.Database`; o modelo aponta para PostgreSQL local em `127.0.0.1:5432`, database `projeto_bi`. O modelo é Import. Credenciais não estão no PBIP e precisam ser configuradas de forma local no destino. Consulte `evidence/phase-5.7/dependency-inventory.md` para requisitos e instruções de reprodução.

## 12. Reprodutibilidade

**Entrega de código-fonte:** estruturalmente, o remoto inclui os cinco dashboards, modelo e recursos de marca. O PBIR JSON passa parsing; há, porém, referências internas incoerentes na página Devoluções e diferenças materiais frente ao workspace homologado.

**Reprodução local completa:** requer Power BI Desktop compatível, fonte PostgreSQL acessível, database/schema/dataset sintético até 30/09/2026, identidade somente leitura, credenciais locais e refresh configurado. O `.pbi/` local não é versionado; os dados Import não acompanham o archive. Não foi testada abertura a partir de clone limpo nem executado refresh. A versão Desktop documentada como testada anteriormente foi `2.158.1304.0 (26.09)`; isso não estabelece versão mínima.

Logo, o remoto é um código-fonte PBIP inspecionável, mas ainda não é uma reprodução fiel comprovada do estado atualmente homologado.

## 13. Pendências para publicação

- `queryLimitOption=None` aparece apenas no PBIR local; historicamente pendente, mas não classificado como defeito comprovado.
- Serialização PBIR/TMDL não foi recompilada nesta fase.
- Cache/dados Import ausentes do Git são esperados e exigem fonte/refresh no destino.
- Ambiente do Power BI Service, workspace, gateway/rede, credenciais de atualização, RLS, políticas, limites e responsável operacional não foram definidos.
- Desempenho frio, acessibilidade assistiva, WCAG, leitor de tela e layout mobile continuam sem homologação integral.

Não houve publicação.

## 14. Acessibilidade e responsividade

**Acessibilidade parcialmente validada.** A aprovação estética e os cenários funcionais documentados não equivalem a percurso completo por teclado, tab order, foco em todos os controles, leitor de tela, contraste total ou certificação WCAG.

O canvas desktop é 1920 × 1080 e FitToWidth; layout mobile não foi homologado. Não reprova uma distribuição explicitamente limitada a Desktop, mas requer escopo claro.

## 15. Matriz de riscos

Nenhum P0 foi constatado. Foram registrados 3 P1 e 5 P2 em `evidence/phase-5.7/readiness-matrix.csv`. Os P1 são divergência do estado PBIR, referências de interação incoerentes e dependência de ambiente para reproduzir dados Import. Os P2 cobrem cultura TMDL, query limit, arquivos/duplicata de evidência, acessibilidade/viewport e publicação não definida.

## 16. Plano de regularização

1. Preservar o estado local e escolher, com revisão explícita, qual PBIR representa a entrega aprovada.
2. Revisar os 20 JSONs com mudanças de conteúdo; conferir filtros sincronizados, estados de controles, estilos, página ativa e `queryLimitOption`.
3. Corrigir/validar as 30 referências cruzadas de Devoluções e a configuração TMDL de cultura, se sua inclusão for desejada.
4. Em escopo autorizado próprio, gerar archive limpo do candidato, abrir no Desktop compatível sem sobrescrever a working tree, validar navegação/interações/bookmarks, salvar/reabrir e documentar o resultado. Configurar PostgreSQL/credenciais apenas no ambiente de teste e executar refresh somente quando autorizado.
5. Tratar ZIP duplicado e export Performance Analyzer em organização separada; preservar até confirmar a finalidade.
6. Após versão fiel aprovada, atualizar inventário e instruções de reprodução. Publicação no Service exige uma decisão/fase própria.

Esta auditoria não executou as ações acima.

## 17. Gates E1/E2/E3

| Gate | Estado | Fundamentação |
|---|---|---|
| E1 — Integridade do repositório | **GO** | Fetch/remote confirmados, branch sincronizada, série de 19 commits e commit e91 verificados, arquivos essenciais versionados, alterações locais inventariadas, nenhuma perda e nenhum segredo de alta confiança identificado no escopo pesquisado. O workspace continua sujo. |
| E2 — Reprodução do PBIP | **NO-GO** | A estrutura de cinco páginas e o modelo esperado existem, mas 30 referências a visuais de outra página são incoerentes e 20 definições PBIR diferem estruturalmente do workspace; clone limpo não foi aberto e dados Import exigem ambiente/refresh. |
| E3 — Publicação/distribuição operacional | **NOT EVALUATED** | Destino, gateway, refresh, credenciais, segurança operacional, limites e responsáveis não foram definidos. |

Gate Git: **PASS** (estado e divergências documentados). Gate segurança: **PASS no escopo de arquivos/histórico verificado**, com limitações explícitas. Gate PBIP para fidelidade de reprodução: **NO-GO** até regularização. Gate documentação: **PASS** com matriz e evidências produzidas.

## 18. Resultado geral

`FASE 5.7 PASS — RELEASE READINESS AUDIT COMPLETED`: a auditoria alcançou evidência suficiente para decidir separadamente cada modalidade. O Git remoto está sincronizado; a reprodução fiel do PBIP remoto não está pronta (**E2 NO-GO**) e a publicação permanece fora de avaliação (**E3 NOT EVALUATED**). Não fazer push nem iniciar regularização funcional sem autorização da fase correspondente.

## 19. Estado Git final

O commit local desta fase contém somente este relatório, a atualização do plano mestre e os arquivos documentais em `evidence/phase-5.7/`, com a mensagem `docs(powerbi): audita prontidao de entrega do ProjetoBI`. Nenhum PBIR, TMDL, dado, cache, credencial, exportação anterior ou ZIP preexistente foi incluído. As alterações locais preexistentes permanecem preservadas e não staged. Sem push, merge, rebase, reset, clean, amend ou tags.
