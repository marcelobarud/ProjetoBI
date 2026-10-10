"""Rollback-only planner and validation scaling experiment for Portfolio."""

from __future__ import annotations

import argparse
from dataclasses import replace
import json
import os
from pathlib import Path
import threading
from time import perf_counter, sleep

from projectbi_generator.config import load_config
from projectbi_generator.database import (
    OPERATIONAL_TABLES,
    confirm_empty_after_rollback,
    connect,
    connection_settings,
    guard_empty_target,
    validate_loaded_master,
)
from projectbi_generator.generators.completion import generate_full_transactions_incremental
from projectbi_generator.generators.master import generate_master_data
from projectbi_generator.portfolio_load import _PortfolioProgressSink, _StreamSummary
from projectbi_generator.repositories.master_data import load_master_data
from projectbi_generator.validation.database_transactions import validate_loaded_transactions
from projectbi_generator.validation.master_data import validate_master_data
from projectbi_generator.validation.portfolio import validate_portfolio_critical
from projectbi_generator.validation.sql_diagnostics import (
    VALIDATION_TIMINGS,
    analyze_tables,
    print_validation_timing_summary,
    reset_validation_timings,
    run_sql_validation,
    set_validation_timeout,
)


def _plans() -> dict[str, str]:
    return {
        "catalog.price_validity": """SELECT count(*) FROM sales.sales_order_items i JOIN sales.sales_orders o USING (sales_order_id)
            WHERE NOT EXISTS (SELECT 1 FROM catalog.product_prices p WHERE p.product_id=i.product_id
              AND p.sales_channel_id=o.sales_channel_id AND p.valid_from<=o.placed_at
              AND (p.valid_to IS NULL OR o.placed_at<p.valid_to) AND p.amount=i.unit_sale_price)""",
        "inventory.stock_ledger_balance": """SELECT count(*) FROM (
            SELECT coalesce(p.product_id,m.product_id) product_id,coalesce(p.stock_location_id,m.stock_location_id) location_id,
                   coalesce(p.on_hand_quantity,0) on_hand,coalesce(sum(m.quantity_delta),0) ledger
              FROM inventory.stock_positions p FULL JOIN inventory.stock_movements m
                ON p.product_id=m.product_id AND p.stock_location_id=m.stock_location_id
             GROUP BY p.product_id,p.stock_location_id,p.on_hand_quantity,m.product_id,m.stock_location_id
            HAVING coalesce(p.on_hand_quantity,0)<>coalesce(sum(m.quantity_delta),0)) q""",
        "inventory.stock_movement_ledger_read": """SELECT m.stock_movement_id,m.product_id,p.sku,m.stock_location_id,l.location_code,
                   m.movement_type,m.occurred_at,m.quantity_delta,m.unit_cost
              FROM inventory.stock_movements m JOIN catalog.products p USING(product_id)
              JOIN inventory.stock_locations l USING(stock_location_id)
              LEFT JOIN procurement.goods_receipt_items gri USING(goods_receipt_item_id)
              LEFT JOIN procurement.goods_receipts gr USING(goods_receipt_id)
              LEFT JOIN procurement.purchase_order_items poi USING(purchase_order_item_id)
              LEFT JOIN logistics.fulfillment_items fi USING(fulfillment_item_id)
              LEFT JOIN logistics.fulfillments f USING(fulfillment_id)
              LEFT JOIN sales.sales_order_items soi USING(sales_order_item_id)
              LEFT JOIN inventory.stock_transfer_items sti USING(stock_transfer_item_id)
              LEFT JOIN inventory.stock_transfers st USING(stock_transfer_id)
              LEFT JOIN after_sales.return_items ri USING(return_item_id)""",
        "master.product_price_nonoverlap": """SELECT EXISTS (
              SELECT 1 FROM catalog.product_prices a JOIN catalog.product_prices b
                ON a.product_id=b.product_id AND a.sales_channel_id=b.sales_channel_id AND a.product_price_id<b.product_price_id
               AND a.valid_from<coalesce(b.valid_to,'infinity'::timestamptz)
               AND b.valid_from<coalesce(a.valid_to,'infinity'::timestamptz))""",
        "payments.installment_method_eligibility": """SELECT count(*) FROM payments.payment_installments i
              JOIN payments.payments p USING(payment_id) JOIN payments.payment_methods m USING(payment_method_id)
             WHERE m.is_installment_capable IS FALSE OR m.method_type IN ('cash','instant')""",
        "portfolio.refund_eligibility_by_return": """SELECT count(*) FROM (
              WITH item_discount AS (
                SELECT sales_order_id,sales_order_item_id,sum(amount) amount FROM sales.applied_discounts GROUP BY sales_order_id,sales_order_item_id
              ), eligible AS (
                SELECT ri.return_id,sum(ri.quantity_approved*round(oi.unit_sale_price-coalesce(d.amount,0)/nullif(oi.quantity,0),2)) amount
                  FROM after_sales.return_items ri JOIN sales.sales_order_items oi
                    ON oi.sales_order_id=ri.sales_order_id AND oi.sales_order_item_id=ri.sales_order_item_id
                  LEFT JOIN item_discount d ON d.sales_order_id=oi.sales_order_id AND d.sales_order_item_id=oi.sales_order_item_id
                 GROUP BY ri.return_id
              ), refunded AS (
                SELECT return_id,sum(amount) amount FROM payments.refunds WHERE status='completed' AND return_id IS NOT NULL GROUP BY return_id
              ) SELECT e.return_id FROM eligible e JOIN refunded r USING(return_id) WHERE r.amount>e.amount) q""",
        "sales.discount_amount_cap": """SELECT count(*) FROM (
              SELECT i.sales_order_item_id,i.quantity*i.unit_sale_price gross,coalesce(sum(d.amount),0) discounts
                FROM sales.sales_order_items i LEFT JOIN sales.applied_discounts d USING(sales_order_id,sales_order_item_id)
               GROUP BY i.sales_order_item_id,i.quantity,i.unit_sale_price
              HAVING coalesce(sum(d.amount),0)>i.quantity*i.unit_sale_price) q""",
        "payments.installment_total_reconciliation": """SELECT count(*) FROM (
              SELECT p.payment_id,p.amount,coalesce(sum(i.amount),0) installments
                FROM payments.payments p LEFT JOIN payments.payment_installments i USING(payment_id)
               GROUP BY p.payment_id,p.amount
              HAVING count(i.payment_installment_id)>0 AND coalesce(sum(i.amount),0)<>p.amount) q""",
        "payments.capture_order_reconciliation": """SELECT CASE WHEN EXISTS(SELECT 1 FROM payments.payments) THEN count(*) ELSE 0 END FROM (
              SELECT o.sales_order_id,o.order_status,o.total_amount,
                     coalesce(sum(p.amount) FILTER(WHERE p.status IN ('captured','settled')),0) captured
                FROM sales.sales_orders o LEFT JOIN payments.payments p USING(sales_order_id)
               GROUP BY o.sales_order_id,o.order_status,o.total_amount
              HAVING (o.order_status='cancelled' AND coalesce(sum(p.amount) FILTER(WHERE p.status IN ('captured','settled')),0)<>0)
                  OR (o.order_status<>'cancelled' AND coalesce(sum(p.amount) FILTER(WHERE p.status IN ('captured','settled')),0)<>o.total_amount)) q""",
        "logistics.fulfillment_quantity_cap": """SELECT count(*) FROM (
              SELECT oi.sales_order_item_id,oi.quantity,coalesce(sum(fi.fulfilled_quantity),0) fulfilled
                FROM sales.sales_order_items oi LEFT JOIN logistics.fulfillment_items fi USING(sales_order_item_id)
               GROUP BY oi.sales_order_item_id,oi.quantity HAVING coalesce(sum(fi.fulfilled_quantity),0)>oi.quantity) q""",
        "inventory.reservation_product_match": """SELECT count(*) FROM inventory.stock_reservations r
              JOIN sales.sales_order_items i ON i.sales_order_id=r.sales_order_id AND i.sales_order_item_id=r.sales_order_item_id
             WHERE r.product_id<>i.product_id""",
    }


