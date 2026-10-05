# Regras de negócio conceituais

## Como interpretar este documento

As regras marcadas como **Decisão do projeto** vêm diretamente do escopo aprovado para esta fase. As marcadas como **Proposta** são recomendações para tornar a futura modelagem menos ambígua; podem ser revistas durante a aprovação do domínio. Nenhum item define colunas ou restrições físicas.

## Comercial e pedidos

### Decisões do projeto

- Um pedido representa uma operação de venda e pode conter vários itens.
- O sistema precisa acompanhar a origem do pedido, itens, descontos, situação e participação de vendedores quando aplicável.
- Pedido, pagamento, atendimento logístico e devolução possuem ciclos que precisam ser compreendidos separadamente.
- A empresa vende em loja física, e-commerce próprio e marketplace.

### Propostas

- Registrar um pedido mesmo quando ele ainda não esteja confirmado, para acompanhar rascunho, aguardando pagamento, confirmado, em atendimento, concluído e cancelado conforme as etapas efetivamente adotadas.
- Manter o histórico das mudanças relevantes de situação, com momento, motivo e responsável quando conhecido; a situação atual não substitui o histórico.
- Exigir um cliente associado a todos os pedidos na primeira versão. Em vendas presenciais, o cadastro pode ser feito no atendimento com os dados mínimos definidos futuramente. Essa escolha simplifica devolução, comprovantes e histórico; uma operação de venda anônima exigiria uma decisão posterior.
- Permitir pedido sem vendedor individual em e-commerce e marketplace; loja física assistida registra o funcionário responsável. A atribuição digital pode existir quando houver campanha ou atendimento humano, sem torná-la obrigatória.
- Tratar marketplace como canal de origem próprio, registrando a referência externa da plataforma separadamente da identidade interna do pedido.
- Congelar conceitualmente no item vendido a descrição comercial, quantidade, preço efetivamente praticado e desconto aplicado naquele momento, para que a alteração futura do catálogo não reescreva a venda histórica.
- Representar desconto como valor ou regra aplicada no pedido ou nos itens, identificando a origem quando houver campanha. O total descontado não pode exceder o valor elegível; regras de acumulação e arredondamento dependem de decisão comercial posterior.
- Registrar frete como componente do atendimento do pedido, separado do preço dos produtos. Frete gratuito pode ser representado como valor cobrado igual a zero, sem apagar a modalidade ou o custo logístico interno.

## Clientes

### Decisões do projeto

- O público inclui pessoas físicas e jurídicas.
- O sistema precisa manter informações cadastrais, contatos e endereços relevantes à operação.

### Propostas

- Compartilhar uma identidade cadastral comum entre PF e PJ e manter os atributos específicos de cada tipo em extensões conceituais próprias.
- Cada cliente pode ter vários contatos e endereços, que podem ser usados para cobrança, entrega ou comunicação. O pedido deve preservar conceitualmente o endereço e os dados de destinatário usados na operação, para manter o histórico mesmo se o cadastro mudar.
- A situação cadastral do cliente não altera retroativamente pedidos concluídos; impedir novas operações para cadastro inativo ou restrito é uma regra operacional a definir antes da implementação.
- Os dados exigidos para identificar PF/PJ, emitir documentos e atender obrigações legais serão definidos conforme a jurisdição, ainda não escolhida.

## Produtos, catálogo, preço e custo

### Decisões do projeto

- O catálogo inclui produtos, categorias e subcategorias, marcas e referências relevantes.
- Produtos podem ser descontinuados e sua história comercial precisa ser preservada.
- Um produto pode ser obtido de mais de um fornecedor.
- O sistema deve comportar alterações de preço e histórico ao longo do tempo.

### Propostas

