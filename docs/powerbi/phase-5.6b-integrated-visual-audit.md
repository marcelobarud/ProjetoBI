# Fase 5.6B — Auditoria visual integrada InfoTech

**Resultado:** `FASE 5.6B TECHNICAL PASS — AWAITING AESTHETIC APPROVAL`
**Workspace:** `D:\Codex\ProjetoBI`
**Entrada:** branch `main`, HEAD `48edec921f96eaf2b33d4dabf841e4de65489805` (`test(powerbi): automatiza validacao funcional integrada`).
**Design System:** InfoTech v0.2 preservado. A Fase 5.6C não foi iniciada.

## 1. Objetivo e segurança

Revisar em conjunto as cinco páginas existentes, registrar o baseline visual e corrigir apenas uma inconsistência de apresentação verificada no PBIR. DAX, TMDL semântico, Power Query, calendário, relações, dados, PostgreSQL, credenciais, medidas e interações não foram alterados. Nenhum refresh foi executado.

Antes da alteração foi criado o snapshot externo `C:\Users\D2\AppData\Local\Temp\ProjetoBI-Phase5.6B-preflight-20261014-201340.zip`, SHA-256 `B3C939CB403B555C5C8A33951DED8CB6484789B9069FA05247282F6F94A49BFB`. Ele preserva diffs, hashes e cópias dos 107 caminhos modificados ou não rastreados que já existiam. A branch, o HEAD e todas as alterações preexistentes foram mantidos.

## 2. Estado observado e ambiente

- O PBIP abriu no Power BI Desktop sem erro antes e depois do ajuste.
- As cinco páginas têm canvas lógico 1920 × 1080. O viewport de Computer Use desta sessão foi 1152 × 575 px; a resolução física do monitor não foi determinada.
- O Desktop mostrou Fit to Width entre 36% e 51%, Fit to Page a 37% e 100% durante inspeções. O painel de Visualizações/Dados ocupou parte do viewport em algumas capturas.
- Contexto encontrado: 30/04/2025 a 30/09/2026, Canal `Loja física`, Loja `Unidade Sintética Campinas`. Na página Produtos e Categorias, Categoria e Produto estavam em `All`. O contexto não foi alterado.
- Fit to Page torna o canvas inteiro visível neste viewport, mas reduz os textos. As capturas pequenas não demonstram legibilidade em qualquer monitor; a escala Full HD de apresentação precisa ser revisada pelo usuário em seu ambiente.

## 3. Matriz de achados

| ID | Página/componente | Evidência e impacto | Prioridade | Correção proposta | Risco | Resultado |
|---|---|---|---|---|---|---|
| V-01 | Produtos e Categorias — opção de exibição | A página estava em `ActualSize`; as demais estavam em `FitToWidth`. A abertura em 100% deixava a maior parte do canvas fora do viewport e tornava a experiência inconsistente. | P1 | Restaurar `FitToWidth`, sem alterar os 1920 × 1080, geometria, filtros ou visuais. | Baixo | Corrigido; após reabrir, a página abriu em 36% e o canvas inteiro coube na largura disponível. |
| V-02 | DS-C02 — painel de filtros | O painel aberto se sobrepõe temporariamente à primeira faixa de cartões nas páginas em que estava aberto. Foi visto aberto nas páginas 1–4 e fechado em Devoluções. | P2 | Preservado: a sobreposição é o comportamento desenhado do painel e libera a área analítica quando fechado. O usuário já havia confirmado o botão “Fechar filtros”; bookmarks não foram reserializados. | Médio para alteração de bookmarks | Preservado, com estado documentado nas capturas. A consistência estética do estado inicial fica para aprovação do usuário. |
| V-03 | Análise Comercial — séries temporais | Em Fit to Width reduzido, os eixos temporais podem exibir rolagem nativa para navegar por intervalos longos. A documentação da Fase 5.2 já registra essa decisão e que os pontos não são descartados. | P2 | Preservar largura mínima e rolagem deliberada; nenhuma categoria foi removida. | Baixo | Preservado conforme contrato anterior. |
| V-04 | Todas — tipografia, cores e densidade | Cabeçalho InfoTech, monograma, títulos, KPIs e cores aparecem coerentes nas capturas. Em escalas reduzidas, a fonte aparenta menor; isso resulta do zoom do viewport. Não foi feita medição automatizada de contraste. | P2 | Preservar DS v0.2; não promover tamanhos ou cores com base em screenshots reduzidos. | — | Sem mudança; revisão estética e assistiva continua com o usuário. |

