# Escopo do negócio

## Propósito e status das definições

Este documento descreve o negócio fictício que servirá de contexto para o ProjetoBI. É uma especificação conceitual para revisão antes da modelagem relacional; não define a estrutura física do PostgreSQL.

### Decisões do projeto

- A empresa fictícia atua no varejo de tecnologia e informática, em porte pequeno ou médio.
- A operação principal ocorre no Brasil, com moeda operacional Real brasileiro (BRL).
- Os endereços e cadastros de PF/PJ seguem conceitualmente o contexto brasileiro, incluindo referências como CPF, CNPJ, CEP, UF e municípios quando pertinentes.
- A operação combina lojas físicas, e-commerce próprio e vendas por marketplace.
- O público inclui pessoas físicas e pessoas jurídicas.
- A operação abrange catálogo, relacionamento com fornecedores, compras, estoque, vendas, pagamentos, atendimento logístico e devoluções.
- O sistema operacional deverá atender às rotinas da empresa, inclusive informações administrativas que talvez não sejam usadas em relatórios.
- O horizonte pretendido para os dados históricos é aproximadamente de 2023 a 2026; nenhuma amostra de dados será gerada nesta fase.
- O nome comercial permanece indefinido. A referência neutra é “empresa fictícia de varejo de informática”.

### Hipóteses e propostas revisáveis

- Tratar o e-commerce próprio e cada marketplace como canais distintos, para preservar origem do pedido, referência externa e responsabilidades de atendimento.
- Permitir que uma loja tenha mais de um local operacional de estoque e que um local central abasteça mais de uma loja. Isso dá flexibilidade sem exigir uma rede logística complexa.
- Manter uma base cadastral comum para clientes PF e PJ, com informações específicas de cada tipo em extensões conceituais próprias. A proposta evita duplicar contatos e endereços.
- Não fixar cidade, quantidade de lojas, marcas comerciais, metas ou volume de pedidos antes de uma decisão explícita.

## Descrição da empresa e operação

A empresa compra produtos de informática de fornecedores, recebe e armazena mercadorias em locais associados às lojas ou à operação digital, e vende produtos a clientes PF e PJ. As vendas podem ocorrer presencialmente, no canal digital próprio ou em marketplaces. Os pedidos podem ser atendidos por entrega ou retirada em loja, conforme a modalidade oferecida no canal e a disponibilidade operacional.

A operação acompanha o ciclo do pedido, o atendimento por funcionários quando aplicável, os pagamentos, a preparação e entrega, eventuais devoluções e os efeitos correspondentes em estoque e financeiro. Compras podem ser recebidas em etapas, e o estoque precisa refletir entradas, saídas, reservas e transferências de forma rastreável.

O sistema manterá dados operacionais e administrativos coerentes, como referências internas e externas, situação cadastral e operacional, observações, histórico de alterações relevantes e datas administrativas. O uso analítico de cada informação será decidido mais tarde; este escopo não prescreve tabelas para o Power BI.

## Canais de venda

- **Loja física:** atendimento presencial, com possível associação a vendedor e à loja/local que atende a venda.
- **E-commerce próprio:** pedido originado nos meios digitais da empresa e associado a um cliente identificado.
- **Marketplace:** pedido originado em uma plataforma de terceiros e associado ao cliente identificado no contexto disponível para a operação, com referência externa e responsabilidades que podem variar por acordo comercial.

Em venda presencial, o cliente pode ser identificado ou permanecer como consumidor não identificado. Não se cria um cadastro genérico artificial para representar a venda anônima. A identificação é obrigatória nos dois canais digitais. A representação física dessa diferença será decidida na modelagem relacional.

Os nomes das plataformas, contratos, comissões e regras específicas de integração permanecem em aberto. No conceito, o canal identifica a origem comercial; o meio de atendimento identifica como o pedido chega ao cliente.

## Público e relacionamento com clientes

O cadastro atende pessoas físicas e pessoas jurídicas no contexto brasileiro. Conceitualmente, pode incluir CPF para PF, CNPJ para PJ, CEP, UF e município, além de nomes de referência, contatos, endereços e situação de relacionamento. Esta definição não determina nomes, tipos, tamanhos ou validações físicas, nem estabelece requisitos legais completos.

## Portfólio

