# Plano de geração de dados sintéticos — Fase 3A

## Estado e objetivo

Este documento especifica a geração futura para a empresa fictícia brasileira de informática e eletrônicos. É planejamento: não há código de gerador, seed executada, carga, dado sintético persistido ou alteração do schema nesta fase. Os dados devem ser plausíveis, relacionais, reproduzíveis e temporalmente coerentes, sem erros fabricados para testar limpeza.

O schema operacional aplicado e validado tem 9 schemas e 40 tabelas. A revisão de adequação conclui **SCHEMA CHANGES RECOMMENDED**: falta geografia estruturada em `core.stores`, recomendação a decidir antes de iniciar a Fase 3B. Não foi encontrado blocker para gerar os demais domínios.

## Período, relógio e moeda

- Janela comercial inclusiva: **2023-01-01 a 2026-09-30**. Nenhum evento comercial depois do cutoff; não há Black Friday 2026.
- Bootstrap de estoque permitido: **2022-11-01 a 2022-12-31**, somente compras, recebimentos, formação de saldo e custo inicial; sem vendas relevantes.
- Usar `America/Sao_Paulo` como calendário e relógio de negócio. Construir instantes como datetimes com fuso explícito e armazená-los em `TIMESTAMPTZ`; converter entradas locais para instante UTC sem retirar informação de fuso antes do cálculo. Para agregações diárias, usar a data local de São Paulo.
- Datas civis como admissão, abertura e nascimento usam `DATE`. Alimentar todos os timestamps explicitamente, sem depender de `now()` nem do relógio da máquina.
- Valores de venda e compra em BRL. Usar `Decimal` nas operações monetárias e quantização explícita para centavos; custo unitário respeita oito casas decimais.

## Escala e perfis

Os perfis são configurações conceituais, não implementados nesta fase. Faixas completas, derivação e as 40 tabelas estão em [entity-volumes.md](entity-volumes.md).

| Perfil | Intenção | Escala principal |
|---|---|---|
| `smoke` | Verificar rapidamente regras, persistência e integridade em database descartável/aprovada. | 2 lojas, 30 produtos, 20 clientes identificados, cerca de 300 pedidos e 600–700 itens. |
| `portfolio` | Base principal explorável em Power BI, adequada a computador de desenvolvimento comum. | 10 lojas, 12–15 locais, 80–100 funcionários, ~1.000 SKUs, 40–50 fornecedores, 40–50 mil clientes e cerca de 120 mil pedidos / 240–280 mil itens. |
| `large` | Dobrar aproximadamente o volume transacional para observar tempo e memória, sem inventar escala extrema. | Catálogo e organização semelhantes ao portfolio; cerca de 240 mil pedidos / 500–560 mil itens e ~80–100 mil clientes. |

O portfolio deve ficar na ordem de **2,0–2,8 milhões de linhas** somando dados mestres, cabeçalhos, itens e eventos. A maior contribuição vem de vendas/atendimento, histórico de estoque, pagamentos, compras e históricos operacionais. A contagem é estimativa, pois tabelas de evento derivam das operações e suas cardinalidades.

## Configuração e reprodutibilidade

- Um `root_seed` inteiro versionado na configuração seleciona o conjunto. Mesma versão do gerador, configuração e seed produzem as mesmas entidades, IDs lógicos, valores e instantes.
- Derivar sub-seeds estáveis por domínio (`catalog`, `customers`, `employees`, `sales`, `procurement`, `inventory`, `payments`, `logistics`, `returns`) usando função de hash documentada sobre `(root_seed, domínio, versão)`. Não usar `hash()` nativo de Python, cuja estabilidade entre processos não é garantida.
- Cada domínio usa seu próprio RNG para evitar que pequenas alterações de consumo aleatório em vendas mudem catálogo e clientes. Para independência ainda maior, quando necessário derivar RNG por entidade/chave de negócio estável.
- Cutoff, datas inicial/final, profile e configuração entram como parâmetros explícitos. Nenhuma decisão depende da data de execução, ordem incidental de diretório ou estado global de RNG.
- IDs técnicos identity são gerados pelo PostgreSQL; referências lógicas como SKU/pedido usam códigos determinísticos. O gerador mantém mapeamento entre chave lógica e ID retornado durante a carga.

