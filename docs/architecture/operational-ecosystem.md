# Ecossistema operacional conceitual

## Objetivo e convenções

Este documento descreve os domínios operacionais e entidades candidatas que poderão orientar a futura modelagem relacional do ProjetoBI. É uma visão de negócio, não um diagrama físico.

- **Decisão do projeto** identifica exigências aprovadas nas Fases 1 e 1.1.
- **Proposta** identifica recomendações sujeitas à revisão antes da modelagem.
- As entidades são candidatas, não uma lista definitiva de tabelas.
- Os “principais conceitos mantidos” descrevem informação de negócio, não nomes ou tipos de colunas.
- Não estão definidos tipos SQL, identificadores físicos, constraints, índices, migrations ou quais fontes entrarão no Power BI.

## Contexto operacional aprovado

- A operação principal ocorre no Brasil e usa BRL como moeda operacional principal.
- Endereços são brasileiros. A identificação de PF/PJ pode incluir conceitualmente CPF, CNPJ, CEP, UF e município quando pertinentes, sem especificar representação ou validações físicas.
- Cálculo tributário, legislação fiscal detalhada, NF-e/NFC-e, ICMS, PIS/COFINS, SPED, escrituração, contabilidade e obrigações legais completas estão fora do escopo.

## Visão dos domínios e relações

A operação começa com a organização de lojas, locais de estoque, funcionários, funções e canais. O catálogo descreve os itens comercializados e suas relações com marcas, categorias e fornecedores. Pedidos se originam em canais distintos e podem referenciar clientes identificados conforme as regras do canal; cada pedido reúne itens, preços e descontos, que podem exigir reservas de estoque, pagamentos e atendimento logístico. Suprimentos repõem estoque por compras e recebimentos. Devoluções referenciam itens vendidos e podem resultar em retorno ao estoque e reembolso.

As relações atravessam domínios: a origem comercial do pedido não determina seu meio de pagamento; o status do pedido não determina a liquidação financeira; o atendimento pode ocorrer em mais de um local; e uma devolução aprovada não equivale automaticamente a um produto disponível ou a um reembolso concluído.

## Organização e canais

**Objetivo:** representar os pontos e as pessoas que executam a operação e distinguir onde ou por qual canal a venda foi originada.

| Entidade candidata | Responsabilidade e principais conceitos | Relações conceituais | Ciclo de vida |
| --- | --- | --- | --- |
| Loja | Representar um ponto físico, com dados de identificação, localização, situação e datas administrativas. | Pode possuir locais de estoque e receber pedidos para atendimento/retirada; relaciona-se aos funcionários por períodos de lotação. | Planejada, aberta, em operação e encerrada; encerramento preserva o histórico. |
| Local de estoque | Identificar depósito, área de loja ou ponto de expedição onde mercadorias são controladas. | Vincula-se a uma loja ou operação digital; relaciona-se a posições, movimentos, reservas, recebimentos e atendimentos. | Ativo ou desativado, mantendo histórico dos saldos e movimentos anteriores. |
| Canal de venda | Distinguir loja física, e-commerce próprio e cada marketplace relevante. | Origem de pedidos; pode conter referência externa específica do canal. | Habilitado ou desativado conforme a operação, sem apagar pedidos existentes. |
| Funcionário | Representar pessoa vinculada à operação, seus dados administrativos e situação de vínculo. | Pode exercer função e lotação por períodos; pode ser responsável por venda, recebimento, ajuste ou atendimento. | Admitido, ativo, afastado ou desligado conforme regras futuras; atribuições históricas permanecem. |
| Função | Classificar responsabilidade operacional básica, como vendedor ou estoque. | Pode ser associada a funcionários em períodos de atuação. | Pode evoluir sem reclassificar atribuições históricas. |
| Lotação/atribuição funcional | Preservar a função, loja ou área em que o funcionário atua durante um período. | Liga funcionário a função e, quando pertinente, a loja ou área. | Inicia e termina em datas efetivas; períodos históricos não são apagados. |

**Hipótese recomendada:** manter canais como conceitos próprios, em vez de inferi-los a partir da loja ou modalidade de entrega. Assim, marketplace permanece identificável mesmo quando a empresa executa entrega ou atendimento.

## Clientes

**Objetivo:** apoiar identificação, comunicação, faturamento/atendimento e histórico de relacionamento para PF e PJ.