- Descontinuar um produto impede sua oferta em novos pedidos a partir da data definida, mas preserva catálogo, compras e vendas históricas. Produtos descontinuados podem permanecer vendáveis enquanto houver política explícita de liquidação.
- Um produto pode pertencer a uma categoria terminal da hierarquia e possuir uma marca; especificações variam conforme a categoria, sem impor um catálogo técnico universal nesta fase.
- Associar fornecedores a produtos com referências de compra e, se necessário, indicar um fornecedor preferencial. A preferência é operacional e não impede compras de outro fornecedor.
- Manter períodos de vigência para os preços comerciais; alterações futuras não modificam o preço registrado nos pedidos existentes.
- Registrar custo por aquisição nos itens de compra e manter uma referência do custo considerado no momento da venda. Para margem e valorização do estoque, recomendar método de custo médio móvel como ponto inicial pela simplicidade em um varejista com múltiplas entradas. A escolha do método, tratamento de frete de compra, impostos e custos acessórios exige revisão antes da modelagem.
- Preços e custos pertencem a contextos temporais distintos: preço é condição de venda; custo nasce de aquisições e da política de valorização definida. Não presumir que o último preço de compra seja automaticamente o custo de todo o estoque.

## Fornecedores e compras

### Decisões do projeto

- A empresa possui fornecedores, emite compras e recebe produtos.
- Uma compra pode incluir vários itens e a entrada de mercadoria precisa refletir o recebimento.

### Propostas

- Uma ordem de compra pode ter vários itens e evoluir por preparação, aprovação, envio, recebimento parcial ou completo, fechamento e cancelamento.
- Registrar cada recebimento relacionado à compra e aos itens correspondentes; apenas as quantidades efetivamente aceitas geram entrada física em estoque. Diferenças ou rejeições são resolvidas por registro operacional e não por criação intencional de dados inconsistentes.
- Permitir vários recebimentos para uma compra. Cancelar saldo não recebido não desfaz as entradas já aceitas; correções posteriores devem gerar movimento de ajuste rastreável.
- Fornecedor pode estar ativo ou inativo. A inativação impede novas compras conforme a política definida, sem eliminar o histórico.
- Condições de pagamento, moedas, impostos e processo de aprovação da compra permanecem fora das decisões desta fase.

## Estoque

### Decisões do projeto

- O estoque é controlado por local e precisa refletir entradas, saídas, reservas, transferências e ajustes.
- Compras recebidas, vendas atendidas, devoluções aceitas e operações internas podem afetar o estoque.

### Propostas

- Uma loja pode ter vários locais de estoque; podem existir locais associados ao atendimento digital. O saldo é conceitualmente acompanhado por produto e local.
- Manter um histórico de movimentos como trilha de auditoria. O saldo operacional pode ser mantido para consulta rápida, mas deve ser conciliável com os movimentos; a abordagem física será decidida na modelagem.
- A reserva reduz a disponibilidade para novos pedidos, mas não é saída física. A saída ocorre quando o item é entregue ao cliente, despachado ou baixado conforme o processo de atendimento.
- Reservar itens quando o pedido for confirmado e liberá-los em cancelamento ou expiração antes do atendimento. O prazo e os eventos exatos dependem da política de pagamento e separação.
- Transferências entre locais produzem saída de origem e entrada de destino vinculadas à mesma operação; uma transferência em trânsito poderá exigir uma etapa intermediária se essa necessidade for confirmada.
- Ajustes exigem motivo e responsável e não devem ser usados para esconder divergências. Não gerar divergências artificiais nos dados de estudo.
- Cancelamento antes da saída física libera reserva, sem criar entrada de devolução. Se já houve saída, tratar o retorno pelo processo de devolução.

## Pagamentos

### Decisões do projeto

- Existem diferentes formas de pagamento.
- Um pedido pode ser pago por uma ou mais operações de pagamento, com parcelamento quando aplicável.
- O status do pagamento é independente do status do pedido.

### Propostas

- Permitir múltiplas operações de pagamento por pedido para suportar divisão entre meios, tentativas e ajustes sem confundir isso com a quantidade de itens.
- Separar conceitualmente autorização, captura, falha, cancelamento e estorno/reembolso. Uma tentativa recusada não é valor recebido.
- Quando houver parcelamento, preservar o plano e a situação de cada parcela. A venda pode estar confirmada sem que todas as parcelas futuras tenham sido liquidadas.
- Concluir financeiramente um pedido segundo uma política de liquidação ainda a aprovar; não inferir situação de pagamento exclusivamente pela situação comercial do pedido.
- Reembolsar pelo meio original sempre que possível. A regra para crédito, troca, estorno parcial e prazo depende do meio e da política comercial.

