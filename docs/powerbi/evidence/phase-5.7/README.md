# Evidências da Fase 5.7

Os arquivos desta pasta registram uma auditoria estática local/remota. Nenhum contém dados importados, credenciais ou conteúdo de `.env`.

- `git-manifest.json`: branch, hashes, divergência, estado inicial e reflog de pushes observados.
- `versioned-pbip-inventory.json`: inventário separado do workspace e do archive de `origin/main`, páginas, modelo, recursos e referências de interações.
- `pbir-comparison.json`: comparação JSON normalizada dos arquivos PBIR modificados e resumo das diferenças materiais.
- `local-change-inventory.csv`: cada caminho modificado, não rastreado e os arquivos de cache ignorados; hashes e recomendação de tratamento.
- `validation-results.json`: resultados e limites das verificações estáticas.
- `dependency-inventory.md`: dependências PostgreSQL/Import e requisitos para reprodução/publicação.
- `security-scan-summary.md`: padrões examinados, falsos positivos contextualizados e limites do exame.
- `readiness-matrix.csv`: pendências priorizadas, evidência e plano recomendado.

A referência remota foi obtida por `git fetch origin` e exportada via `git archive origin/main` para uma pasta temporária fora do workspace. Não foi feito checkout, refresh nem abertura em Desktop limpo.
