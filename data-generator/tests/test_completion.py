from copy import deepcopy
from dataclasses import replace

import pytest

from projectbi_generator.generators.completion import extend_transactions
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
