from pathlib import Path

import pytest

from projectbi_generator.config import ConfigurationError, load_config
from projectbi_generator.database import connection_settings, validate_database_identity
from projectbi_generator.seeds import DOMAINS, create_domain_randoms, derive_subseed
from projectbi_generator.validation.master_data import CITY_STATES


def test_smoke_toml_dates_seed_and_exact_volumes(config):
    assert config.profile == "smoke"
    assert config.root_seed == 20261005
    assert config.start_date.isoformat() == "2023-01-01"
    assert config.end_date.isoformat() == "2026-09-30"
    assert config.bootstrap_start_date.isoformat() == "2022-11-01"
    assert config.bootstrap_end_date.isoformat() == "2022-12-31"
    assert len(config.volumes) == 19
    assert config.timezone.key == "America/Sao_Paulo"


@pytest.mark.parametrize("profile", ("portfolio", "large"))
def test_profiles_have_configured_transaction_targets_and_plan_values(profile):
    config = load_config(profile)
    assert config.profile == profile
    assert config.volumes["stores"] == 10
    assert len(config.stores) == 10
    assert all((store.city, store.state_code) in CITY_STATES for store in config.stores)
    assert config.sales_order_target == {"portfolio": 120000, "large": 240000}[profile]
    assert config.batch_size == 5000


@pytest.mark.parametrize(("profile", "orders", "items"), (("portfolio", 120000, 264000), ("large", 240000, 528000)))
def test_full_plan_is_configuration_only(profile, orders, items, capsys):
    from projectbi_generator.cli import main

    assert main(["full", "--profile", profile, "--plan"]) == 0
    result = __import__("json").loads(capsys.readouterr().out)
    assert result["sales_orders_target"] == orders
    assert result["sales_order_items_estimate"] == items
    assert result["database_connected"] is False
    assert result["generated"] is False
    assert result["persistent_write"] is False


def test_unknown_profile_is_rejected():
    with pytest.raises(ConfigurationError):
        load_config("unknown")


def test_subseeds_are_stable_and_domain_specific(config):
    first = derive_subseed(config.root_seed, "catalog", config.generator_version)
    assert first == derive_subseed(config.root_seed, "catalog", config.generator_version)
    assert first != derive_subseed(config.root_seed, "customers", config.generator_version)
    assert set(create_domain_randoms(config.root_seed, config.generator_version)) == set(DOMAINS)
    with pytest.raises(ValueError):
        derive_subseed(config.root_seed, "stores", config.generator_version)


def test_customer_rng_calls_do_not_advance_other_domain_rngs(config):
    first = create_domain_randoms(config.root_seed, config.generator_version)
    expected = {domain: first[domain].rng.random() for domain in ("catalog", "employees", "inventory")}
    second = create_domain_randoms(config.root_seed, config.generator_version)
    for _ in range(100):
        second["customers"].rng.random()
    actual = {domain: second[domain].rng.random() for domain in ("catalog", "employees", "inventory")}
    assert actual == expected


def test_env_process_values_override_local_fallback(tmp_path: Path):
    (tmp_path / ".env").write_text(
        "POSTGRES_HOST=local-host\nPOSTGRES_PORT=5432\nPOSTGRES_DB=projeto_bi\nPOSTGRES_USER=local-user\nPOSTGRES_PASSWORD=local-secret\n",
        encoding="utf-8",
    )
    settings = connection_settings(tmp_path, {
        "POSTGRES_HOST": "process-host", "POSTGRES_PORT": "5433", "POSTGRES_DB": "projeto_bi",
        "POSTGRES_USER": "process-user", "POSTGRES_PASSWORD": "process-secret",
    })
    assert settings.host == "process-host"
    assert settings.port == 5433
    assert settings.user == "process-user"
    assert bool(settings.password)


@pytest.mark.parametrize(("database", "version"), (("other_db", "18.6"), ("projeto_bi", "17.9")))
def test_database_guard_rejects_wrong_target(database, version):
    from projectbi_generator.database import DatabaseGuardError

    with pytest.raises(DatabaseGuardError):
        validate_database_identity(database, version)


def test_database_guard_accepts_approved_identity():
    validate_database_identity("projeto_bi", "18.6")