## Logística e atendimento

### Decisões do projeto

- Um pedido pode ser entregue ou retirado em loja.
- A operação pode utilizar transportadora quando houver entrega.

### Propostas

- Representar o atendimento do pedido independentemente do pedido comercial, permitindo preparar, despachar, entregar, disponibilizar para retirada e registrar a conclusão.
- Associar transportadora e referência de rastreamento quando aplicável; não exigir transportadora para retirada em loja.
- Um pedido pode exigir mais de uma remessa se a separação ocorrer em locais distintos. Para reduzir o escopo inicial, a recomendação é permitir uma ou mais unidades de atendimento/remessa por pedido, mas validar se entregas parciais são necessárias para a primeira implementação.
- Registrar eventos relevantes de logística e retirada, sem exigir integração automática com transportadoras nesta fase.
- A conclusão logística não altera automaticamente a liquidação de pagamentos nem elimina o direito de solicitar devolução.

## Devoluções e impactos

### Decisões do projeto

- Uma devolução pode ser total ou parcial, deve ter motivo e referenciar itens vendidos.
- Uma devolução aprovada que retorna produto vendável pode gerar entrada em estoque.
- Devoluções podem ter consequência financeira.

### Propostas

- Registrar uma solicitação de devolução por pedido, com um ou mais itens, quantidades, motivo, análise e decisão. A quantidade aceita cumulativamente não pode superar a quantidade vendida, descontadas devoluções anteriores.
- Separar solicitação, aprovação/recusa, recebimento físico e reembolso. Aprovação não significa automaticamente que o item retornou ao estoque ou que o dinheiro foi devolvido.
- Após inspeção, destinar o item a estoque vendável, quarentena/avaliação ou descarte, conforme condição e política. Só o destino vendável gera entrada no saldo disponível; os outros destinos continuam rastreados.
- Relacionar o reembolso à devolução e à operação de pagamento original sempre que possível. Trocas podem ser tratadas como uma devolução mais um novo pedido na primeira versão, evitando um ciclo de troca especial.
- Cancelar pedido antes do atendimento é diferente de devolver item após entrega ou retirada; os dois processos devem manter estados e impactos distintos.

## Funcionários e vendedores

### Decisões do projeto

- A operação possui funcionários e vendedores.
- Lojas, funções e participação em vendas são contextos relevantes.
- Mudanças de vínculo e de loja ao longo do tempo devem poder ser representadas.

### Propostas

- Manter função básica e períodos de atuação/lotação, para que vendas antigas permaneçam atribuídas ao contexto vigente na ocasião.
- Não tratar todo funcionário como vendedor; a participação comercial é uma atribuição que pode ser associada a pedidos presenciais ou a atendimento identificado.
- Encerramento de vínculo impede novas atribuições após a data efetiva, sem remover registros históricos.
- Regras de comissão, metas, escalas, folha de pagamento e gestão de desempenho estão fora do escopo atual.

## Regras temporais transversais

### Decisões do projeto

- O domínio deve comportar histórico aproximadamente de 2023 a 2026 e eventos ao longo do tempo, incluindo abertura de lojas, cadastro de clientes/produtos, mudanças de preço, funcionários, compras, pedidos, movimentações e devoluções.
- Os dados sintéticos futuros devem ser consolidados e coerentes; não se deve inserir sujeira intencional para criar exercícios de limpeza.

### Propostas

- Diferenciar o momento em que um fato ocorreu do momento em que foi registrado, quando essa distinção for importante para auditoria ou operação.
- Informações mutáveis que expliquem o contexto histórico — como preço, situação, lotação, referência comercial e endereço usado — devem preservar a versão aplicável ao evento, por cópia contextual ou histórico de vigência a decidir na modelagem.
- Usar períodos de validade sem sobreposição para condições que não podem estar simultaneamente vigentes, como preço ativo no mesmo contexto. A forma de assegurar isso será física e ficará para a Fase 2.
- Não assumir que todas as entidades existiam desde 2023 ou cobrem todo o período; lojas, pessoas, produtos e canais entram na operação em momentos diferentes.
