# Ecossistema operacional conceitual

## Objetivo e convenções

Este documento descreve os domínios operacionais e entidades candidatas que poderão orientar a futura modelagem relacional do ProjetoBI. É uma visão de negócio, não um diagrama físico.

- **Decisão do projeto** identifica exigências já estabelecidas no escopo da Fase 1.
- **Proposta** identifica recomendações sujeitas à revisão antes da modelagem.
- As entidades são candidatas, não uma lista definitiva de tabelas.
- Os “principais conceitos mantidos” descrevem informação de negócio, não nomes ou tipos de colunas.
- Não estão definidos tipos SQL, identificadores físicos, constraints, índices, migrations ou quais fontes entrarão no Power BI.

## Visão dos domínios e relações

A operação começa com a organização de lojas, locais de estoque, funcionários, funções e canais. O catálogo descreve os itens comercializados e suas relações com marcas, categorias e fornecedores. Clientes originam pedidos em canais distintos; pedidos reúnem itens, preços e descontos, que podem exigir reservas de estoque, pagamentos e atendimento logístico. Suprimentos repõem estoque por compras e recebimentos. Devoluções referenciam itens vendidos e podem resultar em retorno ao estoque e reembolso.

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
| Cliente | Identidade comum do comprador, com classificação PF/PJ, situação, referências e datas administrativas. | Pode ter dados específicos PF ou PJ, vários contatos/endereço e vários pedidos. | Cadastrado, ativo, inativo ou restrito; histórico comercial é preservado. |
| Perfil de pessoa física | Complementar o cadastro comum com atributos de identificação próprios de PF. | Extensão do cliente classificado como pessoa física. | Acompanha a situação e as alterações cadastrais relevantes do cliente. |
| Perfil de pessoa jurídica | Complementar o cadastro comum com atributos de identificação e representação próprios de PJ. | Extensão do cliente classificado como pessoa jurídica. | Acompanha alterações cadastrais sem modificar o contexto de pedidos passados. |
| Contato do cliente | Manter meios e preferências de contato e a finalidade de uso. | Pertence ao cliente; pode ser selecionado para comunicação ou atendimento. | Incluído, atualizado e eventualmente inativado sem apagar o histórico necessário. |
| Endereço do cliente | Manter localizações cadastradas e sua finalidade, como cobrança, entrega ou sede. | Pertence ao cliente; pode ser usado por pedidos e entregas. | Atualizações cadastrais preservam o endereço efetivamente usado no pedido. |

**Hipótese recomendada:** usar uma identidade cadastral comum com perfis PF/PJ complementares. Cada pedido preservará o contexto necessário do destinatário/endereço utilizado, sem exigir que o cadastro atual permaneça imutável.

## Catálogo e fornecedores

**Objetivo:** manter o que a empresa vende, sua organização comercial, relação de abastecimento e evolução de preço.

| Entidade candidata | Responsabilidade e principais conceitos | Relações conceituais | Ciclo de vida |
| --- | --- | --- | --- |
| Categoria | Organizar famílias de produtos e permitir subcategorias em uma hierarquia. | Pode conter categorias filhas e classificar produtos. | Ativa/inativa; reorganizações não apagam a classificação histórica necessária. |
| Marca | Identificar marca ou fabricante associado ao produto. | Pode identificar muitos produtos. | Ativa/inativa sem remover vendas e compras históricas. |
| Produto | Descrever item comercializado, especificações pertinentes, referências internas/externas, marca, categoria e situação. | Pode ter preços ao longo do tempo, diversos fornecedores e estar presente em vendas, compras e estoque. | Preparado, comercializado, descontinuado; descontinuação não apaga o histórico. |
| Vigência de preço comercial | Registrar preço e período/contexto em que a oferta comercial vale. | Refere-se ao produto e pode ser aplicado a pedidos segundo canal ou condição definida futuramente. | Entra em vigor, é substituída ou expira; pedidos mantêm o preço efetivamente aplicado. |
| Fornecedor | Representar entidade que oferece mercadorias, com referências cadastrais, contatos e situação. | Relaciona-se a produtos e compras. | Avaliado, ativo, suspenso ou inativo; transações anteriores são preservadas. |
| Relação produto-fornecedor | Registrar que um fornecedor pode abastecer um produto, com referências comerciais e preferência eventual. | Liga produtos a fornecedores; pode contextualizar itens de compra. | Ativada/desativada por vigência; preferência não impede compras alternativas. |

**Hipóteses recomendadas:** categoria e subcategoria são uma hierarquia, não tipos físicos distintos; produto pode ter vários fornecedores; histórico de compra suporta a análise de custo, mas método de valorização ainda precisa ser aprovado.

