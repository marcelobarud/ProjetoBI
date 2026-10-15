# Guia rápido — PBIX demonstrativo InfoTech

## Disponibilidade

O PBIX que existe hoje fora do repositório é `ProjetoBI-InfoTech-Demo.pbix`, em `D:\Codex\ProjetoBI-Distribution\Fase-5.7.2\ProjetoBI-InfoTech-Demo.pbix`. Ele é a versão anterior à correção desta fase: 38.910.666 bytes, SHA-256 `398EB0B3866810F2ABD787AC71FAE4ED9CD8327A84589BF43567F7CA85A399D2`. Ainda não há um PBIX atualizado nem link de download público. A GitHub Release continua apenas como minuta em [`GITHUB_RELEASE_DRAFT.md`](GITHUB_RELEASE_DRAFT.md); não anexar a versão anterior como se incluísse as correções de 5.8.1.

## Requisitos e abertura

O relatório foi aberto e validado no Power BI Desktop versão **2.158.1304.0**. Essa é a versão registrada nos testes, não um requisito mínimo declarado.

1. Quando o arquivo estiver disponível por um canal de distribuição aprovado, baixe o PBIX e abra-o no Power BI Desktop.
2. O arquivo usa dados sintéticos incorporados no modo Import. Navegue pelas páginas pelo navegador do relatório.
3. Use os segmentadores de período, Canal e Loja. A página Custos e Margens também possui filtros recolhíveis.
4. Para voltar ao estado inicial, reabra o arquivo sem salvar as seleções temporárias.

O intervalo dos dados comerciais vai de **2023-01-01 a 2026-09-30**. No PBIX anterior, a página inicial homologada era Visão Executiva, com painel de filtros fechado, período **04/01/2026–30/09/2026** e Canal/Loja em Todos. A configuração `FitToPage` foi aplicada estaticamente ao candidato PBIP desta fase; sua validação no Desktop e a geração de um novo PBIX continuam pendentes.

## Limites da validação

A abertura, as cinco páginas, os filtros e a persistência do estado do PBIX anterior foram confirmados. Não execute **Atualizar** nem conecte o arquivo ao PostgreSQL: a validação em ambiente isolado, sem acesso à origem, está pendente. A homologação do PBIX permanece **PARTIAL — OFFLINE VALIDATION PENDING**. Acessibilidade universal, conformidade WCAG e uso móvel também não foram certificados.

O Power BI Desktop pode permitir editar o relatório. Para apenas explorar, evite salvar mudanças. A disponibilidade pública do arquivo depende de uma decisão e publicação futuras.