Nenhum P0 foi observado. Os dois eixos monetários da Análise Comercial mantêm as limitações de abreviação/rolagem nativa documentadas na Fase 5.2; seus títulos e tooltips continuam identificando a unidade. A rolagem interna da matriz de Produtos e Categorias é própria do volume tabular e não representa perda de linhas.

## 4. Avaliação integrada das páginas

| Página | Identidade | KPIs | Gráficos e rankings | Filtros | Navegação | Resultado |
|---|---|---|---|---|---|---|
| Visão Executiva | InfoTech e monograma alinhados; nome completo | Quatro cartões alinhados | Tendência, Canal e Top 5; contexto temporal e unidades nos títulos | Período, Canal e Loja visíveis; painel aberto na captura | Cinco destinos visíveis | Preservada; viewport reduzido limita leitura em Fit to Width |
| Análise Comercial | Cabeçalho e estado ativo coerentes | Quatro principais e quatro secundários | Séries temporais, Canal e Top 5 lojas; rolagem temporal é comportamento documentado | Filtros compartilhados visíveis; painel aberto | Cinco destinos visíveis | Preservada; abreviações nativas já documentadas |
| Produtos e Categorias | Marca e navegador coerentes | Quatro cartões financeiros no layout PBIR | Top 5, 12 categorias e matriz; Fit to Page mostra a página inteira; rolagem da matriz permanece interna | Filtros globais e locais visíveis | Cinco destinos visíveis em Fit to Width | P1 corrigido; padrão de exibição alinhado às outras páginas |
| Custos e Margens | Cabeçalho e nome vigentes, sem terminologia histórica | Cartões de coorte/custo alinhados | Tendência por mês do pedido e comparações por Canal/Categoria, perspectivas rotuladas | Painel aberto observado; filtros globais presentes | Cinco destinos | Preservada; título por pedido mantido |
| Devoluções | Marca e navegação coerentes | Quatro cartões e percentual | Linha por mês do pedido, categorias e Top 5; valores e unidades rotulados | Painel fechado após abertura e ao final; filtros compartilhados | Cinco destinos | Preservada; página restaurada como estado final da sessão |

### Identidade, títulos e tipografia

O monograma I/T e o nome InfoTech foram observados nos cabeçalhos; a navegação usa nomes completos, realce azul da página ativa e botão Filtros. O SVG-fonte e o recurso registrado no PBIP têm raiz XML `svg` e SHA-256 idêntico: `29CA228E30EF819E4EF204C8864CCA155F31EB9C979E6E25E779E736667B343A`.

Os títulos e tamanhos vigentes permanecem os de v0.2: wordmark 30 pt; título da página 12 pt; título de gráfico 17 pt; eixos/categorias conforme o componente (16 pt como referência, 14 pt para eixos monetários em gráficos comerciais/de produto quando documentado); legenda 15 pt; valor de cartão 32 pt e título de cartão 13 pt. Esses valores foram conferidos nas referências PBIR e nos relatórios das fases, mas não foram reeditados nem homologados como legíveis em toda escala. Fit to Page em 37% reduz a representação, não o tamanho lógico configurado.

### Contraste e acessibilidade básica

Azul, verde-petróleo, fundos claros e textos escuros mantêm a identidade. Uma checagem de luminância relativa foi feita sobre os tokens definidos (não sobre todos os pixels renderizados): `#2563EB`/branco 5,17:1; `#0F9D92`/branco 3,36:1; texto principal `#142238`/branco 15,96:1; texto secundário `#5B6B82`/branco 5,43:1; botão azul `#1D4ED8`/texto branco 6,70:1; texto principal no fechamento `#142238`/`#DBEAFE` 13,08:1. O verde-petróleo é apropriado como linha/swatch não textual (acima de 3:1), mas não para texto pequeno sobre branco; o padrão existente já evita esse uso. Isso não equivale a certificação WCAG do relatório inteiro. O estado de acessibilidade do Computer Use não expôs árvore de elementos nesta janela (`accessibility=null`). Tabulação, foco, leitor de tela e operação por teclado permanecem não testados nesta fase.

