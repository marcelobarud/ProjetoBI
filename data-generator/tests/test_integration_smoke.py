import os
from dataclasses import replace
from pathlib import Path

import pytest

from projectbi_generator.config import load_config
import projectbi_generator.database as database_module
from projectbi_generator.database import connection_settings, run_rollback_smoke, run_rollback_incremental_full_smoke
from projectbi_generator.generators.master import generate_master_data
from projectbi_generator.validation.baselines import BASELINE_QUERIES, validate_baseline_results
from projectbi_generator.validation.portfolio import collect_portfolio_metrics


@pytest.mark.integration
@pytest.mark.skipif(os.getenv("PROJECTBI_RUN_INTEGRATION") != "1", reason="Defina PROJECTBI_RUN_INTEGRATION=1 para o PostgreSQL local aprovado.")
def test_postgresql_master_smoke_rolls_back_every_table():
    config = load_config("smoke")
    data = generate_master_data(config)
    settings = connection_settings(__import__("pathlib").Path(__file__).resolve().parents[2])
    result = run_rollback_smoke(settings, config, data)
    assert result["server_version"].startswith("18.")
    assert result["id_map_tables"] == 19
    assert sum(result["remaining"].values()) == 0
    assert result["counts"] == config.volumes


@pytest.mark.integration
@pytest.mark.skipif(os.getenv("PROJECTBI_RUN_INTEGRATION") != "1", reason="Defina PROJECTBI_RUN_INTEGRATION=1 para o PostgreSQL local aprovado.")
def test_postgresql_transaction_smoke_rolls_back_every_table():
    config = load_config("smoke")
    settings = connection_settings(__import__("pathlib").Path(__file__).resolve().parents[2])
    result = run_rollback_incremental_full_smoke(settings, config, include_completion=False)
    assert result["server_version"].startswith("18.")
    assert result["master_id_maps"] == 19
    assert result["id_metrics"]["current_transaction_id_entries"] == 0
    assert sum(result["remaining"].values()) == 0
    assert result["counts"]["sales_orders"] == 300
    assert result["counts"]["sales_order_items"] == 630
    assert len(result["sql_counts"]) == 23  # 22 tabelas transacionais incluindo cancelamentos, mais custo realizado


@pytest.mark.integration
@pytest.mark.skipif(os.getenv("PROJECTBI_RUN_INTEGRATION") != "1", reason="Defina PROJECTBI_RUN_INTEGRATION=1 para o PostgreSQL local aprovado.")
def test_postgresql_full_smoke_rolls_back_every_table():
    config = load_config("smoke")
    settings = connection_settings(__import__("pathlib").Path(__file__).resolve().parents[2])
    result = run_rollback_incremental_full_smoke(settings, config)
    assert result["server_version"].startswith("18.")
    assert result["master_id_maps"] == 19
    assert result["id_metrics"]["current_transaction_id_entries"] == 0, result["id_metrics"]["current_transaction_id_entries_by_type"]
    assert len(result["sql_counts"]) == 23  # 22 tabelas transacionais mais custo realizado
    assert result["counts"]["payments"] == 314
    assert result["counts"]["stock_transfers"] == 2
    assert result["counts"]["returns"] == 8
    assert sum(result["remaining"].values()) == 0


@pytest.mark.integration
@pytest.mark.skipif(os.getenv("PROJECTBI_RUN_INTEGRATION") != "1", reason="Defina PROJECTBI_RUN_INTEGRATION=1 para o PostgreSQL local aprovado.")
def test_postgresql_smoke_baselines_and_portfolio_metrics_reconcile_roll_back(monkeypatch):
    config = load_config("smoke")
    settings = connection_settings(Path(__file__).resolve().parents[2])
    original_analyze = database_module.analyze_tables
    validation = {}

    def analyze_and_validate_baselines(connection, tables):
        original_analyze(connection, tables)
        results = {}
        for filename, statement in BASELINE_QUERIES.items():
            cursor = connection.execute(statement)
            rows = cursor.fetchall()
            assert rows and cursor.description
            results[filename] = rows

        metrics = collect_portfolio_metrics(connection, config.timezone.key)
        validation.update(validate_baseline_results(results, metrics))
        validation["control_table_rows"] = len(results["00_control_totals.sql"])
        validation["baseline_query_count"] = len(results)
        validation["ytd_years"] = tuple(row[0] for row in results["12_yoy_ytd.sql"])

    monkeypatch.setattr(database_module, "analyze_tables", analyze_and_validate_baselines)
    result = run_rollback_incremental_full_smoke(settings, config)

    assert validation["baseline_query_count"] == 13
    assert validation["control_table_rows"] == 41
    assert validation["00_control_totals.sql"] == "41 table counts reconcile"
    assert validation["11_cost_and_margin.sql"].startswith("canonical fulfillment COGS")
    assert set(validation["ytd_years"]) == {2025, 2026}
    assert len(result["sql_invariant_counts"]) == 39
    assert all(count == 0 for count in result["sql_invariant_counts"].values())
    assert len(result["remaining"]) == 41
    assert sum(result["remaining"].values()) == 0


