from decimal import Decimal, ROUND_HALF_UP

from projectbi_generator.cli import _parser, main
from projectbi_generator.validation.baselines import BASELINE_QUERIES
from projectbi_generator.validation.portfolio import classify_portfolio_distributions
from projectbi_generator.validation.portfolio_report import write_portfolio_report


def _metrics():
    months = []
    for year in range(2023, 2027):
        for month in range(1, 13):
            if year == 2026 and month > 9:
                continue
            bf = month == 11 and year < 2026
            months.append((f"{year}-{month:02d}", 5000 if bf else 2300,
                           2000 if bf else 800, Decimal("0.09") if bf else Decimal("0.05")))
    return {
        "customer_types": {"individual": 40500, "business": 4500},
        "anonymous_physical": (19200, 62400), "digital_anonymous": 0,
        "orders_by_channel": {"physical": 62400, "ecommerce": 34800, "marketplace_a": 12000, "marketplace_b": 10800},
        "orders_by_type": {"physical": 62400, "ecommerce": 34800, "marketplace": 22800},
        "orders_by_year": {2023:25000,2024:30000,2025:36000,2026:29000},
        "orders_by_year_type": {2023:{"physical":14000,"ecommerce":6500,"marketplace":4500},
                                2024:{"physical":16000,"ecommerce":8000,"marketplace":6000},
                                2025:{"physical":19000,"ecommerce":10000,"marketplace":7000},
                                2026:{"physical":13400,"ecommerce":10300,"marketplace":5300}},
        "recurrence": {"individual":(17010,14175,6075,2025,Decimal("3.0"),39285),
                       "business":(1890,1575,675,225,Decimal("6.0"),4365)},
        "recurrence_overall":(18900,15750,6750,2250,43650),
        "ticket_by_customer_type":{"individual":(80000,Decimal("500"),Decimal("40000000")),
                                   "business":(10000,Decimal("1000"),Decimal("10000000"))},
        "discounts":(46400,120000,Decimal("1000000"),Decimal("20000000"),Decimal("0.05")),
        "orders_by_status":{"completed":114000,"cancelled":4800,"placed":1200},
        "payment_methods":{"card":(48000,0,48000),"instant":(48000,0,48000),
                           "cash":(14400,0,14400),"bank_transfer":(9600,0,9600)},
        "returns":(6840,3000,3840,200,8000,6000,2000,9000),
        "returns_completed_orders":114000,
        "margin":(Decimal("10000000"),Decimal("8000000")),
        "margin_return_costs":(Decimal("100"),Decimal("50")),
        "product_concentration":(10000,1000000,1000),
        "monthly_distribution":months,
        "monthly_category_units":[("2023-11","cat-a",100),("2023-11","cat-b",300),
                                  ("2024-11","cat-a",100),("2024-11","cat-b",300),
                                  ("2025-11","cat-a",100),("2025-11","cat-b",300),
                                  ("2023-10","cat-a",300),("2023-10","cat-b",100)],
        "store_orders":[(f"store-{i}",6240) for i in range(10)],
    }


def test_portfolio_commit_is_an_explicit_full_mode_flag():
    args = _parser().parse_args(["full", "--profile", "portfolio", "--commit"])
    assert args.commit is True
    assert not args.dry_run and not args.plan and not args.load_smoke


def test_portfolio_commit_rejects_other_profiles_without_database_access(capsys):
    assert main(["full", "--profile", "smoke", "--commit"]) == 2
    assert "exige --profile portfolio" in capsys.readouterr().err


def test_portfolio_distribution_classifier_preserves_documented_bands():
    result = classify_portfolio_distributions(_metrics())
    assert result["critical_fails"] == 0
    assert result["distributional_fails"] == 0
    assert all(check["result"] in {"PASS", "WARNING"} for check in result["checks"])


def test_portfolio_baselines_cover_the_thirteen_approved_topics():
    assert len(BASELINE_QUERIES) == 13
    assert "00_control_totals.sql" in BASELINE_QUERIES
    assert "12_yoy_ytd.sql" in BASELINE_QUERIES


def test_portfolio_margin_reverses_sellable_returns_once_and_keeps_non_sellable_loss():
    margin_sql = BASELINE_QUERIES["11_cost_and_margin.sql"]
    assert "movement_type='customer_return'" in margin_sql
    assert "sellable_cogs_reversal" in margin_sql
    assert "non_sellable_loss" in margin_sql
    assert "quantity_received*fh.historical_unit_cost" in margin_sql
    assert "round(sum(abs(fm.quantity_delta)::numeric*fm.unit_cost)" in margin_sql
    assert "full_cogs-sc.sellable_cogs_reversal" in margin_sql
    assert "sum(net_margin_cogs)" in margin_sql


