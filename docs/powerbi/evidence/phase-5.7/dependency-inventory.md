# Dependências e reprodução — Fase 5.7

**Escopo:** inspeção estática do `git archive origin/main` em `e91ce059dd44ee34a9d7c3e9134338f441efc6b6`; nenhum refresh, acesso PostgreSQL ou abertura do Desktop foi executado.

## Código-fonte PBIP

- Abra `powerbi/ProjetoBI.pbip`; ele aponta para `ProjetoBI.Report`.
- `ProjetoBI.Report/definition.pbir` referencia o modelo relativo `../ProjetoBI.SemanticModel`.
- `ProjetoBI.SemanticModel/definition.pbism`, 10 arquivos TMDL de tabela, `model.tmdl`, `relationships.tmdl` e cultura pt-BR compõem a definição semântica versionada.
- As cinco páginas, visuais, bookmarks, tema InfoTech e SVG do monograma estão no pacote Git. Os dois SVGs registrados e de origem têm SHA-256 idêntico. Não foram encontrados caminhos absolutos de filesystem nas definições PBIP inspecionadas.
- Versão observada na homologação Desktop: Power BI Desktop Store `2.158.1304.0 (26.09)`; isso documenta o ambiente testado, não define um mínimo compatível nem comprova abertura do archive limpo.

## PostgreSQL e modelo Import

- As consultas de oito tabelas usam `PostgreSQL.Database`; destino codificado no modelo é local (`127.0.0.1:5432`, database `projeto_bi`). DimCalendario é definida no modelo.
- O modelo possui 10 partições Import e nenhuma partição DirectQuery. Definições de consulta são versionadas, enquanto dados importados e cache local do Desktop não estão no Git archive.
- Um clone para reprodução requer PostgreSQL 18 acessível no ambiente, schema/dataset sintético aprovado disponível até `2026-09-30`, credencial apropriada somente leitura e configuração da fonte no Power BI. O usuário do sistema de destino deve inserir credenciais localmente; nenhuma senha é fornecida por este pacote.
- Abrir o PBIP não garante que os visuais exibam dados. Atualização/carregamento é necessária no ambiente destinatário, depois de configurar a fonte e verificar o destino. Esta auditoria não executou refresh.
- O `.env.example` contém nomes de variáveis vazios para o gerador; não é configuração de credenciais do Power BI. Um `.env` local ignorado existe, mas seu conteúdo não foi lido.

## Entrega e publicação

- **Código-fonte PBIP:** as definições estão versionadas; o cache e os dados Import não acompanham o código.
- **Reprodução local:** requer Desktop compatível, PostgreSQL, schema/dataset, conectividade, identidade de leitura, credenciais e refresh validado. Uma abertura em máquina limpa não foi testada.
- **Power BI Service:** requer decisão de workspace/tenant, credenciais de refresh, gateway ou rede que alcance PostgreSQL, política de segurança/RLS quando aplicável, refresh, limites e operação. Nenhuma publicação foi avaliada ou iniciada.

## Limites de compatibilidade

`queryLimitOption=None` aparece no PBIR do workspace local e está ausente no commit remoto. O histórico de documentação registra a opção como pendência. O valor não comprova defeito funcional; pode retirar limites e merece decisão antes de operar consultas maiores. Não foi alterado.
