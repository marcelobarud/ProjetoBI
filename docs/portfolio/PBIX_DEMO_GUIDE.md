# Guia rápido — PBIX demonstrativo InfoTech

## Disponibilidade

O arquivo demonstrativo preparado para revisão é `ProjetoBI-InfoTech-Demo.pbix`. Ele está fora deste repositório em `D:\Codex\ProjetoBI-Distribution\Fase-5.7.2\ProjetoBI-InfoTech-Demo.pbix`. Ainda não há link de download público: a GitHub Release é apenas uma minuta em [`GITHUB_RELEASE_DRAFT.md`](GITHUB_RELEASE_DRAFT.md).

## Requisitos e abertura

O relatório foi aberto e validado no Power BI Desktop versão **2.158.1304.0**. Essa é a versão registrada nos testes, não um requisito mínimo declarado.

1. Quando o arquivo estiver disponível por um canal de distribuição aprovado, baixe o PBIX e abra-o no Power BI Desktop.
2. O arquivo usa dados sintéticos incorporados no modo Import. Navegue pelas páginas pelo navegador do relatório.
3. Use os segmentadores de período, Canal e Loja. A página Custos e Margens também possui filtros recolhíveis.
4. Para voltar ao estado inicial, reabra o arquivo sem salvar as seleções temporárias.

O intervalo dos dados comerciais vai de **2023-01-01 a 2026-09-30**. O estado inicial homologado da página executiva mostra **04/01/2026–30/09/2026**, Canal e Loja em Todos.

## Limites da validação

A abertura, as cinco páginas, os filtros e a persistência do estado foram confirmados. Não execute **Atualizar** nem conecte o arquivo ao PostgreSQL: a validação em ambiente isolado, sem acesso à origem, está pendente. A homologação do PBIX permanece **PARTIAL — OFFLINE VALIDATION PENDING**. Acessibilidade universal, conformidade WCAG e uso móvel também não foram certificados.

O Power BI Desktop pode permitir editar o relatório. Para apenas explorar, evite salvar mudanças. A disponibilidade pública do arquivo depende de uma decisão e publicação futuras.
