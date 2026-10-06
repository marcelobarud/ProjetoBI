"""Validation of deterministic master data before any database connection."""

from __future__ import annotations

import json
import re
from collections import defaultdict
from datetime import datetime
from decimal import Decimal

from projectbi_generator.config import GeneratorConfig
from projectbi_generator.models.entities import MasterData
from projectbi_generator.validation.tax_ids import valid_cnpj, valid_cpf

VALID_UFS = frozenset(
    "AC AL AP AM BA CE DF ES GO MA MT MS MG PA PB PR PE PI RJ RN RS RO RR SC SP SE TO".split()
)
CITY_STATES = frozenset(
    {
        ("São Paulo", "SP"), ("Curitiba", "PR"), ("Porto Alegre", "RS"),
        ("Belo Horizonte", "MG"), ("Recife", "PE"), ("Goiânia", "GO"),
        ("Brasília", "DF"), ("Rio de Janeiro", "RJ"), ("Salvador", "BA"),
        ("Manaus", "AM"), ("Belém", "PA"), ("Florianópolis", "SC"),
        ("Campinas", "SP"),
    }
)
FAMILY_KEYS = {
    "NOTEBOOK": {"cpu_model", "ram_gb", "storage_gb", "screen_inches", "gpu_model", "operating_system"},
    "DESKTOP": {"cpu_model", "ram_gb", "storage_gb", "gpu_model", "motherboard_chipset", "power_supply_w"},
    "PROCESSOR": {"socket", "cores", "threads", "base_clock_ghz", "boost_clock_ghz", "tdp_w"},
    "GRAPHICS": {"chipset", "vram_gb", "memory_type", "interface", "recommended_psu_w"},
    "MEMORY": {"capacity_gb", "memory_type", "module_count", "speed_mts", "form_factor"},
    "MONITOR": {"screen_inches", "resolution", "refresh_rate_hz", "panel_type", "adaptive_sync"},
    "STORAGE": {"capacity_gb", "interface", "form_factor", "read_mbps"},
    "INPUT": {"device_type", "connection_type"},
    "AUDIO": {"connection_type", "microphone", "frequency_response_hz"},
    "NETWORK": {"device_type", "connection_type", "wifi_standard", "ethernet_ports", "max_speed_mbps"},
    "PRINTING": {"print_technology", "color", "duplex", "connectivity", "ppm"},
    "ACCESSORIES": {"accessory_type", "compatible_device_family", "length_cm"},
}
FAMILY_CATEGORY = {
    "CAT-NOTEBOOK": "NOTEBOOK", "CAT-DESKTOP": "DESKTOP",
    "CAT-PROCESSOR": "PROCESSOR", "CAT-GRAPHICS": "GRAPHICS",
    "CAT-MEMORY": "MEMORY", "CAT-MONITOR": "MONITOR",
    "CAT-STORAGE": "STORAGE", "CAT-INPUT": "INPUT", "CAT-AUDIO": "AUDIO",
    "CAT-NETWORK": "NETWORK", "CAT-PRINTING": "PRINTING", "CAT-ACCESSORIES": "ACCESSORIES",
}


def _require_unique(label: str, values: list[str]) -> None:
    if len(values) != len(set(values)):
        raise ValueError(f"Chaves lógicas duplicadas: {label}.")


def _check_category_tree(data: MasterData) -> None:
    by_code = {row.code: row for row in data.categories}
    if len(by_code) != len(data.categories):
        raise ValueError("Código de categoria duplicado.")
    parents = {row.code: row.parent_code for row in data.categories}
    for parent in parents.values():
        if parent is not None and parent not in by_code:
            raise ValueError("Categoria referencia pai inexistente.")
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(code: str) -> None:
        if code in visiting:
            raise ValueError("Ciclo encontrado na árvore de categorias.")
        if code in visited:
            return
        visiting.add(code)
        parent = parents[code]
        if parent is not None:
            visit(parent)
        visiting.remove(code)
        visited.add(code)

    for code in by_code:
        visit(code)


def _check_assignments(data: MasterData) -> None:
    employees = {row.code: row for row in data.employees}
    roles = {row.code for row in data.employee_roles}
    stores = {row.code for row in data.stores}
    grouped = defaultdict(list)
    for row in data.employee_assignments:
        employee = employees.get(row.employee_code)
        if employee is None or row.role_code not in roles:
            raise ValueError("Assignment referencia funcionário ou função inexistente.")
        if row.store_code is not None and row.store_code not in stores:
            raise ValueError("Assignment referencia loja inexistente.")
        if row.valid_from < employee.hired_on:
            raise ValueError("Assignment começa antes da admissão.")
        if employee.terminated_on is not None and (row.valid_to is None or row.valid_to > employee.terminated_on):
            raise ValueError("Assignment ultrapassa o desligamento.")
        if row.valid_to is not None and row.valid_to < row.valid_from:
            raise ValueError("Período de assignment invertido.")
        grouped[row.employee_code].append(row)
    for assignments in grouped.values():
        ordered = sorted(assignments, key=lambda row: row.valid_from)
        for previous, current in zip(ordered, ordered[1:]):
            if previous.valid_to is None or current.valid_from <= previous.valid_to:
                raise ValueError("Assignments do mesmo funcionário se sobrepõem.")


