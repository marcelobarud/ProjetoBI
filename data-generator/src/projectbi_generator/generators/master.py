"""Deterministic smoke master-data generation, independent of persistence."""

from __future__ import annotations

import random
from datetime import date, datetime, time, timedelta
from decimal import Decimal

from faker import Faker

from projectbi_generator.config import GeneratorConfig
from projectbi_generator.models.entities import (
    Brand,
    Carrier,
    Category,
    Customer,
    CustomerAddress,
    CustomerContact,
    Employee,
    EmployeeAssignment,
    EmployeeRole,
    MasterData,
    PaymentMethod,
    Product,
    ProductPrice,
    ProductSupplier,
    SalesChannel,
    StockLocation,
    Store,
    Supplier,
    IndividualProfile,
    BusinessProfile,
)
from projectbi_generator.seeds import create_domain_randoms
from projectbi_generator.validation.tax_ids import generate_cnpj, generate_cpf

CREATED_ON = date(2022, 10, 1)
CITY_PAIRS = (
    ("São Paulo", "SP"), ("Curitiba", "PR"), ("Porto Alegre", "RS"),
    ("Belo Horizonte", "MG"), ("Recife", "PE"), ("Goiânia", "GO"),
    ("Brasília", "DF"), ("Rio de Janeiro", "RJ"), ("Salvador", "BA"),
    ("Manaus", "AM"), ("Belém", "PA"), ("Florianópolis", "SC"),
)
SYLLABLES = ("zu", "ni", "va", "ke", "lo", "mi", "ra", "vo", "ta", "xi", "pa", "re", "du", "ka")
FAMILIES = {
    "CAT-NOTEBOOK": ("notebook", "NOTEBOOK", (200000, 1800000)),
    "CAT-DESKTOP": ("desktop", "DESKTOP", (180000, 1600000)),
    "CAT-PROCESSOR": ("processador", "PROCESSOR", (35000, 700000)),
    "CAT-GRAPHICS": ("placa gráfica", "GRAPHICS", (90000, 1500000)),
    "CAT-MEMORY": ("memória", "MEMORY", (10000, 180000)),
    "CAT-MONITOR": ("monitor", "MONITOR", (50000, 500000)),
    "CAT-STORAGE": ("armazenamento", "STORAGE", (12000, 350000)),
    "CAT-INPUT": ("periférico", "INPUT", (3500, 250000)),
    "CAT-AUDIO": ("áudio", "AUDIO", (8000, 250000)),
    "CAT-NETWORK": ("rede", "NETWORK", (6000, 400000)),
    "CAT-PRINTING": ("impressora", "PRINTING", (60000, 600000)),
    "CAT-ACCESSORIES": ("acessório", "ACCESSORIES", (2000, 150000)),
}


def _stamp(config: GeneratorConfig, day: date = CREATED_ON, hour: int = 10) -> datetime:
    return datetime.combine(day, time(hour, 0), tzinfo=config.timezone)


def _fake(locale: str, seed: int) -> Faker:
    result = Faker(locale)
    result.seed_instance(seed)
    return result


def _invented_word(rng: random.Random) -> str:
    return "".join(rng.choice(SYLLABLES).capitalize() if index == 0 else rng.choice(SYLLABLES) for index in range(2))


def _entity_code(config: GeneratorConfig, prefix: str, index: int) -> str:
    if config.profile == "smoke":
        return f"{prefix}-SM-{index + 1:03d}"
    return f"{prefix}-{config.profile[:2].upper()}-{index + 1:05d}"


def _build_roles(config: GeneratorConfig) -> tuple[EmployeeRole, ...]:
    values = (
        ("SALES", "Vendas"), ("STOCK", "Estoque"), ("MANAGER", "Gestão"),
        ("PROCUREMENT", "Compras"), ("ADMIN", "Administrativo"),
    )
    stamp = _stamp(config)
    rows = [EmployeeRole(code, name, True, stamp, stamp) for code, name in values]
    for ordinal in range(len(rows) + 1, config.volumes["employee_roles"] + 1):
        rows.append(EmployeeRole(f"ROLE-{ordinal:02d}", f"Função operacional {ordinal:02d}", True, stamp, stamp))
    if len(rows) != config.volumes["employee_roles"]:
        raise ValueError("O volume de funções deve incluir o conjunto operacional mínimo.")
    return tuple(rows)


