"""Command line interface for dry-run and rollback-only smoke integration."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

import psycopg

from projectbi_generator import __version__
from projectbi_generator.config import load_config
from projectbi_generator.database import connection_settings, run_rollback_smoke, run_rollback_transaction_smoke
from projectbi_generator.generators.master import generate_master_data
from projectbi_generator.generators.transactions import generate_transactions
from projectbi_generator.seeds import DOMAINS, derive_subseed
from projectbi_generator.validation.master_data import validate_master_data
from projectbi_generator.validation.transactions import validate_transactional_data

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
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        config = load_config(args.profile)
        if args.command == "transactions":
            master = generate_master_data(config)
            validate_master_data(master, config)
            data = generate_transactions(config, master)
            validate_transactional_data(data, master, config)
            if args.dry_run:
                print(json.dumps({"profile": "smoke", "root_seed": config.root_seed,
                                  "database_connected": False, **data.summary()}, ensure_ascii=False,
                                 sort_keys=True, default=str))
                return 0
            result = run_rollback_transaction_smoke(connection_settings(PROJECT_ROOT), config)
            print(json.dumps({"database": "projeto_bi", "server_version": result["server_version"],
                              "transaction": "ROLLBACK", "remaining_rows_all_40_tables": sum(result["remaining"].values()),
                              "master_id_maps": result["id_map_tables"], "transaction_id_maps": result["transaction_id_maps"],
                              "summary": result["summary"], "validated_table_counts": result["sql_counts"]},
                             ensure_ascii=False, sort_keys=True, default=str))
            return 0

        if config.profile != "smoke":
            raise ValueError("Nesta fase, somente o profile smoke pode ser gerado ou carregado.")
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
            "remaining_rows_all_40_tables": sum(result["remaining"].values()),
        }, ensure_ascii=False, sort_keys=True, default=str))
        return 0
    except psycopg.Error as exc:
        print(f"Falha PostgreSQL: {type(exc).__name__}; a transação foi revertida quando iniciada.", file=sys.stderr)
        return 2
    except (OSError, ValueError, RuntimeError) as exc:
        print(f"Erro: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