| Entidade candidata | Responsabilidade e principais conceitos | Relações conceituais | Ciclo de vida |
| --- | --- | --- | --- |
| Cliente | Identidade comum do comprador identificado, com classificação PF/PJ, situação, referências e datas administrativas. | Pode ter dados específicos PF ou PJ, vários contatos/endereço e vários pedidos identificados. Um pedido presencial pode não ter cliente; canais digitais exigem cliente identificado. | Cadastrado, ativo, inativo ou restrito; histórico comercial é preservado. |
| Perfil de pessoa física | Complementar o cadastro comum com atributos de identificação próprios de PF. | Extensão do cliente classificado como pessoa física. | Acompanha a situação e as alterações cadastrais relevantes do cliente. |
| Perfil de pessoa jurídica | Complementar o cadastro comum com atributos de identificação e representação próprios de PJ. | Extensão do cliente classificado como pessoa jurídica. | Acompanha alterações cadastrais sem modificar o contexto de pedidos passados. |
| Contato do cliente | Manter meios e preferências de contato e a finalidade de uso. | Pertence ao cliente; pode ser selecionado para comunicação ou atendimento. | Incluído, atualizado e eventualmente inativado sem apagar o histórico necessário. |
| Endereço do cliente | Manter localizações cadastradas e sua finalidade, como cobrança, entrega ou sede. | Pertence ao cliente; pode ser usado por pedidos e entregas. | Atualizações cadastrais preservam o endereço efetivamente usado no pedido. |

**Hipótese ainda revisável:** usar uma identidade cadastral comum com perfis PF/PJ complementares. Cada pedido identificado preservará o contexto necessário do destinatário/endereço utilizado, sem exigir que o cadastro atual permaneça imutável. A venda presencial anônima não cria cliente genérico; como a eventual identificação posterior será tratada permanece para a modelagem.

## Catálogo e fornecedores

**Objetivo:** manter o que a empresa vende, sua organização comercial, relação de abastecimento e evolução de preço.

| Entidade candidata | Responsabilidade e principais conceitos | Relações conceituais | Ciclo de vida |
| --- | --- | --- | --- |
| Categoria | Organizar famílias de produtos e permitir subcategorias em uma hierarquia. | Pode conter categorias filhas e classificar produtos. | Ativa/inativa; reorganizações não apagam a classificação histórica necessária. |
| Marca | Identificar marca ou fabricante associado ao produto. | Pode identificar muitos produtos. | Ativa/inativa sem remover vendas e compras históricas. |
| Produto (SKU vendável) | Representar o item/configuração comercial efetivamente vendido, com especificações pertinentes, referências internas/externas, marca, categoria e situação. | Pode ter preços ao longo do tempo, diversos fornecedores e estar presente em vendas, compras e estoque. | Preparado, comercializado, descontinuado; descontinuação não apaga o histórico. |
| Vigência de preço comercial | Registrar preço e período/contexto em que a oferta comercial vale. | Refere-se ao produto e pode ser aplicado a pedidos segundo canal ou condição definida futuramente. | Entra em vigor, é substituída ou expira; pedidos mantêm o preço efetivamente aplicado. |
| Fornecedor | Representar entidade que oferece mercadorias, com referências cadastrais, contatos e situação. | Relaciona-se a produtos e compras. | Avaliado, ativo, suspenso ou inativo; transações anteriores são preservadas. |
| Relação produto-fornecedor | Registrar que um fornecedor pode abastecer um produto, com referências comerciais e preferência eventual. | Liga produtos a fornecedores; pode contextualizar itens de compra. | Ativada/desativada por vigência; preferência não impede compras alternativas. |

**Decisões do projeto:** cada combinação comercial distinta pode ser representada por um produto/SKU próprio; a primeira versão não exige uma camada adicional de variantes. Especificações podem variar por categoria, e sua organização será decidida na modelagem. Produto pode ter vários fornecedores. O método inicial aprovado de valorização é custo médio móvel; cada item vendido preserva o custo aplicável no momento da venda, e detalhes de cálculo e custos elegíveis permanecem para decisão posterior.

**Hipótese ainda revisável:** organizar categorias e subcategorias como hierarquia conceitual.

## Comercial e vendas

**Objetivo:** acompanhar o pedido desde a origem até sua conclusão/cancelamento, incluindo itens, condições e mudanças de situação.

| Entidade candidata | Responsabilidade e principais conceitos | Relações conceituais | Ciclo de vida |
| --- | --- | --- | --- |
| Pedido de venda | Registrar canal, cliente quando identificado, momento comercial, endereço/atendimento, referências externas, situação e valores. | Tem vários itens; cliente é obrigatório nos canais digitais e opcional em venda presencial. Pode ter vendedor, pagamentos, uma ou mais unidades de atendimento, reservas e devoluções. | Criado, aguardando condições, confirmado, em atendimento, concluído ou cancelado segundo etapas a aprovar. |
| Item de pedido | Registrar produto/SKU, quantidade, preço, desconto e custo considerado na venda, preservando o contexto comercial e de custo daquele momento. | Pertence ao pedido e referencia produto/SKU; pode gerar movimentos, uma ou mais unidades de atendimento e devolução. | Criado com o pedido; quantidades atendidas e devolvidas e o custo histórico não são reescritos por mudanças posteriores de catálogo ou custo médio. |
| Histórico de situação do pedido | Guardar transições, momento e motivo de mudanças relevantes. | Relaciona-se ao pedido e, quando disponível, ao responsável pela alteração. | Cada transição é adicionada como evento; situação atual deriva da sequência definida. |
| Regra/campanha de desconto | Descrever campanha ou condição promocional e seu período/escopo. | Pode ser aplicada ao pedido ou item e registrada como origem do desconto. | Planejada, vigente, encerrada ou cancelada; aplicação passada permanece identificável. |