## Arquitetura futura do gerador

Recomendação: pacote Python pequeno sob `data-generator/src/`, separado em configuração, seeds/distribuições, geração por domínio, repositórios de carga e validações. A engine transacional processa eventos cronologicamente em lotes e conserva somente catálogos, estados de estoque/custo e buffers limitados em memória.

Etapas conceituais:

1. Validar profile/configuração, versão do schema e database alvo antes de qualquer escrita.
2. Gerar e carregar master data determinístico.
3. Criar catálogo/preços e calendário de vigências.
4. Inicializar disponibilidade exclusivamente com compras e recebimentos do bootstrap.
5. Percorrer dias/eventos comerciais em ordem, formando pedidos, descontos, reservas, pagamentos, fulfillments e eventos associados.
6. Gerar reposições e transferências orientadas por necessidade e disponibilidade correntes.
7. Gerar devoluções após atendimento, custos de retorno, estoque e eventuais reembolsos.
8. Rodar validações de integridade, conciliação, bandas de distribuição e baselines SQL.

Não é necessário inventar sequência de INSERTs independente: a ordem exata respeitando as FKs está em [dependency-order.md](dependency-order.md). Eventos com estado são processados por tempo de ocorrência, ainda que seus registros relacionais sejam gravados em lotes.

## Princípios comerciais e correlações

- Empresa fictícia sem nome definitivo. Dez lojas com datas de abertura, escala, mix, ticket, equipe e perfil de estoque distintos; diferenças graduais, nenhuma unidade domina o resultado.
- Quatro canais iniciais: físico, e-commerce próprio e dois marketplaces genéricos. Participação digital cresce ao longo dos anos; marketplaces seguem identificados como canal.
- 88–92% dos clientes identificados PF e 8–12% PJ. PJ é minoria em quantidade, mas contribui parcela maior da receita, com compras em dias úteis, mais unidades e ticket superior sem assumir que toda PJ é grande.
- 25–35% dos pedidos físicos podem ser anônimos (`customer_id = NULL`); pedidos digitais sempre identificados. Nunca cadastrar “cliente genérico”.
- Recorrência explícita, baseada em coortes e intensidade por perfil; não sortear um cliente novo por pedido.
- Categoria, faixa de preço/custo e tipo de produto condicionam a cesta. SKUs seguem long-tail e idade comercial limita a primeira venda.
- Preço comercial é o vigente no instante da venda. Custo realizado vem apenas dos movimentos `fulfillment` e da média móvel por SKU/local; não inventar `unit_cost_snapshot` na venda.
- Demanda sazonal não uniforme: Black Friday de 2023–2025, dezembro elevado, janeiro pós-pico mais fraco, variações por categoria e evolução anual. Mais detalhe e bandas em [business-distributions.md](business-distributions.md).

## Catálogo, especificações e unidade

Planejar 35–50 categorias/subcategorias, 50–80 marcas e aproximadamente 1.000 SKUs. Cada SKU tem ciclo de vida, categoria coerente, marca quando aplicável, nome comercial sintético, fornecedores plausíveis, preços e custos temporalmente coerentes. Categorias incluem computadores, componentes, monitores, periféricos, redes, impressoras e acessórios.

Faixas de preço abaixo são faixas nominais de geração para o horizonte do projeto, não cotações atuais nem cópia de catálogo real. Configuração premium e variação temporal ficam dentro de cada família; custo é gerado por fornecedor/recebimento e política de estoque, não por aplicar um percentual fixo universal ao preço.

| Família de SKU | Faixa sintética inicial por unidade (BRL) |
|---|---:|
| Notebook | R$ 2.000–18.000 |
| Desktop | R$ 1.800–16.000 |
| Monitor | R$ 500–5.000 |
| CPU | R$ 350–7.000 |
| GPU | R$ 900–15.000 |
| Placa-mãe | R$ 400–5.000 |
| Memória RAM | R$ 100–1.800 |
| SSD/HDD e armazenamento | R$ 120–3.500 |
| Periféricos (mouse, teclado, headset, webcam) | R$ 35–2.500 |
| Redes (roteador, switch, adaptador) | R$ 60–4.000 |
| Impressoras | R$ 600–6.000 |
| Acessórios | R$ 20–1.500 |