@pytest.mark.integration
@pytest.mark.skipif(os.getenv("PROJECTBI_RUN_INTEGRATION") != "1", reason="Defina PROJECTBI_RUN_INTEGRATION=1 para o PostgreSQL local aprovado.")
def test_postgresql_portfolio_master_with_1000_order_multibatch_fixture_rolls_back():
    config = load_config("portfolio")
    generation = {**config.generation, "sales_orders": 1000, "estimated_order_items": 2200,
                  "estimated_transaction_rows": 20000}
    config = replace(config, generation=generation, order_plan={"mode": "intentions"})
    settings = connection_settings(Path(__file__).resolve().parents[2])
    result = run_rollback_incremental_full_smoke(settings, config)
    assert result["server_version"].startswith("18.")
    # The Portfolio target counts attempted intentions; physical stock gating
    # can reject some, so the multibatch fixture validates a bounded target.
    assert 0 < result["counts"]["sales_orders"] <= generation["sales_orders"]
    assert result["sink_metrics"]["flush_count"] >= 100
    assert result["sink_metrics"]["rows_inserted"] > 10000
    assert result["sink_metrics"]["max_batch_rows"] <= config.batch_size
    assert result["id_metrics"]["current_transaction_id_entries"] == 0
    assert result["id_metrics"]["max_transaction_id_entries"] < result["sink_metrics"]["rows_inserted"] // 10
    assert sum(result["remaining"].values()) == 0


@pytest.mark.integration
@pytest.mark.skipif(os.getenv("PROJECTBI_RUN_INTEGRATION") != "1", reason="Defina PROJECTBI_RUN_INTEGRATION=1 para o PostgreSQL local aprovado.")
def test_postgresql_portfolio_10000_partial_cancellation_and_split_payments_roll_back():
    config = load_config("portfolio")
    generation = {**config.generation, "sales_orders": 10000, "estimated_order_items": 22000,
                  "estimated_transaction_rows": 180000}
    config = replace(config, generation=generation)
    settings = connection_settings(Path(__file__).resolve().parents[2])
    result = run_rollback_incremental_full_smoke(settings, config)
    checks = result["cancellation_checks"]
    assert result["server_version"].startswith("18.")
    assert result["counts"]["sales_order_item_cancellations"] > 0
    assert checks["partially_fulfilled_cancellation_rows"] > 0
    assert checks["cancellations_with_completed_refund"] > 0
    assert checks["split_payment_orders"] > 0
    assert checks["over_limit_insert_rejected"] is True
    assert checks["split_cancellation_refund_payments"] == 2
    assert str(checks["split_cancellation_refund_amount"]) == "90.00"
    assert result["aggregates"]["cancelled_units"] > 0
    assert result["aggregates"]["gross_cancelled_amount"] >= result["aggregates"]["net_cancelled_amount"]
    assert result["id_metrics"]["current_transaction_id_entries"] == 0
    assert sum(result["remaining"].values()) == 0


@pytest.mark.integration
@pytest.mark.skipif(os.getenv("PROJECTBI_RUN_INTEGRATION") != "1", reason="Defina PROJECTBI_RUN_INTEGRATION=1 para o PostgreSQL local aprovado.")
def test_postgresql_portfolio_supply_policy_with_transfers_rolls_back():
    config = load_config("portfolio")
    generation = {
        **config.generation,
        "sales_orders": 10000,
        "estimated_order_items": 22000,
        "estimated_transaction_rows": 180000,
        "bootstrap_location_balance": 65,
        "supply_transfer_enabled": 1,
        "coverage_replenishment_enabled": 1,
        "coverage_safety_units": 2,
    }
    config = replace(config, generation=generation)
    settings = connection_settings(Path(__file__).resolve().parents[2])
    result = run_rollback_incremental_full_smoke(settings, config)

    assert result["server_version"].startswith("18.")
    assert result["counts"]["sales_orders"] > 0
    assert result["counts"]["stock_transfers"] > 0
    assert result["counts"]["stock_transfer_items"] > 0
    assert result["counts"]["stock_movements"] > 0
    assert result["cancellation_checks"]["over_limit_insert_rejected"] is True
    assert result["cancellation_checks"]["split_cancellation_refund_payments"] == 2
    assert str(result["cancellation_checks"]["split_cancellation_refund_amount"]) == "90.00"
    assert result["id_metrics"]["current_transaction_id_entries"] == 0, result["id_metrics"]["current_transaction_id_entries_by_type"]
    assert result["sink_metrics"]["max_batch_rows"] <= config.batch_size
    assert len(result["remaining"]) == 41
    assert sum(result["remaining"].values()) == 0
