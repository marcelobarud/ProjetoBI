"""Explicit parameterized inserts with logical-key to database-ID mapping."""

from __future__ import annotations

from psycopg import Connection, sql
from psycopg.types.json import Jsonb

from projectbi_generator.models.entities import MasterData


def _insert_many_returning(
    connection: Connection,
    schema: str,
    table: str,
    columns: tuple[str, ...],
    rows: list[tuple[str, tuple]],
    logical_column: str,
    id_column: str,
    batch_size: int = 500,
) -> dict[str, int]:
    statement = sql.SQL("INSERT INTO {}.{} ({}) VALUES ({}) RETURNING {}").format(
        sql.Identifier(schema),
        sql.Identifier(table),
        sql.SQL(", ").join(map(sql.Identifier, columns)),
        sql.SQL(", ").join(sql.Placeholder() for _ in columns),
        sql.Identifier(id_column),
    )
    identifiers: dict[str, int] = {}
    for offset in range(0, len(rows), batch_size):
        batch = rows[offset : offset + batch_size]
        with connection.cursor() as cursor:
            cursor.executemany(statement, [values for _, values in batch], returning=True)
            for index, (logical_key, _) in enumerate(batch):
                result = cursor.fetchone()
                if result is None:
                    raise RuntimeError(f"INSERT sem ID retornado para {schema}.{table}.")
                identifiers[logical_key] = result[0]
                if index + 1 < len(batch) and not cursor.nextset():
                    raise RuntimeError(f"Resultado em lote incompleto para {schema}.{table}.")
    return identifiers


