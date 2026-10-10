# Fase 3E.2 — validação do dataset Portfolio persistido

Dataset portfolio persistente ativo em `projeto_bi`. PostgreSQL 18.6; COMMIT concluído em 2026-10-10T06:17:06.669915-03:00. A validação posterior ocorreu em nova conexão somente leitura.

## Perfil e período

Profile `portfolio`; root seed `20261005`; gerador `0.1.0`; configuração `1`; timezone `America/Sao_Paulo`.

Bootstrap 2022-11-01 a 2022-12-31; comercial 2023-01-01 a 2026-09-30. Execução iniciada em 2026-10-09T23:36:01.220446-03:00; relatório concluído em 2026-10-10T06:18:18.129052-03:00.

## Execução e performance

Master: 1.8s para gerar/validar e 16.4s para persistir/validar. Pipeline transacional: 24006.6s; validações SQL pré-COMMIT: 40.3s; baselines SQL: 38.746617500000866s; validação pós-COMMIT: 32.7s. Total até validação pós-COMMIT: 24098.2s; total com baselines: 24136.906799999997s.

Linhas relacionais transacionais inseridas: 3675448; atualizações: 846799; flushes: 1546; batch máximo: 5000; IDs transitórios pico/final: 11614/0. Throughput transacional aproximado: 5.0 pedidos/s. Pico de memória não foi medido: tracemalloc não foi habilitado para evitar desacelerar a carga completa.

Tempo por ano no progresso do sink marca o intervalo entre o primeiro evento comercial do ano e a transição observada para o próximo ano; 2026 cobre janeiro–setembro.

| Período | Segundos observados |
|---|---|
| 2023 | 1281.3908 |
| 2024 | 4979.9599 |
| 2025 | 8842.7197 |
| 2026 | 8877.6832 |

## Dados mestre

| Entidade | Linhas |
|---|---|
| brands | 65 |
| business_profiles | 4500 |
| carriers | 12 |
| categories | 42 |
| customer_addresses | 52000 |
| customer_contacts | 60000 |
| customers | 45000 |
| employee_assignments | 115 |
| employee_roles | 7 |
| employees | 90 |
| individual_profiles | 40500 |
| payment_methods | 5 |
| product_prices | 14000 |
| product_suppliers | 1600 |
| products | 1000 |
| sales_channels | 4 |
| stock_locations | 14 |
| stores | 10 |
| suppliers | 45 |

## Transações

| Tabela lógica | Linhas |
|---|---|
| applied_discounts | 94045 |
| fulfillment_events | 540647 |
| fulfillment_items | 237742 |
| fulfillments | 176716 |
| goods_receipt_items | 188870 |
| goods_receipts | 188870 |
| order_status_history | 478483 |
| payment_installments | 196731 |
| payments | 127380 |
| purchase_order_items | 188869 |
| purchase_orders | 188869 |
| refunds | 7201 |
| return_items | 7129 |
| returns | 7129 |
| sales_order_item_cancellations | 0 |
| sales_order_items | 241637 |
| sales_orders | 120000 |
| stock_movements | 429462 |
| stock_positions | 13837 |
| stock_reservations | 241831 |
| stock_transfer_items | 0 |
| stock_transfers | 0 |

### Pedidos por ano, canal e status

| Ano local | Pedidos |
|---|---|
| 2023 | 24000 |
| 2024 | 30000 |
| 2025 | 36000 |
| 2026 | 30000 |

| Canal | Pedidos | Participação |
|---|---|---|
| ecommerce | 35400 | 29.50% |
| marketplace | 22020 | 18.35% |
| physical | 62580 | 52.15% |

Evolução por tipo de canal e ano:

| Ano | Tipo de canal | Pedidos |
|---|---|---|
| 2023 | ecommerce | 6960 |
| 2023 | marketplace | 4080 |
| 2023 | physical | 12960 |
| 2024 | ecommerce | 8700 |
| 2024 | marketplace | 5400 |
| 2024 | physical | 15900 |
| 2025 | ecommerce | 10440 |
| 2025 | marketplace | 6840 |
| 2025 | physical | 18720 |
| 2026 | ecommerce | 9300 |
| 2026 | marketplace | 5700 |
| 2026 | physical | 15000 |

| Status final | Pedidos | Participação |
|---|---|---|
| cancelled | 3265 | 2.72% |
| completed | 116305 | 96.92% |
| confirmed | 430 | 0.36% |

Pedidos e incidência/intensidade de desconto por mês local `America/Sao_Paulo`:

| Mês | Pedidos | Com desconto | % com desconto | Desconto médio sobre pedidos descontados |
|---|---|---|---|---|
| 2023-01 | 1735 | 633 | 36.48% | 5.39% |
| 2023-02 | 1928 | 726 | 37.66% | 5.43% |
| 2023-03 | 1928 | 709 | 36.77% | 5.57% |
| 2023-04 | 1928 | 708 | 36.72% | 5.30% |
| 2023-05 | 1927 | 701 | 36.38% | 5.51% |
| 2023-06 | 1927 | 699 | 36.27% | 5.49% |
| 2023-07 | 1927 | 717 | 37.21% | 5.49% |
| 2023-08 | 1927 | 708 | 36.74% | 5.43% |
| 2023-09 | 1927 | 700 | 36.33% | 5.45% |
| 2023-10 | 1929 | 712 | 36.91% | 5.52% |
| 2023-11 | 2699 | 1480 | 54.84% | 8.44% |
| 2023-12 | 2218 | 848 | 38.23% | 5.53% |
| 2024-01 | 2169 | 808 | 37.25% | 5.55% |
| 2024-02 | 2410 | 865 | 35.89% | 5.55% |
| 2024-03 | 2410 | 908 | 37.68% | 5.50% |
| 2024-04 | 2410 | 927 | 38.46% | 5.55% |
| 2024-05 | 2410 | 937 | 38.88% | 5.51% |
| 2024-06 | 2410 | 940 | 39.00% | 5.39% |
| 2024-07 | 2410 | 911 | 37.80% | 5.48% |
| 2024-08 | 2410 | 890 | 36.93% | 5.46% |
| 2024-09 | 2409 | 892 | 37.03% | 5.45% |
| 2024-10 | 2410 | 920 | 38.17% | 5.48% |
| 2024-11 | 3372 | 1854 | 54.98% | 8.49% |
| 2024-12 | 2770 | 1017 | 36.71% | 5.54% |
| 2025-01 | 2603 | 983 | 37.76% | 5.46% |
| 2025-02 | 2892 | 1065 | 36.83% | 5.40% |
| 2025-03 | 2892 | 1054 | 36.45% | 5.56% |
| 2025-04 | 2892 | 1052 | 36.38% | 5.48% |
| 2025-05 | 2892 | 1061 | 36.69% | 5.45% |
| 2025-06 | 2891 | 1038 | 35.90% | 5.52% |
| 2025-07 | 2890 | 1070 | 37.02% | 5.52% |
| 2025-08 | 2890 | 1075 | 37.20% | 5.43% |
| 2025-09 | 2890 | 1087 | 37.61% | 5.48% |
| 2025-10 | 2893 | 1108 | 38.30% | 5.41% |
| 2025-11 | 4049 | 2201 | 54.36% | 8.48% |
| 2025-12 | 3326 | 1240 | 37.28% | 5.45% |
| 2026-01 | 3034 | 1158 | 38.17% | 5.47% |
| 2026-02 | 3372 | 1263 | 37.46% | 5.44% |
| 2026-03 | 3372 | 1256 | 37.25% | 5.47% |
| 2026-04 | 3372 | 1282 | 38.02% | 5.58% |
| 2026-05 | 3370 | 1266 | 37.57% | 5.52% |
| 2026-06 | 3370 | 1288 | 38.22% | 5.48% |
| 2026-07 | 3370 | 1251 | 37.12% | 5.48% |
| 2026-08 | 3370 | 1256 | 37.27% | 5.52% |
| 2026-09 | 3370 | 1223 | 36.29% | 5.41% |

Pedidos físicos por loja:

