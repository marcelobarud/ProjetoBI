from copy import deepcopy
from dataclasses import replace
from collections import Counter
from decimal import Decimal
import hashlib
import json

import pytest

from projectbi_generator.generators.completion import extend_transactions, generate_full_transactions_incremental
from projectbi_generator.sinks import CollectingSink, CountingDiscardingSink
from projectbi_generator.sinks import _canonical
from projectbi_generator.validation.completion import validate_completed_data


def test_phase3d_is_deterministic_and_preserves_phase3c_sales(config, master_data, transaction_data, completed_data):
    first = deepcopy(transaction_data)
    second = deepcopy(transaction_data)
    extend_transactions(config, master_data, first)
    extend_transactions(config, master_data, second)
    assert first == second == completed_data
    # Phase 3D enriches, but does not mutate, the Phase 3C sales/fulfillment baseline.
    for field in ("sales_orders", "sales_order_items", "order_status_history", "applied_discounts",
                  "stock_reservations", "fulfillments", "fulfillment_items"):
        assert getattr(completed_data, field) == getattr(transaction_data, field)
    assert completed_data.summary()["realized_cost"] == transaction_data.summary()["realized_cost"]


def test_payment_reconciliation_retries_splits_and_installment_bands(completed_data, master_data, config):
    metrics = validate_completed_data(completed_data, master_data, config)
    orders = {row.key: row for row in completed_data.sales_orders}
    successful = {row.key: row for row in completed_data.payments if row.status in {"captured", "settled"}}
    methods = {row.code: row for row in master_data.payment_methods}
    assert metrics["payments"] > len(completed_data.sales_orders)
    assert metrics["declined_attempts"] > 0
    assert completed_data.summary()["payment_retries"] == metrics["declined_attempts"]
    assert metrics["captured_amount"] == sum((row.total for row in completed_data.sales_orders if row.status != "cancelled"), start=type(completed_data.payments[0].amount)("0.00"))
    assert completed_data.summary()["split_payment_orders"] > 0
    installment_counts = {}
    for installment in completed_data.payment_installments:
        payment = successful[installment.payment_key]
        installment_counts[payment.key] = installment_counts.get(payment.key, 0) + 1
        assert methods[payment.method_code].is_installment_capable
        assert installment.amount > 0
    assert any(count == 1 for count in installment_counts.values())
    assert any(2 <= count <= 4 for count in installment_counts.values())
    assert any(count >= 5 for count in installment_counts.values())
    assert all(not any(i.payment_key == p.key for i in completed_data.payment_installments)
               for p in completed_data.payments if methods[p.method_code].method_type in {"cash", "instant"})
    assert all(row.channel_type == "physical" for row in orders.values() if any(
        p.order_key == row.key and methods[p.method_code].method_type == "cash" for p in completed_data.payments))


def test_payment_capture_mismatch_and_invalid_retry_are_rejected(completed_data, master_data, config):
    bad = deepcopy(completed_data)
    index = next(i for i, row in enumerate(bad.payments) if row.status in {"captured", "settled"})
    bad.payments[index] = replace(bad.payments[index], amount=bad.payments[index].amount + 1)
    with pytest.raises(ValueError, match="não conciliam exatamente"):
        validate_completed_data(bad, master_data, config)
    bad = deepcopy(completed_data)
    index = next(i for i, row in enumerate(bad.payments) if row.status == "declined")
    bad.payments[index] = replace(bad.payments[index], authorized_at=bad.payments[index].attempted_at)
    with pytest.raises(ValueError, match="não pode conter autorização"):
        validate_completed_data(bad, master_data, config)


def test_fulfillment_event_sequences_and_cutoff(completed_data, master_data, config):
    events_by_key = {}
    for event in completed_data.fulfillment_events:
        events_by_key.setdefault(event.fulfillment_key, []).append(event)
        assert event.occurred_at.date() <= config.end_date
    deliveries = [row for row in completed_data.fulfillments if row.status == "completed" and row.fulfillment_type == "delivery"]
    pickups = [row for row in completed_data.fulfillments if row.status == "completed" and row.fulfillment_type == "store_pickup"]
    assert deliveries and pickups
    delivery = deliveries[0]
    events = events_by_key[delivery.key]
    dispatched = next(row for row in events if row.event_type == "dispatched")
    delivered = next(row for row in events if row.event_type == "delivered")
    bad = deepcopy(completed_data)
    bad.fulfillment_events[bad.fulfillment_events.index(dispatched)] = replace(dispatched, occurred_at=delivered.occurred_at)
    with pytest.raises(ValueError, match="delivery"):
        validate_completed_data(bad, master_data, config)
    pickup = pickups[0]
    pickup_events = events_by_key[pickup.key]
    ready = next(row for row in pickup_events if row.event_type == "pickup_ready")
    picked = next(row for row in pickup_events if row.event_type == "picked_up")
    bad = deepcopy(completed_data)
    bad.fulfillment_events[bad.fulfillment_events.index(ready)] = replace(ready, occurred_at=picked.occurred_at)
    with pytest.raises(ValueError, match="pickup"):
        validate_completed_data(bad, master_data, config)


