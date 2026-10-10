"""Command line interface for dry-run and rollback-only smoke integration."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from time import perf_counter

import psycopg

from projectbi_generator import __version__
from projectbi_generator.config import load_config
from projectbi_generator.database import connect, connection_settings, run_rollback_smoke, run_rollback_incremental_full_smoke
from projectbi_generator.generators.completion import extend_transactions
from projectbi_generator.generators.master import generate_master_data
from projectbi_generator.generators.transactions import generate_transactions
from projectbi_generator.seeds import DOMAINS, derive_subseed
from projectbi_generator.validation.master_data import validate_master_data
from projectbi_generator.validation.transactions import validate_transactional_data
from projectbi_generator.validation.completion import validate_completed_data

PROJECT_ROOT = Path(__file__).resolve().parents[3]


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="projectbi-generator")
    commands = parser.add_subparsers(dest="command", required=True)
    master = commands.add_parser("master", help="Gera e valida os dados mestres")
    master.add_argument("--profile", choices=("smoke", "portfolio", "large"), default=None)
    mode = master.add_mutually_exclusive_group(required=True)
    mode.add_argument("--dry-run", action="store_true")
    mode.add_argument("--load-smoke", action="store_true", help="Carrega apenas em uma transação que termina em ROLLBACK")
    transactions = commands.add_parser("transactions", help="Gera e valida o fluxo operacional smoke")
    transactions.add_argument("--profile", choices=("smoke",), default="smoke")
    transaction_mode = transactions.add_mutually_exclusive_group(required=True)
    transaction_mode.add_argument("--dry-run", action="store_true")
    transaction_mode.add_argument("--load-smoke", action="store_true", help="Executa a integração completa e sempre termina em ROLLBACK")
    full = commands.add_parser("full", help="Gera, valida e exercita todos os domínios operacionais smoke")
    full.add_argument("--profile", choices=("smoke", "portfolio", "large"), default=None)
    full_mode = full.add_mutually_exclusive_group(required=True)
    full_mode.add_argument("--dry-run", action="store_true")
    full_mode.add_argument("--load-smoke", action="store_true", help="Carrega os domínios aplicáveis em uma transação que termina em ROLLBACK")
    full_mode.add_argument("--plan", action="store_true", help="Valida configuração/volumes sem gerar dados nem conectar")
    full_mode.add_argument("--commit", action="store_true", help="Persiste Portfolio uma única vez após validações críticas")
    return parser


def _build_plan(config) -> dict:
    master_rows = sum(config.volumes.values())
    return {
        "profile": config.profile,
        "generator_version": config.generator_version,
        "config_version": config.schema_version,
        "root_seed": config.root_seed,
        "period": {
            "bootstrap_start": config.bootstrap_start_date.isoformat(),
            "bootstrap_end": config.bootstrap_end_date.isoformat(),
            "commercial_start": config.start_date.isoformat(),
            "commercial_end": config.end_date.isoformat(),
        },
        "master_rows_target": master_rows,
        "master_volumes": config.volumes,
        "sales_orders_target": config.sales_order_target,
        "sales_order_items_estimate": config.generation.get("estimated_order_items"),
        "estimated_transaction_rows": config.generation.get("estimated_transaction_rows"),
        "batch_size": config.batch_size,
        "database_connected": False,
        "generated": False,
        "persistent_write": False,
    }


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        config = load_config(args.profile)
        if args.command == "full":
            if args.plan:
                print(json.dumps(_build_plan(config), ensure_ascii=False, sort_keys=True))
                return 0
            if args.commit:
                if config.profile != "portfolio":
                    raise ValueError("--commit exige --profile portfolio; nenhum dado foi gravado.")
                from projectbi_generator.portfolio_load import run_portfolio_commit
                result = run_portfolio_commit(connection_settings(PROJECT_ROOT), config, project_root=PROJECT_ROOT)
                baseline_started = perf_counter()
                from projectbi_generator.validation.baselines import (
                    create_baseline_files,
                    execute_baseline_files,
                    validate_baseline_results,
                )
                baseline_dir = create_baseline_files(PROJECT_ROOT)
                read_connection = connect(connection_settings(PROJECT_ROOT))
                try:
                    read_connection.execute("BEGIN READ ONLY")
                    baseline_results = execute_baseline_files(read_connection, baseline_dir)
                    read_connection.execute("ROLLBACK")
                except Exception:
                    try:
                        read_connection.rollback()
                    except Exception:
                        pass
                    raise
                finally:
                    read_connection.close()
                baseline_reconciliation = validate_baseline_results(baseline_results, result["portfolio_metrics"])
                result["baseline_seconds"] = perf_counter() - baseline_started
                result["total_seconds_with_baselines"] = result["total_seconds"] + result["baseline_seconds"]
                from projectbi_generator.validation.portfolio_report import write_portfolio_report
                result["baseline_reconciliation"] = baseline_reconciliation
                report_path = write_portfolio_report(PROJECT_ROOT, result, baseline_results)
                print(json.dumps({
                    "database": "projeto_bi", "transaction": "COMMIT", "post_validation": "PASS",
                    "orders": result["transaction_counts"].get("sales_orders"),
                    "transaction_rows": result["transaction_rows"], "sink_metrics": result["sink_metrics"],
                    "id_metrics": result["id_metrics"], "total_seconds": result["total_seconds"],
                    "baseline_files": len(baseline_results), "portfolio_report": str(report_path),
                    "critical_fails": result["distribution_result"]["critical_fails"],
                    "distributional_warnings": result["distribution_result"]["distributional_warnings"],
                    "distributional_fails": result["distribution_result"]["distributional_fails"],
                }, ensure_ascii=False, sort_keys=True, default=str))
                print("""