def _build_categories(config: GeneratorConfig) -> tuple[Category, ...]:
    stamp = _stamp(config)
    rows = [
        Category("CAT-COMPUTING", "Computação", None, True, stamp, stamp),
        Category("CAT-NOTEBOOK", "Notebooks", "CAT-COMPUTING", True, stamp, stamp),
        Category("CAT-DESKTOP", "Computadores de mesa", "CAT-COMPUTING", True, stamp, stamp),
        Category("CAT-COMPONENTS", "Componentes", None, True, stamp, stamp),
        Category("CAT-PROCESSOR", "Processadores", "CAT-COMPONENTS", True, stamp, stamp),
        Category("CAT-GRAPHICS", "Gráficos", "CAT-COMPONENTS", True, stamp, stamp),
        Category("CAT-MEMORY", "Memória", "CAT-COMPONENTS", True, stamp, stamp),
        Category("CAT-DEVICES", "Dispositivos", None, True, stamp, stamp),
        Category("CAT-MONITOR", "Monitores", "CAT-DEVICES", True, stamp, stamp),
        Category("CAT-STORAGE", "Unidades de armazenamento", "CAT-DEVICES", True, stamp, stamp),
        Category("CAT-INPUT", "Entrada", "CAT-DEVICES", True, stamp, stamp),
        Category("CAT-AUDIO", "Áudio", "CAT-DEVICES", True, stamp, stamp),
        Category("CAT-NETWORK", "Redes", "CAT-DEVICES", True, stamp, stamp),
        Category("CAT-PRINTING", "Impressão", "CAT-DEVICES", True, stamp, stamp),
        Category("CAT-ACCESSORIES", "Acessórios", "CAT-DEVICES", True, stamp, stamp),
    ]
    for ordinal in range(len(rows) + 1, config.volumes["categories"] + 1):
        rows.append(Category(
            f"CAT-ADDITIONAL-{ordinal:03d}", f"Categoria sintética {ordinal:02d}",
            "CAT-COMPONENTS" if ordinal % 2 else "CAT-DEVICES", True, stamp, stamp,
        ))
    if len(rows) != config.volumes["categories"]:
        raise ValueError("O volume de categorias deve incluir a taxonomia mínima.")
    return tuple(rows)


