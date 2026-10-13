# Fase 5.1 — Visão Executiva InfoTech

**Status:** `PARTIAL — ABERTURA E COMPONENTES CONFIRMADOS PELO USUÁRIO; VALIDAÇÃO FUNCIONAL PENDENTE`

**Data:** 2026-10-12

**Canvas:** Full HD 1920×1080 px (16:9), conforme orientação do usuário

**Projeto:** `powerbi/ProjetoBI.pbip`

## Escopo executado

- Reutilizada a única página existente e renomeada para **Visão Executiva**; não foram criadas páginas de destino ou placeholders.
- Importado o tema `InfoTech Intelligence — Light v0.1`. O Power BI Desktop aceitou a importação e indicou esse tema como atual. Na cópia registrada, o Desktop expandiu `dataColors` de 8 para 480 entradas; os oito tokens aprovados iniciais permanecem na mesma ordem e todas as demais propriedades continuam iguais ao tema-fonte. O recurso está registrado em `powerbi/ProjetoBI.Report/StaticResources/RegisteredResources/InfoTech_Intelligence___Light_537872542319678.json`.
- Definido o fundo `#F5F7FB` e canvas Full HD 1920×1080. O cabeçalho textual usa InfoTech Intelligence e identifica a página e a janela Jan–Set/2026.
- Composta uma linha de três segmentações: data comercial de `DimCalendario[Data]`, `DimCanal[name]` e `DimLoja[name]`. A seleção inicial de data foi configurada para 2026-01-01 a 2026-09-30, permanecendo editável no slicer.
- Adicionados quatro cartões nativos, todos baseados em medidas existentes de `_Medidas`:
  - Receita líquida — `Receita Analítica Após Devoluções`.
  - Lucro bruto — `Lucro Bruto Analítico`.
  - Margem bruta — `Margem Bruta Analítica`.
  - Pedidos concluídos — `Pedidos Concluídos`.
- Definida formatação local aos visuais: valores monetários com prefixo `R$` e duas casas, margem com duas casas percentuais e pedidos como inteiro sem casas. Nenhuma propriedade de formatação ou fórmula no TMDL foi alterada; a apresentação pt-BR ainda precisa ser confirmada no Desktop.
- Adicionada uma linha mensal com `DimCalendario[AnoMes]`, ordenado no modelo por `AnoMesOrdem`, e as medidas Receita Analítica Após Devoluções e Lucro Bruto Analítico.
- Adicionadas barras horizontais agrupadas por canal (`DimCanal[name]`) e Top 5 categorias (`DimProduto[category_name]`), ambas ordenadas pela Receita Analítica Após Devoluções.
- A interação categoria → cartão Pedidos concluídos está explicitamente definida como `NoFilter`; as demais interações permanecem no comportamento padrão dos visuais.
- O layout usa margens de 36 px; cartões de 450×136 px e intervalos de 16 px; gráfico temporal de 1848×300 px; detalhamentos inferiores de 912×350 px com intervalo de 24 px. Todos os componentes permanecem dentro do canvas.

## Regras semânticas preservadas

- Não foram modificadas fórmulas DAX, tabelas, relações, Power Query, dados ou objetos PostgreSQL. Ao reabrir e salvar o PBIP, o Desktop gerou metadados linguísticos em `powerbi/ProjetoBI.SemanticModel/definition/cultures/pt-BR.tmdl`; essa alteração automática foi mantida na working tree e ficará fora do commit desta fase.
- Receita, lucro e margem usam as medidas financeiras por coorte do pedido já homologadas. A linha de tendência usa `AnoMes` do calendário comercial; não contém meses fora da cobertura até setembro de 2026.
- O ranking de categorias usa a medida financeira atribuível ao grão de produto. Nenhuma medida de cabeçalho de pedido foi atribuída a produto.
- Não foram incluídos os KPIs secundários opcionais de COGS e variação YTD; quatro cartões principais e os três blocos de análise foram priorizados.
- Nenhum valor financeiro ou contagem foi codificado nos visuais.

## Verificações locais realizadas

- Os 11 arquivos `visual.json` passam no schema oficial PBIR Visual Container 2.7.0; `page.json` passa no schema PBIR Page 2.1.0.
- Os arquivos JSON foram analisados; as posições ficam dentro do canvas 1920×1080; a interação declarada aponta para dois visuais existentes.
- Uma verificação local comparou todas as referências de colunas e medidas dos visuais com o TMDL do projeto. Os nomes existem no modelo, que permanece com 10 tabelas, 55 medidas e 21 relações.
- A cópia registrada do tema mantém os tokens aprovados e a expansão de `dataColors` feita pelo Desktop; a importação foi anteriormente aceita. A definição da página e os 11 visuais foram salvos em PBIR com o Desktop fechado, evitando conflito entre arquivo e estado em memória. Depois, o usuário reabriu o PBIP e confirmou que a página abriu e os componentes aparecem.
- Não foi feita consulta direta ao PostgreSQL. Nenhuma credencial foi modificada.

## Validação ainda necessária no Desktop

Esta classificação permanece **PARTIAL** até completar os testes funcionais e visuais a seguir:

1. Conferir visualmente que tema, textos, cartões, filtros e três gráficos foram renderizados como esperado; a abertura e a presença dos componentes foram confirmadas pelo usuário, mas não inspecionadas diretamente nesta sessão.
2. A apresentação dos valores completos, incluindo a cultura pt-BR (`R$`, separadores decimais e de milhar), os percentuais com duas casas, os inteiros e BLANK sem conversão artificial.
3. A janela inicial Jan–Set/2026 e sua edição/limpeza; os cenários de 2025, Canal, Loja, combinações e ausência de dados.
4. O Top 5 decrescente e a proteção do cartão Pedidos concluídos ao selecionar categoria.
5. A reconciliação dos cartões para Jan–Set/2026 com as referências já homologadas — receita R$ 228.660.758,74, lucro R$ 52.590.608,65, margem aproximada 23,00% — usando consulta DAX de diagnóstico no mecanismo local. Esses valores são critérios de verificação, não foram inseridos nos visuais.
6. Acessibilidade operacional: contraste no canvas real, texto alternativo, ordem/foco de teclado, leitura das segmentações e distinção entre BLANK e zero.
7. Performance Analyzer para tendência, rankings e resposta a filtros.
8. Salvar, fechar e reabrir novamente, confirmando persistência da página.

A ordem de tabulação está registrada nos visuais (`tabOrder` 0–10), mas não foi testada com teclado. A análise de contraste dos tokens existe no Design System; a página real ainda não foi inspecionada em escala de cinza nem com leitor de tela. Nenhum resultado de desempenho ou regressão de medida é declarado.

## Limites e Git

- `queryLimitOption=None` e a expansão `outspacePane` existentes em `report.json` são alterações locais preexistentes e foram preservadas. A importação do tema acrescentou a referência `customTheme` e o pacote registrado; o restante do diff preexistente deverá permanecer fora do commit.
- O desenvolvimento local foi autorizado pela Fase 5.1. A pendência de limite de consultas não invalida o modelo semântico, mas precisa ser revisada antes de publicação.
- O commit local só deve incluir os artefatos da página, o recurso de tema e a documentação da Fase 5.1; nenhuma alteração de publicação, push ou merge foi feita.

## Resultado

**FASE 5.1 PARTIAL — FUNCTIONAL VALIDATION PENDING**. A estrutura PBIR e o layout Full HD estão compostos e validados estaticamente. O usuário confirmou que o projeto abriu e que os componentes aparecem; valores, renderização detalhada e comportamento funcional ainda não foram validados.
