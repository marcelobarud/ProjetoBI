import os

import pytest

from projectbi_generator.config import load_config
from projectbi_generator.database import connection_settings, run_rollback_full_smoke, run_rollback_smoke, run_rollback_transaction_smoke
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
    result = run_rollback_transaction_smoke(settings, config)
    assert result["server_version"].startswith("18.")
    assert result["id_map_tables"] == 19
    assert result["transaction_id_maps"] == 9
    assert sum(result["remaining"].values()) == 0
    assert result["summary"]["sales_orders"] == 300
    assert result["summary"]["sales_order_items"] == 630
    assert len(result["sql_counts"]) == 14  # 13 tabelas mais custo realizado


@pytest.mark.integration
@pytest.mark.skipif(os.getenv("PROJECTBI_RUN_INTEGRATION") != "1", reason="Defina PROJECTBI_RUN_INTEGRATION=1 para o PostgreSQL local aprovado.")
def test_postgresql_full_smoke_rolls_back_every_table():
    config = load_config("smoke")
    settings = connection_settings(__import__("pathlib").Path(__file__).resolve().parents[2])
    result = run_rollback_full_smoke(settings, config)
    assert result["server_version"].startswith("18.")
    assert result["master_id_maps"] == 19
    assert result["transaction_id_maps"] == 16
    assert len(result["sql_counts"]) == 22  # 21 tabelas transacionais mais custo realizado
    assert result["summary"]["payments"] == 314
    assert result["summary"]["transfers"] == 2
    assert result["summary"]["returns"] == 8
    assert sum(result["remaining"].values()) == 0