**Decisões do projeto:** pedido e item são conceitos separados; preço, desconto e custo aplicável são preservados no contexto histórico do item vendido. O cliente pode estar ausente somente na venda presencial aprovada; nos canais digitais é identificado. Vendedor é opcional em e-commerce e marketplace.

## Suprimentos e recebimento

**Objetivo:** registrar reposição de mercadorias, compromisso de compra e entradas efetivamente aceitas.

| Entidade candidata | Responsabilidade e principais conceitos | Relações conceituais | Ciclo de vida |
| --- | --- | --- | --- |
| Pedido de compra | Representar ordem enviada a fornecedor, datas, referências, condições e situação. | Tem vários itens e pode originar um ou mais recebimentos em etapas. | Preparado, aprovado, enviado, parcial, recebido, fechado ou cancelado. |
| Item de compra | Registrar produto, quantidade solicitada, condição de custo e quantidade recebida associada. | Pertence ao pedido e referencia produto/fornecedor. | Solicitado, parcialmente recebido, completo ou cancelado quanto ao saldo não recebido. |
| Recebimento de mercadoria | Registrar evento de chegada e conferência em um local de estoque. | Origina-se de pedido de compra e contém itens de recebimento; gera movimentos de entrada para quantidades aceitas. | Aberto, conferido e finalizado; correções posteriores são rastreadas. |
| Item de recebimento | Detalhar produto, quantidade recebida, aceita ou rejeitada e vínculo com item de compra. | Pertence a recebimento e item de compra; aceites afetam estoque. | Conferido e destinado; rejeições não são entrada disponível. |

**Decisão do projeto:** uma compra pode ser recebida em várias etapas. A entrada física decorre das quantidades efetivamente aceitas em cada recebimento, nunca apenas da criação ou aprovação da ordem. Recebimentos parciais são suportados, mas não precisam ser comuns nos dados sintéticos futuros.

## Estoque

**Objetivo:** conhecer disponibilidade por produto e local, registrar eventos físicos e reservar unidades para pedidos.

| Entidade candidata | Responsabilidade e principais conceitos | Relações conceituais | Ciclo de vida |
| --- | --- | --- | --- |
| Posição de estoque | Representar a posição operacional de um produto em um local, distinguindo quantidades físicas, reservadas e disponíveis conforme a política. | Relaciona produto e local; deve ser conciliável com movimentos e reservas. | Varia com eventos confirmados; não substitui a trilha histórica. |
| Movimento de estoque | Registrar entrada, saída, transferência, devolução ou ajuste com motivo, origem/destino e referência operacional. | Relaciona produto/local a recebimento, pedido, devolução ou operação interna. | Confirmado após evento físico; correção é novo movimento rastreável. |
| Reserva de estoque | Representar unidades comprometidas a pedido antes da saída física. | Liga pedido/item, produto e local; pode ser liberada ou convertida em saída. | Criada, parcialmente atendida, liberada ou expirada conforme política futura. |

**Decisões do projeto:** estoque é acompanhado conceitualmente por produto e local; movimentos formam a trilha operacional histórica; reserva reduz disponibilidade sem representar saída física.

**Hipóteses ainda revisáveis:** manter uma posição de saldo conciliável com os movimentos para consulta rápida; representar transferências com efeitos correspondentes nos dois locais e, caso necessário, uma etapa em trânsito.

## Pagamentos

**Objetivo:** acompanhar os meios, tentativas, parcelas e reversões financeiras sem confundir sua situação com a do pedido.

| Entidade candidata | Responsabilidade e principais conceitos | Relações conceituais | Ciclo de vida |
| --- | --- | --- | --- |
| Meio de pagamento | Classificar opções aceitas e suas características operacionais. | Pode ser usado por pagamentos em vários pedidos. | Habilitado/desabilitado sem alterar pagamentos existentes. |
| Pagamento/operação financeira | Registrar tentativa ou operação de cobrança ligada ao pedido, meio, valor e referência externa. | Um pedido pode ter várias operações; pode possuir parcelas e reembolsos. | Iniciado, autorizado, capturado, recusado, cancelado, estornado ou parcialmente reembolsado conforme integração. |
| Parcela | Representar vencimento e situação de cada parte quando um pagamento parcelado for aplicável. | Pertence à operação/plano de pagamento. | Programada, paga, vencida, cancelada ou revertida conforme a regra definida. |
| Reembolso/estorno | Registrar devolução financeira, montante, motivo e vínculo com pagamento e devolução. | Relaciona-se à operação original e a uma devolução ou ajuste autorizado. | Solicitado, processado, recusado ou concluído. |