def test_transfers_reconcile_paired_movements_and_cost(completed_data, master_data, config):
    assert completed_data.stock_transfers
    assert sum(row.movement_type in {"transfer_out", "transfer_in"} for row in completed_data.stock_movements) >= 4
    assert sum(row.movement_type == "transfer_out" for row in completed_data.stock_movements) == len(completed_data.stock_transfer_items)
    assert sum(row.movement_type == "transfer_in" for row in completed_data.stock_movements) == len(completed_data.stock_transfer_items)
    out = next(row for row in completed_data.stock_movements if row.movement_type == "transfer_out")
    bad = deepcopy(completed_data)
    index = next(i for i, row in enumerate(bad.stock_movements) if row.transfer_item_key == out.transfer_item_key and row.movement_type == "transfer_in")
    bad.stock_movements[index] = replace(bad.stock_movements[index], unit_cost=out.unit_cost + 1)
    with pytest.raises(ValueError, match="não conciliam quantidade/custo/tempo"):
        validate_completed_data(bad, master_data, config)


def test_returns_refunds_historical_cost_and_stock_destinations(completed_data, master_data, config):
    assert len(completed_data.returns) == 8
    assert any(row.status == "rejected" for row in completed_data.returns)
    assert any(row.stock_destination == "sellable" for row in completed_data.return_items)
    assert any(row.stock_destination in {"quarantine", "repair", "discard"} for row in completed_data.return_items)
    assert completed_data.refunds
    assert all(row.source_fulfillment_item_key for row in completed_data.return_items)
    assert completed_data.summary()["ending_stock"] == sum(row.accepted_quantity for row in completed_data.goods_receipt_items) - sum(
        row.fulfilled_quantity for row in completed_data.fulfillment_items) + sum(
        row.quantity_received for row in completed_data.return_items if row.stock_destination == "sellable")
    returned = next(row for row in completed_data.return_items if row.quantity_received and row.stock_destination == "sellable")
    bad = deepcopy(completed_data)
    index = next(i for i, row in enumerate(bad.return_items) if row.key == returned.key)
    bad.return_items[index] = replace(returned, source_fulfillment_item_key="missing-fulfillment")
    with pytest.raises(ValueError, match="Return item aponta"):
        validate_completed_data(bad, master_data, config)
    bad = deepcopy(completed_data)
    refund = bad.refunds[0]
    index = next(i for i, row in enumerate(bad.payments) if row.key == refund.payment_key)
    captured_payment = bad.payments[index]
    bad.payments[index] = replace(captured_payment, status="cancelled", authorized_at=None, settled_at=None)
    bad.payment_installments = [row for row in bad.payment_installments if row.payment_key != captured_payment.key]
    bad.payments.append(replace(captured_payment, key=captured_payment.key + "-OTHER",
                                reference=captured_payment.reference + "-OTHER"))
    with pytest.raises(ValueError, match="não referencia pagamento capturado"):
        validate_completed_data(bad, master_data, config)


def test_completion_all_transactional_dates_respect_cutoff(completed_data, config):
    for row in completed_data.payments:
        assert row.attempted_at.date() <= config.end_date
    for row in completed_data.fulfillment_events:
        assert row.occurred_at.date() <= config.end_date
    for row in completed_data.stock_transfers:
        assert row.received_at.date() <= config.end_date
    for row in completed_data.returns:
        assert row.requested_at.date() <= config.end_date
    for row in completed_data.refunds:
        assert row.requested_at.date() <= config.end_date


