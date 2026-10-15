# Fase 5.7.2 — PBIX demonstrativo público e validação de distribuição

**Data:** 2026-10-15
**Resultado geral:** **PARTIAL**
**Origem versionada:** `5433d26284b76c07081e73bc1be7aba516d2fa51` (`fix(powerbi): regulariza PBIR para portfolio publico`)

## Objetivo e limites

Validar o PBIR da Fase 5.7.1 e produzir um PBIX local com as cinco páginas InfoTech e os dados sintéticos autorizados pelo usuário para divulgação pública. O PBIX fica fora do Git, em `D:\Codex\ProjetoBI-Distribution\Fase-5.7.2\ProjetoBI-InfoTech-Demo.pbix`. Não houve refresh, acesso ao PostgreSQL, alteração do modelo, publicação, push, merge ou release.

## Estado inicial e preservação

Entrada: branch `main`, HEAD `5433d26284b76c07081e73bc1be7aba516d2fa51`, staging vazio e 104 caminhos locais modificados/não rastreados. Um snapshot completo foi criado antes das operações: `C:\Users\D2\AppData\Local\Temp\ProjetoBI-Phase5.7.2-preflight-20261015-090904.zip`, 4.333.748 bytes, SHA-256 `D2E4576D472B6A32A7A8F61857396429B96AA2B9B9B87AE1553A06415D3A27CF`. O PBIX e o cache ficaram fora da worktree; somente documentação e evidências desta fase entram no commit.

## Gate A — candidato PBIR

O candidato foi extraído do commit de origem com `git archive`, fora do workspace, sem usar as definições PBIR modificadas localmente. Arquivo de origem: `ProjetoBI-Phase5.7.2-candidate-20261015-093200.zip`, SHA-256 `4B770412950665A988D5E3FC49AEC4AD80AF4CA80C9EF29F43D5D7E69316F57D`.

Validação estática: **PASS** — 117 JSONs parseáveis; cinco páginas de 1920 × 1080; 17, 22, 19, 22 e 18 visuais; cinco destinos de navegação; grupos globais `InfoTech.Canal`, `InfoTech.Loja` e `InfoTech.PeriodoComercial`; 10 bookmarks com estado de visuais; tema InfoTech; 10 tabelas, 55 medidas, 11 Display Folders e 21 relacionamentos; nenhuma referência de interação a visual inexistente; `labelPrecision=1L` nos dois gráficos monetários homologados. Inventário em `evidence/phase-5.7.2/candidate-static-validation.json`.

Validação ao vivo do PBIR candidato no Desktop: **PASS para abertura e renderização observadas**. O projeto abriu sem erro e o cache Import isolado exibiu valores nos visuais. As cinco páginas foram visitadas, com visuais populados; a página Devoluções também renderizou seus quatro KPIs e gráficos. Painel de filtros abriu; Canal, Loja e slider de período foram exercitados. Canal e período propagaram resultados entre páginas. Uma combinação de filtros sem dados gerou visuais em branco, comportamento compatível com esse contexto. Nenhum refresh foi executado.

## Gate B — PBIX

O Desktop salvou nativamente o candidato como `ProjetoBI-InfoTech-Demo.pbix`. O cache utilizado veio de `D:\Codex\ProjetoBI\powerbi\ProjetoBI.SemanticModel\.pbi\cache.abf`, copiado somente para a pasta temporária do candidato. Cache: 38.797.870 bytes, SHA-256 `36664F23ECA1A39762A86008E95D59AD663BD99F92106CE0437CD1E3502D7305`. Essa cópia permitiu renderizar dados Import sem consultar ou atualizar a origem.