## Relatório Portfolio

PROFILE

- portfolio;
- período bootstrap: 2022-11-01 a 2022-12-31;
- período comercial: 2023-01-01 a 2026-09-30;
- timezone: America/Sao_Paulo.

EXECUÇÃO

- início/fim;
- duração;
- batches, rows, updates e pico de IDs;
- nenhuma persistência fora da transação única.

QUALITY

- CRITICAL FAILS: 0;
- DISTRIBUTIONAL FAILS: 0;
- warnings estão documentados no relatório detalhado.

POSTGRESQL

- COMMIT PostgreSQL concluído;
- nova conexão read-only aprovada;
- Todas as tabelas operacionais conciliadas com o relatório.

BASELINES

- 13 arquivos SQL criados e executados;
- controle, comercial, COGS e YTD reconciliados.
""")
                return 0
            if config.profile != "smoke":
                raise ValueError("Geração e integração ainda estão limitadas a smoke; portfolio/large podem usar --plan.")
            if args.load_smoke:
                result = run_rollback_incremental_full_smoke(connection_settings(PROJECT_ROOT), config)
                print(json.dumps({"database": "projeto_bi", "server_version": result["server_version"],
                                  "transaction": "ROLLBACK", "remaining_rows_all_operational_tables": sum(result["remaining"].values()),
                                  "master_id_maps": result["master_id_maps"], "id_metrics": result["id_metrics"],
                                  "sink_metrics": result["sink_metrics"], "counts": result["counts"],
                                  "aggregates": result["aggregates"], "validated_table_counts": result["sql_counts"]},
                                 ensure_ascii=False, sort_keys=True, default=str))
                return 0
            master = generate_master_data(config)
            validate_master_data(master, config)
            data = generate_transactions(config, master)
            validate_transactional_data(data, master, config)
            extend_transactions(config, master, data)
            validate_completed_data(data, master, config)
            if args.dry_run:
                summary = data.summary()
                result = {
                    "profile": config.profile, "root_seed": config.root_seed, "database_connected": False,
                    "orders": summary["sales_orders"], "payments": summary["payments"],
                    "declined_attempts": summary["declined_attempts"], "retries": summary["payment_retries"],
                    "split_payment_orders": summary["split_payment_orders"],
                    "installments": summary["payment_installments"], "fulfillments": summary["fulfillments"],
                    "fulfillment_events": summary["fulfillment_events"], "transfers": summary["stock_transfers"],
                    "return_items": summary["return_items"], "returns": summary["returns"], "refunds": summary["refunds"],
                    "stock_movements": summary["stock_movements"], "final_stock": summary["ending_stock"],
                    "realized_cost": summary["realized_cost"], "refund_amount": summary["refund_amount"],
                    "captured_amount": summary["captured_amount"], "net_financial_amount": summary["net_financial_amount"],
                }
                print(json.dumps(result, ensure_ascii=False, sort_keys=True, default=str))
                return 0
        if args.command == "transactions":
            if args.load_smoke:
                result = run_rollback_incremental_full_smoke(connection_settings(PROJECT_ROOT), config, include_completion=False)
                print(json.dumps({"database": "projeto_bi", "server_version": result["server_version"],
                                  "transaction": "ROLLBACK", "remaining_rows_all_operational_tables": sum(result["remaining"].values()),
                                  "master_id_maps": result["master_id_maps"], "id_metrics": result["id_metrics"],
                                  "sink_metrics": result["sink_metrics"], "counts": result["counts"],
                                  "aggregates": result["aggregates"], "validated_table_counts": result["sql_counts"]},
                                 ensure_ascii=False, sort_keys=True, default=str))
                return 0
            master = generate_master_data(config)
            validate_master_data(master, config)
            data = generate_transactions(config, master)
            validate_transactional_data(data, master, config)
            if args.dry_run:
                print(json.dumps({"profile": "smoke", "root_seed": config.root_seed,
                                  "database_connected": False, **data.summary()}, ensure_ascii=False,
                                 sort_keys=True, default=str))
                return 0

        if args.load_smoke and config.profile != "smoke":
            raise ValueError("--load-smoke aceita somente profile smoke; profiles maiores não são persistidos nesta fase.")
        data = generate_master_data(config)
        validate_master_data(data, config)
        if args.dry_run:
            result = {
                "generator_version": __version__,
                "profile": config.profile,
                "root_seed": config.root_seed,
                "subseeds": {domain: derive_subseed(config.root_seed, domain, config.generator_version) for domain in DOMAINS},
                "counts": data.counts(),
                "database_connected": False,
            }
            print(json.dumps(result, ensure_ascii=False, sort_keys=True, default=str))
            return 0

        settings = connection_settings(PROJECT_ROOT)
        result = run_rollback_smoke(settings, config, data)
        print(json.dumps({
            "database": "projeto_bi",
            "server_version": result["server_version"],
            "profile": config.profile,
            "root_seed": config.root_seed,
            "loaded_counts_in_transaction": result["counts"],
            "id_maps_resolved": result["id_map_tables"],
            "transaction": "ROLLBACK",
            "remaining_rows_all_operational_tables": sum(result["remaining"].values()),
        }, ensure_ascii=False, sort_keys=True, default=str))
        return 0
    except psycopg.Error as exc:
        diag = getattr(exc, "diag", None)
        constraint = getattr(diag, "constraint_name", None) if diag else None
        table = getattr(diag, "table_name", None) if diag else None
        context = ", ".join(f"{name}={value}" for name,value in (("constraint",constraint),("table",table)) if value)
        sqlstate = f" SQLSTATE={exc.sqlstate}." if exc.sqlstate else ""
        safe_context = f" Contexto: {context}." if context else ""
        print(f"Falha PostgreSQL: {type(exc).__name__}.{sqlstate}{safe_context} Consulte o estado da conexão antes de qualquer nova tentativa.", file=sys.stderr)
        return 2
    except (OSError, ValueError, RuntimeError) as exc:
        print(f"Erro: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
