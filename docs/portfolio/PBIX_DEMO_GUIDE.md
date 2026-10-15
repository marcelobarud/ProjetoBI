# Guia rápido — PBIX demonstrativo InfoTech

## Disponibilidade

O PBIX atualizado fora do repositório é `ProjetoBI-InfoTech-Demo.pbix`, em `D:\Codex\ProjetoBI-Distribution\Fase-5.7.2\ProjetoBI-InfoTech-Demo.pbix`: 38.911.257 bytes, SHA-256 `B114FE56897C8376E6FF896ABF4FDF478D8203498925BF255B6E8A8D1CDB8E6B`. O usuário confirmou a correção do bookmark, enquadramento e página inicial. Ainda não há link de download público; a GitHub Release continua apenas como minuta em [`GITHUB_RELEASE_DRAFT.md`](GITHUB_RELEASE_DRAFT.md).

## Requisitos e abertura

O Power BI Desktop instalado no ambiente foi identificado como versão **2.158.1304.0**. Essa informação não confirma diretamente qual versão salvou o PBIX atual e não é um requisito mínimo declarado.

1. Quando o arquivo estiver disponível por um canal de distribuição aprovado, baixe o PBIX e abra-o no Power BI Desktop.
2. O arquivo usa dados sintéticos incorporados no modo Import. Navegue pelas páginas pelo navegador do relatório.
3. Use os segmentadores de período, Canal e Loja. A página Custos e Margens também possui filtros recolhíveis.
4. Para voltar ao estado inicial, reabra o arquivo sem salvar as seleções temporárias.

O intervalo dos dados comerciais vai de **2023-01-01 a 2026-09-30**. O usuário confirmou que validou o PBIP e corrigiu o bookmark aberto, páginas em `FitToWidth` e página inicial. A inspeção somente leitura do PBIX atual confirma Visão Executiva como página inicial, as cinco páginas em `FitToPage` e os cinco grupos de filtros serializados como ocultos.

## Limites da validação

O usuário reportou a validação do PBIP e confirmou que o PBIX corrigido foi salvo e reaberto, iniciando em Visão Executiva e com o painel de Devoluções fechado. A inspeção do pacote confirmou a integridade estrutural, cinco páginas, `FitToPage`, página inicial e bookmarks. Não execute **Atualizar** nem conecte o arquivo ao PostgreSQL: a validação em ambiente isolado, sem acesso à origem, está pendente. A distribuição permanece parcial até essa verificação. Acessibilidade universal, conformidade WCAG e uso móvel também não foram certificados.

O Power BI Desktop pode permitir editar o relatório. Para apenas explorar, evite salvar mudanças. A disponibilidade pública do arquivo depende de uma decisão e publicação futuras.