def test_incremental_full_smoke_matches_legacy_all_21_tables(completed_data, master_data, config):
    sink = CollectingSink()
    result = generate_full_transactions_incremental(config, master_data, sink, batch_size=37)
    fields = (
        "purchase_orders", "purchase_order_items", "goods_receipts", "goods_receipt_items",
        "sales_orders", "sales_order_items", "order_status_history", "applied_discounts",
        "stock_reservations", "fulfillments", "fulfillment_items", "stock_movements",
        "payments", "payment_installments", "fulfillment_events", "stock_transfers",
        "stock_transfer_items", "returns", "return_items", "refunds",
    )
    for field in fields:
        assert Counter(map(repr, getattr(completed_data, field))) == Counter(map(repr, sink.rows_by_table[field])), field
    assert Counter(map(repr, completed_data.stock_positions.values())) == Counter(map(repr, sink.rows_by_table["stock_positions"]))
    def canonical_digest(rows_by_table):
        digest = hashlib.sha256()
        for table in sorted(rows_by_table):
            digest.update(table.encode("utf-8"))
            encoded = sorted(json.dumps(_canonical(row), ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8") for row in rows_by_table[table])
            for row in encoded:
                digest.update(len(row).to_bytes(8, "big"))
                digest.update(row)
        return digest.hexdigest()
    legacy_tables = {field: getattr(completed_data, field) for field in fields}
    legacy_tables["stock_positions"] = list(completed_data.stock_positions.values())
    streamed_tables = {name: sink.rows_by_table[name] for name in legacy_tables}
    assert canonical_digest(legacy_tables) == canonical_digest(streamed_tables)
    actual = {"orders": 300, "items": 630, "payments": 314, "installments": 587,
              "fulfillments": 193, "fulfillment_items": 227, "fulfillment_events": 590,
              "transfers": 2, "returns": 8, "refunds": 6}
    assert result.counts()["sales_orders"] == actual["orders"]
    assert result.counts()["sales_order_items"] == actual["items"]
    assert result.counts()["payments"] == actual["payments"]
    assert result.counts()["payment_installments"] == actual["installments"]
    assert result.counts()["fulfillment_events"] == actual["fulfillment_events"]
    assert result.counts()["stock_transfers"] == actual["transfers"]
    assert result.counts()["returns"] == actual["returns"]
    assert result.counts()["refunds"] == actual["refunds"]
    assert result.aggregates["captured_amount"] == Decimal("2791128.94")
    assert result.aggregates["refund_amount"] == Decimal("18420.97")
    assert result.aggregates["net_financial_amount"] == Decimal("2772707.97")
    assert result.aggregates["ending_stock"] == 222
    assert result.aggregates["realized_cost"] == Decimal("369830.61051434")
    assert result.runtime_metrics["current_active_orders"] == 0
    assert result.runtime_metrics["current_active_payments"] == 0
    assert result.runtime_metrics["current_active_transfers"] == 0
    assert result.runtime_metrics["current_return_eligibility"] == 0
    assert result.runtime_metrics["max_buffered_rows"] <= 37


def test_incremental_full_digest_and_bounded_state_ignore_batch_size(master_data, config):
    results = []
    for batch_size in (31, 127):
        sink = CountingDiscardingSink()
        result = generate_full_transactions_incremental(config, master_data, sink, batch_size=batch_size)
        results.append((sink.logical_digest, sink.rows_by_table))
        assert result.runtime_metrics["max_buffered_rows"] <= batch_size
        assert result.runtime_metrics["current_active_payments"] == 0
        assert result.runtime_metrics["current_active_transfers"] == 0
        assert result.runtime_metrics["current_return_eligibility"] == 0
        assert result.runtime_metrics["max_active_payments"] > 0
        assert result.runtime_metrics["max_active_transfers"] > 0
    assert results[0] == results[1]


def test_sellable_return_updates_average_before_later_fulfillment(completed_data):
    events = sorted(completed_data.stock_state_events, key=lambda row: (row.occurred_at, row.priority, row.key))
    movements = {row.key: row for row in completed_data.stock_movements}
    for index, returned in enumerate(events):
        if returned.event_type != "customer_return":
            continue
        later = next((row for row in events[index + 1:]
                      if row.event_type == "fulfillment"
                      and (row.product_sku, row.location_code) == (returned.product_sku, returned.location_code)), None)
        if later is None:
            continue
        movement = movements[later.movement_key]
        assert later.occurred_at > returned.occurred_at
        assert movement.unit_cost == returned.unit_cost
        return
    pytest.fail("Smoke não exercitou fulfillment posterior a retorno vendável no mesmo produto/local.")


def test_distant_return_and_refund_keep_only_bounded_active_state(master_data, config):
    sink = CollectingSink()
    result = generate_full_transactions_incremental(config, master_data, sink, batch_size=37)
    refund = sink.rows_by_table["refunds"][0]
    return_row = next(row for row in sink.rows_by_table["returns"] if row.key == refund.return_key)
    return_item = next(row for row in sink.rows_by_table["return_items"] if row.return_key == return_row.key)
    source = next(row for row in sink.rows_by_table["fulfillment_items"] if row.key == return_item.source_fulfillment_item_key)
    fulfillment = next(row for row in sink.rows_by_table["fulfillments"] if row.key == source.fulfillment_key)
    assert (return_row.requested_at - fulfillment.completed_at).days >= 5
    assert (refund.requested_at - return_row.requested_at).days >= 4
    assert result.runtime_metrics["current_active_orders"] == 0
    assert result.runtime_metrics["current_active_payments"] == 0
    assert result.runtime_metrics["current_active_transfers"] == 0
    assert result.runtime_metrics["current_return_eligibility"] == 0
    assert not result.sales_orders.pending
    assert not result.fulfillment_items.pending
    assert not result.stock_transfers.pending
    assert not result.returns.pending
