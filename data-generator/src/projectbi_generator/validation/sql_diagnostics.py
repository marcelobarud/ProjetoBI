"""Timing and bounded execution helpers for critical SQL validations."""

from __future__ import annotations

import os
from collections.abc import Iterable
from time import perf_counter

from psycopg import Connection
from psycopg import sql


DEFAULT_VALIDATION_TIMEOUT_MS = 120_000
VALIDATION_TIMINGS: list[dict] = []


def reset_validation_timings() -> None:
    VALIDATION_TIMINGS.clear()


def record_validation_timing(name: str, duration_seconds: float, status: str, rows_returned=None) -> None:
    VALIDATION_TIMINGS.append({
        "validation": name,
        "duration_seconds": duration_seconds,
        "status": status,
        "rows_returned": rows_returned,
    })


def print_validation_timing_summary() -> None:
    print("[validation] PERFORMANCE SUMMARY (slowest first)", flush=True)
    for item in sorted(VALIDATION_TIMINGS, key=lambda row: row["duration_seconds"], reverse=True):
        rows = "-" if item["rows_returned"] is None else str(item["rows_returned"])
        print(f"[validation] {item['validation']} {item['duration_seconds']:.2f}s {item['status']} rows={rows}", flush=True)


def set_validation_timeout(connection: Connection, timeout_ms: int | None = None) -> None:
    """Set a transaction-local timeout for subsequent validation SQL only."""
    if timeout_ms is None:
        timeout_ms = int(os.getenv("PROJECTBI_VALIDATION_TIMEOUT_MS", DEFAULT_VALIDATION_TIMEOUT_MS))
    if timeout_ms <= 0:
        raise ValueError("validation timeout must be a positive number of milliseconds")
    connection.execute(f"SET LOCAL statement_timeout = '{int(timeout_ms)}ms'")
    print(f"[validation] statement_timeout_local={timeout_ms}ms", flush=True)


def analyze_tables(connection: Connection, tables: Iterable[tuple[str, str]]) -> float:
    """Refresh planner statistics for the supplied relations inside the current transaction."""
    relations = tuple(tables)
    if not relations:
        raise ValueError("ANALYZE requires at least one relation")
    set_validation_timeout(connection)
    started = perf_counter()
    name = "planner.analyze_operational_tables"
    print(f"[validation] {name} START tables={len(relations)}", flush=True)
    try:
        statement = sql.SQL("ANALYZE {}").format(
            sql.SQL(", ").join(sql.SQL("{}.{}").format(sql.Identifier(schema), sql.Identifier(table))
                                 for schema, table in relations)
        )
        connection.execute(statement)
        elapsed = perf_counter() - started
        print(f"[validation] {name} PASS {elapsed:.2f}s tables={len(relations)}", flush=True)
        record_validation_timing(name, elapsed, "PASS", len(relations))
        return elapsed
    except Exception as exc:
        elapsed = perf_counter() - started
        sqlstate = getattr(exc, "sqlstate", None)
        suffix = f" sqlstate={sqlstate}" if sqlstate else ""
        print(f"[validation] {name} FAIL {elapsed:.2f}s{suffix}", flush=True)
        record_validation_timing(name, elapsed, "FAIL", len(relations))
        raise


def run_sql_validation(
    connection: Connection,
    name: str,
    statement: str,
    params: tuple | None = None,
    *,
    fetch: str = "one",
    expect_zero: bool = False,
    expect_all_zero: bool = False,
    expected_result=None,
    explain: bool = False,
    explain_analyze: bool = False,
):
    """Run one named SQL check, timing it and optionally capturing its plan."""
    explain = explain or os.getenv("PROJECTBI_EXPLAIN_VALIDATION") == name
    explain_analyze = explain_analyze or os.getenv("PROJECTBI_EXPLAIN_ANALYZE_VALIDATION") == name
    started = perf_counter()
    print(f"[validation] {name} START", flush=True)
    try:
        if explain or explain_analyze:
            plan = connection.execute("EXPLAIN " + statement, params or ()).fetchall()
            print(f"[validation] {name} EXPLAIN", flush=True)
            for row in plan:
                print(f"  {row[0]}", flush=True)

        cursor = connection.execute(statement, params or ())
        if fetch == "one":
            result = cursor.fetchone()
            returned = 0 if result is None else 1
        elif fetch == "all":
            result = cursor.fetchall()
            returned = len(result)
        elif fetch == "none":
            result = None
            returned = cursor.rowcount
        else:
            raise ValueError("fetch must be one, all or none")

        elapsed = perf_counter() - started
        violations = result[0] if expect_zero and result is not None else 0
        if expect_all_zero and result is not None:
            violations = sum(bool(value) for value in result)
        if expected_result is not None:
            violations = 0 if result == expected_result else 1
        status = "FAIL" if violations else "PASS"
        detail = f" violations={violations}" if expect_zero else (" expected_result_mismatch" if expected_result is not None and violations else "")
        print(f"[validation] {name} {status} {elapsed:.2f}s rows={returned}{detail}", flush=True)
        record_validation_timing(name, elapsed, status, returned)

        if explain_analyze:
            analyze_started = perf_counter()
            analyzed = connection.execute("EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON) " + statement, params or ()).fetchall()
            analyze_elapsed = perf_counter() - analyze_started
            print(f"[validation] {name} EXPLAIN_ANALYZE {analyze_elapsed:.2f}s", flush=True)
            for row in analyzed:
                print(f"  {row[0]}", flush=True)
        return result
    except Exception as exc:
        elapsed = perf_counter() - started
        sqlstate = getattr(exc, "sqlstate", None)
        suffix = f" sqlstate={sqlstate}" if sqlstate else ""
        print(f"[validation] {name} FAIL {elapsed:.2f}s{suffix}", flush=True)
        record_validation_timing(name, elapsed, "FAIL")
        raise
