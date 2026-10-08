# Orientações do projeto para o Codex

## Finalidade e localização

- Projeto: **ProjetoBI**, iniciativa de estudo e prática de Business Intelligence.
- Diretório raiz: `D:\Codex\ProjetoBI`.
- O domínio planejado é uma empresa fictícia do segmento de informática. Não invente requisitos de negócio que ainda não foram definidos.
- O banco operacional deve representar um ecossistema empresarial coerente e não apenas as necessidades imediatas do dashboard. Campos administrativos e operacionais realistas podem fazer parte do banco, mesmo quando não forem usados na análise.

## Ambiente e ferramentas

- O ambiente de trabalho é Windows; use PowerShell para operações locais.
- PostgreSQL será a fonte operacional de dados. Não crie, altere ou remova bancos, schemas, tabelas, usuários, dados ou outros objetos sem autorização expressa na fase correspondente. Inspecionar ou usar uma conexão também deve respeitar o escopo aprovado para a fase.
- A database alvo aprovada é `projeto_bi`, em PostgreSQL 18. O modelo relacional operacional aprovado em `docs/database/` é a fonte de verdade; mantenha migrations SQL versionadas e não o converta em modelo estrela nesta fase.
- Nunca use `DROP DATABASE` ou recrie uma database preexistente automaticamente. Inspecione e pare diante de objetos inesperados; credenciais ficam em variáveis locais e nunca no Git.
- Regras de concorrência, custo médio, movimentos e devoluções devem seguir `docs/database/operational-transactions.md` quando a camada operacional for implementada.
- Python implementa o gerador sintético em `data-generator/`; use o `.venv/` local e mantenha dependências isoladas. Configuração não sensível fica em TOML versionado e credenciais somente em `.env` local.
- Derive sub-seeds estáveis por domínio; não compartilhe estado aleatório entre domínios. Use `Decimal` para dinheiro e timestamps com fuso explícito.
- Smoke PostgreSQL autorizado para o gerador deve validar alvo/schema/vazio antes de escrever, usar transação com `ROLLBACK` explícito e verificar em conexão nova que todos os dados foram revertidos. Nunca persista dados sem autorização de fase.
- Dados de estudo devem ser 100% sintéticos, determinísticos por seed/configuração e sem defeitos intencionais. Respeite o cutoff comercial aprovado para cada conjunto; nunca desabilite constraints de integridade para facilitar cargas.
- Power BI será a camada analítica, com Power Query, modelo semântico, DAX e relatórios. O Power BI Project (`.pbip`) deverá ser usado quando a fase do Power BI for autorizada; seus arquivos de definição necessários devem ser versionados.

## Forma de trabalhar

- Divida o trabalho em fases pequenas e conclua apenas o escopo autorizado.
- Antes de modificar qualquer arquivo, inspecione o estado atual do diretório, os documentos relevantes e o estado do Git. Preserve conteúdo válido e não sobrescreva arquivos sem avaliá-los.
- Valide as mudanças pertinentes antes de criar um commit e descreva o que foi verificado.
- Mantenha a documentação sincronizada com mudanças arquiteturais relevantes.
- Não gere dados, não modele o negócio e não avance etapas sem que o usuário solicite ou aprove o escopo correspondente.

## Fontes de verdade

- Regras e decisões de negócio aprovadas definem o comportamento esperado; modelos, contratos e documentos arquiteturais aprovados definem a estrutura autorizada.
- Código e testes demonstram o comportamento implementado. Documentação histórica fornece contexto e deve ser revalidada.
- Ao encontrar divergências relevantes entre essas fontes, investigue e comunique evidências e incertezas; não escolha uma versão por suposição.

## Delegação, revisão e encerramento

- O agente principal permanece responsável pelo resultado. Delegue somente quando houver benefício concreto em investigação independente, revisão crítica ou análise arquitetural; tarefas pequenas não exigem subagentes.
- Considere primeiro o planner para diagnóstico incerto e o reviewer para revisão independente de mudanças com risco. Use architect somente para decisões estruturais reais e implementer para escopos compreendidos e delimitados. Não imponha uma sequência fixa nem paralelismo desnecessário.
- Priorize revisão de persistência, estoque, pedidos, pagamentos, migrations, integridade e cálculos monetários. Registre achados concretos com arquivo, evidência, impacto e recomendação.
- Valide proporcionalmente ao escopo. Mudanças apenas documentais ou de configuração não exigem a suíte completa; nunca declare uma verificação que não foi executada.
- Ao concluir, resuma mudanças, verificações, limitações e commit quando autorizado. Todos os subagentes seguem este arquivo; poder editar arquivos não autoriza acesso ou alteração ao banco de dados.

## Git e credenciais

- Use commits locais pequenos e mensagens no padrão Conventional Commits.
- Não configure um remoto nem faça push automaticamente. Só publique alterações quando o usuário solicitar explicitamente.
- Nunca versionar senhas, tokens, chaves, arquivos `.env` reais, connection strings com credenciais ou outros segredos. Use `.env.example` apenas com nomes de variáveis e valores vazios ou fictícios explicitamente seguros.
- Antes de commitar, confira o conteúdo staged e o `git status` para garantir que não há credenciais ou arquivos locais indevidos.
- Crie commits somente quando o usuário ou a fase correspondente os autorizar explicitamente. Não faça merge, rebase ou push sem solicitação explícita.
