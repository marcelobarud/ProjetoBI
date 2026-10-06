from dataclasses import replace
from datetime import date

import pytest

from projectbi_generator.config import GeneratorConfig
from projectbi_generator.config import load_config
from projectbi_generator.generators.master import generate_master_data
from projectbi_generator.validation.master_data import validate_master_data
from projectbi_generator.validation.tax_ids import valid_cnpj, valid_cpf


def test_smoke_exact_table_volumes_and_customer_mix(master_data, config):
    assert master_data.counts() == config.volumes
    assert sum(row.customer_type == "individual" for row in master_data.customers) == 18
    assert sum(row.customer_type == "business" for row in master_data.customers) == 2
    assert len(master_data.individual_profiles) == 18
    assert len(master_data.business_profiles) == 2


def test_portfolio_brand_names_satisfy_database_unique_constraint():
    config = load_config("portfolio")
    master = generate_master_data(config)
    validate_master_data(master, config)
    names = [row.name for row in master.brands]
    assert len(names) == len(set(names))


def test_all_synthetic_documents_have_checksums_and_are_unique(master_data):
    cpfs = [row.cpf for row in master_data.individual_profiles]
    cnpjs = [row.cnpj for row in master_data.business_profiles]
    assert len(cpfs) == len(set(cpfs)) and all(valid_cpf(value) for value in cpfs)
    assert len(cnpjs) == len(set(cnpjs)) and all(valid_cnpj(value) for value in cnpjs)


def test_same_seed_config_and_version_generate_identical_master_data(config, master_data):
    assert generate_master_data(config) == master_data


def test_different_seed_changes_data_and_preserves_integrity(config, master_data):
    alternate = replace(config, root_seed=config.root_seed + 1)
    generated = generate_master_data(alternate)
    validate_master_data(generated, alternate)
    assert generated != master_data
    assert [row.sku for row in generated.products] == [row.sku for row in master_data.products]


def test_store_geography_and_customer_addresses_are_brazilian(master_data):
    assert all(len(row.postal_code) == 8 and row.postal_code.isdigit() for row in master_data.stores)
    assert all(row.state_code in {"SP", "PR"} and row.country_code == "BR" for row in master_data.stores)
    assert all(row.country_code == "BR" for row in master_data.customer_addresses)


def test_contacts_use_reserved_email_domain_and_single_primary(master_data):
    assert all(row.contact_value.endswith("@example.com") for row in master_data.customer_contacts)
    assert all(sum(c.customer_code == row.code and c.is_primary and c.is_active for c in master_data.customer_contacts) == 1 for row in master_data.customers)


def test_catalog_tree_specs_suppliers_prices_and_decimal_values_are_valid(master_data, config):
    validate_master_data(master_data, config)
    assert len({row.sku for row in master_data.products}) == 30
    assert all(row.unit_of_measure == "unit" and isinstance(row.specifications, dict) for row in master_data.products)
    assert all(row.amount.as_tuple().exponent == -2 for row in master_data.product_prices)
    assert len(master_data.product_suppliers) == 36
    assert len(master_data.product_prices) == 120


def test_category_cycle_is_rejected(master_data, config):
    categories = tuple(
        replace(row, parent_code="CAT-NOTEBOOK") if row.code == "CAT-COMPUTING" else row
        for row in master_data.categories
    )
    with pytest.raises(ValueError, match="Ciclo"):
        validate_master_data(replace(master_data, categories=categories), config)


def test_pf_pj_profile_mismatch_is_rejected(master_data, config):
    customers = (replace(master_data.customers[0], customer_type="business"), *master_data.customers[1:])
    with pytest.raises(ValueError, match="[Pp]erfil"):
        validate_master_data(replace(master_data, customers=customers), config)


def test_json_array_specification_is_rejected(master_data, config):
    products = (replace(master_data.products[0], specifications=["not", "an", "object"]), *master_data.products[1:])
    with pytest.raises(ValueError, match="JSON object"):
        validate_master_data(replace(master_data, products=products), config)


def test_invalid_cpf_and_cnpj_are_rejected(master_data, config):
    individual = (replace(master_data.individual_profiles[0], cpf="11111111111"), *master_data.individual_profiles[1:])
    with pytest.raises(ValueError, match="CPF inválido"):
        validate_master_data(replace(master_data, individual_profiles=individual), config)
    business = (replace(master_data.business_profiles[0], cnpj="00000000000000"), *master_data.business_profiles[1:])
    with pytest.raises(ValueError, match="CNPJ inválido"):
        validate_master_data(replace(master_data, business_profiles=business), config)


def test_two_preferred_suppliers_for_same_sku_are_rejected(master_data, config):
    links = tuple(replace(row, is_preferred=True) if row.product_sku == master_data.product_suppliers[1].product_sku else row for row in master_data.product_suppliers)
    with pytest.raises(ValueError, match="Mais de um fornecedor preferencial"):
        validate_master_data(replace(master_data, product_suppliers=links), config)


def test_overlapping_price_periods_are_rejected(master_data, config):
    prices = (*master_data.product_prices, master_data.product_prices[0])
    volumes = dict(config.volumes)
    volumes["product_prices"] += 1
    altered_config = replace(config, volumes=volumes)
    with pytest.raises(ValueError, match="se sobrepõem"):
        validate_master_data(replace(master_data, product_prices=prices), altered_config)


def test_assignment_before_employee_hire_is_rejected(master_data, config):
    employee = master_data.employees[0]
    employees = (replace(employee, hired_on=date(2023, 1, 1)), *master_data.employees[1:])
    with pytest.raises(ValueError, match="antes da admissão"):
        validate_master_data(replace(master_data, employees=employees), config)


def test_invalid_uf_is_rejected(master_data, config):
    stores = (replace(master_data.stores[0], state_code="XX"), *master_data.stores[1:])
    with pytest.raises(ValueError, match="UF ou país de loja inválido"):
        validate_master_data(replace(master_data, stores=stores), config)


@pytest.mark.parametrize("profile", ("portfolio", "large"))
def test_configured_profiles_generate_valid_master_volumes(profile):
    from projectbi_generator.config import load_config

    config = load_config(profile)
    data = generate_master_data(config)
    validate_master_data(data, config)
    assert data.counts() == config.volumes
