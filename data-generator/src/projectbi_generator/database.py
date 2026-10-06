"""Safe PostgreSQL configuration, schema guards and rollback-only smoke load."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

import psycopg
from psycopg import sql

SCHEMAS = (
    "core", "crm", "catalog", "sales", "procurement", "inventory",
    "payments", "logistics", "after_sales",
)
OPERATIONAL_TABLES = (
    ("core", "stores"), ("core", "employees"), ("core", "employee_roles"), ("core", "employee_assignments"),
    ("crm", "customers"), ("crm", "individual_profiles"), ("crm", "business_profiles"), ("crm", "customer_contacts"), ("crm", "customer_addresses"),
    ("catalog", "categories"), ("catalog", "brands"), ("catalog", "products"), ("catalog", "product_suppliers"), ("catalog", "product_prices"),
    ("sales", "sales_channels"), ("sales", "sales_orders"), ("sales", "sales_order_items"), ("sales", "order_status_history"), ("sales", "applied_discounts"),
    ("procurement", "suppliers"), ("procurement", "purchase_orders"), ("procurement", "purchase_order_items"), ("procurement", "goods_receipts"), ("procurement", "goods_receipt_items"),
    ("inventory", "stock_locations"), ("inventory", "stock_positions"), ("inventory", "stock_movements"), ("inventory", "stock_reservations"), ("inventory", "stock_transfers"), ("inventory", "stock_transfer_items"),
    ("payments", "payment_methods"), ("payments", "payments"), ("payments", "payment_installments"), ("payments", "refunds"),
    ("logistics", "carriers"), ("logistics", "fulfillments"), ("logistics", "fulfillment_items"), ("logistics", "fulfillment_events"),
    ("after_sales", "returns"), ("after_sales", "return_items"),
)


@dataclass(frozen=True)
class ConnectionSettings:
    host: str
    port: int
    database: str
    user: str
    password: str


class DatabaseGuardError(RuntimeError):
    """Raised before writes if the database differs from the approved empty schema."""


def _dotenv_values(path: Path) -> dict[str, str]:
    result: dict[str, str] = {}
    if not path.is_file():
        return result
    for raw_line in path.read_text(encoding="utf-8-sig").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        name, value = line.split("=", 1)
        name, value = name.strip(), value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
            value = value[1:-1]
        result[name] = value
    return result


def connection_settings(project_root: Path, environ: dict[str, str] | None = None) -> ConnectionSettings:
    process = os.environ if environ is None else environ
    fallback = _dotenv_values(project_root / ".env")

    def get(name: str) -> str:
        process_value = process.get(name, "")
        return process_value if process_value.strip() else fallback.get(name, "")

    required = ("POSTGRES_HOST", "POSTGRES_PORT", "POSTGRES_DB", "POSTGRES_USER", "POSTGRES_PASSWORD")
    values = {name: get(name) for name in required}
    missing = [name for name, value in values.items() if not value.strip()]
    if missing:
        raise ValueError("Configuração de banco ausente: " + ", ".join(missing))
    if values["POSTGRES_DB"] != "projeto_bi":
        raise DatabaseGuardError("POSTGRES_DB deve ser projeto_bi.")
    try:
        port = int(values["POSTGRES_PORT"])
    except ValueError as exc:
        raise ValueError("POSTGRES_PORT deve ser inteiro.") from exc
    return ConnectionSettings(values["POSTGRES_HOST"], port, values["POSTGRES_DB"], values["POSTGRES_USER"], values["POSTGRES_PASSWORD"])


def connect(settings: ConnectionSettings) -> psycopg.Connection:
    return psycopg.connect(
        host=settings.host,
        port=settings.port,
        dbname=settings.database,
        user=settings.user,
        password=settings.password,
        connect_timeout=10,
        application_name="projectbi_generator_smoke",
    )


def validate_database_identity(database_name: str, server_version: str) -> None:
    if database_name != "projeto_bi":
        raise DatabaseGuardError("Database conectada não é projeto_bi.")
    major = server_version.split(".", 1)[0]
    if major != "18":
        raise DatabaseGuardError("A integração exige PostgreSQL major version 18.")


def _table_counts(connection: psycopg.Connection) -> dict[str, int]:
    return {
        f"{schema}.{table}": connection.execute(
            sql.SQL("SELECT count(*) FROM {}.{}").format(sql.Identifier(schema), sql.Identifier(table))
        ).fetchone()[0]
        for schema, table in OPERATIONAL_TABLES
    }


def guard_empty_target(connection: psycopg.Connection) -> tuple[str, dict[str, int]]:
    identity = connection.execute("SELECT current_database(), current_setting('server_version')").fetchone()
    validate_database_identity(identity[0], identity[1])

    actual_schemas = tuple(row[0] for row in connection.execute(
        "SELECT nspname FROM pg_namespace WHERE nspname !~ '^pg_' AND nspname NOT IN ('information_schema', 'public') ORDER BY nspname"
    ).fetchall())
    if actual_schemas != tuple(sorted(SCHEMAS)):
        raise DatabaseGuardError("Schemas operacionais ausentes ou inesperados.")

    actual_tables = {
        (schema, table)
        for schema, table in connection.execute(
            "SELECT schemaname, tablename FROM pg_tables WHERE schemaname = ANY(%s)", (list(SCHEMAS),)
        ).fetchall()
    }
    if actual_tables != set(OPERATIONAL_TABLES):
        raise DatabaseGuardError("Tabelas ausentes ou inesperadas nos schemas aprovados.")

    address_columns = connection.execute(
        "SELECT column_name FROM information_schema.columns WHERE table_schema='core' AND table_name='stores' AND column_name = ANY(%s)",
        (["postal_code", "street", "street_number", "complement", "district", "city", "state_code", "country_code"],),
    ).fetchall()
    if len(address_columns) != 8:
        raise DatabaseGuardError("Migration incremental de endereço não está integralmente presente.")
    address_definition = {
        row[0]: (row[1], row[2], row[3])
        for row in connection.execute(
            "SELECT column_name, udt_name, character_maximum_length, is_nullable FROM information_schema.columns WHERE table_schema='core' AND table_name='stores' AND column_name = ANY(%s)",
            (["postal_code", "street", "street_number", "complement", "district", "city", "state_code", "country_code"],),
        ).fetchall()
    }
    expected_address_definition = {
        "postal_code": ("varchar", 8, "NO"), "street": ("varchar", 180, "NO"),
        "street_number": ("varchar", 30, "NO"), "complement": ("varchar", 100, "YES"),
        "district": ("varchar", 100, "NO"), "city": ("varchar", 120, "NO"),
        "state_code": ("bpchar", 2, "NO"), "country_code": ("bpchar", 2, "NO"),
    }
    if address_definition != expected_address_definition:
        raise DatabaseGuardError("Tipos ou nulabilidade das colunas de endereço divergem da migration aprovada.")
    address_checks = connection.execute(
        "SELECT count(*) FROM pg_constraint WHERE conrelid='core.stores'::regclass AND contype='c' AND conname = ANY(%s)",
        (["ck_stores_postal_code", "ck_stores_state_code", "ck_stores_country_code"],),
    ).fetchone()[0]
    address_index = connection.execute(
        "SELECT indexdef FROM pg_indexes WHERE schemaname='core' AND indexname='idx_stores_state_city'"
    ).fetchone()
    if address_checks != 3 or address_index is None or "(state_code, city)" not in address_index[0]:
        raise DatabaseGuardError("CHECKs ou índice da migration incremental 002 estão ausentes.")

    structural_counts = connection.execute("""
        SELECT c.contype, count(*)
          FROM pg_constraint c
          JOIN pg_class t ON t.oid=c.conrelid
          JOIN pg_namespace n ON n.oid=t.relnamespace
         WHERE n.nspname = ANY(%s)
         GROUP BY c.contype
    """, (list(SCHEMAS),)).fetchall()
    actual_constraints = dict(structural_counts)
    expected_constraints = {"p": 40, "f": 70, "c": 78, "u": 37}
    if any(actual_constraints.get(kind, 0) != count for kind, count in expected_constraints.items()):
        raise DatabaseGuardError("PK/FK/CHECK/UNIQUE divergem do schema aprovado.")
    physical_indexes = connection.execute(
        "SELECT count(*) FROM pg_indexes WHERE schemaname = ANY(%s)", (list(SCHEMAS),)
    ).fetchone()[0]
    if physical_indexes != 149:
        raise DatabaseGuardError("Índices físicos divergem do schema aprovado.")
    if connection.execute(
        "SELECT count(*) FROM pg_constraint c JOIN pg_namespace n ON n.oid=c.connamespace WHERE n.nspname = ANY(%s) AND NOT c.convalidated",
        (list(SCHEMAS),),
    ).fetchone()[0]:
        raise DatabaseGuardError("Há constraints operacionais não validadas.")

    counts = _table_counts(connection)
    if any(counts.values()):
        populated = next(name for name, count in counts.items() if count)
        raise DatabaseGuardError(f"Database contém dados inesperados em {populated}; nenhuma carga foi iniciada.")
    return identity[1], counts


def confirm_empty_after_rollback(settings: ConnectionSettings) -> dict[str, int]:
    with connect(settings) as connection:
        version, counts = guard_empty_target(connection)
        if version.split(".", 1)[0] != "18":
            raise DatabaseGuardError("Versão mudou após rollback.")
        return counts


def run_rollback_smoke(settings: ConnectionSettings, config, data):
    """Load and validate smoke master data in one transaction, then explicitly roll it back."""
    from projectbi_generator.repositories.master_data import load_master_data
    from projectbi_generator.validation.master_data import validate_master_data

    connection = connect(settings)
    version = ""
    counts: dict[str, int] = {}
    try:
        version, _ = guard_empty_target(connection)
        validate_master_data(data, config)
        maps = load_master_data(connection, data)
        counts = validate_loaded_master(connection, config)
        connection.execute("ROLLBACK")
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()

    remaining = confirm_empty_after_rollback(settings)
    if any(remaining.values()):
        raise DatabaseGuardError("Após ROLLBACK, foram encontradas linhas persistidas.")
    return {"server_version": version, "counts": counts, "id_map_tables": len(maps), "remaining": remaining}


def validate_loaded_master(connection: psycopg.Connection, config) -> dict[str, int]:
    from projectbi_generator.models.entities import MasterData

    expected = config.volumes
    table_pairs = {
        "stores": ("core", "stores"), "employees": ("core", "employees"),
        "employee_roles": ("core", "employee_roles"), "employee_assignments": ("core", "employee_assignments"),
        "customers": ("crm", "customers"), "individual_profiles": ("crm", "individual_profiles"),
        "business_profiles": ("crm", "business_profiles"), "customer_contacts": ("crm", "customer_contacts"),
        "customer_addresses": ("crm", "customer_addresses"), "categories": ("catalog", "categories"),
        "brands": ("catalog", "brands"), "products": ("catalog", "products"),
        "product_suppliers": ("catalog", "product_suppliers"), "product_prices": ("catalog", "product_prices"),
        "stock_locations": ("inventory", "stock_locations"), "payment_methods": ("payments", "payment_methods"),
        "carriers": ("logistics", "carriers"), "sales_channels": ("sales", "sales_channels"),
        "suppliers": ("procurement", "suppliers"),
    }
    counts = {}
    for key, (schema, table) in table_pairs.items():
        count = connection.execute(sql.SQL("SELECT count(*) FROM {}.{}").format(sql.Identifier(schema), sql.Identifier(table))).fetchone()[0]
        if count != expected[key]:
            raise DatabaseGuardError(f"Contagem transacional divergente em {schema}.{table}.")
        counts[key] = count

    violations = connection.execute("""
        SELECT
          (SELECT count(*) FROM catalog.products WHERE specifications IS NOT NULL AND jsonb_typeof(specifications) <> 'object'),
          (SELECT count(*) FROM crm.customers c WHERE
             (c.customer_type='individual' AND ((SELECT count(*) FROM crm.individual_profiles p WHERE p.customer_id=c.customer_id)<>1 OR EXISTS(SELECT 1 FROM crm.business_profiles b WHERE b.customer_id=c.customer_id))) OR
             (c.customer_type='business' AND ((SELECT count(*) FROM crm.business_profiles b WHERE b.customer_id=c.customer_id)<>1 OR EXISTS(SELECT 1 FROM crm.individual_profiles p WHERE p.customer_id=c.customer_id)))),
          (SELECT count(*) FROM core.stores WHERE country_code <> 'BR' OR postal_code !~ '^[0-9]{8}$'),
          (SELECT count(*) FROM catalog.products WHERE unit_of_measure <> 'unit'),
          (SELECT count(*) FROM catalog.product_suppliers WHERE is_preferred AND NOT is_active)
    """).fetchone()
    if any(violations):
        raise DatabaseGuardError("Validação SQL encontrou divergência em JSON, perfil, geografia, unidade ou fornecedor preferencial.")

    customer_mix = connection.execute("SELECT customer_type, count(*) FROM crm.customers GROUP BY customer_type").fetchall()
    if dict(customer_mix) != {"individual": config.composition["individual_customers"], "business": config.composition["business_customers"]}:
        raise DatabaseGuardError("Distribuição PF/PJ no banco diverge da configuração smoke.")

    if connection.execute("""
        SELECT EXISTS (
          SELECT 1 FROM catalog.product_prices a JOIN catalog.product_prices b
            ON a.product_id=b.product_id AND a.sales_channel_id=b.sales_channel_id AND a.product_price_id<b.product_price_id
           AND a.valid_from < coalesce(b.valid_to, 'infinity'::timestamptz)
           AND b.valid_from < coalesce(a.valid_to, 'infinity'::timestamptz)
        )
    """).fetchone()[0]:
        raise DatabaseGuardError("Validação SQL encontrou vigências de preço sobrepostas.")

    if connection.execute("SELECT count(*) FROM sales.sales_channels WHERE channel_type='physical'").fetchone()[0] != 1 or connection.execute("SELECT count(*) FROM sales.sales_channels WHERE channel_type='ecommerce'").fetchone()[0] != 1 or connection.execute("SELECT count(*) FROM sales.sales_channels WHERE channel_type='marketplace'").fetchone()[0] != 2:
        raise DatabaseGuardError("Composição dos canais diverge do profile smoke.")
    if connection.execute("SELECT count(*) FROM inventory.stock_locations WHERE status='active' AND location_type IN ('store','warehouse')").fetchone()[0] != expected["stock_locations"]:
        raise DatabaseGuardError("Locais de estoque smoke inválidos.")
    if connection.execute("SELECT count(*) FROM catalog.product_suppliers WHERE is_preferred AND is_active GROUP BY product_id HAVING count(*) > 1").fetchall():
        raise DatabaseGuardError("Há mais de um fornecedor preferencial ativo para algum produto.")
    return counts


def run_rollback_transaction_smoke(settings: ConnectionSettings, config):
    """Load master plus the phase-3C transactional flow, validate it, and explicitly roll back."""
    from projectbi_generator.generators.master import generate_master_data
    from projectbi_generator.generators.transactions import generate_transactions
    from projectbi_generator.repositories.master_data import load_master_data
    from projectbi_generator.repositories.transactions import load_transaction_data
    from projectbi_generator.validation.database_transactions import validate_loaded_transactions
    from projectbi_generator.validation.master_data import validate_master_data
    from projectbi_generator.validation.transactions import validate_transactional_data

    if config.profile != "smoke":
        raise ValueError("A integração transacional aceita somente o profile smoke.")
    master = generate_master_data(config)
    validate_master_data(master, config)
    data = generate_transactions(config, master)
    validate_transactional_data(data, master, config)

    connection = connect(settings)
    try:
        connection.execute("BEGIN")
        version, _ = guard_empty_target(connection)
        ids = load_master_data(connection, master)
        transaction_ids = load_transaction_data(connection, master, data, ids)
        validate_loaded_master(connection, config)
        sql_counts = validate_loaded_transactions(connection, config, master, data)
        connection.execute("ROLLBACK")
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()

    remaining = confirm_empty_after_rollback(settings)
    if any(remaining.values()):
        raise DatabaseGuardError("Após ROLLBACK, foram encontradas linhas nas 40 tabelas operacionais.")
    return {
        "server_version": version,
        "summary": data.summary(),
        "sql_counts": sql_counts,
        "id_map_tables": len(ids),
        "transaction_id_maps": sum(bool(value) for value in transaction_ids.values()),
        "remaining": remaining,
    }


def run_rollback_full_smoke(settings: ConnectionSettings, config):
    """Load and validate all applicable operational domains, then prove complete rollback."""
    from projectbi_generator.generators.completion import extend_transactions
    from projectbi_generator.generators.master import generate_master_data
    from projectbi_generator.generators.transactions import generate_transactions
    from projectbi_generator.repositories.master_data import load_master_data
    from projectbi_generator.repositories.transactions import load_transaction_data
    from projectbi_generator.validation.completion import validate_completed_data
    from projectbi_generator.validation.database_transactions import validate_loaded_transactions
    from projectbi_generator.validation.master_data import validate_master_data
    from projectbi_generator.validation.transactions import validate_transactional_data

    if config.profile != "smoke":
        raise ValueError("A integração full aceita somente o profile smoke.")
    master = generate_master_data(config)
    validate_master_data(master, config)
    data = generate_transactions(config, master)
    validate_transactional_data(data, master, config)
    extend_transactions(config, master, data)
    validate_completed_data(data, master, config)

    connection = connect(settings)
    try:
        connection.execute("BEGIN")
        version, _ = guard_empty_target(connection)
        ids = load_master_data(connection, master)
        transaction_ids = load_transaction_data(connection, master, data, ids)
        validate_loaded_master(connection, config)
        sql_counts = validate_loaded_transactions(connection, config, master, data, validate_phase3c=False)
        connection.execute("ROLLBACK")
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()

    remaining = confirm_empty_after_rollback(settings)
    if any(remaining.values()):
        raise DatabaseGuardError("Após ROLLBACK, foram encontradas linhas nas 40 tabelas operacionais.")
    summary = data.summary()
    return {
        "server_version": version,
        "summary": {
            "orders": summary["sales_orders"],
            "payments": summary["payments"],
            "declined_attempts": summary["declined_attempts"],
            "retries": summary["payment_retries"],
            "split_payment_orders": summary["split_payment_orders"],
            "installments": summary["payment_installments"],
            "fulfillments": summary["fulfillments"],
            "fulfillment_events": summary["fulfillment_events"],
            "delivery_events": sum(row.event_type in {"prepared", "dispatched", "delivery_attempt", "delivered", "exception", "cancelled"} for row in data.fulfillment_events),
            "pickup_events": sum(row.event_type in {"prepared", "pickup_ready", "picked_up", "exception", "cancelled"} for row in data.fulfillment_events),
            "transfers": summary["stock_transfers"],
            "transfer_items": summary["stock_transfer_items"],
            "transfer_out_movements": sum(row.movement_type == "transfer_out" for row in data.stock_movements),
            "transfer_in_movements": sum(row.movement_type == "transfer_in" for row in data.stock_movements),
            "returns": summary["returns"],
            "return_items": summary["return_items"],
            "sellable_returns": sum(row.stock_destination == "sellable" and row.quantity_received > 0 for row in data.return_items),
            "nonsellable_returns": sum(row.stock_destination in {"quarantine", "repair", "discard"} and row.quantity_received > 0 for row in data.return_items),
            "refunds": summary["refunds"],
            "stock_movements": summary["stock_movements"],
            "ending_stock": summary["ending_stock"],
            "realized_cost": summary["realized_cost"],
            "captured_amount": summary["captured_amount"],
            "refund_amount": summary["refund_amount"],
            "net_financial_amount": summary["net_financial_amount"],
        },
        "sql_counts": sql_counts,
        "master_id_maps": len(ids),
        "transaction_id_maps": sum(bool(value) for value in transaction_ids.values()),
        "remaining": remaining,
    }