def _plan_nodes(plan: dict) -> list[dict]:
    nodes: list[dict] = []

    def visit(node: dict) -> None:
        item = {
            key: node[key]
            for key in ("Node Type", "Relation Name", "Join Type", "Plan Rows", "Actual Rows", "Actual Loops",
                        "Startup Cost", "Total Cost", "Shared Hit Blocks", "Shared Read Blocks")
            if key in node
        }
        nodes.append(item)
        for child in node.get("Plans", ()):
            visit(child)

    visit(plan)
    return nodes


def _capture_plans(connection, queries: dict[str, str], phase: str) -> None:
    for name, statement in queries.items():
        result = connection.execute("EXPLAIN (FORMAT JSON) " + statement).fetchone()[0][0]
        print(f"[planner] {phase} {name} " + json.dumps(_plan_nodes(result["Plan"]), ensure_ascii=False), flush=True)


def _table_estimates(connection, phase: str) -> None:
    relevant = (
        ("sales", "sales_orders"), ("sales", "sales_order_items"), ("sales", "order_status_history"),
        ("sales", "applied_discounts"), ("catalog", "product_prices"),
        ("inventory", "stock_movements"), ("inventory", "stock_positions"),
        ("inventory", "stock_reservations"), ("payments", "payments"),
        ("payments", "payment_installments"), ("logistics", "fulfillment_items"),
    )
    print(f"[planner] {phase} reltuples_vs_count BEGIN", flush=True)
    for schema, table in relevant:
        estimate = connection.execute("""SELECT c.reltuples FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace
              WHERE n.nspname=%s AND c.relname=%s AND c.relkind='r'""", (schema, table)).fetchone()[0]
        actual = connection.execute(f'SELECT count(*) FROM "{schema}"."{table}"').fetchone()[0]
        print(f"[planner] {phase} {schema}.{table} reltuples={estimate} count={actual}", flush=True)


