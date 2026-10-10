"""Safe PostgreSQL configuration, schema guards and rollback-only smoke load."""

from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import timedelta
from decimal import Decimal
from pathlib import Path
from time import perf_counter

import psycopg
from psycopg import sql

from projectbi_generator.validation.sql_diagnostics import analyze_tables, run_sql_validation, set_validation_timeout

SCHEMAS = (
    "core", "crm", "catalog", "sales", "procurement", "inventory",
    "payments", "logistics", "after_sales",
)
OPERATIONAL_TABLES = (
    ("core", "stores"), ("core", "employees"), ("core", "employee_roles"), ("core", "employee_assignments"),
    ("crm", "customers"), ("crm", "individual_profiles"), ("crm", "business_profiles"), ("crm", "customer_contacts"), ("crm", "customer_addresses"),
    ("catalog", "categories"), ("catalog", "brands"), ("catalog", "products"), ("catalog", "product_suppliers"), ("catalog", "product_prices"),
    ("sales", "sales_channels"), ("sales", "sales_orders"), ("sales", "sales_order_items"), ("sales", "order_status_history"), ("sales", "applied_discounts"),
    ("sales", "sales_order_item_cancellations"),
    ("procurement", "suppliers"), ("procurement", "purchase_orders"), ("procurement", "purchase_order_items"), ("procurement", "goods_receipts"), ("procurement", "goods_receipt_items"),
    ("inventory", "stock_locations"), ("inventory", "stock_positions"), ("inventory", "stock_movements"), ("inventory", "stock_reservations"), ("inventory", "stock_transfers"), ("inventory", "stock_transfer_items"),
    ("payments", "payment_methods"), ("payments", "payments"), ("payments", "payment_installments"), ("payments", "refunds"),
    ("logistics", "carriers"), ("logistics", "fulfillments"), ("logistics", "fulfillment_items"), ("logistics", "fulfillment_events"),
    ("after_sales", "returns"), ("after_sales", "return_items"),
)
MASTER_TABLES = OPERATIONAL_TABLES[:19]


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