| Loja sintética | Pedidos físicos |
|---|---|
| ST-PO-001 | 8600 |
| ST-PO-002 | 8433 |
| ST-PO-003 | 8264 |
| ST-PO-004 | 6163 |
| ST-PO-005 | 6082 |
| ST-PO-006 | 5940 |
| ST-PO-007 | 5839 |
| ST-PO-008 | 4724 |
| ST-PO-009 | 4595 |
| ST-PO-010 | 3940 |

### Clientes e recorrência

Clientes identificados: 45000; PF: 40500 (90.00%); PJ: 4500 (10.00%). Pedidos físicos anônimos: 19829/62580 (31.69%); pedidos digitais anônimos: 0.

| Tipo | Pedidos por cliente | Clientes | % dos clientes ativos |
|---|---|---|---|
| business | 1 | 732 | 25.01% |
| business | 2–4 | 1317 | 44.99% |
| business | 5–10 | 732 | 25.01% |
| business | 11+ | 146 | 4.99% |
| individual | 1 | 11065 | 42.00% |
| individual | 2–4 | 10012 | 38.00% |
| individual | 5–10 | 4215 | 16.00% |
| individual | 11+ | 1054 | 4.00% |

Ticket médio concluído por tipo de cliente:

| Tipo | Pedidos concluídos | Ticket médio BRL | Valor total BRL |
|---|---|---|---|
| anonymous | 19318 | 7242.74 | 139915207.73 |
| business | 11875 | 13045.07 | 154910186.22 |
| individual | 85112 | 7699.04 | 655281090.24 |

Ticket médio concluído por canal:

| Canal | Pedidos concluídos | Ticket médio BRL | Valor total BRL |
|---|---|---|---|
| ecommerce | 34178 | 8971.82 | 306638901.32 |
| marketplace | 21264 | 9075.72 | 192986172.38 |
| physical | 60863 | 7401.56 | 450481410.49 |

### Descontos

Pedidos com desconto: 46487/120000 (38.74%); montante alocado BRL 22973353.55; desconto médio nos pedidos descontados 5.84% do subtotal.

### Pagamentos e refunds

| Tipo de meio | Capturadas/liquidadas | Falhas/recusas | Tentativas totais |
|---|---|---|---|
| bank_transfer | 916 | 29 | 960 |
| card | 57811 | 1903 | 61298 |
| cash | 9851 | 311 | 10475 |
| instant | 51654 | 1640 | 54647 |

| Registro | Meio/status | Status | Linhas | BRL |
|---|---|---|---|---|
| payment | bank_transfer | cancelled | 15 | 218089.07 |
| payment | bank_transfer | declined | 19 | 325367.27 |
| payment | bank_transfer | failed | 10 | 155105.22 |
| payment | bank_transfer | settled | 916 | 11979371.58 |
| payment | card | cancelled | 1584 | 12421651.38 |
| payment | card | declined | 1343 | 10741904.29 |
| payment | card | failed | 560 | 4216680.28 |
| payment | card | settled | 57811 | 455017490.47 |
| payment | cash | cancelled | 313 | 2216107.89 |
| payment | cash | declined | 224 | 1801879.10 |
| payment | cash | failed | 87 | 685111.52 |
| payment | cash | settled | 9851 | 71920858.54 |
| payment | instant | cancelled | 1353 | 11180237.37 |
| payment | instant | declined | 1156 | 9749080.21 |
| payment | instant | failed | 484 | 3960159.52 |
| payment | instant | settled | 51654 | 415056851.45 |
| refund | refund | completed | 7201 | 26727257.07 |

Split orders: 3497; retries: 3883; declined/failed attempts: 3883; installments: 196731; captured BRL 953974572.04; refunds concluídos BRL 26727257.07; net captured BRL 927247314.97.

### Logística, transferências e devoluções

Fulfillments: 176716; fulfillment items: 237742; eventos: 540647; transferências: 0; itens: 0.

| Canal | Tipo de cliente | Status | Destino | Returns | Itens | Solicitadas | Aprovadas | Recebidas | Refund rows | Refund BRL |
|---|---|---|---|---|---|---|---|---|---|---|
| ecommerce | business | closed | discard | 82 | 82 | 82 | 82 | 82 | 82 | 279180.22 |
| ecommerce | business | closed | quarantine | 96 | 96 | 96 | 96 | 96 | 96 | 328394.77 |
| ecommerce | business | closed | repair | 78 | 78 | 78 | 78 | 78 | 78 | 284081.59 |
| ecommerce | business | closed | sellable | 194 | 194 | 194 | 194 | 194 | 195 | 739296.18 |
| ecommerce | individual | closed | discard | 484 | 484 | 484 | 484 | 484 | 488 | 1651958.45 |
| ecommerce | individual | closed | quarantine | 495 | 495 | 495 | 495 | 495 | 500 | 1878193.71 |
| ecommerce | individual | closed | repair | 506 | 506 | 506 | 506 | 506 | 511 | 1940595.26 |
| ecommerce | individual | closed | sellable | 953 | 953 | 953 | 953 | 953 | 963 | 3538958.81 |
| ecommerce | individual | received | repair | 1 | 1 | 1 | 1 | 1 | 0 | 0 |
| marketplace | business | closed | discard | 58 | 58 | 58 | 58 | 58 | 58 | 264812.88 |
| marketplace | business | closed | quarantine | 43 | 43 | 43 | 43 | 43 | 43 | 183420.43 |
| marketplace | business | closed | repair | 42 | 42 | 42 | 42 | 42 | 42 | 139709.41 |
| marketplace | business | closed | sellable | 102 | 102 | 102 | 102 | 102 | 102 | 366452.36 |
| marketplace | individual | closed | discard | 307 | 307 | 307 | 307 | 307 | 310 | 1257171.10 |
| marketplace | individual | closed | quarantine | 308 | 308 | 308 | 308 | 308 | 314 | 1209494.82 |
| marketplace | individual | closed | repair | 308 | 308 | 308 | 308 | 308 | 311 | 1157820.51 |
| marketplace | individual | closed | sellable | 626 | 626 | 626 | 626 | 626 | 633 | 2362157.73 |
| marketplace | individual | received | sellable | 1 | 1 | 1 | 1 | 1 | 0 | 0 |
| physical | anonymous | closed | discard | 156 | 156 | 156 | 156 | 156 | 157 | 532517.14 |
| physical | anonymous | closed | quarantine | 169 | 169 | 169 | 169 | 169 | 171 | 652673.42 |
| physical | anonymous | closed | repair | 153 | 153 | 153 | 153 | 153 | 155 | 593806.02 |
| physical | anonymous | closed | sellable | 299 | 299 | 299 | 299 | 299 | 303 | 1017478.28 |
| physical | anonymous | rejected | — | 1 | 1 | 1 | 0 | 0 | 0 | 0 |
| physical | business | closed | discard | 14 | 14 | 14 | 14 | 14 | 14 | 87002.36 |
| physical | business | closed | quarantine | 12 | 12 | 12 | 12 | 12 | 12 | 44687.40 |
| physical | business | closed | repair | 5 | 5 | 5 | 5 | 5 | 5 | 14743.07 |
| physical | business | closed | sellable | 28 | 28 | 28 | 28 | 28 | 28 | 68831.46 |
| physical | individual | closed | discard | 325 | 325 | 325 | 325 | 325 | 330 | 1201249.31 |
| physical | individual | closed | quarantine | 303 | 303 | 303 | 303 | 303 | 308 | 1013490.45 |
| physical | individual | closed | repair | 332 | 332 | 332 | 332 | 332 | 335 | 1372795.58 |
| physical | individual | closed | sellable | 648 | 648 | 648 | 648 | 648 | 657 | 2546284.35 |

Returns em pedidos concluídos: 6924/116305 (5.95%); itens: 7129; sellable: 2851; non-sellable: 4277; unidades sellable recebidas: 2851.

### Estoque e reconciliação