## 5. Refinamento realizado

Antes, `d5302600000000000001/page.json` tinha `displayOption: ActualSize`, enquanto as outras quatro páginas usavam `FitToWidth`. A propriedade foi restaurada para `FitToWidth`. A dimensão da página continuou 1920 × 1080; nenhum visual ou dado foi movido. O Desktop reabriu o PBIP e mostrou a página 3 em 36% com o canvas inteiro visível na largura disponível.

O valor restaurado coincide com o conteúdo já presente em `HEAD`. Por isso, não há patch PBIR novo a incluir neste commit; o arquivo conserva apenas a alteração de fim de linha preexistente e fica fora do staging. Não foram introduzidas alterações cosméticas artificiais.

**Candidatos à v0.3, sem promoção:** comportamento de exibição uniforme do DS-C02, estados do painel por página, resposta responsiva em viewports pequenos e evidência comparável de contraste/acessibilidade. DS-C01–06 e a versão oficial v0.2 permanecem inalterados.

## 6. Capturas e comparações

As capturas são imagens reais do Power BI Desktop, não mockups. O inventário inclui SHA-256 e dimensões do arquivo. Comparação pareada de Produtos e Categorias usa o mesmo viewport, zoom de 100%, período, Canal, Loja e estado aberto do painel; a comparação principal mostra que os visuais permaneceram iguais. Uma captura pós-ajuste adicional em Fit to Width/Fit to Page demonstra o enquadramento de abertura esperado. Ver [`comparisons/phase-5.6b-comparisons.md`](evidence/phase-5.6b/comparisons/phase-5.6b-comparisons.md) e [`capture-inventory.csv`](evidence/phase-5.6b/validation/capture-inventory.csv) e [pacote ZIP](evidence/archives/fase-5.6b-evidencias.zip).

## 7. Regressão, persistência e integridade

- O PBIP foi aberto, as cinco páginas foram visitadas e Produtos e Categorias foi renderizada após a alteração. A página Devoluções, o contexto inicial e o painel fechado foram restaurados na interface.
- Nenhum refresh foi executado. A Fase 5.6A.2 continua referência funcional aprovada para filtros, navegação, interação e persistência; esta alteração somente troca a opção de exibição da página 3.
- Inspeção estrutural: 5 páginas, canvas 1920 × 1080; 10 tabelas, 55 medidas, 11 Display Folders e 21 relacionamentos. Os 117 arquivos JSON PBIR foram analisados sem erro de sintaxe.
- O SVG-fonte e o recurso registrado são íntegros e iguais pelo hash. Nenhum TMDL semântico foi modificado nesta fase; PostgreSQL não foi acessado.
- O estado temporário de UI não foi salvo no Desktop. A propriedade de apresentação foi escrita com o Desktop fechado e verificada após reabrir. Não há diffs de medidas, relações, Power Query, dados ou recursos de marca.
- Não foi possível repetir por esta interface a ativação de botões via Ctrl+clique em modo de edição; a confirmação anterior do usuário e os testes F01–F14/S01–S07 da Fase 5.6A.2 permanecem a evidência funcional principal. Nenhuma falha funcional nova foi observada.

## 8. Gates e pendências

| Gate | Resultado | Evidência/limite |
|---|---|---|
| Visual | PASS técnico | Cinco páginas inspecionadas; P0 nenhum; P1 V-01 corrigido; P2 intencional/adiado documentado; capturas disponíveis para revisão estética. |
| Funcional | PASS no escopo semântico preservado | Nenhuma mudança semântica; páginas abriram; testes aprovados da 5.6A.2 permanecem referência. Operação de botões não foi repetida nesta sessão. |
| Técnico | PASS | PBIR JSON válido; dimensões, modelo e SVG íntegros; preexistências e snapshot preservados. |
| Acessibilidade | Parcial, pendente | Contraste WCAG, teclado/foco e leitor de tela não foram homologados. |
| Aprovação estética | Pendente do usuário | Aguardar análise das capturas antes da Fase 5.6C e da consolidação v0.3. |

## 9. Estado Git

Branch `main`; HEAD de entrada `48edec9`. As alterações preexistentes permanecem sem staging. O commit desta fase inclui somente o relatório, as atualizações de documentação e o pacote de evidências. Sem push, merge, rebase, tags ou amend.