def _check_customers(data: MasterData) -> None:
    customers = {row.code: row for row in data.customers}
    individuals = {row.customer_code: row for row in data.individual_profiles}
    businesses = {row.customer_code: row for row in data.business_profiles}
    if len(individuals) != len(data.individual_profiles) or len(businesses) != len(data.business_profiles):
        raise ValueError("Perfil de cliente duplicado.")
    used_documents: set[str] = set()
    for code, customer in customers.items():
        has_individual = code in individuals
        has_business = code in businesses
        if has_individual == has_business:
            raise ValueError("Cliente deve possuir exatamente um perfil.")
        if customer.customer_type == "individual":
            profile = individuals.get(code)
            if profile is None or not valid_cpf(profile.cpf):
                raise ValueError("Perfil individual incompatível ou CPF inválido.")
            if profile.cpf in used_documents:
                raise ValueError("Documento fiscal sintético duplicado.")
            used_documents.add(profile.cpf)
        elif customer.customer_type == "business":
            profile = businesses.get(code)
            if profile is None or not valid_cnpj(profile.cnpj):
                raise ValueError("Perfil empresarial incompatível ou CNPJ inválido.")
            if profile.cnpj in used_documents:
                raise ValueError("Documento fiscal sintético duplicado.")
            used_documents.add(profile.cnpj)
        else:
            raise ValueError("Tipo de cliente inválido.")
    if set(individuals) - set(customers) or set(businesses) - set(customers):
        raise ValueError("Perfil referencia cliente inexistente.")


def _check_catalog(data: MasterData) -> None:
    category_codes = {row.code for row in data.categories}
    brand_codes = {row.code for row in data.brands}
    product_by_sku = {row.sku: row for row in data.products}
    supplier_codes = {row.code for row in data.suppliers}
    channel_codes = {row.code for row in data.sales_channels}
    if len(product_by_sku) != len(data.products):
        raise ValueError("SKU duplicado.")
    for product in data.products:
        if product.category_code not in category_codes or (product.brand_code and product.brand_code not in brand_codes):
            raise ValueError("Produto referencia categoria ou marca inexistente.")
        if product.unit_of_measure != "unit":
            raise ValueError("unit_of_measure deve ser 'unit'.")
        if not isinstance(product.specifications, dict):
            raise ValueError("specifications deve ter raiz JSON object.")
        if any(not re.fullmatch(r"[a-z][a-z0-9_]*", key) for key in product.specifications):
            raise ValueError("Chaves de specifications devem usar snake_case.")
        json.dumps(product.specifications, allow_nan=False)
        family = FAMILY_CATEGORY.get(product.category_code)
        if family and not FAMILY_KEYS[family].issubset(product.specifications):
            raise ValueError("specifications não corresponde à família do produto.")

    pairs: set[tuple[str, str]] = set()
    preferred: set[str] = set()
    products_with_suppliers: set[str] = set()
    for link in data.product_suppliers:
        pair = (link.product_sku, link.supplier_code)
        if pair in pairs:
            raise ValueError("Associação produto-fornecedor duplicada.")
        pairs.add(pair)
        if link.product_sku not in product_by_sku or link.supplier_code not in supplier_codes:
            raise ValueError("Associação produto-fornecedor tem referência inexistente.")
        products_with_suppliers.add(link.product_sku)
        if link.is_preferred and link.is_active:
            if link.product_sku in preferred:
                raise ValueError("Mais de um fornecedor preferencial ativo para um produto.")
            preferred.add(link.product_sku)
    if products_with_suppliers != set(product_by_sku) or preferred != set(product_by_sku):
        raise ValueError("Todo produto deve ter fornecedor preferencial ativo.")

    by_price_key = defaultdict(list)
    if any(not isinstance(row.amount, Decimal) for row in data.product_prices):
        raise ValueError("Preços devem usar Decimal.")
    for price in data.product_prices:
        if price.product_sku not in product_by_sku or price.channel_code not in channel_codes:
            raise ValueError("Preço referencia produto ou canal inexistente.")
        if price.amount <= 0 or (price.valid_to is not None and price.valid_to <= price.valid_from):
            raise ValueError("Preço ou período inválido.")
        if price.valid_from.tzinfo is None or price.created_at.tzinfo is None:
            raise ValueError("Timestamps de preço devem ter fuso explícito.")
        by_price_key[(price.product_sku, price.channel_code)].append(price)
    for prices in by_price_key.values():
        ordered = sorted(prices, key=lambda row: row.valid_from)
        for previous, current in zip(ordered, ordered[1:]):
            if previous.valid_to is None or current.valid_from < previous.valid_to:
                raise ValueError("Períodos de preço se sobrepõem.")