def _inspect_target(connection: psycopg.Connection, *, require_empty: bool) -> tuple[str, dict[str, int]]:
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

    cancellation_columns = connection.execute("""
        SELECT table_schema, table_name, column_name, data_type, is_nullable
          FROM information_schema.columns
         WHERE (table_schema='sales' AND table_name='sales_order_items'
                AND column_name IN ('fulfilled_quantity','cancelled_quantity'))
            OR (table_schema='sales' AND table_name='sales_order_item_cancellations')
            OR (table_schema='payments' AND table_name='refunds'
                AND column_name='sales_order_item_cancellation_id')
    """).fetchall()
    required_cancellation_columns = {
        ("sales", "sales_order_items", "fulfilled_quantity", "bigint", "NO"),
        ("sales", "sales_order_items", "cancelled_quantity", "bigint", "NO"),
        ("payments", "refunds", "sales_order_item_cancellation_id", "bigint", "YES"),
    }
    actual_cancellation_columns = {
        (row[0], row[1], row[2], row[3], row[4]) for row in cancellation_columns
        if row[1] != "sales_order_item_cancellations"
    }
    if not required_cancellation_columns.issubset(actual_cancellation_columns) or connection.execute(
        "SELECT count(*) FROM information_schema.columns WHERE table_schema='sales' AND table_name='sales_order_item_cancellations'"
    ).fetchone()[0] != 12:
        raise DatabaseGuardError("Migration 003 não possui todas as colunas esperadas de cancelamento/refund.")
    cancellation_guards = connection.execute("""
        SELECT
          (SELECT count(*) FROM pg_constraint WHERE conname = ANY(%s)),
          (SELECT count(*) FROM pg_trigger WHERE NOT tgisinternal AND tgname = ANY(%s)),
          (SELECT count(*) FROM pg_indexes WHERE schemaname IN ('sales','payments') AND indexname = ANY(%s))
    """, (
        ["ck_sales_order_items_resolution_nonnegative", "ck_sales_order_items_resolution_cap",
         "ck_sales_order_item_cancellations_quantity", "ck_sales_order_item_cancellations_reason",
         "ck_sales_order_item_cancellations_amounts", "ck_sales_order_item_cancellations_net",
         "ck_refunds_single_origin", "fk_sales_order_item_cancellations_item",
         "fk_refunds_item_cancellation"],
        ["trg_fulfillment_items_sync_item_quantity", "trg_item_cancellations_sync_item_quantity"],
        ["idx_sales_order_item_cancellations_item", "idx_sales_order_item_cancellations_order",
         "idx_refunds_item_cancellation"],
    )).fetchone()
    if cancellation_guards != (9, 2, 3):
        raise DatabaseGuardError("Constraints, triggers ou índices da migration 003 divergem do schema aprovado.")

    structural_counts = connection.execute("""
        SELECT c.contype, count(*)
          FROM pg_constraint c
          JOIN pg_class t ON t.oid=c.conrelid
          JOIN pg_namespace n ON n.oid=t.relnamespace
         WHERE n.nspname = ANY(%s)
         GROUP BY c.contype
    """, (list(SCHEMAS),)).fetchall()
    actual_constraints = dict(structural_counts)
    expected_constraints = {"p": 41, "f": 72, "c": 85, "u": 38}
    if any(actual_constraints.get(kind, 0) != count for kind, count in expected_constraints.items()):
        raise DatabaseGuardError("PK/FK/CHECK/UNIQUE divergem do schema aprovado.")
    physical_indexes = connection.execute(
        "SELECT count(*) FROM pg_indexes WHERE schemaname = ANY(%s)", (list(SCHEMAS),)
    ).fetchone()[0]
    if physical_indexes != 154:
        raise DatabaseGuardError("Índices físicos divergem do schema aprovado.")
    if connection.execute(
        "SELECT count(*) FROM pg_constraint c JOIN pg_namespace n ON n.oid=c.connamespace WHERE n.nspname = ANY(%s) AND NOT c.convalidated",
        (list(SCHEMAS),),
    ).fetchone()[0]:
        raise DatabaseGuardError("Há constraints operacionais não validadas.")

    counts = _table_counts(connection)
    if require_empty and any(counts.values()):
        populated = next(name for name, count in counts.items() if count)
        raise DatabaseGuardError(f"Database contém dados inesperados em {populated}; nenhuma carga foi iniciada.")
    return identity[1], counts


def guard_empty_target(connection: psycopg.Connection) -> tuple[str, dict[str, int]]:
    """Validate the approved structure and refuse any preexisting row."""
    return _inspect_target(connection, require_empty=True)


