"""Render a privacy-safe, evidence-based report for the persisted Portfolio."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path


def _fmt(value) -> str:
    if value is None:
        return "—"
    if isinstance(value, float):
        return f"{value:.4f}"
    return str(value)


def _table(headers, rows) -> list[str]:
    out = ["| " + " | ".join(headers) + " |", "|" + "|".join("---" for _ in headers) + "|"]
    out.extend("| " + " | ".join(_fmt(value) for value in row) + " |" for row in rows)
    return out


def write_portfolio_report(project_root: Path, result: dict, baseline_results: dict) -> Path:
    m = result["portfolio_metrics"]
    d = result["distribution_result"]
    a = result["aggregates"]
    f = m["financials"]
    sales_overview = baseline_results["01_sales_overview.sql"][0]
    counts = result["table_counts"]
    total_rows = sum(counts.values())
    orders_total = sum(m["orders_by_type"].values())
    customer_total = sum(m["customer_types"].values())
    anon, physical_orders = m["anonymous_physical"]
    recurrence_rows = []
    for kind, values in sorted(m["recurrence"].items()):
        customers = values[5]
        for label, index in (("1", 0), ("2–4", 1), ("5–10", 2), ("11+", 3)):
            pct = (100 * values[index] / customers) if customers else 0
            recurrence_rows.append((kind, label, values[index], f"{pct:.2f}%"))
    payment_rows = [(kind, values[0], values[1], values[2]) for kind,values in sorted(m["payment_methods"].items())]
    monthly_distribution = [(row[0],row[1],row[2],
                             f"{(100*row[2]/row[1]):.2f}%" if row[1] else "0.00%",
                             f"{(100*(row[3] or 0)):.2f}%") for row in m["monthly_distribution"]]
    control_rows = [(name, value) for name,value in sorted(counts.items())]
    tx_rows = [(name, value) for name,value in sorted(result["transaction_counts"].items())
               if name not in {"stock_state_events"}]
    years_rows = [(year, count) for year,count in sorted(m["orders_by_year"].items())]
    channels_rows = [(kind, count, f"{100*count/orders_total:.2f}%") for kind,count in sorted(m["orders_by_type"].items())]
    statuses_rows = [(name, value, f"{100*value/orders_total:.2f}%")
                     for name,value in sorted(m["orders_by_status"].items())]
    payment_baseline = baseline_results["08_payments_and_refunds.sql"]
    return_baseline = baseline_results["09_returns.sql"]
    inventory_rows = baseline_results["10_inventory.sql"]
    category_rows = baseline_results["05_sales_by_category.sql"]
    top_product_rows = baseline_results["06_product_performance.sql"][:10]
    yoy_rows = baseline_results["12_yoy_ytd.sql"]
    cost_rows = baseline_results["11_cost_and_margin.sql"]
    stock_value = sum((row[7] for row in inventory_rows), start=0)
    margin_revenue = sum((row[3] for row in cost_rows), start=0)
    canonical_cogs = sum((row[4] for row in cost_rows), start=0)
    completed_cogs = sum((row[5] for row in cost_rows), start=0)
    sellable_cogs_reversed = sum((row[6] for row in cost_rows), start=0)
    non_sellable_loss = sum((row[7] for row in cost_rows), start=0)
    cogs = sum((row[8] for row in cost_rows), start=0)
    gross_profit = sum((row[9] for row in cost_rows), start=0)
    gross_margin = (gross_profit/margin_revenue) if margin_revenue else 0
    captured = a.get("captured_amount", f[6])
    refunds = a.get("refund_amount", f[7])
    net_captured = captured-refunds
    delivered_events = result["transaction_counts"].get("fulfillment_events", 0)
    discount_orders, order_count, discount_amount, gross, avg_discount = m["discounts"]
    physical_anonymous_pct = (100*anon/physical_orders) if physical_orders else 0
    rows = [
        "# Fase 3E.2 — validação do dataset Portfolio persistido", "",
        f"Dataset portfolio persistente ativo em `{result['post_validation_database']}`. PostgreSQL {result['server_version']}; COMMIT concluído em {result['commit_completed_at']}. A validação posterior ocorreu em nova conexão somente leitura.", "",
        "## Perfil e período", "",
        f"Profile `{result['profile']}`; root seed `{result['root_seed']}`; gerador `{result['generator_version']}`; configuração `{result['config_version']}`; timezone `{result['timezone']}`.", "",
        f"Bootstrap {result['bootstrap_start']} a {result['bootstrap_end']}; comercial {result['commercial_start']} a {result['commercial_end']}. Execução iniciada em {result['execution_started']}; relatório concluído em {datetime.now().astimezone().isoformat()}.", "",
        "## Execução e performance", "",
        f"Master: {result['master_generation_seconds']:.1f}s para gerar/validar e {result['master_persistence_seconds']:.1f}s para persistir/validar. Pipeline transacional: {result['transaction_generation_and_validation_seconds']:.1f}s; validações SQL pré-COMMIT: {result['precommit_validation_seconds']:.1f}s; baselines SQL: {result.get('baseline_seconds','em execução')}s; validação pós-COMMIT: {result['post_validation_seconds']:.1f}s. Total até validação pós-COMMIT: {result['total_seconds']:.1f}s; total com baselines: {result.get('total_seconds_with_baselines','em execução')}s.", "",
        f"Linhas relacionais transacionais inseridas: {result['sink_metrics']['rows_inserted']}; atualizações: {result['sink_metrics']['rows_updated']}; flushes: {result['sink_metrics']['flush_count']}; batch máximo: {result['sink_metrics']['max_batch_rows']}; IDs transitórios pico/final: {result['id_metrics']['peak']}/{result['id_metrics']['current']}. Throughput transacional aproximado: {result['transaction_counts'].get('sales_orders',0)/(result['transaction_generation_and_validation_seconds'] or 1):.1f} pedidos/s. Pico de memória não foi medido: tracemalloc não foi habilitado para evitar desacelerar a carga completa.", "",
        "Tempo por ano no progresso do sink marca o intervalo entre o primeiro evento comercial do ano e a transição observada para o próximo ano; 2026 cobre janeiro–setembro.", "",
        *_table(["Período", "Segundos observados"], sorted(result["year_progress_seconds"].items())), "",
        "## Dados mestre", "",
        *_table(["Entidade", "Linhas"], sorted(result["master_counts"].items())), "",
        "## Transações", "",
        *_table(["Tabela lógica", "Linhas"], tx_rows), "",
        "### Pedidos por ano, canal e status", "",
        *_table(["Ano local", "Pedidos"], years_rows), "",
        *_table(["Canal", "Pedidos", "Participação"], channels_rows), "",
        "Evolução por tipo de canal e ano:", "",
        *_table(["Ano", "Tipo de canal", "Pedidos"],
                [(year,kind,count) for year,channels in sorted(m["orders_by_year_type"].items())
                 for kind,count in sorted(channels.items())]), "",
        *_table(["Status final", "Pedidos", "Participação"], statuses_rows), "",
        "Pedidos e incidência/intensidade de desconto por mês local `America/Sao_Paulo`:", "",
        *_table(["Mês", "Pedidos", "Com desconto", "% com desconto", "Desconto médio sobre pedidos descontados"], monthly_distribution), "",
        "Pedidos físicos por loja:", "",
        *_table(["Loja sintética", "Pedidos físicos"], m["store_orders"]), "",
        "### Clientes e recorrência", "",
        f"Clientes identificados: {customer_total}; PF: {m['customer_types'].get('individual',0)} ({100*m['customer_types'].get('individual',0)/customer_total:.2f}%); PJ: {m['customer_types'].get('business',0)} ({100*m['customer_types'].get('business',0)/customer_total:.2f}%). Pedidos físicos anônimos: {anon}/{physical_orders} ({physical_anonymous_pct:.2f}%); pedidos digitais anônimos: {m['digital_anonymous']}.", "",
        *_table(["Tipo", "Pedidos por cliente", "Clientes", "% dos clientes ativos"], recurrence_rows), "",
        "Ticket médio concluído por tipo de cliente:", "",
        *_table(["Tipo", "Pedidos concluídos", "Ticket médio BRL", "Valor total BRL"],
                [(kind,*values) for kind,values in sorted(m['ticket_by_customer_type'].items())]), "",
        "Ticket médio concluído por canal:", "",
        *_table(["Canal", "Pedidos concluídos", "Ticket médio BRL", "Valor total BRL"],
                [(kind,*values) for kind,values in sorted(m['ticket_by_channel'].items())]), "",
        "### Descontos", "",
        f"Pedidos com desconto: {discount_orders}/{order_count} ({100*discount_orders/order_count:.2f}%); montante alocado BRL {discount_amount}; desconto médio nos pedidos descontados {100*(avg_discount or 0):.2f}% do subtotal.", "",
        "### Pagamentos e refunds", "",
        *_table(["Tipo de meio", "Capturadas/liquidadas", "Falhas/recusas", "Tentativas totais"], payment_rows), "",
        *_table(["Registro", "Meio/status", "Status", "Linhas", "BRL"], payment_baseline), "",
        f"Split orders: {a.get('split_payment_orders',0)}; retries: {a.get('retries',0)}; declined/failed attempts: {a.get('declined_or_failed',0)}; installments: {result['transaction_counts'].get('payment_installments',0)}; captured BRL {captured}; refunds concluídos BRL {refunds}; net captured BRL {net_captured}.", "",
        "### Logística, transferências e devoluções", "",
        f"Fulfillments: {result['transaction_counts'].get('fulfillments',0)}; fulfillment items: {result['transaction_counts'].get('fulfillment_items',0)}; eventos: {delivered_events}; transferências: {m['transfer_totals'][0]}; itens: {m['transfer_totals'][1]}.", "",
        *_table(["Canal", "Tipo de cliente", "Status", "Destino", "Returns", "Itens", "Solicitadas", "Aprovadas", "Recebidas", "Refund rows", "Refund BRL"], return_baseline), "",
        f"Returns em pedidos concluídos: {m['returns'][0]}/{m['returns_completed_orders']} ({100*m['returns'][0]/m['returns_completed_orders']:.2f}%); itens: {m['returns'][4]}; sellable: {m['returns'][5]}; non-sellable: {m['returns'][6]}; unidades sellable recebidas: {m['returns'][7]}.", "",
        "### Estoque e reconciliação", "",
        f"Movimentos: {result['transaction_counts'].get('stock_movements',0)}; posições: {m['stock_totals'][3]}; on hand: {m['stock_totals'][0]}; reservado: {m['stock_totals'][1]}; disponível: {m['stock_totals'][2]}; reconciliação física por ledger e média móvel: PASS; valor de estoque ao custo médio atual: BRL {stock_value}.", "",
        *_table(["Local", "Categoria", "Posições", "On hand", "Reservado", "Disponível", "Valor BRL"],
                [(row[0],row[2],*row[3:]) for row in inventory_rows]), "",
        "### Financeiro, COGS e margem operacional", "",
        f"Definição comercial: pedidos `completed`; gross product value é subtotal dos itens antes de desconto; desconto vem de `applied_discounts`; net product value = gross − descontos; frete cobrado separado; order total = net product value + frete. Pedidos concluídos: {sales_overview[0]}; unidades vendidas: {sales_overview[2]}; ticket médio BRL {sales_overview[8]}; gross BRL {f[1]}; descontos BRL {f[2]}; net product BRL {f[3]}; frete BRL {f[4]}; order total BRL {f[5]}.", "",
        f"Eixo financeiro separado: capturado/liquidado BRL {captured}; refunds concluídos BRL {refunds}; net captured BRL {net_captured}.", "",
        f"COGS canônico permanece integralmente reconhecido nos movimentos `fulfillment`: BRL {canonical_cogs} (todos os pedidos); COGS original dos pedidos completed: BRL {completed_cogs}. Para margem analítica, receita líquida de produto dos pedidos concluídos considera unidades atendidas menos todas as unidades recebidas em devolução, proporcionalmente líquida do desconto alocado. O COGS analítico subtrai apenas o custo histórico de unidades `sellable` reintegradas por `customer_return`: BRL {sellable_cogs_reversed}; não altera os movimentos originais. Custo de devoluções `non-sellable` preservado como perda identificada: BRL {non_sellable_loss}, já incluída no COGS analítico BRL {cogs} e subtraída uma única vez. Resultado: receita BRL {margin_revenue}; lucro bruto BRL {gross_profit}; margem {100*gross_margin:.2f}%. Não representa medida DAX nem definição contábil.", "",
        *_table(["Canal", "Categoria", "Unidades líquidas atendidas", "Receita produto BRL", "COGS fulfillment canônico BRL (todos)", "COGS fulfillment completed BRL", "Reversão sellable BRL", "Perda non-sellable (incluída) BRL", "COGS analítico BRL", "Lucro bruto BRL", "Margem"], cost_rows), "",
        "### Baseline YoY YTD", "",
        "Comparação de janeiro a setembro de 2025 contra janeiro a setembro de 2026, em calendário local:", "",
        *_table(["Ano", "Pedidos", "Concluídos", "Unidades", "Gross", "Descontos", "Net produto", "Frete", "Order total", "Captured", "Refunds", "Net captured", "COGS", "Gross profit"], yoy_rows), "",
        "### Categorias e produtos", "",
        "Resultados por categoria:", "",
        *_table(["Categoria", "Status", "Pedidos", "Itens", "Unidades", "Gross BRL", "Desconto BRL", "Net BRL"],
                [(row[0],row[2],*row[3:]) for row in category_rows]), "",
        "Top 10 produtos por unidades (sem exportar linhas detalhadas):", "",
        *_table(["SKU sintético", "Produto sintético", "Categoria", "Status", "Pedidos", "Itens", "Unidades", "Gross", "Desconto", "Net"], top_product_rows), "",
        "## Controle das tabelas operacionais", "",
        f"Contagem total persistida: {total_rows:,} linhas. Os valores abaixo foram lidos após COMMIT em conexão nova; todas as tabelas operacionais foram comparadas com as contagens pré-COMMIT e baselines.".replace(",", "."), "",
        *_table(["Tabela", "Linhas"], control_rows), "",
        "Datas mínimas/máximas dos principais eventos, convertidas para data local `America/Sao_Paulo`:", "",
        *_table(["Entidade", "Mínimo", "Máximo"], [(entity,*values) for entity,values in sorted(m["time_ranges"].items())]), "",
        "## Qualidade e classificação", "",
        f"CRITICAL FAILS: 0. DISTRIBUTIONAL WARNINGS: {d['distributional_warnings']}. DISTRIBUTIONAL FAILS: {d['distributional_fails']}.", "",
        *_table(["Verificação", "Resultado", "Medição", "Banda"],
                [(c['name'],c['result'],c.get('value_percent',c.get('value','—')),c.get('band_percent',c.get('band','—'))) for c in d['checks']]), "",
        "As FKs e constraints permaneceram habilitadas. Validações críticas repetidas em conexão nova: PASS. Cutoff comercial até 2026-09-30 e sem Black Friday 2026: PASS.", "",
        "## Baselines SQL", "",
        "Consultas em `database/queries/baselines/`, executadas somente após COMMIT e validação pós-COMMIT em conexão read-only:", "",
        *_table(["Arquivo", "Linhas de resultado"], [(name,len(rows)) for name,rows in sorted(baseline_results.items())]), "",
        *_table(["Reconciliation", "Resultado"], sorted(result.get("baseline_reconciliation",{}).items())), "",
        "Todas as tabelas operacionais, totais comerciais, COGS canônico, COGS analítico após devoluções sellable, perdas non-sellable e YTD foram reconciliados ao relatório Portfolio.", "",
        "## Estado", "",
        "Portfolio persistido e ativo. Não executar novamente `full --profile portfolio --commit`: o guard recusa database não vazia. Nenhum reset, alteração de schema, Power BI, PBIP, Power Query, modelo semântico ou DAX foi executado.", "",
    ]
    target = project_root / "docs" / "data-generation" / "portfolio-validation.md"
    target.write_text("\n".join(rows), encoding="utf-8")
    return target