Movimentos: 429462; posições: 13837; on hand: 10089; reservado: 0; disponível: 10089; reconciliação física por ledger e média móvel: PASS; valor de estoque ao custo médio atual: BRL 28266514.18059302.

| Local | Categoria | Posições | On hand | Reservado | Disponível | Valor BRL |
|---|---|---|---|---|---|---|
| LOC-PO-WH-013 | CAT-ACCESSORIES | 83 | 3 | 0 | 3 | 1217.68676224 |
| LOC-PO-WH-013 | CAT-AUDIO | 83 | 4 | 0 | 4 | 3303.47797195 |
| LOC-PO-WH-013 | CAT-DESKTOP | 84 | 5 | 0 | 5 | 31609.41265570 |
| LOC-PO-WH-013 | CAT-GRAPHICS | 84 | 4 | 0 | 4 | 22912.93098480 |
| LOC-PO-WH-013 | CAT-INPUT | 83 | 6 | 0 | 6 | 6400.59864250 |
| LOC-PO-WH-013 | CAT-MEMORY | 83 | 8 | 0 | 8 | 5923.63694600 |
| LOC-PO-WH-013 | CAT-MONITOR | 83 | 2 | 0 | 2 | 2870.02569560 |
| LOC-PO-WH-013 | CAT-NETWORK | 83 | 5 | 0 | 5 | 7310.32298955 |
| LOC-PO-WH-013 | CAT-NOTEBOOK | 84 | 3 | 0 | 3 | 17157.09794140 |
| LOC-PO-WH-013 | CAT-PRINTING | 83 | 8 | 0 | 8 | 15523.29744500 |
| LOC-PO-WH-013 | CAT-PROCESSOR | 84 | 6 | 0 | 6 | 11520.66182540 |
| LOC-PO-WH-013 | CAT-STORAGE | 83 | 3 | 0 | 3 | 3357.32511400 |
| LOC-PO-WH-014 | CAT-ACCESSORIES | 79 | 0 | 0 | 0 | 0E-8 |
| LOC-PO-WH-014 | CAT-AUDIO | 78 | 0 | 0 | 0 | 0E-8 |
| LOC-PO-WH-014 | CAT-DESKTOP | 80 | 0 | 0 | 0 | 0E-8 |
| LOC-PO-WH-014 | CAT-GRAPHICS | 81 | 0 | 0 | 0 | 0E-8 |
| LOC-PO-WH-014 | CAT-INPUT | 77 | 0 | 0 | 0 | 0E-8 |
| LOC-PO-WH-014 | CAT-MEMORY | 76 | 0 | 0 | 0 | 0E-8 |
| LOC-PO-WH-014 | CAT-MONITOR | 74 | 0 | 0 | 0 | 0E-8 |
| LOC-PO-WH-014 | CAT-NETWORK | 80 | 0 | 0 | 0 | 0E-8 |
| LOC-PO-WH-014 | CAT-NOTEBOOK | 80 | 0 | 0 | 0 | 0E-8 |
| LOC-PO-WH-014 | CAT-PRINTING | 78 | 0 | 0 | 0 | 0E-8 |
| LOC-PO-WH-014 | CAT-PROCESSOR | 81 | 0 | 0 | 0 | 0E-8 |
| LOC-PO-WH-014 | CAT-STORAGE | 78 | 0 | 0 | 0 | 0E-8 |
| LOC-SM-CENTRAL | CAT-ACCESSORIES | 81 | 0 | 0 | 0 | 0E-8 |
| LOC-SM-CENTRAL | CAT-AUDIO | 76 | 0 | 0 | 0 | 0E-8 |
| LOC-SM-CENTRAL | CAT-DESKTOP | 82 | 0 | 0 | 0 | 0E-8 |
| LOC-SM-CENTRAL | CAT-GRAPHICS | 79 | 0 | 0 | 0 | 0E-8 |
| LOC-SM-CENTRAL | CAT-INPUT | 80 | 0 | 0 | 0 | 0E-8 |
| LOC-SM-CENTRAL | CAT-MEMORY | 80 | 0 | 0 | 0 | 0E-8 |
| LOC-SM-CENTRAL | CAT-MONITOR | 77 | 0 | 0 | 0 | 0E-8 |
| LOC-SM-CENTRAL | CAT-NETWORK | 80 | 0 | 0 | 0 | 0E-8 |
| LOC-SM-CENTRAL | CAT-NOTEBOOK | 82 | 0 | 0 | 0 | 0E-8 |
| LOC-SM-CENTRAL | CAT-PRINTING | 77 | 0 | 0 | 0 | 0E-8 |
| LOC-SM-CENTRAL | CAT-PROCESSOR | 81 | 0 | 0 | 0 | 0E-8 |
| LOC-SM-CENTRAL | CAT-STORAGE | 77 | 0 | 0 | 0 | 0E-8 |
| LOC-SM-EXPEDITION | CAT-ACCESSORIES | 80 | 0 | 0 | 0 | 0E-8 |
| LOC-SM-EXPEDITION | CAT-AUDIO | 82 | 0 | 0 | 0 | 0E-8 |
| LOC-SM-EXPEDITION | CAT-DESKTOP | 80 | 0 | 0 | 0 | 0E-8 |
| LOC-SM-EXPEDITION | CAT-GRAPHICS | 80 | 0 | 0 | 0 | 0E-8 |
| LOC-SM-EXPEDITION | CAT-INPUT | 77 | 0 | 0 | 0 | 0E-8 |
| LOC-SM-EXPEDITION | CAT-MEMORY | 81 | 0 | 0 | 0 | 0E-8 |
| LOC-SM-EXPEDITION | CAT-MONITOR | 82 | 0 | 0 | 0 | 0E-8 |
| LOC-SM-EXPEDITION | CAT-NETWORK | 75 | 0 | 0 | 0 | 0E-8 |
| LOC-SM-EXPEDITION | CAT-NOTEBOOK | 79 | 0 | 0 | 0 | 0E-8 |
| LOC-SM-EXPEDITION | CAT-PRINTING | 75 | 0 | 0 | 0 | 0E-8 |
| LOC-SM-EXPEDITION | CAT-PROCESSOR | 78 | 0 | 0 | 0 | 0E-8 |
| LOC-SM-EXPEDITION | CAT-STORAGE | 74 | 0 | 0 | 0 | 0E-8 |
| LOC-ST-PO-001 | CAT-ACCESSORIES | 83 | 61 | 0 | 61 | 29091.20119496 |
| LOC-ST-PO-001 | CAT-AUDIO | 83 | 62 | 0 | 62 | 61548.56253705 |
| LOC-ST-PO-001 | CAT-DESKTOP | 84 | 75 | 0 | 75 | 480715.15606252 |
| LOC-ST-PO-001 | CAT-GRAPHICS | 84 | 64 | 0 | 64 | 403816.50275875 |
| LOC-ST-PO-001 | CAT-INPUT | 83 | 81 | 0 | 81 | 70273.74188300 |
| LOC-ST-PO-001 | CAT-MEMORY | 83 | 64 | 0 | 64 | 45649.74097096 |
| LOC-ST-PO-001 | CAT-MONITOR | 83 | 84 | 0 | 84 | 167425.44935468 |
| LOC-ST-PO-001 | CAT-NETWORK | 83 | 65 | 0 | 65 | 98609.76376690 |
| LOC-ST-PO-001 | CAT-NOTEBOOK | 84 | 61 | 0 | 61 | 473325.82141007 |
| LOC-ST-PO-001 | CAT-PRINTING | 83 | 48 | 0 | 48 | 120444.76375334 |
| LOC-ST-PO-001 | CAT-PROCESSOR | 84 | 62 | 0 | 62 | 162660.18281761 |
| LOC-ST-PO-001 | CAT-STORAGE | 83 | 65 | 0 | 65 | 86450.50649586 |
| LOC-ST-PO-002 | CAT-ACCESSORIES | 83 | 56 | 0 | 56 | 28404.88910102 |
| LOC-ST-PO-002 | CAT-AUDIO | 83 | 66 | 0 | 66 | 62190.72484860 |
| LOC-ST-PO-002 | CAT-DESKTOP | 84 | 70 | 0 | 70 | 469777.63081958 |
| LOC-ST-PO-002 | CAT-GRAPHICS | 84 | 71 | 0 | 71 | 493982.08186747 |
| LOC-ST-PO-002 | CAT-INPUT | 83 | 70 | 0 | 70 | 62768.49519009 |
| LOC-ST-PO-002 | CAT-MEMORY | 83 | 77 | 0 | 77 | 52948.17859393 |
| LOC-ST-PO-002 | CAT-MONITOR | 83 | 62 | 0 | 62 | 114506.85477480 |
| LOC-ST-PO-002 | CAT-NETWORK | 83 | 63 | 0 | 63 | 96868.64849096 |
| LOC-ST-PO-002 | CAT-NOTEBOOK | 84 | 70 | 0 | 70 | 578316.54221728 |
| LOC-ST-PO-002 | CAT-PRINTING | 83 | 65 | 0 | 65 | 150338.52465384 |
| LOC-ST-PO-002 | CAT-PROCESSOR | 84 | 52 | 0 | 52 | 138208.27278621 |
| LOC-ST-PO-002 | CAT-STORAGE | 83 | 64 | 0 | 64 | 80411.71386399 |
| LOC-ST-PO-003 | CAT-ACCESSORIES | 83 | 62 | 0 | 62 | 30293.54344107 |
| LOC-ST-PO-003 | CAT-AUDIO | 83 | 64 | 0 | 64 | 63717.48121637 |
| LOC-ST-PO-003 | CAT-DESKTOP | 84 | 64 | 0 | 64 | 434083.77795275 |
| LOC-ST-PO-003 | CAT-GRAPHICS | 84 | 68 | 0 | 68 | 412679.36891659 |
| LOC-ST-PO-003 | CAT-INPUT | 83 | 68 | 0 | 68 | 59937.12903490 |
| LOC-ST-PO-003 | CAT-MEMORY | 83 | 72 | 0 | 72 | 52602.35677179 |
| LOC-ST-PO-003 | CAT-MONITOR | 83 | 55 | 0 | 55 | 111515.81925394 |
| LOC-ST-PO-003 | CAT-NETWORK | 83 | 60 | 0 | 60 | 92378.13642381 |
| LOC-ST-PO-003 | CAT-NOTEBOOK | 84 | 56 | 0 | 56 | 428017.06237795 |
| LOC-ST-PO-003 | CAT-PRINTING | 83 | 65 | 0 | 65 | 147522.41668985 |
| LOC-ST-PO-003 | CAT-PROCESSOR | 84 | 68 | 0 | 68 | 184610.83859970 |
| LOC-ST-PO-003 | CAT-STORAGE | 83 | 68 | 0 | 68 | 89435.95630266 |
| LOC-ST-PO-004 | CAT-ACCESSORIES | 83 | 82 | 0 | 82 | 39605.02778016 |
| LOC-ST-PO-004 | CAT-AUDIO | 83 | 88 | 0 | 88 | 84272.58617257 |
| LOC-ST-PO-004 | CAT-DESKTOP | 84 | 82 | 0 | 82 | 535775.44576142 |
| LOC-ST-PO-004 | CAT-GRAPHICS | 84 | 85 | 0 | 85 | 503292.39694169 |
| LOC-ST-PO-004 | CAT-INPUT | 83 | 83 | 0 | 83 | 71422.95531632 |
| LOC-ST-PO-004 | CAT-MEMORY | 83 | 86 | 0 | 86 | 58778.58948980 |
| LOC-ST-PO-004 | CAT-MONITOR | 83 | 82 | 0 | 82 | 166607.05690133 |
| LOC-ST-PO-004 | CAT-NETWORK | 83 | 68 | 0 | 68 | 105426.42441159 |
| LOC-ST-PO-004 | CAT-NOTEBOOK | 84 | 76 | 0 | 76 | 598439.54709354 |
| LOC-ST-PO-004 | CAT-PRINTING | 83 | 79 | 0 | 79 | 187357.41405817 |
| LOC-ST-PO-004 | CAT-PROCESSOR | 84 | 77 | 0 | 77 | 203077.23544754 |
| LOC-ST-PO-004 | CAT-STORAGE | 83 | 73 | 0 | 73 | 97251.98593918 |
| LOC-ST-PO-005 | CAT-ACCESSORIES | 83 | 80 | 0 | 80 | 38492.99453172 |
| LOC-ST-PO-005 | CAT-AUDIO | 83 | 80 | 0 | 80 | 77815.26272150 |
| LOC-ST-PO-005 | CAT-DESKTOP | 84 | 80 | 0 | 80 | 566047.68881258 |
| LOC-ST-PO-005 | CAT-GRAPHICS | 84 | 85 | 0 | 85 | 550967.40221189 |
| LOC-ST-PO-005 | CAT-INPUT | 83 | 81 | 0 | 81 | 73224.17067740 |
| LOC-ST-PO-005 | CAT-MEMORY | 83 | 97 | 0 | 97 | 63603.24323227 |
| LOC-ST-PO-005 | CAT-MONITOR | 83 | 84 | 0 | 84 | 164866.08222495 |
| LOC-ST-PO-005 | CAT-NETWORK | 83 | 91 | 0 | 91 | 139919.06769633 |
| LOC-ST-PO-005 | CAT-NOTEBOOK | 84 | 75 | 0 | 75 | 618116.29331005 |
| LOC-ST-PO-005 | CAT-PRINTING | 83 | 82 | 0 | 82 | 200912.35672659 |
| LOC-ST-PO-005 | CAT-PROCESSOR | 84 | 82 | 0 | 82 | 211256.74715059 |
| LOC-ST-PO-005 | CAT-STORAGE | 83 | 99 | 0 | 99 | 132089.22204059 |
| LOC-ST-PO-006 | CAT-ACCESSORIES | 83 | 88 | 0 | 88 | 43492.29685461 |
| LOC-ST-PO-006 | CAT-AUDIO | 83 | 93 | 0 | 93 | 86040.75604375 |
| LOC-ST-PO-006 | CAT-DESKTOP | 84 | 78 | 0 | 78 | 528072.52532580 |
| LOC-ST-PO-006 | CAT-GRAPHICS | 84 | 92 | 0 | 92 | 571298.78328318 |
| LOC-ST-PO-006 | CAT-INPUT | 83 | 96 | 0 | 96 | 84317.66813499 |
| LOC-ST-PO-006 | CAT-MEMORY | 83 | 79 | 0 | 79 | 53209.30504314 |
| LOC-ST-PO-006 | CAT-MONITOR | 83 | 88 | 0 | 88 | 179750.37423842 |
| LOC-ST-PO-006 | CAT-NETWORK | 83 | 88 | 0 | 88 | 140979.92617364 |
| LOC-ST-PO-006 | CAT-NOTEBOOK | 84 | 81 | 0 | 81 | 639037.29918531 |
| LOC-ST-PO-006 | CAT-PRINTING | 83 | 83 | 0 | 83 | 192102.31257038 |
| LOC-ST-PO-006 | CAT-PROCESSOR | 84 | 80 | 0 | 80 | 204889.31828146 |
| LOC-ST-PO-006 | CAT-STORAGE | 83 | 73 | 0 | 73 | 99977.53874286 |
| LOC-ST-PO-007 | CAT-ACCESSORIES | 83 | 72 | 0 | 72 | 35162.43843995 |
| LOC-ST-PO-007 | CAT-AUDIO | 83 | 84 | 0 | 84 | 77960.22222235 |
| LOC-ST-PO-007 | CAT-DESKTOP | 84 | 84 | 0 | 84 | 568834.60926800 |
| LOC-ST-PO-007 | CAT-GRAPHICS | 84 | 85 | 0 | 85 | 520169.57358885 |
| LOC-ST-PO-007 | CAT-INPUT | 83 | 88 | 0 | 88 | 79355.71583728 |
| LOC-ST-PO-007 | CAT-MEMORY | 83 | 88 | 0 | 88 | 60480.42809681 |
| LOC-ST-PO-007 | CAT-MONITOR | 83 | 79 | 0 | 79 | 153952.63259645 |
| LOC-ST-PO-007 | CAT-NETWORK | 83 | 96 | 0 | 96 | 155269.91342050 |
| LOC-ST-PO-007 | CAT-NOTEBOOK | 84 | 91 | 0 | 91 | 736592.09687699 |
| LOC-ST-PO-007 | CAT-PRINTING | 83 | 76 | 0 | 76 | 185068.05418061 |
| LOC-ST-PO-007 | CAT-PROCESSOR | 84 | 80 | 0 | 80 | 210751.24530712 |
| LOC-ST-PO-007 | CAT-STORAGE | 83 | 77 | 0 | 77 | 101897.70073111 |
| LOC-ST-PO-008 | CAT-ACCESSORIES | 83 | 120 | 0 | 120 | 55498.22876707 |
| LOC-ST-PO-008 | CAT-AUDIO | 83 | 93 | 0 | 93 | 87038.30350842 |
| LOC-ST-PO-008 | CAT-DESKTOP | 84 | 95 | 0 | 95 | 613342.94133864 |
| LOC-ST-PO-008 | CAT-GRAPHICS | 84 | 92 | 0 | 92 | 564290.77782638 |
| LOC-ST-PO-008 | CAT-INPUT | 83 | 94 | 0 | 94 | 81776.63491624 |
| LOC-ST-PO-008 | CAT-MEMORY | 83 | 100 | 0 | 100 | 69062.93695819 |
| LOC-ST-PO-008 | CAT-MONITOR | 83 | 115 | 0 | 115 | 232141.31688255 |
| LOC-ST-PO-008 | CAT-NETWORK | 83 | 91 | 0 | 91 | 141821.22284636 |
| LOC-ST-PO-008 | CAT-NOTEBOOK | 84 | 100 | 0 | 100 | 778154.76670415 |
| LOC-ST-PO-008 | CAT-PRINTING | 83 | 100 | 0 | 100 | 238073.40401056 |
| LOC-ST-PO-008 | CAT-PROCESSOR | 84 | 99 | 0 | 99 | 256896.62469047 |
| LOC-ST-PO-008 | CAT-STORAGE | 83 | 98 | 0 | 98 | 138049.68693699 |
| LOC-ST-PO-009 | CAT-ACCESSORIES | 83 | 94 | 0 | 94 | 44850.45326539 |
| LOC-ST-PO-009 | CAT-AUDIO | 83 | 91 | 0 | 91 | 83106.63130285 |
| LOC-ST-PO-009 | CAT-DESKTOP | 84 | 95 | 0 | 95 | 642134.38496846 |
| LOC-ST-PO-009 | CAT-GRAPHICS | 84 | 110 | 0 | 110 | 698578.88189922 |
| LOC-ST-PO-009 | CAT-INPUT | 83 | 92 | 0 | 92 | 84626.72494519 |
| LOC-ST-PO-009 | CAT-MEMORY | 83 | 100 | 0 | 100 | 70145.15246132 |
| LOC-ST-PO-009 | CAT-MONITOR | 83 | 94 | 0 | 94 | 187873.72351286 |
| LOC-ST-PO-009 | CAT-NETWORK | 83 | 92 | 0 | 92 | 146946.09730254 |
| LOC-ST-PO-009 | CAT-NOTEBOOK | 84 | 90 | 0 | 90 | 711250.91246693 |
| LOC-ST-PO-009 | CAT-PRINTING | 83 | 102 | 0 | 102 | 233001.50417559 |
| LOC-ST-PO-009 | CAT-PROCESSOR | 84 | 93 | 0 | 93 | 246968.84406751 |
| LOC-ST-PO-009 | CAT-STORAGE | 83 | 100 | 0 | 100 | 134587.94869846 |
| LOC-ST-PO-010 | CAT-ACCESSORIES | 83 | 109 | 0 | 109 | 53111.06971092 |
| LOC-ST-PO-010 | CAT-AUDIO | 83 | 108 | 0 | 108 | 102504.39914022 |
| LOC-ST-PO-010 | CAT-DESKTOP | 84 | 115 | 0 | 115 | 759890.48152938 |
| LOC-ST-PO-010 | CAT-GRAPHICS | 84 | 115 | 0 | 115 | 718806.97906360 |
| LOC-ST-PO-010 | CAT-INPUT | 83 | 108 | 0 | 108 | 96820.26818683 |
| LOC-ST-PO-010 | CAT-MEMORY | 83 | 111 | 0 | 111 | 77481.82932442 |
| LOC-ST-PO-010 | CAT-MONITOR | 83 | 109 | 0 | 109 | 222143.39772749 |
| LOC-ST-PO-010 | CAT-NETWORK | 83 | 108 | 0 | 108 | 162729.11171005 |
| LOC-ST-PO-010 | CAT-NOTEBOOK | 84 | 107 | 0 | 107 | 825876.16908424 |
| LOC-ST-PO-010 | CAT-PRINTING | 83 | 119 | 0 | 119 | 286749.99335416 |
| LOC-ST-PO-010 | CAT-PROCESSOR | 84 | 116 | 0 | 116 | 305871.76679376 |
| LOC-ST-PO-010 | CAT-STORAGE | 83 | 113 | 0 | 113 | 152396.36725329 |

