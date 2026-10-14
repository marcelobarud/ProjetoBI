# Fase 5.4.2 — Identidade InfoTech e refinamento visual

**Classificação:** `PARTIAL — BRANDING OR VISUAL VALIDATION PENDING`

**Design System vigente:** InfoTech Intelligence v0.2; itens desta fase são candidatos à v0.3.

**Commit local:** registrado no fechamento desta fase.

## Escopo e direção escolhida

O usuário indicou preferência pelo estilo de monograma. A direção A — monograma geométrico I/T — foi usada como piloto. A escolha é uma preferência para esta proposta, não aprovação estética definitiva. Foram consideradas três direções: (A) monograma tecnológico I/T; (B) nós conectados abstratos para inteligência de dados; (C) wordmark com detalhe geométrico discreto. Os vetores locais incluem A e suas variações; B e C ficaram como conceitos, sem aplicação.

Arquivos-fonte: `powerbi/branding/infotech/infotech-monogram.svg` (aplicado), `infotech-monogram-mono.svg` (monocromático) e `infotech-horizontal.svg` (proposta não aplicada). A marca usa azul `#2563EB`, verde-petróleo `#0F9D92`, fundo transparente e viewBox escalável, sem fontes externas. A variante horizontal permanece separada do cabeçalho para evitar duplicar o wordmark que já existe como texto.

## Aplicação PBIP

O símbolo foi incorporado como recurso SVG registrado no PBIP e aplicado por um visual de imagem nativo em cada cabeçalho:

| Página | Visual do monograma | Posição e tamanho |
|---|---|---|
| Visão Executiva | `c4addb2ba10132803698` | x=36, y=36, 48 × 48 px |
| Análise Comercial | `c4addb2ba10132803697` | x=36, y=36, 48 × 48 px |
| Produtos e Categorias | `c4addb2ba10132803696` | x=36, y=36, 48 × 48 px |
| Custos e Margens | `c4addb2ba10132803699` | x=36, y=36, 48 × 48 px |

O textbox de cada cabeçalho fica em x=96, y=22, 520 × 76 px; mantém “InfoTech Intelligence” em 30 pt e o título da página em 12 pt. O Page Navigator continua a partir de x=636; a composição não altera nomes ou destinos.

A inspeção visual após reabrir o PBIP, registrada durante a execução, observou a marca nas quatro páginas. O PBIP usa o mesmo item do RegisteredResources em cada visual. Não foi possível obter nesta sessão uma janela ativa do Power BI Desktop para gerar capturas exportáveis e repetir os testes finais. Assim, o arquivo de evidências inclui os ativos e uma auditoria estrutural, mas não simula nem substitui capturas de tela. A validação visual integrada, a comparação antes/depois e a reabertura final permanecem pendentes.

## Elementos preservados

- O botão Filtros conserva texto, ação de bookmark, fundo `#1D4ED8`, texto branco e fonte Semibold 16 pt. Nenhum ícone foi acrescentado porque não foi estabelecido nesta etapa um suporte nativo seguro que preservasse a área clicável e o comportamento do bookmark.
- Fechar filtros conserva texto, bookmark, fundo `#DBEAFE`, texto `#142238` e fonte Semibold 16 pt.
- Cartões principais e secundários não receberam novos elementos nem alteração de valor, medida ou formato. O padrão existente de valor 32 pt e título 13 pt foi mantido; a reconfirmação visual dos títulos secundários fica pendente.
- O Page Navigator nativo, seus quatro destinos e os gráficos foram mantidos sem alterações nesta fase.
- DAX, calendário, relacionamentos, Power Query, PostgreSQL e dados não foram modificados por esta fase. Diferenças locais preexistentes, inclusive em `report.json`, `pt-BR.tmdl` e visuais, foram preservadas fora do commit.

## Verificações e alcance

| Verificação | Resultado | Evidência / limite |
|---|---|---|
| JSONs de definição do relatório | PASS | 99 arquivos analisados; 0 inválidos |
| Páginas e aplicação da marca | PASS estrutural | Quatro páginas, um visual `image` por página, 48 × 48 px, alt text e referência ao recurso registrado |
| SVG-fonte aplicado | PASS estrutural | Recurso registrado e arquivo-fonte disponível no projeto |
| Modelo semântico | PASS estrutural | 10 tabelas, 55 medidas e 21 relacionamentos verificados localmente |
| Renderização após abertura anterior | Observada | A inspeção da sessão anterior visualizou a marca nas quatro páginas; sem capturas persistidas |
| Power BI Desktop disponível nesta sessão | PENDENTE | Nenhuma janela ativa foi exposta pelo controle de computador nesta sessão |
| Abrir/fechar bookmarks, sincronização e filtros locais | PENDENTE nesta fase | Os controles não foram alterados; esta fase não repetiu o conjunto completo de interações |
| Cartões, navegação e leitura em Full HD/Fit to Page | PENDENTE nesta fase | Sem captura para comparação e sem nova inspeção visual controlada |
| Acessibilidade nova | Não verificada | Contraste, foco, teclado completo, escala de cinza e leitor de tela não foram reavaliados; não declarar WCAG |

O resultado é `PARTIAL`, pois faltam capturas comparativas e repetição final no Desktop. A auditoria estrutural não atesta a integridade de renderização nem substitui os testes de interação.

## Biblioteca candidata e regras de uso

- Variante aplicada: símbolo isolado `infotech-monogram.svg`; preservar proporção 1:1, fundo transparente e cores da paleta clara.
- Referência do visual no cabeçalho: quadro de 48 × 48 px. Área recomendada mínima: 40 × 40 px; deixar respiro entre o quadro e o wordmark.
- Não esticar, recortar, aplicar sombra, criar gradientes ou recolorir sem revisão. Não reutilizar o SVG horizontal no mesmo espaço que já contém wordmark.
- `DS-C01` marca no cabeçalho, identidade gráfica, DS-C02, DS-C03, cartões secundários e acabamento do navegador permanecem **candidatos à v0.3**. A versão oficial continua v0.2 até revisão estética do usuário.

## Arquivos de evidência

O pacote `docs/powerbi/evidence/archives/fase-5.4.2-evidencias.zip` contém o inventário de validação estrutural, o catálogo de variantes e cópias dos três SVGs. Ele não contém capturas de tela. O relatório pode ser atualizado quando a revisão no Desktop estiver disponível; nenhuma fase posterior foi iniciada.