def inspect_target(connection: psycopg.Connection) -> tuple[str, dict[str, int]]:
    """Validate identity/schema/constraints/counts without requiring an empty dataset."""
    return _inspect_target(connection, require_empty=False)


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

    set_validation_timeout(connection)
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
        count = run_sql_validation(
            connection,
            f"master.table_count.{schema}.{table}",
            sql.SQL("SELECT count(*) FROM {}.{}").format(sql.Identifier(schema), sql.Identifier(table)).as_string(connection),
        )[0]
        if count != expected[key]:
            raise DatabaseGuardError(f"Contagem transacional divergente em {schema}.{table}.")
        counts[key] = count

    checks = (
        ("master.product_specifications_json", "SELECT count(*) FROM catalog.products WHERE specifications IS NOT NULL AND jsonb_typeof(specifications) <> 'object'"),
        ("master.customer_profile_exclusivity", """SELECT count(*) FROM crm.customers c WHERE
             (c.customer_type='individual' AND ((SELECT count(*) FROM crm.individual_profiles p WHERE p.customer_id=c.customer_id)<>1 OR EXISTS(SELECT 1 FROM crm.business_profiles b WHERE b.customer_id=c.customer_id))) OR
             (c.customer_type='business' AND ((SELECT count(*) FROM crm.business_profiles b WHERE b.customer_id=c.customer_id)<>1 OR EXISTS(SELECT 1 FROM crm.individual_profiles p WHERE p.customer_id=c.customer_id)))"""),
        ("master.store_geography", "SELECT count(*) FROM core.stores WHERE country_code <> 'BR' OR postal_code !~ '^[0-9]{8}$'"),
        ("master.product_unit_of_measure", "SELECT count(*) FROM catalog.products WHERE unit_of_measure <> 'unit'"),
        ("master.preferred_supplier_active", "SELECT count(*) FROM catalog.product_suppliers WHERE is_preferred AND NOT is_active"),
    )
    violations = {name: run_sql_validation(connection, name, statement, expect_zero=True)[0]
                  for name, statement in checks}
    if any(violations.values()):
        failed = ", ".join(name for name, count in violations.items() if count)
        raise DatabaseGuardError("Validação SQL encontrou divergência em: " + failed)

    customer_mix = run_sql_validation(
        connection, "master.customer_type_distribution",
        "SELECT customer_type, count(*) FROM crm.customers GROUP BY customer_type ORDER BY customer_type",
        fetch="all",
        expected_result=[("business", config.composition["business_customers"]),
                         ("individual", config.composition["individual_customers"])],
    )
    if dict(customer_mix) != {"individual": config.composition["individual_customers"], "business": config.composition["business_customers"]}:
        raise DatabaseGuardError("Distribuição PF/PJ no banco diverge da configuração smoke.")

    if run_sql_validation(connection, "master.product_price_nonoverlap", """SELECT EXISTS (
          SELECT 1 FROM catalog.product_prices a JOIN catalog.product_prices b
            ON a.product_id=b.product_id AND a.sales_channel_id=b.sales_channel_id AND a.product_price_id<b.product_price_id
           AND a.valid_from < coalesce(b.valid_to, 'infinity'::timestamptz)
           AND b.valid_from < coalesce(a.valid_to, 'infinity'::timestamptz)
        )""", expect_zero=True)[0]:
        raise DatabaseGuardError("Validação SQL encontrou vigências de preço sobrepostas.")

    channels = run_sql_validation(
        connection, "master.sales_channel_types",
        "SELECT channel_type, count(*) FROM sales.sales_channels GROUP BY channel_type ORDER BY channel_type",
        fetch="all", expected_result=[("ecommerce", 1), ("marketplace", 2), ("physical", 1)],
    )
    if dict(channels) != {"physical": 1, "ecommerce": 1, "marketplace": 2}:
        raise DatabaseGuardError("Composição dos canais diverge do profile smoke.")
    active_locations = run_sql_validation(
        connection, "master.active_stock_locations",
        "SELECT count(*) FROM inventory.stock_locations WHERE status='active' AND location_type IN ('store','warehouse')",
        expected_result=(expected["stock_locations"],),
    )[0]
    if active_locations != expected["stock_locations"]:
        raise DatabaseGuardError("Locais de estoque smoke inválidos.")
    if run_sql_validation(connection, "master.single_preferred_supplier_per_product",
        "SELECT count(*) FROM (SELECT product_id FROM catalog.product_suppliers WHERE is_preferred AND is_active GROUP BY product_id HAVING count(*) > 1) q",
        expect_zero=True)[0]:
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
        transaction_ids = load_transaction_data(connection, master, data, ids, config.batch_size)
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
        raise DatabaseGuardError("Após ROLLBACK, foram encontradas linhas nas tabelas operacionais aprovadas.")
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
        transaction_ids = load_transaction_data(connection, master, data, ids, config.batch_size)
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
        raise DatabaseGuardError("Após ROLLBACK, foram encontradas linhas nas tabelas operacionais aprovadas.")
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