### Financeiro, COGS e margem operacional

Definição comercial: pedidos `completed`; gross product value é subtotal dos itens antes de desconto; desconto vem de `applied_discounts`; net product value = gross − descontos; frete cobrado separado; order total = net product value + frete. Pedidos concluídos: 116305; unidades vendidas: 251103; ticket médio BRL 8169.0940560594987318; gross BRL 971645716.62; descontos BRL 22325952.43; net product BRL 949319764.19; frete BRL 786720.00; order total BRL 950106484.19.

Eixo financeiro separado: capturado/liquidado BRL 953974572.04; refunds concluídos BRL 26727257.07; net captured BRL 927247314.97.

COGS canônico permanece integralmente reconhecido nos movimentos `fulfillment`: BRL 725981540.99143845 (todos os pedidos); COGS original dos pedidos completed: BRL 725466564.62350805. Para margem analítica, receita líquida de produto dos pedidos concluídos considera unidades atendidas menos todas as unidades recebidas em devolução, proporcionalmente líquida do desconto alocado. O COGS analítico subtrai apenas o custo histórico de unidades `sellable` reintegradas por `customer_return`: BRL 8010914.36386281; não altera os movimentos originais. Custo de devoluções `non-sellable` preservado como perda identificada: BRL 12296704.23413595, já incluída no COGS analítico BRL 717455650.25964524 e subtraída uma única vez. Resultado: receita BRL 922588975.4450000000000000000; lucro bruto BRL 205133325.1853547600000000000; margem 22.23%. Não representa medida DAX nem definição contábil.