PBIX: 38.910.373 bytes; SHA-256 `E25600A3F7EFF6AAFC36956B730D6F4DEE6C6F33369FF698CB86C96A931D1453`; salvo em 2026-10-15 09:23:32 -03:00; Power BI Desktop `2.158.1304.0`. A exportação nativa do Power BI produziu um PDF de cinco páginas (uma por dashboard), 467.549 bytes, SHA-256 `38D2AB2ED72646724FEFCA5811E12329F83BBC32376D0F531EB94368852AC465`. Esse PDF é evidência derivada do relatório, não captura da janela do Desktop.

Os valores observados no Desktop incluíram Receita após devoluções de R$ 922.588.975,45, COGS ajustado de R$ 717.455.650,26, lucro bruto de R$ 205.133.325,19 e margem bruta de 22,23%. Navegação para a página Devoluções exibiu R$ 420.582,31 de devoluções comerciais e 2,14% de devoluções comerciais.

**Geração: PASS. Reabertura independente do PBIX: NOT TESTED.** O PBIX permaneceu aberto na janela em que foi salvo; a validação de fechamento e reabertura não foi concluída.

## Gate C — dados, credenciais e origem

- Dados incorporados são sintéticos e têm autorização explícita do usuário para divulgação pública; podem ser inspecionados ou extraídos do PBIX.
- A pasta de distribuição contém o PBIX demonstrativo, sem `.env`, cache `.abf`, backups ou outros arquivos de credenciais. Nenhuma senha, token ou credencial do Windows foi lida, copiada ou incluída deliberadamente.
- Os metadados Power Query do modelo referenciam `127.0.0.1:5432`, database `projeto_bi`. Isso é metadado técnico de desenvolvimento; não equivale a credenciais nem concede acesso operacional.
- O modo Import e a abertura/renderização sem refresh demonstram que os visuais puderam usar os dados armazenados no arquivo/cache. **Independência em ambiente sem acesso ao PostgreSQL: NOT TESTED**, pois a instância local não foi interrompida nem reconfigurada.
- Não foi feita inspeção de baixo nível do contêiner PBIX para cada bloco interno. A ausência de arquivos de credencial no diretório de entrega foi verificada; a ausência absoluta de qualquer metadado sensível embutido não é declarada.

## Gate D — teste do PBIX final

| Verificação | Resultado |
|---|---|
| PBIX criado nativamente com dados Import | PASS |
| Cinco páginas visualizadas no candidato PBIR | PASS |
| Navegação pelos cinco destinos no candidato PBIR | PASS |
| Canal e período exercitados com propagação entre páginas | PASS |
| Loja exercitada em contexto sem linhas correspondentes | PASS — contexto em branco, sem erro de carregamento |
| Painel de filtros aberto e fechado | PASS no candidato durante a validação anterior |
| Reabertura do arquivo PBIX depois de fechar | NOT TESTED |
| Independência em ambiente onde PostgreSQL esteja inacessível | NOT TESTED |
| Capturas reais da janela Desktop arquivadas | NOT TESTED; o PDF nativo de cinco páginas foi preservado como evidência visual derivada |

Durante a tentativa de exportar o PDF, o Power BI abriu o arquivo no Microsoft Edge. A ferramenta de Computer Use interrompeu ações adicionais porque não conseguiu determinar com segurança a URL da janela; portanto, não foi possível continuar com reabertura do PBIX ou captura por ferramenta de tela. Nenhuma tentativa de contornar essa barreira foi feita.

## Segurança e prontidão

O artefato está disponível apenas localmente para revisão, sem publicação automática. Seu estado de distribuição é **PARTIAL** até uma reabertura do PBIX final, confirmação de abertura das cinco páginas no PBIX e, se possível sem alterar infraestrutura, um teste com PostgreSQL inacessível. O teste offline permanece explicitamente não comprovado.

## Git

O PBIX e o cache não são versionados. O pacote ZIP de evidências contém o relatório desta fase, o inventário estático e a exportação PDF nativa; não contém o PBIX. Nenhum push, merge, rebase, tag ou release foi realizado. O staging inicial estava vazio; as 104 alterações preexistentes foram preservadas e excluídas do commit.
