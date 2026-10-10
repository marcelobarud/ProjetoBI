# Fase 4.0 — preparação para PBIP/TMDL

**Estado:** PASS documental; nenhum projeto Power BI foi criado nesta fase.
**Verificação local:** 2026-10-10. Power BI Desktop não foi localizado por comando, pacote Windows nem nos diretórios padrão consultados; portanto não havia uma instância local disponível para salvar e validar um projeto inicial.

## Decisões registradas

- Formato versionado oficial: Power BI Project (`.pbip`).
- Modelo semântico: TMDL.
- Relatório: PBIR aprimorado, quando disponível/compatível na versão instalada; confirmar a opção do Desktop ao iniciar o projeto.
- Repositório: arquivos de definição legíveis e necessários ao projeto são versionáveis. Ignorar `**/.pbi/cache.abf` e `**/.pbi/localSettings.json`; o `.gitignore` existente foi ajustado para essas exclusões específicas.
- Fonte: PostgreSQL `projeto_bi`, exclusivamente read-only. Não reutilizar a credencial de escrita do gerador no Power BI; antes da conexão, provisionar e validar credencial separada com privilégios de leitura aprovados.
- Armazenamento inicial recomendado: Import, condicionado a avaliação de memória, duração de atualização, granularidade e dimensões selecionadas. A decisão final de modo de armazenamento depende dessa validação.
- Não importar automaticamente todas as 41 tabelas. Começar somente com um conjunto selecionado que sustente grãos e métricas aprovados.

## Estrutura proposta para uma fase posterior

```text
powerbi/
  ProjetoBI.pbip
  ProjetoBI.Report/
    definition.pbir
    definition/                 # PBIR, se suportado
  ProjetoBI.SemanticModel/
    definition.pbism
    definition/                 # TMDL
  README.md                     # instruções de abertura/atualização do projeto
```

Power BI Desktop deve gerar e validar os arquivos de definição. Não criar manualmente arquivos `.pbip`, `.pbism`, `.pbir` ou TMDL incompletos. Após gerar o primeiro projeto em Desktop, abrir novamente, confirmar que modelo e relatório carregam e revisar o diff antes de versionar.

## Inventário M6 e escopo analítico candidato

Referência de granularidade e relações: [`readiness.md`](readiness.md). Para iniciar a seleção na próxima fase, avaliar apenas as entidades necessárias ao grão escolhido:

- Dimensões/cadastros: `core.stores`, `crm.customers` (com perfil PF/PJ somente se necessário), `catalog.products`, `catalog.categories`, `catalog.brands`, `sales.sales_channels`, `payments.payment_methods` e `inventory.stock_locations`.
- Fatos comerciais: `sales.sales_orders` no grão pedido; `sales.sales_order_items` no grão item; `sales.applied_discounts` pré-agregado ao item.
- Fatos de custo/estoque: `inventory.stock_movements` no grão movimento e `inventory.stock_positions` como fotografia atual, com propósitos claramente separados.
- Fatos financeiros e pós-venda: `payments.payments`, `payments.refunds`, `after_sales.returns`/`return_items` e, conforme necessidades de caixa, `payments.payment_installments`.
- `logistics.fulfillments` e `fulfillment_items` entram somente se o relatório precisar do grão de atendimento. Evitar junções cruas entre fatos filhos; pré-agregar ao grão do visual/medida para impedir fanout.

Esta lista é um conjunto candidato para análise, não seleção final nem aprovação de um modelo estrela. Consultar `docs/data-generation/portfolio-validation.md` e os 13 baselines antes de fixar métricas e cardinalidades.

## Tabelas vazias e impacto

A inspeção da origem em transação read-only confirmou `sales.sales_order_item_cancellations=0`, `inventory.stock_transfers=0` e `inventory.stock_transfer_items=0`. Há 3.265 pedidos com status final `cancelled`; os 6.557 itens associados não têm quantidades expedidas nem canceladas. O histórico classifica esses pedidos como cancelados antes de fulfillment. Essa ocorrência não materializou linhas na tabela de cancelamentos parciais da migration 003, cuja semântica operacional é cancelamento de saldo de item por prazo de estoque. Portanto, análises de parcelas de cancelamento, valor de itens cancelados e refunds atribuídos a essas parcelas não podem ser derivadas dessa tabela para este Portfolio.

O profile homologado mantém `supply_transfer_enabled=0` e declara 12 transferências estruturais. A geração dessas transferências depende de déficits/doador elegíveis e de a janela causal caber antes do cutoff. Como não há transferências gravadas e o relatório não guarda contagem de candidatos rejeitados, a causa exata de não seleção não é demonstrável somente com o dataset persistido. Não há amostra de movimentos `transfer_out`/`transfer_in`; não inventar registros ou usar transferências como evidência neste conjunto.

## Fontes oficiais consultadas

- [Documentação do Power BI Desktop Developer Mode](https://learn.microsoft.com/en-us/power-bi/developer/projects/).
- [Visão geral de Power BI Projects (PBIP)](https://learn.microsoft.com/en-us/power-bi/developer/projects/projects-overview).
- [Modelo semântico de projeto e formato TMDL](https://learn.microsoft.com/en-us/power-bi/developer/projects/projects-dataset).
- [Pasta de relatório de projeto e PBIR](https://learn.microsoft.com/en-us/power-bi/developer/projects/projects-report).
- [Formato aprimorado PBIR](https://learn.microsoft.com/en-us/power-bi/developer/embedded/projects-enhanced-report-format).

As páginas oficiais descrevem PBIP com definições textuais adequadas a controle de versão, TMDL para o modelo semântico e PBIR para definições detalhadas do relatório. A compatibilidade e as opções disponíveis devem ser verificadas no Power BI Desktop instalado quando a fase de modelagem for autorizada.