| Canal | Categoria | Unidades líquidas atendidas | Receita produto BRL | COGS fulfillment canônico BRL (todos) | COGS fulfillment completed BRL | Reversão sellable BRL | Perda non-sellable (incluída) BRL | COGS analítico BRL | Lucro bruto BRL | Margem |
|---|---|---|---|---|---|---|---|---|---|---|
| ecommerce | CAT-ACCESSORIES | 6464 | 4962451.05500000000000000000 | 3454843.96112532 | 3448325.08635138 | 56266.49589580 | 95684.91143396 | 3392058.59045558 | 1570392.46454442000000000000 | 0.31645500321099287900 |
| ecommerce | CAT-AUDIO | 6550 | 8616113.87000000000000000000 | 6193197.13343023 | 6184180.02883593 | 69982.26722617 | 124800.80112150 | 6114197.76160976 | 2501916.10839024000000000000 | 0.29037639777504936805 |
| ecommerce | CAT-DESKTOP | 6553 | 60816119.59000000000000000000 | 45213384.93591599 | 45161542.15189129 | 559856.16805865 | 833797.34901368 | 44601685.98383264 | 16214433.60616736000000000000 | 0.26661407724595274527 |
| ecommerce | CAT-GRAPHICS | 6478 | 53790159.81500000000000000000 | 42702811.82112387 | 42612862.19054817 | 573727.24113901 | 924976.70363226 | 42039134.94940916 | 11751024.86559084000000000000 | 0.21846049362943020287 |
| ecommerce | CAT-INPUT | 6332 | 8259713.37000000000000000000 | 5808062.01505236 | 5802563.66970686 | 87276.52101850 | 118343.56019970 | 5715287.14868836 | 2544426.22131164000000000000 | 0.30805260513678575749 |
| ecommerce | CAT-MEMORY | 6350 | 6096776.54500000000000000000 | 4639488.60097645 | 4636372.50832165 | 66282.35064654 | 108419.00510030 | 4570090.15767511 | 1526686.38732489000000000000 | 0.25040878176467430298 |
| ecommerce | CAT-MONITOR | 6520 | 18048363.18500000000000000000 | 14139147.35375920 | 14124355.18651920 | 178550.14125532 | 262293.60623608 | 13945805.04526388 | 4102558.13973612000000000000 | 0.22730915250784388512 |
| ecommerce | CAT-NETWORK | 6428 | 12551430.23000000000000000000 | 9860448.62123295 | 9848035.43670910 | 143736.98481805 | 204970.30153534 | 9704298.45189105 | 2847131.77810895000000000000 | 0.22683723893902009923 |
| ecommerce | CAT-NOTEBOOK | 6549 | 65601634.34000000000000000000 | 52111184.98072688 | 52046774.61948198 | 762763.39508916 | 1105767.08733942 | 51284011.22439282 | 14317623.11560718000000000000 | 0.21825101248852788871 |
| ecommerce | CAT-PRINTING | 6348 | 20924179.11000000000000000000 | 16313559.79885043 | 16297559.32771569 | 280441.84983123 | 454069.63541978 | 16017117.47788446 | 4907061.63211554000000000000 | 0.23451632708354980240 |
| ecommerce | CAT-PROCESSOR | 6550 | 24332698.29500000000000000000 | 18409849.20154335 | 18363335.28492949 | 282447.70978597 | 389768.46156216 | 18080887.57514352 | 6251810.71985648000000000000 | 0.25693043344646788175 |
| ecommerce | CAT-STORAGE | 6425 | 11528562.88500000000000000000 | 8870569.94172292 | 8854851.27411693 | 134219.69465644 | 181199.55814620 | 8720631.57946049 | 2807931.30553951000000000000 | 0.24356299510609036332 |
| marketplace | CAT-ACCESSORIES | 4080 | 3171893.30500000000000000000 | 2175007.55814590 | 2172726.61151459 | 46954.77532987 | 46349.47442039 | 2125771.83618472 | 1046121.46881528000000000000 | 0.32980979125818357248 |
| marketplace | CAT-AUDIO | 4013 | 5056761.30000000000000000000 | 3778729.37800401 | 3774554.46114581 | 50299.82569840 | 72936.59522191 | 3724254.63544741 | 1332506.66455259000000000000 | 0.26350990001299646080 |
| marketplace | CAT-DESKTOP | 4104 | 37705653.79000000000000000000 | 28838637.31148404 | 28794155.21125874 | 453876.48961842 | 539385.89019897 | 28340278.72164032 | 9365375.06835968000000000000 | 0.24838118762028976875 |
| marketplace | CAT-GRAPHICS | 4099 | 32414877.35500000000000000000 | 27053097.78172619 | 27014686.63025999 | 389374.93535113 | 657063.86544368 | 26625311.69490886 | 5789565.66009114000000000000 | 0.17860828522302271102 |
| marketplace | CAT-INPUT | 4073 | 5170553.31500000000000000000 | 3696760.54824909 | 3690334.67036143 | 37786.69332150 | 79812.39435600 | 3652547.97703993 | 1518005.33796007000000000000 | 0.29358663289599403347 |
| marketplace | CAT-MEMORY | 4025 | 3981420.10500000000000000000 | 2914641.20256026 | 2912774.80062266 | 40109.36934327 | 55758.56626753 | 2872665.43127939 | 1108754.67372061000000000000 | 0.27848221099004321223 |
| marketplace | CAT-MONITOR | 3929 | 11393795.81000000000000000000 | 8499546.69048474 | 8485354.39928714 | 95267.77015663 | 165435.54580073 | 8390086.62913051 | 3003709.18086949000000000000 | 0.26362673431739251083 |
| marketplace | CAT-NETWORK | 4014 | 8066828.38500000000000000000 | 6110737.52789183 | 6102242.73682078 | 86739.48111777 | 117248.66269876 | 6015503.25570301 | 2051325.12929699000000000000 | 0.25429140566710965179 |
| marketplace | CAT-NOTEBOOK | 4134 | 43562173.75500000000000000000 | 33146898.73071046 | 33111557.04875106 | 405189.19719033 | 767491.44886550 | 32706367.85156073 | 10855805.90343927000000000000 | 0.24920257571382688683 |
| marketplace | CAT-PRINTING | 3913 | 12691057.71000000000000000000 | 10071454.85808527 | 10067812.07805867 | 199393.94356718 | 268490.64082898 | 9868418.13449149 | 2822639.57550851000000000000 | 0.22241168860845957023 |
| marketplace | CAT-PROCESSOR | 4092 | 15467359.64500000000000000000 | 11397405.21088846 | 11385840.39489686 | 170372.74618050 | 217404.87303448 | 11215467.64871636 | 4251891.99628364000000000000 | 0.27489449355747750184 |
| marketplace | CAT-STORAGE | 3894 | 7042547.04000000000000000000 | 5373992.66410359 | 5365685.65175799 | 66154.65575040 | 117020.67270634 | 5299530.99600759 | 1743016.04399241000000000000 | 0.24749796261103993989 |
| physical | CAT-ACCESSORIES | 9477 | 6803363.70000000000000000000 | 4977518.87003657 | 4977518.87003657 | 52242.24903356 | 71216.82725035 | 4925276.62100301 | 1878087.07899699000000000000 | 0.27605272359568105994 |
| physical | CAT-AUDIO | 9492 | 11797052.81500000000000000000 | 8765303.82262105 | 8765303.82262105 | 71081.99077529 | 96649.11586719 | 8694221.83184576 | 3102830.98315424000000000000 | 0.26301746985560477886 |
| physical | CAT-DESKTOP | 10804 | 91283084.21000000000000000000 | 73615830.69871738 | 73615830.69871738 | 559189.53729065 | 795847.29979459 | 73056641.16142673 | 18226443.04857327000000000000 | 0.19966944813830660992 |
| physical | CAT-GRAPHICS | 10642 | 82415339.85000000000000000000 | 68854352.92884632 | 68854352.92884632 | 611195.78487231 | 900676.87617534 | 68243157.14397401 | 14172182.70602599000000000000 | 0.17196049584725445987 |
| physical | CAT-INPUT | 9504 | 11710316.30500000000000000000 | 8514131.82821598 | 8514131.82821598 | 67569.22273732 | 98772.99394156 | 8446562.60547866 | 3263753.69952134000000000000 | 0.27870756130880958300 |
| physical | CAT-MEMORY | 9498 | 8921807.43000000000000000000 | 6753471.11842793 | 6753471.11842793 | 55590.00225958 | 70117.31649252 | 6697881.11616835 | 2223926.31383165000000000000 | 0.24926858501267270684 |
| physical | CAT-MONITOR | 9574 | 26219341.21000000000000000000 | 20499292.65277021 | 20499292.65277021 | 145654.37817176 | 189385.14294015 | 20353638.27459845 | 5865702.93540155000000000000 | 0.22371664064405949275 |
| physical | CAT-NETWORK | 9606 | 19679982.32000000000000000000 | 14279593.11369561 | 14279593.11369561 | 85872.04484225 | 162088.52012176 | 14193721.06885336 | 5486261.25114664000000000000 | 0.27877368800129287921 |
| physical | CAT-NOTEBOOK | 10668 | 100794184.63000000000000000000 | 84506416.48364528 | 84506416.48364528 | 536517.18531948 | 1064141.54313378 | 83969899.29832580 | 16824285.33167420000000000000 | 0.16691722239168432470 |
| physical | CAT-PRINTING | 9523 | 30020186.26500000000000000000 | 24415205.19535725 | 24415205.19535725 | 254980.64418320 | 448669.09522133 | 24160224.55117405 | 5859961.71382595000000000000 | 0.19520071135128081791 |
| physical | CAT-PROCESSOR | 9777 | 34322815.49500000000000000000 | 27078813.14280075 | 27078813.14280075 | 217346.18921280 | 329594.28621012 | 26861466.95358795 | 7461348.54141205000000000000 | 0.21738742681231926134 |
| physical | CAT-STORAGE | 9493 | 17368377.41000000000000000000 | 12948153.30851033 | 12948153.30851033 | 116604.43311837 | 161055.60640361 | 12831548.87539196 | 4536828.53460804000000000000 | 0.26121199623379441523 |

