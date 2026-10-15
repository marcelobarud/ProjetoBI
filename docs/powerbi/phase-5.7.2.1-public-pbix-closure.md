# Fase 5.7.2.1 — Homologação final do PBIX demonstrativo

**Data:** 2026-10-15 (America/Sao_Paulo)
**Resultado:** **PARTIAL — OFFLINE VALIDATION PENDING**
**Commit PBIR de origem:** `647bdb2c4740131374547b6cfedf669b3b048471`
**Fase anterior:** a Fase 5.7.2 permanece historicamente PARTIAL; seus resultados não foram reescritos.

## Escopo e proteção

Foi homologado o PBIX já existente em `D:\Codex\ProjetoBI-Distribution\Fase-5.7.2\ProjetoBI-InfoTech-Demo.pbix`. Não houve refresh, acesso ou alteração do PostgreSQL, edição de Power Query/DAX/relacionamentos/modelo/dados, publicação ou uso do PBIP de desenvolvimento como substituto.

Antes de salvar qualquer mudança, foi conferida e preservada cópia externa em `D:\Codex\ProjetoBI-Distribution\Fase-5.7.2.1\ProjetoBI-InfoTech-Demo-before-5721.pbix` (38.910.399 bytes; SHA-256 `1E9E6BDD059FFB096650B465B398FD51FF2F3E01CE312DB0B1DCAC1121D73046`). Essa cópia corresponde ao arquivo de entrada desta fase, já diferente do PBIX registrado na Fase 5.7.2; a diferença anterior à presente validação não foi atribuída a uma causa confirmada.

## Validação ao vivo no Power BI Desktop

O PBIX abriu sem erro e apresentou dados incorporados, sem solicitar refresh ou credenciais. As cinco páginas foram abertas e renderizaram KPIs/gráficos:

| Página | Observação ao vivo |
|---|---|
| Visão Executiva | No estado recomendado, Receita líquida R$ 225.848.261,06; Lucro bruto R$ 51.935.391,90; Margem bruta 23,00%; Pedidos concluídos 28.392. Tendência mensal e rankings populados. |
| Análise Comercial | Com E-commerce próprio, período de 04/01/2026 a 30/09/2026 e Loja em Todos: 9.206 pedidos, 8.704 concluídos, receita comercial R$ 78.711.355,44, ticket médio R$ 9.056,89, conclusão 94,55% e cancelamento 2,56%. |
| Produtos e Categorias | Com Loja física + Unidade Sintética Campinas no mesmo período: Receita após devoluções R$ 10.400.562,57; COGS ajustado R$ 8.074.777,25; Lucro bruto R$ 2.325.785,32; Margem bruta 22,36%. Top 5, categorias e matriz estavam populados. |
| Custos e Margens | No mesmo contexto Campinas: COGS original R$ 8.118.437,77; reversão sellable R$ 43.660,52; COGS ajustado R$ 8.074.777,25; perda non-sellable R$ 132.326,24; série mensal e gráficos por canal/categoria populados. |
| Devoluções | No mesmo contexto Campinas: devoluções comerciais R$ 224.497,50; reversão de custo sellable R$ 43.660,52; perda non-sellable R$ 132.326,24; percentual 2,11%; série mensal, categorias e Top 5 populados. |

Navegação entre páginas e o painel de filtros abriram. Canal propagou-se para Análise Comercial; combinar E-commerce próprio com Campinas produziu visuais sem linhas, e trocar para Loja física preencheu os visuais, sem erro de carregamento. As seleções de período e canal foram vistas novamente em outras páginas. O período Between exibiu os dois campos editáveis e o slider com duas alças; a alça inicial foi movida e atualizou os visuais. A digitação manual nos campos de data não foi repetida nesta fase. Os botões de abrir e fechar filtros responderam; a seleção continuou sincronizada.

## Estado inicial corrigido e persistência

O arquivo de entrada mostrava seleções transitórias. O estado de apresentação foi ajustado somente pelo Desktop, sem alterar componentes analíticos:

- página inicial: **Visão Executiva**;
- painel de filtros: fechado;
- período: **04/01/2026–30/09/2026**;
- Canal e Loja: **Todos**;
- filtros locais de categoria/produto: sem seleção temporária visível;
- quatro KPIs, tendência mensal e rankings com dados.

O primeiro dia ficou em 04/01 após o ajuste pela alça do slider; é um intervalo representativo de janeiro a setembro de 2026 e não inclui meses sem dados. O estado foi salvo em 2026-10-15 09:57 (-03:00), o PBIX foi fechado e reaberto pelo diretório de distribuição. A reabertura confirmou a mesma página, os quatro valores executivos e o painel fechado. Ao abrir o painel após a reabertura, os campos mostraram 04/01/2026, 30/09/2026, Canal Todos e Loja Todos; o painel foi recolhido novamente.

## Independência da origem e segurança

**Teste isolado sem PostgreSQL: NOT TESTED.** Não havia ambiente Windows isolado disponível. Não se interrompeu nem se reconfigurou o PostgreSQL local; portanto, os resultados ao vivo com dados Import, sem refresh, comprovam uso dos dados armazenados, mas não provam funcionamento em computador sem acesso à origem.

A pasta de distribuição examinada contém somente o PBIX. Não foram encontrados nela `.env`, `.abf`, backups, credenciais, tokens ou arquivos auxiliares de dados. Os metadados técnicos de origem `127.0.0.1:5432` e database `projeto_bi` já documentados na Fase 5.7.2 não são credenciais. Não foi feita extração exaustiva de cada bloco interno do contêiner PBIX e não se afirma ausência absoluta de todo metadado sensível embutido.

## Evidências

Os registros observados durante a validação estão em `evidence/phase-5.7.2.1/validation.json`; a identificação criptográfica está em `pbix.sha256.txt`. Não foram arquivadas capturas reais. A interface de Captura entrou em uma camada de recorte parcial sem expor uma janela de captura segura para salvar; a operação foi cancelada sem contornar a ferramenta. Conforme permitido pelo prompt da fase, a falta de screenshots não invalida isoladamente a homologação funcional. O PDF nativo da fase anterior continua sendo apenas evidência visual derivada daquela fase.

## Identificação do artefato final

- **Arquivo:** `ProjetoBI-InfoTech-Demo.pbix`
- **Caminho:** `D:\Codex\ProjetoBI-Distribution\Fase-5.7.2\ProjetoBI-InfoTech-Demo.pbix`
- **Tamanho:** 38.910.666 bytes
- **SHA-256:** `398EB0B3866810F2ABD787AC71FAE4ED9CD8327A84589BF43567F7CA85A399D2`
- **Modificado:** 2026-10-15 09:57:15 -03:00
- **Modo do modelo:** Import, conforme origem documentada e dados exibidos sem refresh
- **Páginas:** cinco
- **Power BI Desktop:** 2.158.1304.0, versão registrada na fase de geração anterior; não reconsultada nesta validação

O tamanho e hash mudaram durante o salvamento do estado inicial. A cópia de entrada com hash anterior foi mantida fora do repositório para comparação; o hash final acima identifica a candidata validada nesta fase.

## Gate e próxima etapa

**PARTIAL — OFFLINE VALIDATION PENDING.** Reabertura, renderização das cinco páginas, navegação, filtros e persistência foram confirmadas. A exploração sem acesso à origem PostgreSQL não foi executada, portanto não se recomenda ainda classificar o arquivo como pronto para distribuição pública. Próxima verificação recomendada: abrir esta mesma candidata em ambiente Windows isolado, sem acesso ao PostgreSQL de desenvolvimento, sem executar refresh, e repetir a navegação e os filtros. Isso não autoriza publicação automática.

## Git

O PBIX final e o backup permanecem fora do Git. O commit desta fase inclui somente o relatório, plano mestre e evidências documentais/criptográficas; as 104 entradas preexistentes modificadas ou não rastreadas foram preservadas e excluídas do staging. Não houve push, merge, rebase, tag ou Release.