O catálogo pode abranger notebooks, desktops, monitores, componentes (como processadores, placas de vídeo, placas-mãe, memórias e armazenamento), periféricos, redes, impressoras e acessórios. Categorias e subcategorias organizam o catálogo; marcas identificam fabricantes ou marcas comerciais. Esta lista é ilustrativa, não uma definição de categorias físicas nem uma seleção para o modelo analítico.

Produto representa o item ou SKU efetivamente comercializável. Configurações comerciais distintas de um equipamento podem ser produtos/SKUs próprios; não há uma camada obrigatória separada de variantes na primeira versão do domínio. Produtos podem ter códigos internos e referências de fabricante ou fornecedor, descrição, especificações operacionais, situação comercial e histórico de preços. As especificações podem variar por categoria; sua representação será decidida na modelagem. A disponibilidade de cada item depende do local de estoque e do estado operacional do produto.

## Estrutura organizacional relevante

- **Lojas:** pontos de atendimento físico que podem possuir áreas de armazenamento e retirada.
- **Funcionários:** pessoas que participam de atividades operacionais ou administrativas.
- **Funções:** classificação das responsabilidades básicas, como venda ou operação de estoque, sem estabelecer uma hierarquia corporativa completa.
- **Vínculos e lotações:** registro conceitual da loja ou área em que um funcionário atua ao longo do tempo, permitindo representar mudanças e períodos de atuação.
- **Locais de estoque:** depósitos ou áreas que controlam mercadorias, vinculados a uma loja ou à operação digital.

## Áreas funcionais

1. **Comercial:** origem do pedido, atendimento, itens, descontos, ciclo de situação e histórico do pedido.
2. **Clientes:** cadastro de PF/PJ, contatos, endereços e relacionamento.
3. **Catálogo:** produtos, marcas, hierarquia de categorias, fornecedores associados e preços ao longo do tempo.
4. **Suprimentos:** fornecedores, pedidos de compra e recebimentos, inclusive parciais.
5. **Estoque:** locais, posição operacional, movimentações, reservas, transferências e ajustes controlados.
6. **Pagamentos:** meios, tentativas ou transações, parcelas e estornos/reembolsos, com ciclo independente do pedido.
7. **Logística:** modalidade de atendimento, preparação, transportadora quando aplicável, rastreamento e retirada.
8. **Devoluções:** solicitação e avaliação por item, destino físico do produto e consequência financeira.
9. **Organização:** lojas, funcionários, funções e histórico de atuação.

## Escopo incluído

- Venda de produtos de informática por canais físico e digitais.
- Clientes PF e PJ e seus dados cadastrais e de contato.
- Catálogo organizado por categoria/subcategoria e marca.
- Relação entre produtos e múltiplos fornecedores.
- Compras com possibilidade de múltiplos recebimentos por pedido; entrada de mercadoria conforme quantidades efetivamente aceitas em cada recebimento.
- Estoque por local, movimentações, reservas e ajustes controlados.
- Pedidos com múltiplos itens, pagamentos e modalidades de atendimento.
- Uma ou mais unidades de atendimento/remessas por pedido, permitindo atendimento parcial, origens diferentes e retirada/entrega em etapas quando necessário.
- Cancelamentos e devoluções totais ou parciais, com impacto operacional e financeiro registrado.
- Funcionários, funções e participação em vendas presenciais ou em atribuições digitais.
- Histórico operacional aproximadamente entre 2023 e 2026, com abertura de lojas, entrada de produtos e clientes, alterações comerciais, pedidos, compras e devoluções ao longo do tempo.

## Fora do escopo atual

- Modelagem relacional/física, SQL, migrations, views, constraints, índices ou escolha de tipos de dados.
- Criação ou alteração de objetos ou dados no PostgreSQL.
- Geração de dados sintéticos ou implementação do gerador Python.
- Modelo estrela, seleção de tabelas para o Power BI, Power Query, DAX ou relatórios.
- ERP completo, contabilidade geral, folha de pagamento, CRM avançado, fabricação, serviços de reparo, gestão de contratos, franquias, comércio internacional ou gestão de múltiplas empresas.
- Cálculo tributário, legislação fiscal detalhada, NF-e, NFC-e, ICMS, PIS/COFINS, SPED, escrituração, contabilidade, regras fiscais estaduais e obrigações legais completas.
- Definição de nome, localização, número de lojas, metas, marcas, fornecedores ou marketplaces reais.