### Baseline YoY YTD

Comparação de janeiro a setembro de 2025 contra janeiro a setembro de 2026, em calendário local:

| Ano | Pedidos | Concluídos | Unidades | Gross | Descontos | Net produto | Frete | Order total | Captured | Refunds | Net captured | COGS | Gross profit |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2025 | 25732 | 25034 | 53653 | 213451452.78 | 4370625.80 | 209080826.98 | 171126.50 | 209251953.48 | 209251953.48 | 6161775.75 | 203090177.73 | 158130228.23235039 | 50950598.74764961 |
| 2026 | 30000 | 28736 | 62621 | 239596254.54 | 4992491.77 | 234603762.77 | 201030.80 | 234804793.57 | 238672881.42 | 5943004.03 | 232729877.39 | 178364076.86865342 | 56239685.90134658 |

### Categorias e produtos

Resultados por categoria:

| Categoria | Status | Pedidos | Itens | Unidades | Gross BRL | Desconto BRL | Net BRL |
|---|---|---|---|---|---|---|---|
| CAT-ACCESSORIES | cancelled | 491 | 529 | 560 | 437445.22 | 9973.54 | 427471.68 |
| CAT-ACCESSORIES | completed | 18217 | 19292 | 20748 | 15861854.52 | 366292.43 | 15495562.09 |
| CAT-ACCESSORIES | confirmed | 67 | 68 | 72 | 52053.62 | 1061.27 | 50992.35 |
| CAT-AUDIO | cancelled | 523 | 555 | 586 | 781909.94 | 21315.81 | 760594.13 |
| CAT-AUDIO | completed | 18094 | 19176 | 20577 | 26761487.89 | 620502.78 | 26140985.11 |
| CAT-AUDIO | confirmed | 80 | 83 | 86 | 110862.28 | 1835.03 | 109027.25 |
| CAT-DESKTOP | cancelled | 537 | 562 | 586 | 5316865.05 | 110803.14 | 5206061.91 |
| CAT-DESKTOP | completed | 19262 | 20510 | 22014 | 199468558.96 | 4595943.58 | 194872615.38 |
| CAT-DESKTOP | confirmed | 74 | 79 | 88 | 825533.24 | 14021.05 | 811512.19 |
| CAT-GRAPHICS | cancelled | 566 | 596 | 639 | 5190298.70 | 109275.70 | 5081023.00 |
| CAT-GRAPHICS | completed | 19127 | 20343 | 21856 | 177726433.52 | 4105005.05 | 173621428.47 |
| CAT-GRAPHICS | confirmed | 70 | 77 | 83 | 691609.66 | 14060.22 | 677549.44 |
| CAT-INPUT | cancelled | 511 | 542 | 569 | 701336.62 | 14107.14 | 687229.48 |
| CAT-INPUT | completed | 17963 | 19092 | 20468 | 26458066.61 | 601755.07 | 25856311.54 |
| CAT-INPUT | confirmed | 66 | 70 | 75 | 93714.56 | 1424.18 | 92290.38 |
| CAT-MEMORY | cancelled | 465 | 501 | 520 | 496955.47 | 10228.98 | 486726.49 |
| CAT-MEMORY | completed | 17951 | 19063 | 20429 | 20000462.39 | 458912.45 | 19541549.94 |
| CAT-MEMORY | confirmed | 72 | 78 | 88 | 90399.20 | 1721.79 | 88677.41 |
| CAT-MONITOR | cancelled | 500 | 541 | 563 | 1556901.99 | 38801.43 | 1518100.56 |
| CAT-MONITOR | completed | 18117 | 19147 | 20523 | 58423130.80 | 1336419.49 | 57086711.31 |
| CAT-MONITOR | confirmed | 74 | 81 | 95 | 277406.96 | 4360.05 | 273046.91 |
| CAT-NETWORK | cancelled | 516 | 552 | 572 | 1194113.31 | 25334.36 | 1168778.95 |
| CAT-NETWORK | completed | 18088 | 19229 | 20584 | 42327848.32 | 966158.87 | 41361689.45 |
| CAT-NETWORK | confirmed | 78 | 83 | 91 | 182417.56 | 4355.65 | 178061.91 |
| CAT-NOTEBOOK | cancelled | 529 | 558 | 584 | 5833874.53 | 118138.09 | 5715736.44 |
| CAT-NOTEBOOK | completed | 19283 | 20464 | 21954 | 220959847.84 | 4996269.03 | 215963578.81 |
| CAT-NOTEBOOK | confirmed | 73 | 77 | 82 | 827289.39 | 18169.69 | 809119.70 |
| CAT-PRINTING | cancelled | 485 | 512 | 538 | 1810719.55 | 40582.20 | 1770137.35 |
| CAT-PRINTING | completed | 18081 | 19195 | 20556 | 67720245.00 | 1582342.23 | 66137902.77 |
| CAT-PRINTING | confirmed | 78 | 84 | 93 | 323802.76 | 6436.43 | 317366.33 |
| CAT-PROCESSOR | cancelled | 551 | 595 | 615 | 2249588.51 | 49410.99 | 2200177.52 |
| CAT-PROCESSOR | completed | 18462 | 19599 | 21014 | 78085582.11 | 1826814.88 | 76258767.23 |
| CAT-PROCESSOR | confirmed | 74 | 78 | 91 | 316253.10 | 5283.70 | 310969.40 |
| CAT-STORAGE | cancelled | 485 | 514 | 535 | 1015571.75 | 23590.45 | 991981.30 |
| CAT-STORAGE | completed | 17966 | 19038 | 20380 | 37852198.66 | 869536.57 | 36982662.09 |
| CAT-STORAGE | confirmed | 72 | 74 | 80 | 146297.01 | 3110.23 | 143186.78 |