def _check_contacts_and_addresses(data: MasterData) -> None:
    customers = {row.code for row in data.customers}
    primary_active: set[str] = set()
    contact_keys: set[str] = set()
    for contact in data.customer_contacts:
        if contact.customer_code not in customers or contact.logical_key in contact_keys:
            raise ValueError("Contato referencia cliente inexistente ou chave duplicada.")
        contact_keys.add(contact.logical_key)
        if contact.contact_type == "email" and not contact.contact_value.lower().endswith("@example.com"):
            raise ValueError("E-mails sintéticos devem usar example.com.")
        if contact.is_primary and contact.is_active:
            if contact.customer_code in primary_active:
                raise ValueError("Cliente tem mais de um contato primário ativo.")
            primary_active.add(contact.customer_code)
    if primary_active != customers:
        raise ValueError("Todo cliente deve ter um contato primário ativo.")

    defaults: set[str] = set()
    address_keys: set[str] = set()
    for address in data.customer_addresses:
        if address.customer_code not in customers or address.logical_key in address_keys:
            raise ValueError("Endereço referencia cliente inexistente ou chave duplicada.")
        address_keys.add(address.logical_key)
        if not re.fullmatch(r"[0-9]{8}", address.postal_code):
            raise ValueError("CEP de cliente deve conter oito dígitos.")
        if address.state_code not in VALID_UFS or address.country_code != "BR":
            raise ValueError("UF ou país de endereço de cliente inválido.")
        if (address.city, address.state_code) not in CITY_STATES:
            raise ValueError("Cidade e UF não formam combinação brasileira configurada.")
        if address.is_default and address.is_active:
            if address.customer_code in defaults:
                raise ValueError("Cliente tem mais de um endereço padrão ativo.")
            defaults.add(address.customer_code)
    if defaults != customers:
        raise ValueError("Todo cliente deve ter um endereço padrão ativo.")


def validate_master_data(data: MasterData, config: GeneratorConfig) -> None:
    """Raise ValueError on any invalid, incomplete or inconsistent master dataset."""
    expected = config.volumes
    for name, count in data.counts().items():
        if count != expected[name]:
            raise ValueError(f"Contagem divergente para {name}: esperado {expected[name]}, encontrado {count}.")

    for label, values in (
        ("stores", [row.code for row in data.stores]),
        ("employees", [row.code for row in data.employees]),
        ("employee_roles", [row.code for row in data.employee_roles]),
        ("sales_channels", [row.code for row in data.sales_channels]),
        ("payment_methods", [row.code for row in data.payment_methods]),
        ("suppliers", [row.code for row in data.suppliers]),
        ("carriers", [row.code for row in data.carriers]),
        ("brands", [row.code for row in data.brands]),
        ("customers", [row.code for row in data.customers]),
        ("stock_locations", [row.code for row in data.stock_locations]),
    ):
        _require_unique(label, values)

    supplier_tax_ids = [row.tax_identifier for row in data.suppliers]
    _require_unique("supplier tax identifiers", supplier_tax_ids)
    if any(not valid_cnpj(value) for value in supplier_tax_ids):
        raise ValueError("Fornecedor possui CNPJ sintético inválido.")

    for store in data.stores:
        if not re.fullmatch(r"[0-9]{8}", store.postal_code):
            raise ValueError("CEP de loja deve conter oito dígitos.")
        if store.state_code not in VALID_UFS or store.country_code != "BR":
            raise ValueError("UF ou país de loja inválido.")
        if (store.city, store.state_code) not in CITY_STATES:
            raise ValueError("Cidade e UF de loja não formam combinação configurada.")
        if store.status not in {"active", "inactive", "closed"}:
            raise ValueError("Status de loja inválido.")

    _check_category_tree(data)
    _check_assignments(data)
    _check_customers(data)
    _check_catalog(data)
    _check_contacts_and_addresses(data)

    customer_types = {row.customer_type for row in data.customers}
    if customer_types != {"individual", "business"}:
        raise ValueError("Smoke deve conter clientes PF e PJ.")
    expected_types = {
        "individual": config.composition.get("individual_customers"),
        "business": config.composition.get("business_customers"),
    }
    for customer_type, count in expected_types.items():
        if count is not None and sum(row.customer_type == customer_type for row in data.customers) != count:
            raise ValueError("Composição PF/PJ diverge da configuração.")

    expected_aware = [row.created_at for row in data.stores]
    if any(not isinstance(value, datetime) or value.tzinfo is None for value in expected_aware):
        raise ValueError("Timestamps cadastrais devem incluir fuso horário.")