`specifications`, quando presente, será objeto JSON com chaves `snake_case` e templates semânticos. Exemplos de template (subconjuntos apropriados podem ser usados; valores são fictícios e coerentes):

| Família | Chaves de `specifications` sugeridas |
|---|---|
| Notebook | `cpu_model` (string), `ram_gb` (integer), `storage_gb` (integer), `screen_inches` (number), `gpu_model` (string ou null), `operating_system` (string). |
| Desktop | `cpu_model`, `ram_gb`, `storage_gb`, `gpu_model`, `motherboard_chipset`, `power_supply_w`. |
| Monitor | `screen_inches`, `resolution`, `refresh_rate_hz`, `panel_type`, `adaptive_sync` (boolean). |
| CPU | `socket`, `cores`, `threads`, `base_clock_ghz`, `boost_clock_ghz`, `tdp_w`. |
| GPU | `chipset`, `vram_gb`, `memory_type`, `interface`, `recommended_psu_w`. |
| Placa-mãe | `socket`, `chipset`, `form_factor`, `memory_type`, `memory_slots`, `max_memory_gb`. |
| Memória RAM | `capacity_gb`, `memory_type`, `module_count`, `speed_mts`, `form_factor`. |
| SSD/HDD | `capacity_gb`, `interface`, `form_factor`, `read_mbps` e, para SSD, `write_mbps`. |
| Mouse/teclado | `connection_type`, `dpi` (mouse), `buttons` (mouse), `layout` (teclado), `backlit` (boolean). |
| Headset/webcam | `connection_type`, `microphone` (boolean), `resolution_mp` (webcam), `frequency_response_hz` (headset). |
| Rede | `device_type`, `connection_type`, `wifi_standard` (quando wireless), `ethernet_ports`, `max_speed_mbps`. |
| Impressora | `print_technology`, `color` (boolean), `duplex` (boolean), `connectivity`, `ppm`. |
| Acessórios | `accessory_type`, `compatible_interface` ou `compatible_device_family`, `length_cm` quando aplicável. |

Chaves usam `snake_case`; números são JSON number, booleanos JSON boolean e especificação desconhecida fica ausente/nula, não string aleatória. A engine valida combinações cruzadas (por exemplo socket CPU/placa-mãe, capacidade e módulos de memória, potência recomendada de GPU) e unidades consistentes. O objeto pode ser nulo quando não houver especificação útil. Não converter em EAV.

Vocabulário controlado de `unit_of_measure`: somente **`unit`** na primeira geração. Kits e packs, se futuramente necessários, serão SKUs comercializáveis cujo saldo ainda é contado em unidades; não usar `kit`/`pack` até regra de composição e estoque ser aprovada. A coluna continua sem CHECK no banco.

## Identidades sintéticas e privacidade

CPFs/CNPJs, quando incluídos, serão criados pelo algoritmo de checksum a partir de números aleatórios determinísticos, formatados apenas com dígitos, únicos no conjunto e sem correspondência intencional a pessoa/empresa real. Não importar cadastro público, dados de clientes ou bases de pessoas reais. E-mails usam domínios reservados como `example.com`; não enviar comunicação. Nomes/endereço são sintetizados ou escolhidos de vocabulário controlado local; nenhuma saída deve parecer fonte real conhecida. Identificadores fiscais de fornecedores/transportadoras devem seguir mesma cautela e não simular empresas reais de modo identificável.

Contatos de clientes podem usar e-mail em `example.com`; telefones de contato não são necessários para esta análise e podem ficar ausentes. Telefones opcionais de loja/fornecedor/carrier também podem ficar nulos. Se identificador fiscal de fornecedor for preenchido, usar CNPJ sintético com checksum e unicidade; não copiar CNPJ público. Nenhum dado será usado para contato real.

## Estoque, compras e execução cronológica

O saldo inicial nasce de purchase orders, itens, goods receipts, itens aceitos e movimentos `receipt` no intervalo de bootstrap. `adjustment_in` não é mecanismo normal para fabricar estoque.

