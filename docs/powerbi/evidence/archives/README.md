# Arquivos de evidências do Power BI

Os pacotes abaixo reúnem testes e evidências por fase. Os arquivos originais continuam em `docs/powerbi/evidence/`; os ZIPs são cópias portáteis, com entradas planas na raiz quando a estrutura da fase permite.

| Fase | Pacote | Arquivos | Tamanho | Observação |
|---|---|---:|---:|---|
| 5.1.1 | [fase-5.1.1-evidencias.zip](fase-5.1.1-evidencias.zip) | 2 | 97,6 KB | Capturas de diagnóstico e visão executiva |
| 5.1.2 | [fase-5.1.2-evidencias.zip](fase-5.1.2-evidencias.zip) | 3 | 140,4 KB | Capturas e resumo de desempenho |
| 5.2 | [fase-5.2-evidencias.zip](fase-5.2-evidencias.zip) | 8 | 542,2 KB | Análise comercial, validação DAX e desempenho |
| 5.2.1 | [fase-5.2.1-evidencias.zip](fase-5.2.1-evidencias.zip) | 6 | 683,5 KB | Slider e sincronização de período |
| 5.3 | [fase-5.3-evidencias.zip](fase-5.3-evidencias.zip) | 27 | 2.432,9 KB | Produtos, categorias, interações e validações |
| 5.4 | [fase-5.4-evidencias.zip](fase-5.4-evidencias.zip) | 3 | 160,5 KB | Custos, reconciliação DAX e Performance Analyzer; fase PARTIAL conforme relatório |
| 5.4.1 | [fase-5.4.1-evidencias.zip](fase-5.4.1-evidencias.zip) | 17 | 1.178,6 KB | Painéis de filtros e desempenho aquecido |
| 5.4.2 | [fase-5.4.2-evidencias.zip](fase-5.4.2-evidencias.zip) | 5 | 2,9 KB | Ativos da marca e auditoria estrutural; sem captura visual |
| 5.4.2.1 | [fase-5.4.2.1-evidencias.zip](fase-5.4.2.1-evidencias.zip) | 39 | 3.193,6 KB | Identidade, interações, capturas e artefatos PBIR |
| 5.5 | [fase-5.5-evidencias.zip](fase-5.5-evidencias.zip) | 3 | 171,6 KB | Dashboard de devoluções e resumo de validação |
| 5.6A | [fase-5.6a-evidencias.zip](fase-5.6a-evidencias.zip) | 13 | 8,2 KB | Matriz integrada, consultas DAX e resultados; cópia do pacote preexistente |
| 5.6A.1 | [fase-5.6a.1-evidencias.zip](fase-5.6a.1-evidencias.zip) | 4 | 15,3 KB | Matriz, inventário, export do Performance Analyzer e relatório; status PARTIAL — testes manuais pendentes |
| 5.7.1 | [fase-5.7.1-evidencias.zip](fase-5.7.1-evidencias.zip) | 4 | 7,5 KB | Relatório, candidato PBIR estático, matriz dos 20 diffs e riscos de distribuição; gates B e D PARTIAL |
| 5.7.2 | [fase-5.7.2-evidencias.zip](fase-5.7.2-evidencias.zip) | 4 | 242,6 KB | Relatório, inventário PBIR/PBIX e export PDF nativo de cinco páginas; PARTIAL — reabertura do PBIX, teste offline e screenshots do Desktop pendentes |
| 5.8.1 | [fase-5.8.1-evidencias.zip](fase-5.8.1-evidencias.zip) | 9 | 58,7 KB | PBIR, relatório da fase, guia PBIX e validação estática; PASS para apresentação, teste offline pendente; sem PBIX ou capturas |

Os arquivos originais permanecem nas pastas de evidência correspondentes. O pacote `phase-5.6a.zip` preexistente também foi mantido no local original; sua cópia organizada está em `archives/`.

## Padrão para as próximas fases

- Criar um arquivo por fase no formato `fase-<identificador>-evidencias.zip`, com nomes minúsculos e sem espaços.
- Incluir somente evidências pertencentes à fase: capturas, matrizes/resultados de teste, exportações de desempenho e artefatos aprovados. Manter nomes originais sempre que possível e entradas planas na raiz do ZIP.
- Manter os originais em `docs/powerbi/evidence/`; o ZIP é uma cópia portátil. Atualizar este índice com quantidade, tamanho e classificação da fase.
- Verificar a integridade do ZIP e comparar SHA-256 de cada conteúdo compactado com seu original antes de registrar o pacote como conferido.
- Não incluir credenciais, arquivos `.env`, exportações genéricas compartilhadas, dados operacionais ou evidências de outras fases. O pacote não altera nem amplia a classificação de homologação registrada no relatório.
- Preparar o ZIP ao concluir a fase, sem sobrescrever pacotes existentes implicitamente.