def _specification(family: str, rng: random.Random, ordinal: int) -> dict:
    if family == "NOTEBOOK":
        return {"cpu_model": f"Zuniva M{ordinal % 7 + 1}", "ram_gb": rng.choice((8, 16, 32)), "storage_gb": rng.choice((512, 1024, 2048)), "screen_inches": rng.choice((14, 15.6, 16)), "gpu_model": None if ordinal % 2 else f"Gráficos V{ordinal % 5 + 1}", "operating_system": "Sistema sintético"}
    if family == "DESKTOP":
        return {"cpu_model": f"Kalumi D{ordinal % 6 + 1}", "ram_gb": rng.choice((16, 32, 64)), "storage_gb": rng.choice((512, 1024, 2048)), "gpu_model": f"Gráficos V{ordinal % 5 + 1}", "motherboard_chipset": f"Chipset K{ordinal % 4 + 1}", "power_supply_w": rng.choice((550, 650, 750, 850))}
    if family == "PROCESSOR":
        cores = rng.choice((4, 6, 8, 12))
        return {"socket": f"Socket S{ordinal % 4 + 1}", "cores": cores, "threads": cores * 2, "base_clock_ghz": float(Decimal("2.5") + Decimal(ordinal % 15) / 10), "boost_clock_ghz": float(Decimal("3.5") + Decimal(ordinal % 10) / 10), "tdp_w": rng.choice((65, 95, 125))}
    if family == "GRAPHICS":
        return {"chipset": f"Núcleo gráfico G{ordinal % 8 + 1}", "vram_gb": rng.choice((8, 12, 16, 24)), "memory_type": rng.choice(("GDDR6", "GDDR6X")), "interface": "PCIe x16", "recommended_psu_w": rng.choice((650, 750, 850, 1000))}
    if family == "MEMORY":
        return {"capacity_gb": rng.choice((16, 32, 64)), "memory_type": "DDR5", "module_count": rng.choice((1, 2)), "speed_mts": rng.choice((4800, 5600, 6000)), "form_factor": "DIMM"}
    if family == "MONITOR":
        return {"screen_inches": rng.choice((23.8, 27, 31.5)), "resolution": rng.choice(("1920x1080", "2560x1440", "3840x2160")), "refresh_rate_hz": rng.choice((60, 75, 120, 144)), "panel_type": rng.choice(("IPS", "VA")), "adaptive_sync": bool(ordinal % 2)}
    if family == "STORAGE":
        return {"capacity_gb": rng.choice((512, 1024, 2048, 4000)), "interface": rng.choice(("NVMe", "SATA")), "form_factor": rng.choice(("M.2", "2.5-inch")), "read_mbps": rng.choice((550, 2400, 3500, 5000))}
    if family == "INPUT":
        device = "mouse" if ordinal % 2 else "keyboard"
        values = {"device_type": device, "connection_type": rng.choice(("wired", "wireless"))}
        if device == "mouse":
            values["dpi"] = rng.choice((1600, 3200, 6400))
            values["buttons"] = rng.choice((5, 6, 8))
        else:
            values["layout"] = "ABNT2"
            values["backlit"] = bool(ordinal % 3)
        return values
    if family == "AUDIO":
        return {"connection_type": rng.choice(("wired", "wireless")), "microphone": True, "frequency_response_hz": "20-20000"}
    if family == "NETWORK":
        return {"device_type": "router", "connection_type": "wireless", "wifi_standard": rng.choice(("Wi-Fi 6", "Wi-Fi 6E")), "ethernet_ports": rng.choice((4, 5, 8)), "max_speed_mbps": rng.choice((1000, 2500, 5000))}
    if family == "PRINTING":
        return {"print_technology": rng.choice(("laser", "ink")), "color": bool(ordinal % 2), "duplex": True, "connectivity": rng.choice(("USB", "Wi-Fi")), "ppm": rng.choice((18, 24, 32))}
    return {"accessory_type": "cabo", "compatible_device_family": "computador", "length_cm": rng.choice((100, 150, 200))}