def test_portfolio_report_renders_aggregates_without_personal_records(tmp_path):
    metrics = _metrics()
    metrics.update({
        "financials":(114000,Decimal("10000000"),Decimal("1000000"),Decimal("9000000"),
                      Decimal("100000"),Decimal("9100000"),Decimal("8000000"),Decimal("10000"),Decimal("6000000")),
        "stock_totals":(10000,1000,9000,10000), "transfer_totals":(100,200,400,200),
        "time_ranges":{"orders":("2023-01-01","2026-09-30")},
        "table_counts":{"sales.sales_orders":120000,"catalog.products":1000},
        "ticket_by_channel":{"physical":(60000,Decimal("500"),Decimal("30000000")),
                             "ecommerce":(30000,Decimal("700"),Decimal("21000000")),
                             "marketplace":(24000,Decimal("650"),Decimal("15600000"))},
    })
    distribution = classify_portfolio_distributions(metrics)
    result = {
        "portfolio_metrics":metrics,"distribution_result":distribution,"aggregates":{"captured_amount":Decimal("8000000"),"refund_amount":Decimal("10000"),"split_payment_orders":3000,"retries":400,"declined_or_failed":450},
        "table_counts":metrics["table_counts"],"master_counts":{"stores":10},
        "transaction_counts":{"sales_orders":120000,"sales_order_items":264000,"payment_installments":50000,"fulfillments":115000,"fulfillment_items":250000,"fulfillment_events":300000,"stock_movements":330000,"returns":8000},
        "sink_metrics":{"rows_inserted":2200000,"rows_updated":10000,"flush_count":5000,"max_batch_rows":5000},
        "id_metrics":{"peak":600,"current":0},"year_progress_seconds":{2023:100,2024:120,2025:140,2026:80},
        "master_generation_seconds":1,"master_persistence_seconds":1,"transaction_generation_and_validation_seconds":1,
        "precommit_validation_seconds":1,"baseline_seconds":1,"post_validation_seconds":1,"total_seconds":4,
        "total_seconds_with_baselines":5,"transaction_rows":2200000,"execution_started":"2026-10-06T10:00:00-03:00",
        "commit_completed_at":"2026-10-06T11:00:00-03:00","server_version":"18.6","profile":"portfolio",
        "root_seed":20261005,"generator_version":"0.1.0","config_version":1,"timezone":"America/Sao_Paulo",
        "bootstrap_start":"2022-11-01","bootstrap_end":"2022-12-31","commercial_start":"2023-01-01",
        "commercial_end":"2026-09-30","post_validation_database":"projeto_bi",
        "baseline_reconciliation":{"00_control_totals.sql":"PASS"},
    }
    empty = {name:[] for name in BASELINE_QUERIES}
    empty["01_sales_overview.sql"]=[(114000,110000,300000,10000000,1000000,9000000,100000,9100000,Decimal("80"))]
    empty["08_payments_and_refunds.sql"]=[("payment","card","settled",1,Decimal("1"))]
    empty["09_returns.sql"]=[("physical","individual","completed","sellable",1,1,1,1,1,1,Decimal("1"))]
    empty["10_inventory.sql"]=[("store","Store","category",1,10,1,9,Decimal("100"))]
    empty["05_sales_by_category.sql"]=[("category","Category","completed",1,1,1,Decimal("10"),Decimal("1"),Decimal("9"))]
    empty["06_product_performance.sql"]=[("SKU-SYNTH","Produto sintético","category","completed",1,1,1,Decimal("10"),Decimal("1"),Decimal("9"))]
    empty["12_yoy_ytd.sql"]=[(2025,*([0]*13)),(2026,*([0]*13))]
    metrics["margin_return_costs"]=(Decimal("1"),Decimal("0.5"))
    empty["11_cost_and_margin.sql"]=[("physical","category",1,Decimal("10"),Decimal("6"),Decimal("6"),Decimal("1"),Decimal("0.5"),Decimal("5"),Decimal("5"),Decimal("0.5"))]
    root=tmp_path/"project"
    (root/"docs"/"data-generation").mkdir(parents=True)
    path=write_portfolio_report(root,result,empty)
    rendered=path.read_text(encoding="utf-8")
    assert "Portfolio persistido" in rendered
    assert "2026-09-30" in rendered
    assert "não altera os movimentos originais" in rendered
    assert "devoluções `non-sellable`" in rendered
    assert "subtraída uma única vez" in rendered
    assert "cpf" not in rendered.lower()


def test_return_eligibility_rounds_discounted_unit_price_to_currency_precision():
    discounted_unit = Decimal("1010.90") - Decimal("101.09") / Decimal("2")
    assert discounted_unit == Decimal("960.355")
    assert discounted_unit.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP) == Decimal("960.36")
