"""One-time, guarded persistent load for the approved Portfolio profile."""

from __future__ import annotations

from datetime import datetime
from time import monotonic, perf_counter

from projectbi_generator.database import (
    DatabaseGuardError,
    MASTER_TABLES,
    OPERATIONAL_TABLES,
    connect,
    guard_empty_target,
    inspect_target,
    validate_loaded_master,
)
from projectbi_generator.generators.completion import generate_full_transactions_incremental
from projectbi_generator.generators.master import generate_master_data
from projectbi_generator.repositories.master_data import load_master_data
from projectbi_generator.repositories.postgres_sink import PostgreSQLTransactionSink
from projectbi_generator.validation.database_transactions import validate_loaded_transactions
from projectbi_generator.validation.master_data import validate_master_data
from projectbi_generator.validation.sql_diagnostics import analyze_tables
from projectbi_generator.validation.portfolio import (
    classify_portfolio_distributions,
    collect_portfolio_metrics,
    validate_portfolio_critical,
)


class _PortfolioProgressSink(PostgreSQLTransactionSink):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._last_progress = monotonic()
        self._progress_started = self._last_progress
        self._last_order_mark = 0
        self._latest_year = 2022
        self.year_elapsed: dict[int, float] = {}
        self._year_started = perf_counter()

    def consume(self, batch) -> None:
        dates = [row.placed_at for row in batch.rows_by_table.get("sales_orders", ())]
        dates += [row.placed_at for row in (batch.updates_by_table or {}).get("sales_orders", ())]
        super().consume(batch)
        years = [value.year for value in dates]
        if years:
            latest = max(years)
            if latest > self._latest_year:
                now = perf_counter()
                if self._latest_year >= 2023:
                    self.year_elapsed[self._latest_year] = now - self._year_started
                    print(f"Período {self._latest_year} processado ({self.year_elapsed[self._latest_year]:.1f}s).", flush=True)
                elif latest == 2023:
                    print("Bootstrap concluído; período comercial 2023 iniciado.", flush=True)
                self._latest_year = latest
                self._year_started = now
        now = monotonic()
        if self.metrics.sales_orders_inserted - self._last_order_mark >= 10000 or now - self._last_progress >= 30:
            print(
                "Progresso Portfolio: "
                f"pedidos={self.metrics.sales_orders_inserted}; "
                f"linhas_emitidas={self.metrics.rows_received_from_emitter}; "
                f"linhas_inseridas={self.metrics.rows_inserted}; updates={self.metrics.rows_updated}; "
                f"flushes={self.metrics.flush_count}; batch_max={self.metrics.max_batch_rows}; "
                f"ids_ativos={self.ids.current_entries}; ids_pico={self.ids.max_entries}; "
                f"elapsed={now - self._progress_started:.0f}s.",
                flush=True,
            )
            self._last_progress = now
            self._last_order_mark = self.metrics.sales_orders_inserted


class _StreamSummary:
    def __init__(self, result) -> None:
        self.result = result

    def counts(self):
        counts = self.result.counts()
        counts["discounts"] = counts.pop("applied_discounts", 0)
        counts["reservations"] = counts.pop("stock_reservations", 0)
        return counts

    def summary(self):
        return {"realized_cost": self.result.aggregates["realized_cost"]}


