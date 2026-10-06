import os
from dataclasses import replace
from pathlib import Path

import pytest

from projectbi_generator.config import load_config
from projectbi_generator.database import connection_settings, run_rollback_smoke, run_rollback_incremental_full_smoke
from projectbi_generator.generators.master import generate_master_data


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
    assert len(result["sql_counts"]) == 22  # 21 tabelas, incluindo as tabelas 3D vazias, mais custo realizado


@pytest.mark.integration
@pytest.mark.skipif(os.getenv("PROJECTBI_RUN_INTEGRATION") != "1", reason="Defina PROJECTBI_RUN_INTEGRATION=1 para o PostgreSQL local aprovado.")
def test_postgresql_full_smoke_rolls_back_every_table():
    config = load_config("smoke")
    settings = connection_settings(__import__("pathlib").Path(__file__).resolve().parents[2])
    result = run_rollback_incremental_full_smoke(settings, config)
    assert result["server_version"].startswith("18.")
    assert result["master_id_maps"] == 19
    assert result["id_metrics"]["current_transaction_id_entries"] == 0
    assert len(result["sql_counts"]) == 22  # 21 tabelas transacionais mais custo realizado
    assert result["counts"]["payments"] == 314
    assert result["counts"]["stock_transfers"] == 2
    assert result["counts"]["returns"] == 8
    assert sum(result["remaining"].values()) == 0


@pytest.mark.integration
@pytest.mark.skipif(os.getenv("PROJECTBI_RUN_INTEGRATION") != "1", reason="Defina PROJECTBI_RUN_INTEGRATION=1 para o PostgreSQL local aprovado.")
def test_postgresql_portfolio_master_with_1000_order_multibatch_fixture_rolls_back():
    config = load_config("portfolio")
    generation = {**config.generation, "sales_orders": 1000, "estimated_order_items": 2200,
                  "estimated_transaction_rows": 20000}
    config = replace(config, generation=generation)
    settings = connection_settings(Path(__file__).resolve().parents[2])
    result = run_rollback_incremental_full_smoke(settings, config)
    assert result["server_version"].startswith("18.")
    assert result["counts"]["sales_orders"] == 1000
    assert result["sink_metrics"]["flush_count"] >= 100
    assert result["sink_metrics"]["rows_inserted"] > 10000
    assert result["sink_metrics"]["max_batch_rows"] <= config.batch_size
    assert result["id_metrics"]["current_transaction_id_entries"] == 0
    assert result["id_metrics"]["max_transaction_id_entries"] < result["sink_metrics"]["rows_inserted"] // 10
    assert sum(result["remaining"].values()) == 0