def run_rollback_incremental_full_smoke(settings: ConnectionSettings, config, *, include_completion: bool = True):
    """Run incremental 3C or full 3C+3D through the PostgreSQL sink and roll back."""
    from projectbi_generator.generators.completion import generate_full_transactions_incremental
    from projectbi_generator.generators.master import generate_master_data
    from projectbi_generator.generators.transactions import generate_transactions_incremental
    from projectbi_generator.repositories.master_data import load_master_data
    from projectbi_generator.repositories.postgres_sink import PostgreSQLTransactionSink
    from projectbi_generator.validation.master_data import validate_master_data
    from projectbi_generator.validation.database_transactions import validate_loaded_transactions

    if config.profile not in {"smoke", "portfolio"}:
        raise ValueError("A integração PostgreSQL aceita smoke ou fixture interna portfolio.")
    started = perf_counter()
    master = generate_master_data(config)
    validate_master_data(master, config)
    connection = connect(settings)
    cancellation_checks: dict[str, int | bool | Decimal] = {}
    try:
        connection.execute("BEGIN")
        version, _ = guard_empty_target(connection)
        master_ids = load_master_data(connection, master)
        validate_loaded_master(connection, config)
        sink = PostgreSQLTransactionSink(connection, master, master_ids, config.batch_size)
        if include_completion:
            result = generate_full_transactions_incremental(config, master, sink, batch_size=config.batch_size)
        else:
            result = generate_transactions_incremental(config, master, sink, batch_size=config.batch_size)
        if sink._pending_state_events or sink._pending_movements:
            raise DatabaseGuardError("Sink encerrou com movimentos/estados causais sem par.")
        analyze_tables(connection, OPERATIONAL_TABLES)

        class _StreamSummary:
            def counts(self):
                counts = result.counts()
                counts["discounts"] = counts.pop("applied_discounts", 0)
                counts["reservations"] = counts.pop("stock_reservations", 0)
                return counts

            def summary(self):
                return {"realized_cost": result.aggregates["realized_cost"]}

        sql_counts, sql_invariant_counts = validate_loaded_transactions(
            connection, config, master, _StreamSummary(), validate_phase3c=False, include_check_results=True,
        )
        aggregates = result.aggregates
        sql_margin_metrics = {}
        if include_completion:
            # M3 oracle: execute the same reviewed analytical margin baseline while
            # the rollback fixture is visible, then return only aggregate values.
            from projectbi_generator.validation.baselines import BASELINE_QUERIES

            margin_rows = connection.execute(BASELINE_QUERIES["11_cost_and_margin.sql"]).fetchall()
            column_indexes = {
                "completed_realized_revenue": 3,
                "completed_canonical_fulfillment_cogs": 5,
                "completed_sellable_return_cogs_reversed": 6,
                "completed_non_sellable_return_loss_included": 7,
                "completed_margin_cogs": 8,
            }
            for metric, index in column_indexes.items():
                sql_margin_metrics[metric] = sum((row[index] for row in margin_rows), Decimal("0.00")).quantize(Decimal("0.01"))
        if config.profile == "portfolio" and config.sales_order_target == 10000 and include_completion:
            cancellation_checks = {
                "partially_fulfilled_cancellation_rows": connection.execute("""
                    SELECT count(*) FROM sales.sales_order_item_cancellations c
                    JOIN sales.sales_order_items i USING (sales_order_id,sales_order_item_id)
                    WHERE i.fulfilled_quantity > 0
                """).fetchone()[0],
                "cancellations_with_completed_refund": connection.execute("""
                    SELECT count(*) FROM sales.sales_order_item_cancellations c
                    WHERE EXISTS (SELECT 1 FROM payments.refunds r
                      WHERE r.sales_order_id=c.sales_order_id
                        AND r.sales_order_item_cancellation_id=c.sales_order_item_cancellation_id
                        AND r.status='completed')
                """).fetchone()[0],
                "split_payment_orders": connection.execute("""
                    SELECT count(*) FROM (
                      SELECT sales_order_id FROM payments.payments
                      WHERE status IN ('captured','settled') GROUP BY sales_order_id HAVING count(*)>1
                    ) split
                """).fetchone()[0],
            }
            candidate = connection.execute("""
                SELECT i.sales_order_id,i.sales_order_item_id,o.placed_at
                  FROM sales.sales_order_items i JOIN sales.sales_orders o USING (sales_order_id)
                 WHERE i.fulfilled_quantity+i.cancelled_quantity=i.quantity
                 ORDER BY i.sales_order_item_id LIMIT 1
            """).fetchone()
            if candidate is None:
                raise DatabaseGuardError("Fixture 10k sem item resolvido para testar o limite cumulativo negativo.")
            connection.execute("SAVEPOINT cancellation_limit_negative")
            try:
                connection.execute("""
                    INSERT INTO sales.sales_order_item_cancellations
                      (sales_order_id,sales_order_item_id,cancelled_quantity,cancellation_reason,cancelled_at,
                       gross_cancelled_amount,discount_cancelled_amount,net_cancelled_amount,shipping_cancelled_amount,created_at)
                    VALUES (%s,%s,1,'stock_timeout',%s + interval '14 days',0,0,0,0,%s + interval '14 days')
                """, (candidate[0],candidate[1],candidate[2],candidate[2]))
            except psycopg.errors.CheckViolation as exc:
                connection.execute("ROLLBACK TO SAVEPOINT cancellation_limit_negative")
                if exc.diag.constraint_name != "ck_sales_order_items_resolution_cap":
                    raise
                cancellation_checks["over_limit_insert_rejected"] = True
            else:
                connection.execute("ROLLBACK TO SAVEPOINT cancellation_limit_negative")
                raise DatabaseGuardError("Trigger/cap aceitou cancelamento acima do saldo elegível.")
            finally:
                connection.execute("RELEASE SAVEPOINT cancellation_limit_negative")

            connection.execute("SAVEPOINT split_payment_cancellation_fixture")
            try:
                sample = connection.execute("""
                    SELECT o.sales_channel_id,o.customer_id,i.product_id,i.sku_snapshot,i.product_name_snapshot,o.placed_at,
                           p.payment_method_id
                      FROM sales.sales_orders o
                      JOIN sales.sales_order_items i USING (sales_order_id)
                      JOIN payments.payments p USING (sales_order_id)
                     WHERE o.channel_type='ecommerce' AND p.status IN ('captured','settled')
                     ORDER BY o.sales_order_id,i.line_number,p.payment_id LIMIT 1
                """).fetchone()
                if sample is None:
                    raise DatabaseGuardError("Fixture sem dimensões comerciais para o teste de refund dividido.")
                channel_id,customer_id,product_id,sku,name,placed_at,payment_method_id=sample
                paid_at=placed_at+timedelta(hours=1)
                cancelled_at=placed_at+timedelta(days=14)
                order_id=connection.execute("""
                    INSERT INTO sales.sales_orders
                      (order_number,sales_channel_id,channel_type,customer_id,order_status,placed_at,currency_code,
                       subtotal_amount,discount_amount,shipping_amount,total_amount,created_at,updated_at)
                    VALUES ('SO-CANCEL-SPLIT-TEST',%s,'ecommerce',%s,'confirmed',%s,'BRL',300,30,0,270,%s,%s)
                    RETURNING sales_order_id
                """,(channel_id,customer_id,placed_at,placed_at,placed_at)).fetchone()[0]
                item_id=connection.execute("""
                    INSERT INTO sales.sales_order_items
                      (sales_order_id,line_number,product_id,sku_snapshot,product_name_snapshot,quantity,unit_sale_price,created_at)
                    VALUES (%s,1,%s,%s,%s,3,100,%s) RETURNING sales_order_item_id
                """,(order_id,product_id,sku,name,placed_at)).fetchone()[0]
                connection.execute("""
                    INSERT INTO sales.applied_discounts
                      (sales_order_id,sales_order_item_id,discount_scope,amount,created_at)
                    VALUES (%s,%s,'line',30,%s)
                """,(order_id,item_id,placed_at))
                payment_ids=[]
                for suffix,amount in (("A",Decimal("150.00")),("B",Decimal("120.00"))):
                    payment_ids.append(connection.execute("""
                        INSERT INTO payments.payments
                          (sales_order_id,payment_method_id,payment_reference,status,amount,currency_code,
                           attempted_at,authorized_at,settled_at,created_at,updated_at)
                        VALUES (%s,%s,%s,'captured',%s,'BRL',%s,%s,%s,%s,%s) RETURNING payment_id
                    """,(order_id,payment_method_id,f"SPLIT-CANCEL-{suffix}",amount,paid_at,paid_at,paid_at,paid_at,paid_at)).fetchone()[0])
                # A prior refund leaves only BRL 50.00 on payment A, so the BRL 90.00
                # cancellation refund must continue to payment B.
                connection.execute("""
                    INSERT INTO payments.refunds
                      (sales_order_id,payment_id,status,amount,reason_code,requested_at,processed_at,created_at,updated_at)
                    VALUES (%s,%s,'completed',100,'customer_request',%s,%s,%s,%s)
                """,(order_id,payment_ids[0],cancelled_at,cancelled_at,cancelled_at,cancelled_at))
                cancellation_id=connection.execute("""
                    INSERT INTO sales.sales_order_item_cancellations
                      (sales_order_id,sales_order_item_id,cancelled_quantity,cancellation_reason,cancelled_at,
                       gross_cancelled_amount,discount_cancelled_amount,net_cancelled_amount,created_at)
                    VALUES (%s,%s,1,'stock_timeout',%s,100,10,90,%s) RETURNING sales_order_item_cancellation_id
                """,(order_id,item_id,cancelled_at,cancelled_at)).fetchone()[0]
                for payment_id,amount in ((payment_ids[0],Decimal("50.00")),(payment_ids[1],Decimal("40.00"))):
                    connection.execute("""
                        INSERT INTO payments.refunds
                          (sales_order_id,payment_id,status,amount,reason_code,requested_at,processed_at,
                           sales_order_item_cancellation_id,created_at,updated_at)
                        VALUES (%s,%s,'completed',%s,'stock_timeout',%s,%s,%s,%s,%s)
                    """,(order_id,payment_id,amount,cancelled_at,cancelled_at,cancellation_id,cancelled_at,cancelled_at))
                split_refund = connection.execute("""
                    SELECT count(DISTINCT payment_id),sum(amount)
                      FROM payments.refunds
                     WHERE sales_order_id=%s AND sales_order_item_cancellation_id=%s AND status='completed'
                """,(order_id,cancellation_id)).fetchone()
                over_cap = connection.execute("""
                    SELECT count(*) FROM (
                      SELECT p.payment_id,p.amount captured,coalesce(sum(r.amount),0) refunded
                        FROM payments.payments p LEFT JOIN payments.refunds r
                          ON r.payment_id=p.payment_id AND r.status='completed'
                       WHERE p.sales_order_id=%s GROUP BY p.payment_id,p.amount
                    ) payment_totals WHERE refunded>captured
                """,(order_id,)).fetchone()
                if split_refund != (2,Decimal("90.00")) or over_cap[0] != 0:
                    raise DatabaseGuardError("Refund de cancelamento dividido não reconciliou dentro dos limites capturados.")
                cancellation_checks["split_cancellation_refund_payments"] = split_refund[0]
                cancellation_checks["split_cancellation_refund_amount"] = split_refund[1]
            finally:
                connection.execute("ROLLBACK TO SAVEPOINT split_payment_cancellation_fixture")
                connection.execute("RELEASE SAVEPOINT split_payment_cancellation_fixture")
        relational_rows = sum(value for table, value in result.counts().items() if table != "stock_state_events")
        if sink.metrics.rows_inserted != relational_rows:
            raise DatabaseGuardError(
                "Métrica de inserts do sink diverge das linhas relacionais: "
                f"inserted={sink.metrics.rows_inserted}, fluxo={relational_rows}, counts={result.counts()}."
            )
        if include_completion:
            expected_financials = (Decimal("2791128.94"), Decimal("18420.97"), Decimal("2772707.97"), Decimal("369830.61051434"))
            actual_financials = (aggregates["captured_amount"], aggregates["refund_amount"], aggregates["net_financial_amount"], aggregates["realized_cost"])
            if config.profile == "smoke" and actual_financials != expected_financials:
                raise DatabaseGuardError("Totais financeiros/custo do full smoke incremental divergiram do oracle.")
        connection.execute("ROLLBACK")
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()

    remaining = confirm_empty_after_rollback(settings)
    if any(remaining.values()):
        raise DatabaseGuardError("Após ROLLBACK, foram encontradas linhas nas tabelas operacionais aprovadas.")
    return {
        "server_version": version,
        "duration_seconds": perf_counter() - started,
        "includes_completion": include_completion,
        "counts": result.counts(),
        "transaction_rows": relational_rows,
        "aggregates": dict(aggregates),
        "sql_margin_metrics": sql_margin_metrics,
        "cancellation_checks": cancellation_checks,
        "sql_counts": sql_counts,
        "sql_invariant_counts": sql_invariant_counts,
        "master_id_maps": len(master_ids),
        "sink_metrics": vars(sink.metrics),
        "id_metrics": {
            "current_transaction_id_entries": sink.ids.current_entries,
            "current_transaction_id_entries_by_type": sink.ids.current_by_type,
            "max_transaction_id_entries": sink.ids.max_entries,
            "max_by_type": dict(sink.ids.max_by_type),
        },
        "emitter_metrics": dict(result.runtime_metrics),
        "remaining": remaining,
    }