def generate_master_data(config: GeneratorConfig) -> MasterData:
    """Generate all profile-configured master tables with independent domain RNGs."""
    domain_randoms = create_domain_randoms(config.root_seed, config.generator_version)
    rng = {key: value.rng for key, value in domain_randoms.items()}
    fake_employees = _fake("pt_BR", domain_randoms["employees"].seed)
    fake_customers = _fake("pt_BR", domain_randoms["customers"].seed)
    now = _stamp(config)

    stores = tuple(
        Store(
            code=row.code, name=row.name, postal_code=row.postal_code, street=row.street,
            street_number=row.street_number, complement=None, district=row.district,
            city=row.city, state_code=row.state_code, country_code="BR", status="active",
            opened_on=row.opened_on, created_at=now, updated_at=now,
        )
        for row in config.stores
    )
    employee_roles = _build_roles(config)
    role_codes = [row.code for row in employee_roles]
    employees_list = []
    used_names: set[str] = set()
    for index in range(config.volumes["employees"]):
        if config.profile == "smoke":
            first_name, last_name = fake_employees.unique.first_name(), fake_employees.unique.last_name()
            full_name = f"{first_name} {last_name}"
            if full_name in used_names:
                first_name, last_name = fake_employees.unique.first_name(), fake_employees.unique.last_name()
            used_names.add(f"{first_name} {last_name}")
        else:
            first_name, last_name = fake_employees.first_name(), fake_employees.last_name()
        code = _entity_code(config, "EMP", index)
        hired = CREATED_ON + timedelta(days=index * 4)
        employees_list.append(Employee(code, first_name, last_name, f"{code.lower()}@example.com", None, hired, None, "active", now, now))
    employees = tuple(employees_list)

    assignments = []
    extra_assignment_count = config.volumes["employee_assignments"] - len(employees)
    if extra_assignment_count < 0 or extra_assignment_count > len(employees):
        raise ValueError("employee_assignments deve conter uma atribuição-base e no máximo uma adicional por funcionário.")
    for index, employee in enumerate(employees):
        role_code = role_codes[index % len(role_codes)]
        store_code = stores[index % len(stores)].code if role_code in {"SALES", "STOCK", "MANAGER"} else None
        if index < extra_assignment_count:
            assignments.append(EmployeeAssignment(f"ASG-{index + 1:03d}-A", employee.code, role_code, store_code, employee.hired_on, date(2024, 12, 31), now))
            next_role = role_codes[(index + 1) % len(role_codes)]
            assignments.append(EmployeeAssignment(f"ASG-{index + 1:03d}-B", employee.code, next_role, store_code, date(2025, 1, 1), None, now))
        else:
            assignments.append(EmployeeAssignment(f"ASG-{index + 1:03d}-A", employee.code, role_code, store_code, employee.hired_on, None, now))
    employee_assignments = tuple(assignments)

    sales_channels = tuple(
        SalesChannel(code, name, kind, True, now, now)
        for code, name, kind in (
            ("CH-PHYSICAL", "Loja física", "physical"),
            ("CH-ECOM", "E-commerce próprio", "ecommerce"),
            ("CH-MARKET-A", "Marketplace genérico Aurora", "marketplace"),
            ("CH-MARKET-B", "Marketplace genérico Horizonte", "marketplace"),
        )
    )
    payment_method_specs = [
            ("PM-CARD", "Cartão de crédito", "card", True),
            ("PM-CASH", "Dinheiro", "cash", False),
            ("PM-INSTANT", "Pagamento instantâneo", "instant", False),
            ("PM-BANK", "Transferência bancária", "bank_transfer", False),
    ]
    for ordinal in range(len(payment_method_specs) + 1, config.volumes["payment_methods"] + 1):
        payment_method_specs.append((f"PM-OTHER-{ordinal:02d}", f"Meio de pagamento sintético {ordinal:02d}", "other", False))
    if len(payment_method_specs) != config.volumes["payment_methods"]:
        raise ValueError("O volume configurado de meios de pagamento é menor que o conjunto mínimo de pagamentos.")
    payment_methods = tuple(PaymentMethod(code, name, kind, installment, True, now, now)
                           for code, name, kind, installment in payment_method_specs)

    supplier_used: set[str] = set()
    suppliers_list = []
    for index in range(config.volumes["suppliers"]):
        word = _invented_word(rng["procurement"])
        tax_id = generate_cnpj(rng["procurement"], supplier_used)
        code = _entity_code(config, "SUP", index)
        suppliers_list.append(Supplier(code, f"Distribuidora {word} Sintética Ltda", f"{word} Componentes", tax_id, f"compras-{code.lower()}@example.com", "active", now, now))
    suppliers = tuple(suppliers_list)

    logistics_rng = rng["logistics"]
    carriers = tuple(
        Carrier(_entity_code(config, "CAR", index), f"Logística {_invented_word(logistics_rng)} Sintética", None, True, now, now)
        for index in range(config.volumes["carriers"])
    )
    categories = _build_categories(config)
    brand_rows = []
    used_brand_names: set[str] = set()
    for index in range(config.volumes["brands"]):
        name = _invented_word(rng["catalog"])
        if name in used_brand_names:
            suffix = index + 1
            candidate = f"{name} {suffix:03d}"
            while candidate in used_brand_names:
                suffix += 1
                candidate = f"{name} {suffix:03d}"
            name = candidate
        used_brand_names.add(name)
        brand_rows.append(Brand(_entity_code(config, "BR", index), name, True, now, now))
    brands = tuple(brand_rows)

    family_rows = list(FAMILIES.items())
    products_list = []
    for index in range(config.volumes["products"]):
        category_code, (family_name, family, _) = family_rows[index % len(family_rows)]
        suffix = rng["catalog"].choice(("Nova", "Orbe", "Vértice", "Fluxo", "Prisma", "Pulso"))
        brand = brands[index % len(brands)]
        sku = f"SKU-{family[:3]}-{index + 1:03d}" if config.profile == "smoke" else f"SKU-{family[:3]}-{index + 1:05d}"
        products_list.append(Product(sku, category_code, brand.code, f"{family_name.title()} {suffix} {index + 1:03d}", f"Modelo sintético da família {family_name}.", _specification(family, rng["catalog"], index), "unit", "active", now, now))
    products = tuple(products_list)

    product_suppliers_list = []
    for index, product in enumerate(products):
        primary_supplier = suppliers[index % len(suppliers)]
        product_suppliers_list.append(ProductSupplier(product.sku, primary_supplier.code, f"REF-{index + 1:04d}-A", True, True, now, now))
        if index < config.generation["secondary_supplier_products"]:
            secondary = suppliers[(index + 1) % len(suppliers)]
            product_suppliers_list.append(ProductSupplier(product.sku, secondary.code, f"REF-{index + 1:04d}-B", False, True, now, now))
    product_suppliers = tuple(product_suppliers_list)

    product_prices_list = []
    pair_count = len(products) * len(sales_channels)
    target_price_count = config.volumes["product_prices"]
    if target_price_count < pair_count:
        raise ValueError("product_prices deve fornecer ao menos um preço por produto/canal.")
    max_periods = config.generation["price_periods_per_product_channel"]
    minimum_periods, remainder = divmod(target_price_count, pair_count)
    if minimum_periods > max_periods or (remainder and minimum_periods + 1 > max_periods):
        raise ValueError("O profile não oferece períodos de preço suficientes para o volume configurado.")
    period_starts = (date(2022, 10, 1), date(2024, 1, 1), date(2025, 1, 1), date(2026, 1, 1))
    pair_ordinal = 0
    for product_index, product in enumerate(products):
        _, family, (low, high) = FAMILIES[product.category_code]
        for channel_index, channel in enumerate(sales_channels):
            count = minimum_periods + int(pair_ordinal < remainder)
            starts = period_starts[:count]
            for period_index, starts_on in enumerate(starts):
                cents = rng["catalog"].randint(low, high)
                cents = cents * (100 + channel_index * 2) // 100
                amount = (Decimal(cents) / Decimal(100)).quantize(Decimal("0.01"))
                valid_from = _stamp(config, starts_on, 0)
                valid_to = _stamp(config, starts[period_index + 1], 0) if period_index + 1 < count else None
                product_prices_list.append(ProductPrice(
                    product.sku, channel.code, amount, valid_from, valid_to, now,
                    employees[product_index % len(employees)].code,
                ))
            pair_ordinal += 1
    product_prices = tuple(product_prices_list)

    customer_rng = rng["customers"]
    individual_count = config.composition["individual_customers"]
    customer_count = config.volumes["customers"]
    customers_list = []
    individual_profiles = []
    business_profiles = []
    used_cpfs: set[str] = set()
    used_cnpjs: set[str] = set()
    used_customer_names: set[str] = set()
    for index in range(customer_count):
        code = f"CUS-SM-{index + 1:03d}"
        individual = index < individual_count
        if individual:
            if config.profile == "smoke":
                display_name = fake_customers.unique.name()
                if display_name in used_customer_names:
                    display_name = fake_customers.unique.name()
                used_customer_names.add(display_name)
            else:
                display_name = f"{fake_customers.name()} — Cliente {index + 1:06d}"
            customers_list.append(Customer(code, "individual", display_name, "active", now, now))
            individual_profiles.append(IndividualProfile(code, generate_cpf(customer_rng, used_cpfs), date(1978 + index % 25, 1 + index % 12, 1 + index % 27), now, now))
        else:
            word = _invented_word(customer_rng)
            display_name = f"Organização Sintética {word} {index + 1:03d}"
            customers_list.append(Customer(code, "business", display_name, "active", now, now))
            cnpj = generate_cnpj(customer_rng, used_cnpjs)
            business_profiles.append(BusinessProfile(code, display_name, f"{word} Soluções", cnpj, now, now))
    customers = tuple(customers_list)

    customer_contacts_list = []
    for index, customer in enumerate(customers):
        value = f"{customer.code.lower()}@example.com"
        width = 3 if config.profile == "smoke" else 6
        customer_contacts_list.append(CustomerContact(f"CONTACT-{index + 1:0{width}d}-A", customer.code, "email", value, True, True, now, now))
        if index < config.generation["extra_contacts"]:
            customer_contacts_list.append(CustomerContact(f"CONTACT-{index + 1:0{width}d}-B", customer.code, "email", f"alternate-{customer.code.lower()}@example.com", False, True, now, now))
    customer_contacts = tuple(customer_contacts_list)

    addresses = []
    street_nouns = ("Paineira", "Manacá", "Jatobá", "Cambará", "Araucária", "Quaresmeira")
    districts = ("Centro", "Jardim Novo", "Vila das Fontes", "Parque Sintético")
    for index in range(config.volumes["customer_addresses"]):
        customer = customers[index % len(customers)]
        city, state = CITY_PAIRS[customer_rng.randrange(len(CITY_PAIRS))]
        width = 3 if config.profile == "smoke" else 6
        addresses.append(CustomerAddress(
            f"ADDR-{index + 1:0{width}d}", customer.code,
            "principal" if index < len(customers) else "alternativo",
            customer.display_name, f"{customer_rng.randrange(10**8):08d}",
            f"Rua {street_nouns[customer_rng.randrange(len(street_nouns))]} Sintética",
            str(customer_rng.randrange(1, 990)), None,
            districts[customer_rng.randrange(len(districts))], city, state, "BR",
            index < len(customers), True, now, now,
        ))
    customer_addresses = tuple(addresses)

    stock_locations_list = [
        StockLocation(f"LOC-{store.code}", f"Estoque {store.name}", "store", "active", store.code, now, now)
        for store in stores
    ]
    stock_locations_list.extend((
        StockLocation("LOC-SM-CENTRAL", "Centro de estoque sintético", "warehouse", "active", None, now, now),
        StockLocation("LOC-SM-EXPEDITION", "Ponto de expedição sintético", "warehouse", "active", None, now, now),
    ))
    for ordinal in range(len(stock_locations_list) + 1, config.volumes["stock_locations"] + 1):
        stock_locations_list.append(StockLocation(
            f"LOC-{config.profile[:2].upper()}-WH-{ordinal:03d}",
            f"Armazém sintético {ordinal:02d}", "warehouse", "active", None, now, now,
        ))
    if len(stock_locations_list) != config.volumes["stock_locations"]:
        raise ValueError("stock_locations deve incluir cada loja e pelo menos dois armazéns.")

    return MasterData(
        stores=stores,
        employee_roles=employee_roles,
        employees=employees,
        employee_assignments=employee_assignments,
        sales_channels=sales_channels,
        payment_methods=payment_methods,
        suppliers=suppliers,
        carriers=carriers,
        categories=categories,
        brands=brands,
        products=products,
        product_suppliers=product_suppliers,
        product_prices=product_prices,
        customers=customers,
        individual_profiles=tuple(individual_profiles),
        business_profiles=tuple(business_profiles),
        customer_contacts=customer_contacts,
        customer_addresses=customer_addresses,
        stock_locations=tuple(stock_locations_list),
    )