def load_master_data(connection: Connection, data: MasterData) -> dict[str, dict[str, int]]:
    """Insert the 19 approved master tables, resolving FKs only from returned IDs."""
    ids: dict[str, dict[str, int]] = {}

    ids["stores"] = _insert_many_returning(connection, "core", "stores", (
        "store_code", "name", "postal_code", "street", "street_number", "complement", "district", "city", "state_code", "country_code", "status", "opened_on", "created_at", "updated_at",
    ), [(r.code, (r.code, r.name, r.postal_code, r.street, r.street_number, r.complement, r.district, r.city, r.state_code, r.country_code, r.status, r.opened_on, r.created_at, r.updated_at)) for r in data.stores], "store_code", "store_id")

    ids["employee_roles"] = _insert_many_returning(connection, "core", "employee_roles", (
        "role_code", "name", "is_active", "created_at", "updated_at",
    ), [(r.code, (r.code, r.name, r.is_active, r.created_at, r.updated_at)) for r in data.employee_roles], "role_code", "employee_role_id")

    ids["employees"] = _insert_many_returning(connection, "core", "employees", (
        "employee_code", "first_name", "last_name", "email", "phone", "hired_on", "terminated_on", "status", "created_at", "updated_at",
    ), [(r.code, (r.code, r.first_name, r.last_name, r.email, r.phone, r.hired_on, r.terminated_on, r.status, r.created_at, r.updated_at)) for r in data.employees], "employee_code", "employee_id")

    ids["employee_assignments"] = _insert_many_returning(connection, "core", "employee_assignments", (
        "employee_id", "employee_role_id", "store_id", "valid_from", "valid_to", "created_at",
    ), [(r.logical_key, (ids["employees"][r.employee_code], ids["employee_roles"][r.role_code], ids["stores"].get(r.store_code) if r.store_code else None, r.valid_from, r.valid_to, r.created_at)) for r in data.employee_assignments], "employee_assignment_id", "employee_assignment_id")

    ids["sales_channels"] = _insert_many_returning(connection, "sales", "sales_channels", (
        "channel_code", "name", "channel_type", "is_active", "created_at", "updated_at",
    ), [(r.code, (r.code, r.name, r.channel_type, r.is_active, r.created_at, r.updated_at)) for r in data.sales_channels], "channel_code", "sales_channel_id")

    ids["payment_methods"] = _insert_many_returning(connection, "payments", "payment_methods", (
        "method_code", "name", "method_type", "is_installment_capable", "is_active", "created_at", "updated_at",
    ), [(r.code, (r.code, r.name, r.method_type, r.is_installment_capable, r.is_active, r.created_at, r.updated_at)) for r in data.payment_methods], "method_code", "payment_method_id")

    ids["suppliers"] = _insert_many_returning(connection, "procurement", "suppliers", (
        "supplier_code", "legal_name", "trade_name", "tax_identifier", "email", "status", "created_at", "updated_at",
    ), [(r.code, (r.code, r.legal_name, r.trade_name, r.tax_identifier, r.email, r.status, r.created_at, r.updated_at)) for r in data.suppliers], "supplier_code", "supplier_id")

    ids["carriers"] = _insert_many_returning(connection, "logistics", "carriers", (
        "carrier_code", "name", "tax_identifier", "is_active", "created_at", "updated_at",
    ), [(r.code, (r.code, r.name, r.tax_identifier, r.is_active, r.created_at, r.updated_at)) for r in data.carriers], "carrier_code", "carrier_id")

    categories: dict[str, int] = {}
    for row in data.categories:
        statement = sql.SQL("INSERT INTO catalog.categories (parent_category_id,category_code,name,is_active,created_at,updated_at) VALUES (%s,%s,%s,%s,%s,%s) RETURNING category_id")
        cursor = connection.execute(statement, (categories.get(row.parent_code) if row.parent_code else None, row.code, row.name, row.is_active, row.created_at, row.updated_at))
        categories[row.code] = cursor.fetchone()[0]
    ids["categories"] = categories

    ids["brands"] = _insert_many_returning(connection, "catalog", "brands", (
        "brand_code", "name", "is_active", "created_at", "updated_at",
    ), [(r.code, (r.code, r.name, r.is_active, r.created_at, r.updated_at)) for r in data.brands], "brand_code", "brand_id")

    ids["products"] = _insert_many_returning(connection, "catalog", "products", (
        "sku", "category_id", "brand_id", "name", "description", "specifications", "unit_of_measure", "status", "created_at", "updated_at",
    ), [(r.sku, (r.sku, ids["categories"][r.category_code], ids["brands"][r.brand_code] if r.brand_code else None, r.name, r.description, Jsonb(r.specifications), r.unit_of_measure, r.status, r.created_at, r.updated_at)) for r in data.products], "sku", "product_id")

    ids["product_suppliers"] = _insert_many_returning(connection, "catalog", "product_suppliers", (
        "product_id", "supplier_id", "supplier_product_code", "is_preferred", "is_active", "created_at", "updated_at",
    ), [(f"{r.product_sku}|{r.supplier_code}", (ids["products"][r.product_sku], ids["suppliers"][r.supplier_code], r.supplier_product_code, r.is_preferred, r.is_active, r.created_at, r.updated_at)) for r in data.product_suppliers], "product_supplier_id", "product_supplier_id")

    ids["product_prices"] = _insert_many_returning(connection, "catalog", "product_prices", (
        "product_id", "sales_channel_id", "amount", "valid_from", "valid_to", "created_at", "created_by_employee_id",
    ), [(f"{r.product_sku}|{r.channel_code}", (ids["products"][r.product_sku], ids["sales_channels"][r.channel_code], r.amount, r.valid_from, r.valid_to, r.created_at, ids["employees"][r.created_by_employee_code] if r.created_by_employee_code else None)) for r in data.product_prices], "product_price_id", "product_price_id")

    ids["customers"] = _insert_many_returning(connection, "crm", "customers", (
        "customer_code", "customer_type", "display_name", "status", "created_at", "updated_at",
    ), [(r.code, (r.code, r.customer_type, r.display_name, r.status, r.created_at, r.updated_at)) for r in data.customers], "customer_code", "customer_id")
    customers = ids["customers"]

    for row in data.individual_profiles:
        connection.execute("INSERT INTO crm.individual_profiles (customer_id,cpf,birth_date,created_at,updated_at) VALUES (%s,%s,%s,%s,%s)", (customers[row.customer_code], row.cpf, row.birth_date, row.created_at, row.updated_at))
    ids["individual_profiles"] = {row.customer_code: customers[row.customer_code] for row in data.individual_profiles}
    for row in data.business_profiles:
        connection.execute("INSERT INTO crm.business_profiles (customer_id,legal_name,trade_name,cnpj,created_at,updated_at) VALUES (%s,%s,%s,%s,%s,%s)", (customers[row.customer_code], row.legal_name, row.trade_name, row.cnpj, row.created_at, row.updated_at))
    ids["business_profiles"] = {row.customer_code: customers[row.customer_code] for row in data.business_profiles}

    ids["customer_contacts"] = _insert_many_returning(connection, "crm", "customer_contacts", (
        "customer_id", "contact_type", "contact_value", "is_primary", "is_active", "created_at", "updated_at",
    ), [(r.logical_key, (customers[r.customer_code], r.contact_type, r.contact_value, r.is_primary, r.is_active, r.created_at, r.updated_at)) for r in data.customer_contacts], "customer_contact_id", "customer_contact_id")

    ids["customer_addresses"] = _insert_many_returning(connection, "crm", "customer_addresses", (
        "customer_id", "address_label", "recipient_name", "postal_code", "street", "street_number", "complement", "district", "city", "state_code", "country_code", "is_default", "is_active", "created_at", "updated_at",
    ), [(r.logical_key, (customers[r.customer_code], r.address_label, r.recipient_name, r.postal_code, r.street, r.street_number, r.complement, r.district, r.city, r.state_code, r.country_code, r.is_default, r.is_active, r.created_at, r.updated_at)) for r in data.customer_addresses], "customer_address_id", "customer_address_id")

    ids["stock_locations"] = _insert_many_returning(connection, "inventory", "stock_locations", (
        "store_id", "location_code", "name", "location_type", "status", "created_at", "updated_at",
    ), [(r.code, (ids["stores"].get(r.store_code) if r.store_code else None, r.code, r.name, r.location_type, r.status, r.created_at, r.updated_at)) for r in data.stock_locations], "location_code", "stock_location_id")
    return ids
