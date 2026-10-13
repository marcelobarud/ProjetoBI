# Fase 5.2.1 — Refinamento do filtro de período

**Resultado:** PASS local — Between com datas editáveis e slider horizontal de duas alças nas duas páginas.

**Data:** 2026-10-13, America/Sao_Paulo. **Entrada:** `main`, checkpoint `0017f84`.

## Implementação

Foram reutilizados os segmentadores `a2000000000000000001` e `b2000000000000000001`, ambos sobre `DimCalendario[Data]`. O painel nativo já indicava Slider On; as alturas compactas não mostravam o controle completo. A primeira ampliação ainda deixou alças próximas ao limite inferior, por isso a composição final reserva área própria.

| Configuração | Final nas duas páginas |
|---|---|
| Tipo | Between; dois campos de data e seus calendários nativos |
| Área | x36/y104; 760 × 112 px |
| Slider | `visual.objects.slider.show=true` |
| Responsividade | `visual.objects.general.responsive=false` |
| Datas | Segoe UI, 13 pt configurados explicitamente em `date` |
| Título | Período comercial; Segoe UI Semibold 13 pt preservados |
| Sincronização | `InfoTech.PeriodoComercial`, `fieldChanges=true`, `filterChanges=true` preservados |

O slider fica abaixo dos campos, com trilha completa e faixa selecionada. Nesta versão as alças são barras verticais, com controles nativos de largura 5 px/altura 17 px observados no painel. Não é necessário outro visual.

Canal e Loja permaneceram byte a byte iguais ao preflight. Os doze visuais analíticos comerciais receberam somente deslocamento vertical de 16 px: KPIs y224, status y376, temporais y492 e rankings y788. Dimensões, fontes, consultas, ordenações e interações desses visuais foram preservadas. A margem inferior comercial fica em 24 px; período termina em y216, com 8 px até os KPIs. A Executiva conserva seus blocos analíticos. Ambos os canvases permanecem 1920 × 1080.

## Validação efetiva no Power BI Desktop

Testes por automação da interface nativa, sobre o modelo Import já carregado; não houve refresh de dados ou acesso ao PostgreSQL.

| Cenário | Evidência observada |
|---|---|
| Alça inicial comercial | 01/01/2026 → 18/05/2025, mantendo 30/09/2026; total 30.000 → 52.877, concluídos 51.001 e receita R$ 418.474.203,53; gráficos acompanharam |
| Alça final comercial | 30/09/2026 → 08/04/2026, mantendo 18/05/2025; total 33.742, concluídos 32.833 e receita R$ 270.161.582,17; gráficos acompanharam |
| Digitação comercial | Inicial 01/01/2026, depois final 30/09/2026; alças retornaram às posições correspondentes, total 30.000 e receita R$ 234.603.762,77 |
| Comercial → Executiva | Jan–Set/2026 chegou com 28.736 concluídos e receita analítica R$ 228.660.758,74 |
| Alça inicial executiva | 01/01/2026 → 11/03/2026; concluídos 21.215 e receita R$ 169.256.384,68; linha e rankings acompanharam |
| Alça final executiva | 30/09/2026 → 07/07/2026; concluídos 12.714 e receita R$ 101.552.374,13; gráficos acompanharam |
| Executiva → Comercial | 11/03/2026–07/07/2026 chegou com 13.085 pedidos, 12.714 concluídos e receita comercial R$ 104.577.955,59 |
| Digitação executiva | Ambos os campos editados para 01/01/2026 e 30/09/2026; slider e indicadores retornaram ao contexto inicial da sessão |
| Aparência | Campos completos, duas alças abaixo, sem cortes ou sobreposição do componente; Fit to Page observado em viewports 1152 × 638 e 1366 × 720 |
| Persistência | Salvamento pelo Desktop às 13:19, fechamento normal e reabertura sem erro; configuração e Jan–Set/2026 presentes nas duas páginas |

Os valores são observações da interface, não nova reconciliação independente de DAX. Durante um arraste de teste, a seleção do visual interceptou a borda e alterou sua largura; a ação foi desfeita pelo Undo nativo. O teste foi repetido com o visual desselecionado e a alça final funcionou. A definição final conserva largura 760, altura 112 e tabOrder 1 nas duas páginas.

### Capturas

- [Duas alças comerciais após arrastes](evidence/phase-5.2.1-commercial-handles.jpg).
- [Duas alças executivas após arrastes](evidence/phase-5.2.1-executive-handles.jpg).
- [Seleção executiva sincronizada na Comercial](evidence/phase-5.2.1-sync-commercial.jpg).
- [Comercial após reabertura em Fit to Page](evidence/phase-5.2.1-commercial-reopened.jpg).
- [Composição comercial ampliada](evidence/phase-5.2.1-commercial-final.png) e [executiva ampliada](evidence/phase-5.2.1-executive-final.png), bridge escala 2.

Fit to Page reduz os controles e a precisão do arraste; datas exatas continuam disponíveis nos campos. Não se promete precisão diária por pixel, legibilidade em qualquer viewport ou alças circulares. As capturas escala 2 não equivalem a operar em zoom 100%. Restrições anteriores dos eixos e rolagem temporal dos gráficos permanecem documentadas na Fase 5.2; não foram modificadas nem homologadas novamente como padrões universais.

## Preservação e verificações locais

Snapshot anterior à edição em `C:/Users/D2/AppData/Local/Temp/ProjetoBI-phase-5.2.1-preserve`, com arquivos, hashes, status e diff. A sessão aberta tinha Jan–Set/2026 selecionado, embora a definição inicial em disco estivesse limpa. Esse estado foi salvo antes da edição e restaurado após os testes; fica fora do commit, preservado na working tree dos dois slicers. O commit conserva a seleção limpa do checkpoint, sem impor outro período inicial ao projeto versionado.

O Desktop normalizou a serialização dos visuais e regenerou metadados linguísticos ao salvar. Cópias dessas saídas foram mantidas em snapshots externos; com o Desktop fechado, foram restaurados os arquivos anteriores ao salvamento e preservadas as propriedades funcionais e a seleção final dos dois slicers. O PBIP resultante foi reaberto e capturado nas duas páginas.

Hashes confirmaram todos os arquivos semânticos, `report.json`, Canal/Loja e demais arquivos fora dos 14 visuais da tarefa idênticos ao preflight. JSONs do relatório foram lidos com sucesso; posições e dimensões ficaram dentro do Full HD. Não houve alteração de DAX, calendário, relações, temas, fontes de dados ou credenciais; nenhum filtro adicional foi criado. DS-C02 atualizado mantendo Design System v0.2.

Staging seletivo dos dois componentes a partir de HEAD, incluindo somente geometria, slider, responsividade e fonte dos campos; doze deslocamentos comerciais, documentação e capturas. Alterações locais preexistentes de schema/serialização, `report.json`, `pt-BR.tmdl` e exportação bruta de desempenho ficam fora. Commit local autorizado: `fix(powerbi): aprimora slider do filtro de periodo`. Sem push, merge ou início da Fase 5.3.