## Comercial e vendas

**Objetivo:** acompanhar o pedido desde a origem até sua conclusão/cancelamento, incluindo itens, condições e mudanças de situação.

| Entidade candidata | Responsabilidade e principais conceitos | Relações conceituais | Ciclo de vida |
| --- | --- | --- | --- |
| Pedido de venda | Registrar cliente, canal, momento comercial, endereço/atendimento, referências externas, situação e valores do pedido. | Tem vários itens; pode ter vendedor, pagamentos, unidades de atendimento, reservas e devoluções. | Criado, aguardando condições, confirmado, em atendimento, concluído ou cancelado segundo etapas a aprovar. |
| Item de pedido | Registrar produto, quantidade, preço e desconto praticados e contexto comercial daquele item. | Pertence ao pedido e referencia produto; pode gerar movimentos, atendimento e devolução. | Criado com o pedido; quantidade atendida e devolvida é acompanhada sem reescrever o fato histórico. |
| Histórico de situação do pedido | Guardar transições, momento e motivo de mudanças relevantes. | Relaciona-se ao pedido e, quando disponível, ao responsável pela alteração. | Cada transição é adicionada como evento; situação atual deriva da sequência definida. |
| Regra/campanha de desconto | Descrever campanha ou condição promocional e seu período/escopo. | Pode ser aplicada ao pedido ou item e registrada como origem do desconto. | Planejada, vigente, encerrada ou cancelada; aplicação passada permanece identificável. |

**Hipótese recomendada:** manter pedido e item como conceitos separados; preço/desconto aplicado fica preservado no contexto do item vendido. O canal identifica origem e vendedor é opcional dependendo da operação.

## Suprimentos e recebimento

**Objetivo:** registrar reposição de mercadorias, compromisso de compra e entradas efetivamente aceitas.

| Entidade candidata | Responsabilidade e principais conceitos | Relações conceituais | Ciclo de vida |
| --- | --- | --- | --- |
| Pedido de compra | Representar ordem enviada a fornecedor, datas, referências, condições e situação. | Tem vários itens e pode originar vários recebimentos. | Preparado, aprovado, enviado, parcial, recebido, fechado ou cancelado. |
| Item de compra | Registrar produto, quantidade solicitada, condição de custo e quantidade recebida associada. | Pertence ao pedido e referencia produto/fornecedor. | Solicitado, parcialmente recebido, completo ou cancelado quanto ao saldo não recebido. |
| Recebimento de mercadoria | Registrar evento de chegada e conferência em um local de estoque. | Origina-se de pedido de compra e contém itens de recebimento; gera movimentos de entrada para quantidades aceitas. | Aberto, conferido e finalizado; correções posteriores são rastreadas. |
| Item de recebimento | Detalhar produto, quantidade recebida, aceita ou rejeitada e vínculo com item de compra. | Pertence a recebimento e item de compra; aceites afetam estoque. | Conferido e destinado; rejeições não são entrada disponível. |

**Hipótese recomendada:** permitir recebimentos parciais para representar entregas em etapas. Entrada de estoque decorre de quantidade aceita, não apenas da criação da ordem de compra.

## Estoque

**Objetivo:** conhecer disponibilidade por produto e local, registrar eventos físicos e reservar unidades para pedidos.

| Entidade candidata | Responsabilidade e principais conceitos | Relações conceituais | Ciclo de vida |
| --- | --- | --- | --- |
| Posição de estoque | Representar a posição operacional de um produto em um local, distinguindo quantidades físicas, reservadas e disponíveis conforme a política. | Relaciona produto e local; deve ser conciliável com movimentos e reservas. | Varia com eventos confirmados; não substitui a trilha histórica. |
| Movimento de estoque | Registrar entrada, saída, transferência, devolução ou ajuste com motivo, origem/destino e referência operacional. | Relaciona produto/local a recebimento, pedido, devolução ou operação interna. | Confirmado após evento físico; correção é novo movimento rastreável. |
| Reserva de estoque | Representar unidades comprometidas a pedido antes da saída física. | Liga pedido/item, produto e local; pode ser liberada ou convertida em saída. | Criada, parcialmente atendida, liberada ou expirada conforme política futura. |

**Hipóteses recomendadas:** posição é por produto e local; movimento é a trilha auditável; reserva reduz disponibilidade sem representar saída física. Transferência cria efeitos correspondentes nos dois locais e pode ter etapa em trânsito caso o domínio exija.

## Pagamentos

**Objetivo:** acompanhar os meios, tentativas, parcelas e reversões financeiras sem confundir sua situação com a do pedido.