def _wait_event_monitor(settings, application_name: str, stop: threading.Event) -> None:
    monitor = None
    try:
        monitor = connect(settings)
        monitor.execute("BEGIN READ ONLY")
        reported: set[tuple] = set()
        while not stop.wait(1):
            rows = monitor.execute("""SELECT pid,state,wait_event_type,wait_event,
                       extract(epoch FROM clock_timestamp()-query_start)::numeric(12,1),pg_blocking_pids(pid)
                  FROM pg_stat_activity WHERE application_name=%s AND state='active'""", (application_name,)).fetchall()
            for pid, state, wait_type, wait_event, elapsed, blockers in rows:
                signature = (pid, wait_type, wait_event, elapsed // 5)
                if elapsed >= 5 and signature not in reported:
                    reported.add(signature)
                    print(f"[wait] pid={pid} state={state} wait_event_type={wait_type} wait_event={wait_event} elapsed={elapsed}s blockers={blockers}", flush=True)
    except Exception as exc:
        print(f"[wait] monitor unavailable: {type(exc).__name__}", flush=True)
    finally:
        if monitor is not None:
            try:
                monitor.rollback()
            except Exception:
                pass
            monitor.close()


def _negative_controls(connection, queries: dict[str, str]) -> None:
    connection.execute("SAVEPOINT negative_ledger")
    connection.execute("""UPDATE inventory.stock_positions SET on_hand_quantity=on_hand_quantity+1
          WHERE stock_position_id=(SELECT min(stock_position_id) FROM inventory.stock_positions)""")
    ledger_violations = run_sql_validation(connection, "diagnostic.negative.ledger", queries["inventory.stock_ledger_balance"], expect_zero=True)[0]
    if ledger_violations != 1:
        raise RuntimeError(f"negative ledger expected one violation; observed {ledger_violations}")
    connection.execute("ROLLBACK TO SAVEPOINT negative_ledger")
    connection.execute("RELEASE SAVEPOINT negative_ledger")
    print("[diagnostic] negative ledger PASS violations=1", flush=True)

    connection.execute("SAVEPOINT negative_history_non_draft")
    connection.execute("""UPDATE sales.order_status_history h SET occurred_at=o.placed_at-interval '1 minute'
          FROM sales.sales_orders o WHERE h.sales_order_id=o.sales_order_id AND h.status='confirmed'
            AND o.sales_order_id=(SELECT min(sales_order_id) FROM sales.sales_orders)""")
    invalid_before = run_sql_validation(connection, "diagnostic.negative.history_non_draft_before_placed", queries["portfolio.sales_status_history_chronology"], expect_zero=True)[0]
    if invalid_before != 1:
        raise RuntimeError(f"negative history expected one violation; observed {invalid_before}")
    connection.execute("ROLLBACK TO SAVEPOINT negative_history_non_draft")
    connection.execute("RELEASE SAVEPOINT negative_history_non_draft")
    print("[diagnostic] negative history non-draft PASS violations=1", flush=True)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--orders", type=int, choices=(10_000, 25_000, 50_000), required=True)
    parser.add_argument("--statement-timeout-ms", type=int, default=120_000)
    args = parser.parse_args()
    os.environ["PROJECTBI_VALIDATION_TIMEOUT_MS"] = str(args.statement_timeout_ms)

    root = Path(__file__).resolve().parents[2]
    settings = connection_settings(root)
    config = load_config("portfolio")
    config = replace(config, generation={
        **config.generation,
        "sales_orders": args.orders,
        "estimated_order_items": args.orders * 22 // 10,
        "estimated_transaction_rows": args.orders * 20,
    }, order_plan={"mode": "intentions"})
    application_name = f"projectbi-validation-{args.orders}"
    queries = _plans()
    queries["portfolio.sales_status_history_chronology"] = """SELECT count(*) FROM sales.order_status_history h
         JOIN sales.sales_orders o USING(sales_order_id)
        WHERE (h.status='draft' AND h.occurred_at>=o.placed_at)
           OR (h.status<>'draft' AND h.occurred_at<o.placed_at)"""
    reset_validation_timings()
    connection = None
    monitor_stop = threading.Event()
    monitor_thread = None
    failure: Exception | None = None
    transaction_started = False
    run_started = perf_counter()

    try:
        master = generate_master_data(config)
        validate_master_data(master, config)
        connection = connect(settings)
        connection.execute(f"SET application_name='{application_name}'")
        connection.execute("BEGIN")
        transaction_started = True
        connection.execute(f"SET LOCAL statement_timeout='{args.statement_timeout_ms}ms'")
        server_version, existing = guard_empty_target(connection)
        if not server_version.startswith("18.") or len(existing) != 40 or any(existing.values()):
            raise RuntimeError("Preflight requires PostgreSQL 18 and all 40 operational tables empty")
        print(f"[diagnostic] preflight PASS PostgreSQL={server_version} tables=40 empty=True", flush=True)

        master_ids = load_master_data(connection, master)
        sink = _PortfolioProgressSink(connection, master, master_ids, config.batch_size)
        result = generate_full_transactions_incremental(config, master, sink, batch_size=config.batch_size)
        if sink._pending_state_events or sink._pending_movements:
            raise RuntimeError("Incremental sink ended with pending stock state")
        print(f"[diagnostic] loaded orders={args.orders} master_rows={sum(config.volumes.values())}", flush=True)

        set_validation_timeout(connection, args.statement_timeout_ms)
        monitor_thread = threading.Thread(target=_wait_event_monitor,
            args=(settings, application_name, monitor_stop), daemon=True)
        monitor_thread.start()
        _table_estimates(connection, "before_analyze")
        _capture_plans(connection, queries, "before_analyze")
        analyze_started = perf_counter()
        analyze_tables(connection, OPERATIONAL_TABLES)
        analyze_elapsed = perf_counter() - analyze_started
        print(f"[diagnostic] analyze_total_seconds={analyze_elapsed:.2f} tables={len(OPERATIONAL_TABLES)}", flush=True)
        _table_estimates(connection, "after_analyze")
        _capture_plans(connection, queries, "after_analyze")

        summary = _StreamSummary(result)
        for run_number in (1, 2):
            reset_validation_timings()
            print(f"[diagnostic] NAMED_VALIDATIONS_RUN_{run_number} START", flush=True)
            validate_loaded_master(connection, config)
            validate_loaded_transactions(connection, config, master, summary, validate_phase3c=False)
            validate_portfolio_critical(connection, config)
            print_validation_timing_summary()
            if run_number == 1:
                ranked = sorted(
                    (item for item in VALIDATION_TIMINGS if item["validation"] in queries),
                    key=lambda item: item["duration_seconds"], reverse=True,
                )[:3]
                for item in ranked:
                    name = item["validation"]
                    print(f"[planner] SELECTIVE_EXPLAIN_ANALYZE {name} START", flush=True)
                    rows = connection.execute(
                        "EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT JSON) " + queries[name]
                    ).fetchone()[0]
                    plan = rows[0]["Plan"]
                    print(f"[planner] SELECTIVE_EXPLAIN_ANALYZE {name} " +
                          json.dumps(_plan_nodes(plan), ensure_ascii=False) +
                          f" execution_time_ms={rows[0].get('Execution Time')}", flush=True)
            print(f"[diagnostic] NAMED_VALIDATIONS_RUN_{run_number} PASS", flush=True)

        _negative_controls(connection, queries)
    except Exception as exc:
        failure = exc
        sqlstate = getattr(exc, "sqlstate", None)
        suffix = f" sqlstate={sqlstate}" if sqlstate else ""
        print(f"[diagnostic] FAILED {type(exc).__name__}{suffix}: {exc}", flush=True)
    finally:
        monitor_stop.set()
        if monitor_thread is not None:
            monitor_thread.join(timeout=3)
        if connection is not None:
            if transaction_started:
                try:
                    connection.rollback()
                    print("[diagnostic] ROLLBACK completed", flush=True)
                except Exception as exc:
                    if failure is None:
                        failure = exc
                    print(f"[diagnostic] ROLLBACK failed: {type(exc).__name__}", flush=True)
            connection.close()

    remaining = confirm_empty_after_rollback(settings)
    empty = len(remaining) == 40 and not any(remaining.values())
    print(f"[diagnostic] fresh_connection tables={len(remaining)} empty={empty}", flush=True)
    print(f"[diagnostic] total_seconds={perf_counter()-run_started:.2f}", flush=True)
    return 0 if failure is None and empty else 1


if __name__ == "__main__":
    raise SystemExit(main())