def run_portfolio_commit(settings, config, *, project_root):
    """Persist the full Portfolio once, after strict in-transaction gates.

    Once COMMIT succeeds this function never issues a rollback or retries. It
    opens a fresh read-only connection and repeats the critical checks.
    """
    if config.profile != "portfolio":
        raise DatabaseGuardError("--commit só aceita o profile portfolio.")

    overall_started = perf_counter()
    execution_started = datetime.now(config.timezone).isoformat()
    print("Verificando database/projeto/schema/vazio antes de gerar Portfolio...", flush=True)
    preflight = connect(settings)
    try:
        preflight.execute("BEGIN READ ONLY")
        server_version, empty_counts = guard_empty_target(preflight)
        if len(empty_counts) != len(OPERATIONAL_TABLES) or any(empty_counts.values()):
            raise DatabaseGuardError("Gate inicial exige todas as tabelas operacionais vazias.")
        preflight.execute("ROLLBACK")
    except Exception:
        try:
            preflight.rollback()
        except Exception:
            pass
        raise
    finally:
        preflight.close()

    print("Gerando e validando master portfolio...", flush=True)
    master_started = perf_counter()
    master = generate_master_data(config)
    validate_master_data(master, config)
    master_generation_seconds = perf_counter() - master_started
    print(f"Master concluída e validada: {sum(config.volumes.values()):,} linhas em {master_generation_seconds:.1f}s.".replace(",", "."), flush=True)

    connection = connect(settings)
    committed = False
    try:
        connection.execute("BEGIN")
        transaction_server_version, before_counts = guard_empty_target(connection)
        if transaction_server_version != server_version:
            raise DatabaseGuardError("Servidor PostgreSQL mudou entre preflight e BEGIN.")
        if len(before_counts) != len(OPERATIONAL_TABLES) or any(before_counts.values()):
            raise DatabaseGuardError("Gate de base vazia/estrutura falhou; carga não iniciada.")
        print("BEGIN aberto; guard PostgreSQL 18, schema, migrations 002/003 e tabelas vazias passaram.", flush=True)

        master_persist_started = perf_counter()
        master_ids = load_master_data(connection, master)
        analyze_tables(connection, MASTER_TABLES)
        persisted_master_counts = validate_loaded_master(connection, config)
        master_persistence_seconds = perf_counter() - master_persist_started
        print(f"Master persistida e conferida em {master_persistence_seconds:.1f}s; iniciando pipeline transacional.", flush=True)

        sink = _PortfolioProgressSink(connection, master, master_ids, config.batch_size)
        transaction_started = perf_counter()
        result = generate_full_transactions_incremental(config, master, sink, batch_size=config.batch_size)
        transaction_generation_seconds = perf_counter() - transaction_started
        if sink._latest_year >= 2023:
            sink.year_elapsed[sink._latest_year] = perf_counter() - sink._year_started
            print(f"Período {sink._latest_year}{' YTD' if sink._latest_year == 2026 else ''} processado ({sink.year_elapsed[sink._latest_year]:.1f}s desde início do intervalo).", flush=True)
        precommit_validation_started = perf_counter()
        if sink._pending_state_events or sink._pending_movements:
            raise RuntimeError("Sink terminou com movimentos/estados causais pendentes.")

        summary = _StreamSummary(result)
        analyze_tables(connection, OPERATIONAL_TABLES)
        sql_counts = validate_loaded_transactions(connection, config, master, summary, validate_phase3c=False)
        critical_checks = validate_portfolio_critical(connection, config)
        portfolio_metrics = collect_portfolio_metrics(connection, config.timezone.key)
        distribution_result = classify_portfolio_distributions(portfolio_metrics)
        if distribution_result["critical_fails"] != 0 or distribution_result["distributional_fails"] != 0:
            failed_checks = [check for check in distribution_result["checks"] if check["result"] == "FAIL"]
            raise RuntimeError(
                "DISTRIBUTIONAL FAILS impedem COMMIT: "
                + "; ".join(f"{check['name']}={check.get('value_percent',check.get('value','?'))}; banda={check.get('band_percent',check.get('band','?'))}"
                             for check in failed_checks)
            )
        if len(portfolio_metrics["table_counts"]) != len(OPERATIONAL_TABLES):
            raise RuntimeError("Validação pré-COMMIT não retornou todas as tabelas operacionais.")
        transaction_rows = sum(value for table, value in result.counts().items() if table != "stock_state_events")
        if sink.metrics.rows_inserted != transaction_rows:
            raise RuntimeError("Linhas inseridas pelo sink divergem das contagens do fluxo incremental.")

        print(
            "Validação crítica e distribucional aprovada; "
            f"linhas={sink.metrics.rows_inserted}; updates={sink.metrics.rows_updated}; "
            f"flushes={sink.metrics.flush_count}; IDs pico={sink.ids.max_entries}; "
            f"tempo transacional={transaction_generation_seconds:.1f}s. Enviando COMMIT.",
            flush=True,
        )
        precommit_validation_seconds = perf_counter() - precommit_validation_started
        connection.execute("COMMIT")
        committed = True
        commit_completed_at = datetime.now(config.timezone).isoformat()
        print("COMMIT PostgreSQL concluído.", flush=True)
    except Exception:
        if not committed:
            try:
                connection.rollback()
            except Exception:
                pass
        raise
    finally:
        connection.close()

    # The load is already committed. Any failure below is reported without reset/retry.
    print("Validando o dataset persistido em nova conexão somente leitura...", flush=True)
    post_started = perf_counter()
    post_connection = connect(settings)
    try:
        post_connection.execute("BEGIN READ ONLY")
        post_version, post_counts = inspect_target(post_connection)
        if post_version != server_version or post_counts != portfolio_metrics["table_counts"]:
            raise RuntimeError("Validação pós-COMMIT diverge do estado conferido antes do COMMIT.")
        post_master_counts = validate_loaded_master(post_connection, config)
        post_sql_counts = validate_loaded_transactions(post_connection, config, master, summary, validate_phase3c=False)
        post_critical_checks = validate_portfolio_critical(post_connection, config)
        post_metrics = collect_portfolio_metrics(post_connection, config.timezone.key)
        post_distribution = classify_portfolio_distributions(post_metrics)
        if post_distribution["distributional_fails"] or post_metrics["table_counts"] != portfolio_metrics["table_counts"]:
            raise RuntimeError("A validação de distribuição/contagens pós-COMMIT falhou.")
        post_connection.execute("ROLLBACK")
    except Exception:
        try:
            post_connection.rollback()
        except Exception:
            pass
        raise
    finally:
        post_connection.close()
    post_validation_seconds = perf_counter() - post_started
    if post_master_counts != persisted_master_counts or post_sql_counts != sql_counts or post_critical_checks != critical_checks:
        raise RuntimeError("Os resultados críticos da conexão nova divergem dos resultados pré-COMMIT.")

    total_seconds = perf_counter() - overall_started
    return {
        "profile": config.profile,
        "root_seed": config.root_seed,
        "generator_version": config.generator_version,
        "config_version": config.schema_version,
        "timezone": config.timezone.key,
        "bootstrap_start": config.bootstrap_start_date.isoformat(),
        "bootstrap_end": config.bootstrap_end_date.isoformat(),
        "commercial_start": config.start_date.isoformat(),
        "commercial_end": config.end_date.isoformat(),
        "execution_started": execution_started,
        "commit_completed_at": commit_completed_at,
        "server_version": server_version,
        "master_generation_seconds": master_generation_seconds,
        "master_persistence_seconds": master_persistence_seconds,
        "transaction_generation_and_validation_seconds": transaction_generation_seconds,
        "precommit_validation_seconds": precommit_validation_seconds,
        "post_validation_seconds": post_validation_seconds,
        "total_seconds": total_seconds,
        "master_counts": persisted_master_counts,
        "transaction_counts": result.counts(),
        "transaction_rows": transaction_rows,
        "validated_table_counts": sql_counts,
        "table_counts": post_counts,
        "sink_metrics": vars(sink.metrics),
        "id_metrics": {"current": sink.ids.current_entries, "peak": sink.ids.max_entries,
                       "peak_by_type": dict(sink.ids.max_by_type)},
        "year_progress_seconds": sink.year_elapsed,
        "aggregates": dict(result.aggregates),
        "portfolio_metrics": post_metrics,
        "distribution_result": post_distribution,
        "critical_checks": post_critical_checks,
        "post_validation_database": "projeto_bi",
        "post_validation_read_only": True,
    }