| Entidade candidata | Responsabilidade e principais conceitos | Relações conceituais | Ciclo de vida |
| --- | --- | --- | --- |
| Meio de pagamento | Classificar opções aceitas e suas características operacionais. | Pode ser usado por pagamentos em vários pedidos. | Habilitado/desabilitado sem alterar pagamentos existentes. |
| Pagamento/operação financeira | Registrar tentativa ou operação de cobrança ligada ao pedido, meio, valor e referência externa. | Um pedido pode ter várias operações; pode possuir parcelas e reembolsos. | Iniciado, autorizado, capturado, recusado, cancelado, estornado ou parcialmente reembolsado conforme integração. |
| Parcela | Representar vencimento e situação de cada parte quando um pagamento parcelado for aplicável. | Pertence à operação/plano de pagamento. | Programada, paga, vencida, cancelada ou revertida conforme a regra definida. |
| Reembolso/estorno | Registrar devolução financeira, montante, motivo e vínculo com pagamento e devolução. | Relaciona-se à operação original e a uma devolução ou ajuste autorizado. | Solicitado, processado, recusado ou concluído. |

**Hipótese recomendada:** pagamento pode ser dividido em mais de uma operação e pode ser parcelado; uma recusa de tentativa não é recebimento. Política de liquidação, estorno e crédito permanece por aprovar.

## Logística e atendimento

**Objetivo:** executar entrega ou retirada, com rastreabilidade operacional independente do estado financeiro.

| Entidade candidata | Responsabilidade e principais conceitos | Relações conceituais | Ciclo de vida |
| --- | --- | --- | --- |
| Unidade de atendimento/remessa | Representar preparação e entrega/retirada de todo ou parte do pedido, origem de estoque, modalidade e situação. | Liga pedido/itens a local de origem, transportadora quando aplicável e eventos de rastreio. | A separar, separado, despachado, entregue, disponível para retirada, retirado, falhou ou cancelado. |
| Transportadora | Identificar prestador logístico e referências necessárias para atendimento. | Pode estar associada a unidades de entrega e eventos de rastreamento. | Habilitada/desabilitada sem apagar remessas históricas. |
| Evento logístico | Registrar eventos de preparação, despacho, tentativa de entrega, entrega ou retirada e suas referências. | Pertence a uma unidade de atendimento e pode ter origem interna ou externa. | Acrescentado conforme a execução; correções preservam a trilha. |

**Hipótese recomendada:** permitir conceitualmente mais de uma unidade de atendimento por pedido para acomodar expedições de locais diferentes, mas confirmar se entregas parciais serão necessárias na primeira versão. Retirada não exige transportadora.

## Devoluções

**Objetivo:** tratar solicitação, análise, retorno físico e eventual consequência financeira dos itens vendidos.

| Entidade candidata | Responsabilidade e principais conceitos | Relações conceituais | Ciclo de vida |
| --- | --- | --- | --- |
| Devolução | Registrar solicitação, motivo, pedido de origem, decisão e andamento geral. | Pertence a cliente/pedido e possui itens; pode originar movimento e reembolso. | Solicitada, em análise, aprovada parcialmente/totalmente, recusada, recebida e concluída. |
| Item de devolução | Identificar item vendido, quantidade solicitada/aceita, condição e destinação do produto. | Referencia item do pedido; pode originar entrada disponível, quarentena ou descarte. | Solicitado, avaliado, aceito/recusado e destinado. |

**Hipótese recomendada:** a soma devolvida não excede o vendido; aprovação, recebimento, retorno vendável ao saldo e reembolso são eventos distintos. Troca pode ser representada inicialmente por devolução e novo pedido.

## Relações transversais e fronteiras operacionais

- Um pedido liga cliente, canal e itens; funcionário/vendedor pode estar associado conforme o atendimento.
- Cada item liga produto e condições praticadas à operação comercial. A compra liga produto a fornecedor e recebimento aceito.
- Pedido confirmado pode criar reserva; atendimento concluído cria saída; cancelamento libera reserva antes da saída; devolução aceita cria evento de retorno conforme inspeção.
- Pagamento e pedido evoluem independentemente. Reembolso liga retorno comercial a uma operação financeira.
- O histórico operacional pode guardar criação/atualização, referências, estados e observações coerentes com cada processo, sem presumir que todos esses dados serão analíticos.

## Limites para a modelagem posterior

A lista pode resultar aproximadamente em algumas dezenas de entidades, mas não é uma meta nem compromisso de quantidade. A Fase 2 deverá revisar este domínio e decidir cardinalidades exatas, obrigatoriedades, nomenclatura, histórico, chaves e regras de integridade antes de criar qualquer objeto PostgreSQL. Não há aqui modelo estrela, seleção de fontes para o Power BI, SQL ou definição física de colunas.
