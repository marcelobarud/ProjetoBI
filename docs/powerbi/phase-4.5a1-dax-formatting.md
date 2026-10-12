# Fase 4.5A.1 — Padronização da Formatação DAX em TMDL

**Status: BLOCKED — o Power BI Desktop reformatou expressões simples ao salvar.**
**Checkpoint:** `71ed581` — `refactor(powerbi): centraliza medidas DAX em _Medidas`
**Projeto:** `powerbi/ProjetoBI.pbip`

## Padrão adotado

O escopo solicitou que todas as 28 medidas em `_Medidas` mantivessem a declaração com `=` ao final da linha e a expressão DAX iniciando na linha seguinte, com o recuo nativo de expressões TMDL. O padrão é permitido pela documentação oficial: expressões multilinha ficam na linha posterior à declaração e um nível de indentação além das propriedades do objeto ([visão geral oficial de TMDL](https://learn.microsoft.com/pt-br/analysis-services/tmdl/tmdl-overview?view=sql-analysis-services-2025)).

Foram separadas oito expressões simples que estavam inline; as outras 20 já começavam na linha seguinte. A tentativa foi salva, fechada e reaberta no Power BI Desktop sem erro. Depois do salvamento, o TMDL no workspace mostrou novamente as oito expressões simples na linha de declaração; as 20 expressões multilinha permaneceram multilinha. O serializador normalizou o estilo e, portanto, o padrão completo não persistiu. Conforme o escopo, não foram feitas novas rodadas de edição para forçar o formato.

## Equivalência e estrutura

- O serializador TMDL do Power BI leu o modelo após a reabertura: oito tabelas e nove relacionamentos.
- O mecanismo semântico contém 28 medidas exclusivamente em `_Medidas`; as duas fatos continuam sem medidas.
- Permaneceram sete Display Folders, sem erros de medida, descrições ou formatos ausentes.
- As 28 expressões após o salvamento são equivalentes ao snapshot original quando se ignoram espaços em branco. Nomes, referências, descrições, formatos, Display Folders e lineage tags são idênticos.
- A verificação pós-salvamento encontrou oito declarações com expressão inline e 20 com expressão iniciada na linha seguinte.
- A verificação visual reportada pelo usuário: PBIP reabriu sem erro.

## Regressão DAX após reabrir

| Indicador | Resultado |
|---|---:|
| Total de pedidos | 120.000 |
| Pedidos concluídos | 116.305 |
| Receita líquida de produtos antes de devoluções | R$ 949.319.764,19 |
| Receita YTD 2026 | R$ 234.603.762,77 |
| Receita YTD 2025 comparável | R$ 209.080.826,98 |
| Crescimento YTD YoY | +12,2072100817% |

## Git e limitações

As alterações locais existentes antes desta fase nos artefatos PBIR/TMDL do Desktop foram preservadas fora do commit. A pasta `TMDLScripts/` não foi alterada. O commit registra a tentativa do padrão em TMDL e a limitação observada no serializador; após o salvamento, a worktree refletiu novamente as oito expressões simples inline.

Não iniciar a Fase 4.5B.