Top 10 produtos por unidades (sem exportar linhas detalhadas):

| SKU sintético | Produto sintético | Categoria | Status | Pedidos | Itens | Unidades | Gross | Desconto | Net |
|---|---|---|---|---|---|---|---|---|---|
| SKU-NOT-00517 | Notebook Prisma 517 | CAT-NOTEBOOK | completed | 281 | 281 | 304 | 3474916.04 | 86437.89 | 3388478.15 |
| SKU-NOT-00793 | Notebook Pulso 793 | CAT-NOTEBOOK | completed | 281 | 281 | 302 | 3579148.97 | 75980.13 | 3503168.84 |
| SKU-NOT-00361 | Notebook Nova 361 | CAT-NOTEBOOK | completed | 278 | 278 | 298 | 3633379.61 | 83110.04 | 3550269.57 |
| SKU-GRA-00964 | Placa Gráfica Pulso 964 | CAT-GRAPHICS | completed | 276 | 276 | 296 | 1577446.54 | 30047.43 | 1547399.11 |
| SKU-DES-00302 | Desktop Orbe 302 | CAT-DESKTOP | completed | 271 | 271 | 295 | 2481575.23 | 62511.23 | 2419064.00 |
| SKU-PRO-00783 | Processador Pulso 783 | CAT-PROCESSOR | completed | 281 | 281 | 295 | 1188925.89 | 26685.82 | 1162240.07 |
| SKU-GRA-00868 | Placa Gráfica Vértice 868 | CAT-GRAPHICS | completed | 267 | 267 | 294 | 2797176.77 | 59501.15 | 2737675.62 |
| SKU-DES-00422 | Desktop Fluxo 422 | CAT-DESKTOP | completed | 268 | 268 | 293 | 3252242.23 | 72773.99 | 3179468.24 |
| SKU-NOT-00757 | Notebook Orbe 757 | CAT-NOTEBOOK | completed | 273 | 273 | 292 | 2553861.79 | 49714.38 | 2504147.41 |
| SKU-DES-00590 | Desktop Prisma 590 | CAT-DESKTOP | completed | 266 | 266 | 291 | 2562190.51 | 60525.18 | 2501665.33 |