Processar recebimentos, reserva/liberação, atendimento, transferências e devoluções respeitando ordem temporal e estado atual. Proteger saldo e custo por produto/local; nunca permitir `on_hand < 0` ou `reserved > on_hand`. Entrada elegível recalcula custo médio ponderado com `Decimal`; saída `fulfillment` aplica a média vigente e grava `unit_cost`; transferência leva custo da origem; retorno vendável usa a média ponderada histórica dos movimentos `fulfillment` da origem e então recalcula a posição no destino. Compra popular deriva de cobertura/demanda, fornecedor preferencial ativo e lead time; pedidos recebidos nunca excedem quantidades compradas.

Restrições, agrupamentos e invariantes são mantidos ativos. Carga transacional não desabilita FK/CHECK/UNIQUE nem falsifica posições diretamente para acertar a conciliação. Processar cada fato de estado numa transação atômica, com ordenação determinística de locks entre locais em transferência.

## Estratégia de escrita, segurança e reset futuro

Master data pode ser gravado em lotes/COPY após validação de chaves e dependências. Transações com custo/saldo ficam em lotes cronológicos pequenos e transacionais; eventos relacionados são atômicos. Não carregar todo o portfolio em memória. Credenciais somente em `.env`, nunca na configuração versionada, argumento CLI, logs ou documentação.

Futuro reset deve ser comando explícito, separado da geração normal, com validação de `current_database() = 'projeto_bi'`, confirmação inequívoca, limpeza por ordem inversa de FK e opção explícita de reiniciar identities. Nunca executar `DROP DATABASE`, nunca atingir outra database, nunca resetar automaticamente por conveniência. Esta fase não implementa nem chama reset.

Recomendação para parâmetros não sensíveis: **TOML**, por ser legível, suportado pela biblioteca padrão do Python e adequado para perfis, datas, seed, volumes e pesos. `.env` permanece exclusivamente para conexão/segredos. Registrar `schema_version` e versão de configuração no TOML.

## Tecnologia recomendada

- Python 3 padrão para domínio, `datetime`/`zoneinfo`, `decimal.Decimal`, `random.Random` e geração em batches.
- `psycopg` 3 para acesso PostgreSQL e COPY/batches controlados; escolher instalação binária em ambiente isolado quando a fase de implementação chegar.
- `Faker` com locale `pt_BR` apenas para nomes/endereços plausíveis, com seed por domínio; não é fonte de documentação ou identidade real. Endereços não devem ser apresentados como geografia comercial exata até revisão de geografia de lojas.
- **Não exigir Pandas nem NumPy** para a engine. A geração é relacional/event-driven e pode usar estruturas padrão; análises e validações ficam em SQL. Avaliar NumPy somente se benchmark demonstrar gargalo real em amostragens vetorizadas; não carregar tabelas transacionais em DataFrame.
- Não instalar dependências nesta fase.

## Validações e baselines planejados

As verificações executáveis ficam para fases de implementação/carga, definidas em [data-quality-and-validation.md](data-quality-and-validation.md). Baselines SQL pós-carga devem cobrir: pedidos, unidades, receita bruta/desconto/líquida, custo realizado, lucro/margem bruta, ticket, clientes identificados/recorrentes, devoluções/reembolsos e vendas por canal, categoria, loja, mês e ano. Power BI será comparado com as mesmas definições; não há DAX nesta fase.

## Fases sugeridas e gate humano

- **3B — fundação e master data:** configuração, sub-seeds, dimensões operacionais, catálogos, clientes, pessoas e preços, após revisão humana e decisão sobre geografia de loja.
- **3C — engine operacional de compras, vendas e estoque:** bootstrap, compras/recebimentos, reposições, pedidos, descontos, reservas, saídas e custo móvel.
- **3D — pagamentos, fulfillment, logística, devoluções e reembolsos:** eventos relacionados e conciliações por operação.
- **3E — carga portfolio, qualidade e baselines:** volume principal, validação integral e resultados SQL de referência.

Este documento encerra o planejamento da Fase 3A. A implementação não deve começar até revisão humana do plano e decisão sobre a recomendação marcada em [schema-gap-review.md](schema-gap-review.md).