**Decisões do projeto:** um pedido pode ter uma ou mais operações de pagamento e parcelamento quando aplicável; os ciclos de pedido e pagamento são independentes; uma tentativa recusada não representa receita recebida.

**Hipótese ainda revisável:** política de liquidação, estorno e crédito.

## Logística e atendimento

**Objetivo:** executar entrega ou retirada, com rastreabilidade operacional independente do estado financeiro.

| Entidade candidata | Responsabilidade e principais conceitos | Relações conceituais | Ciclo de vida |
| --- | --- | --- | --- |
| Unidade de atendimento/remessa | Representar preparação e entrega/retirada de todo ou parte do pedido, origem de estoque, modalidade e situação. | Um pedido pode possuir várias unidades, ligando seus itens a locais de origem, transportadora quando aplicável e eventos de rastreio. | A separar, separado, despachado, entregue, disponível para retirada, retirado, falhou ou cancelado. |
| Transportadora | Identificar prestador logístico e referências necessárias para atendimento. | Pode estar associada a unidades de entrega e eventos de rastreamento. | Habilitada/desabilitada sem apagar remessas históricas. |
| Evento logístico | Registrar eventos de preparação, despacho, tentativa de entrega, entrega ou retirada e suas referências. | Pertence a uma unidade de atendimento e pode ter origem interna ou externa. | Acrescentado conforme a execução; correções preservam a trilha. |

**Decisão do projeto:** uma ou mais unidades de atendimento por pedido são suportadas, incluindo atendimento parcial, origem em locais distintos, retirada de parte do pedido e entrega/retirada em etapas quando necessário. Esses eventos podem ser minoritários na geração futura de dados. Retirada não exige transportadora.

## Devoluções

**Objetivo:** tratar solicitação, análise, retorno físico e eventual consequência financeira dos itens vendidos.

| Entidade candidata | Responsabilidade e principais conceitos | Relações conceituais | Ciclo de vida |
| --- | --- | --- | --- |
| Devolução | Registrar solicitação, motivo, pedido de origem, decisão e andamento geral. | Referencia o pedido e seus itens; o cliente é associado quando identificado. A eventual devolução vinculada a uma venda presencial anônima será definida na modelagem. Pode originar movimento e reembolso. | Solicitada, em análise, aprovada parcialmente/totalmente, recusada, recebida e concluída. |
| Item de devolução | Identificar item vendido, quantidade solicitada/aceita, condição e destinação do produto. | Referencia item do pedido; pode originar entrada disponível, quarentena ou descarte. | Solicitado, avaliado, aceito/recusado e destinado. |

**Decisões do projeto:** devolução referencia itens vendidos e pode ser parcial. Aprovação, recebimento, retorno vendável ao saldo e reembolso são eventos distintos; aprovar uma devolução não significa que o item já está disponível ou que o reembolso foi concluído. Na primeira versão, uma troca pode ser representada por devolução e novo pedido.

**Hipótese ainda revisável:** a soma devolvida não exceder a quantidade vendida, descontadas devoluções anteriores.

## Relações transversais e fronteiras operacionais

- Um pedido liga canal e itens; pode ligar um cliente identificado conforme as regras do canal (obrigatório no digital, opcional no presencial). Funcionário/vendedor pode estar associado conforme o atendimento.
- Cada item liga produto e condições praticadas à operação comercial. A compra liga produto a fornecedor e recebimento aceito.
- Pedido confirmado pode criar reserva; um ou mais atendimentos concluídos criam saídas totais ou parciais; cancelamento libera reserva antes da saída; devolução aceita cria evento de retorno conforme inspeção.
- Pagamento e pedido evoluem independentemente. Reembolso liga retorno comercial a uma operação financeira.
- O histórico operacional pode guardar criação/atualização, referências, estados e observações coerentes com cada processo, sem presumir que todos esses dados serão analíticos.

## Limites para a modelagem posterior

A lista pode resultar aproximadamente em algumas dezenas de entidades, mas não é uma meta nem compromisso de quantidade. A Fase 2 deverá revisar este domínio e decidir cardinalidades exatas, obrigatoriedades, nomenclatura, histórico, chaves e regras de integridade antes de criar qualquer objeto PostgreSQL. Não há aqui modelo estrela, seleção de fontes para o Power BI, SQL ou definição física de colunas.