## Controle das tabelas operacionais

Contagem total persistida: 3.894.457 linhas. Os valores abaixo foram lidos após COMMIT em conexão nova; todas as tabelas operacionais foram comparadas com as contagens pré-COMMIT e baselines.

| Tabela | Linhas |
|---|---|
| after_sales.return_items | 7129 |
| after_sales.returns | 7129 |
| catalog.brands | 65 |
| catalog.categories | 42 |
| catalog.product_prices | 14000 |
| catalog.product_suppliers | 1600 |
| catalog.products | 1000 |
| core.employee_assignments | 115 |
| core.employee_roles | 7 |
| core.employees | 90 |
| core.stores | 10 |
| crm.business_profiles | 4500 |
| crm.customer_addresses | 52000 |
| crm.customer_contacts | 60000 |
| crm.customers | 45000 |
| crm.individual_profiles | 40500 |
| inventory.stock_locations | 14 |
| inventory.stock_movements | 429462 |
| inventory.stock_positions | 13837 |
| inventory.stock_reservations | 241831 |
| inventory.stock_transfer_items | 0 |
| inventory.stock_transfers | 0 |
| logistics.carriers | 12 |
| logistics.fulfillment_events | 540647 |
| logistics.fulfillment_items | 237742 |
| logistics.fulfillments | 176716 |
| payments.payment_installments | 196731 |
| payments.payment_methods | 5 |
| payments.payments | 127380 |
| payments.refunds | 7201 |
| procurement.goods_receipt_items | 188870 |
| procurement.goods_receipts | 188870 |
| procurement.purchase_order_items | 188869 |
| procurement.purchase_orders | 188869 |
| procurement.suppliers | 45 |
| sales.applied_discounts | 94045 |
| sales.order_status_history | 478483 |
| sales.sales_channels | 4 |
| sales.sales_order_item_cancellations | 0 |
| sales.sales_order_items | 241637 |
| sales.sales_orders | 120000 |

Datas mínimas/máximas dos principais eventos, convertidas para data local `America/Sao_Paulo`:

| Entidade | Mínimo | Máximo |
|---|---|---|
| fulfillment events | 2023-01-02 | 2026-09-30 |
| payments | 2023-01-02 | 2026-09-29 |
| refunds | 2023-01-16 | 2026-09-21 |
| returns | 2023-01-10 | 2026-09-15 |
| sales orders | 2023-01-02 | 2026-09-29 |
| stock movements | 2022-11-08 | 2026-09-30 |

## Qualidade e classificação

CRITICAL FAILS: 0. DISTRIBUTIONAL WARNINGS: 0. DISTRIBUTIONAL FAILS: 0.

| Verificação | Resultado | Medição | Banda |
|---|---|---|---|
| identified_customers_pf | PASS | 90.00 | ['88', '92'] |
| identified_customers_pj | PASS | 10.00 | ['8', '12'] |
| anonymous_physical_orders | PASS | 31.69 | ['25', '35'] |
| digital_anonymous_orders | PASS | 0 | — |
| channel_physical | PASS | 52.15 | ['50', '55'] |
| channel_ecommerce | PASS | 29.50 | ['25', '32'] |
| channel_marketplace_combined | PASS | 18.35 | ['15', '22'] |
| orders_2023 | PASS | 24000 | [20000, 26000] |
| orders_2024 | PASS | 30000 | [25000, 32000] |
| orders_2025 | PASS | 36000 | [32000, 40000] |
| orders_2026 | PASS | 30000 | [27000, 34000] |
| orders_total | PASS | 120000 | [110000, 130000] |
| recurrence_one_order | PASS | 40.30 | ['35', '50'] |
| recurrence_two_to_four | PASS | 38.70 | ['30', '40'] |
| recurrence_five_to_ten | PASS | 16.90 | ['10', '18'] |
| recurrence_eleven_plus | PASS | 4.10 | ['2', '6'] |
| pj_recurrence_higher_than_pf | PASS | — | — |
| pj_to_pf_ticket_ratio | PASS | 1.69 | ['1.5', '3.0'] |
| completed_orders | PASS | 96.92 | ['93', '97'] |
| cancelled_orders | PASS | 2.72 | ['2', '5'] |
| pending_orders | PASS | 0.36 | ['0', '3'] |
| orders_with_discount | PASS | 38.74 | ['30', '45'] |
| average_discount_on_discounted_orders | PASS | 5.84 | ['2', '12'] |
| payment_mix_card | PASS | 48.08 | ['35', '50'] |
| payment_mix_instant | PASS | 42.96 | ['30', '45'] |
| payment_mix_cash | PASS | 8.19 | ['8', '18'] |
| returns_orders_completed_denominator | PASS | 5.95 | ['4', '8'] |
| operational_gross_margin | PASS | 22.23 | ['8', '28'] |
| product_leader_units_share | PASS | 0.12 | ['0', '2'] |
| largest_store_share_of_physical_orders | PASS | 13.74 | — |
| black_friday_november_peak | PASS | — | — |
| black_friday_discount_incidence | PASS | 54.69 | — |
| black_friday_category_mix_shift | PASS | — | — |
| december_elevated | PASS | — | — |
| january_post_peak_lower | PASS | — | — |
| digital_share_trend | PASS | — | — |

As FKs e constraints permaneceram habilitadas. Validações críticas repetidas em conexão nova: PASS. Cutoff comercial até 2026-09-30 e sem Black Friday 2026: PASS.

## Baselines SQL

Consultas em `database/queries/baselines/`, executadas somente após COMMIT e validação pós-COMMIT em conexão read-only:

| Arquivo | Linhas de resultado |
|---|---|
| 00_control_totals.sql | 41 |
| 01_sales_overview.sql | 1 |
| 02_sales_monthly.sql | 272 |
| 03_sales_by_channel.sql | 11 |
| 04_sales_by_store.sql | 20 |
| 05_sales_by_category.sql | 36 |
| 06_product_performance.sql | 2619 |
| 07_customer_recurrence.sql | 8 |
| 08_payments_and_refunds.sql | 17 |
| 09_returns.sql | 31 |
| 10_inventory.sql | 168 |
| 11_cost_and_margin.sql | 36 |
| 12_yoy_ytd.sql | 2 |

| Reconciliation | Resultado |
|---|---|
| 00_control_totals.sql | 41 table counts reconcile |
| 01_sales_overview.sql | completed orders, gross value, and discounts reconcile |
| 08_payments_and_refunds.sql | captured payments and completed refunds reconcile |
| 11_cost_and_margin.sql | canonical fulfillment COGS, adjusted margin COGS, and non-sellable return loss reconcile |
| 12_yoy_ytd.sql | 2025 and 2026 Jan-Sep available |

Todas as tabelas operacionais, totais comerciais, COGS canônico, COGS analítico após devoluções sellable, perdas non-sellable e YTD foram reconciliados ao relatório Portfolio.

## Estado

Portfolio persistido e ativo. Não executar novamente `full --profile portfolio --commit`: o guard recusa database não vazia. Nenhum reset, alteração de schema, Power BI, PBIP, Power Query, modelo semântico ou DAX foi executado.
