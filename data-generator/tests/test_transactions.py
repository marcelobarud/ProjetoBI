from copy import deepcopy
from dataclasses import replace
from datetime import datetime, time, timedelta
from decimal import Decimal

import pytest

from projectbi_generator.generators.transactions import EventQueue, ScheduledEvent, _location_balanced_bootstrap_plan, allocate_cents, generate_transactions, generate_transactions_incremental, weighted_moving_average
from projectbi_generator.models.transactions import OrderStatusEvent, StockStateEvent
from projectbi_generator.sinks import CollectingSink, CountingDiscardingSink
from projectbi_generator.validation.transactions import validate_transactional_data
from projectbi_generator.validation.order_history import validate_order_history


def test_order_history_allows_draft_five_minutes_before_placed_and_valid_progression(config):
    placed_at = datetime.combine(config.start_date, time(10), tzinfo=config.timezone)
    events = [
        OrderStatusEvent("order", "draft", placed_at - timedelta(minutes=5)),
        OrderStatusEvent("order", "placed", placed_at),
        OrderStatusEvent("order", "confirmed", placed_at + timedelta(minutes=3)),
        OrderStatusEvent("order", "completed", placed_at + timedelta(hours=2)),
    ]
    validate_order_history(events, placed_at, "completed")


def test_order_history_rejects_non_draft_before_placed(config):
    placed_at = datetime.combine(config.start_date, time(10), tzinfo=config.timezone)
    events = [
        OrderStatusEvent("order", "draft", placed_at - timedelta(minutes=5)),
        OrderStatusEvent("order", "confirmed", placed_at - timedelta(minutes=4)),
        OrderStatusEvent("order", "placed", placed_at),
    ]
    with pytest.raises(ValueError, match="Status diferente de draft"):
        validate_order_history(events, placed_at, "placed")


def test_order_history_rejects_draft_after_placed(config):
    placed_at = datetime.combine(config.start_date, time(10), tzinfo=config.timezone)
    events = [
        OrderStatusEvent("order", "placed", placed_at),
        OrderStatusEvent("order", "draft", placed_at + timedelta(minutes=5)),
    ]
    with pytest.raises(ValueError, match="draft antes de placed_at"):
        validate_order_history(events, placed_at, "draft")


def test_order_history_rejects_backward_or_unordered_transitions(config):
    placed_at = datetime.combine(config.start_date, time(10), tzinfo=config.timezone)
    backwards = [
        OrderStatusEvent("order", "draft", placed_at - timedelta(minutes=5)),
        OrderStatusEvent("order", "placed", placed_at),
        OrderStatusEvent("order", "completed", placed_at + timedelta(hours=2)),
    ]
    with pytest.raises(ValueError, match="Transição de status inválida"):
        validate_order_history(backwards, placed_at, "completed")
    unordered = [backwards[0], backwards[2], backwards[1]]
    with pytest.raises(ValueError, match="fora de ordem cronológica"):
        validate_order_history(unordered, placed_at, "confirmed")


def test_event_queue_orders_by_time_priority_then_stable_key(config):
    at = config.start_date
    from datetime import datetime, time

    stamp = datetime.combine(at, time(10), tzinfo=config.timezone)
    queue = EventQueue()
    queue.push(ScheduledEvent(stamp, 20, "z", "sale", {}))
    queue.push(ScheduledEvent(stamp, 10, "b", "receipt", {}))
    queue.push(ScheduledEvent(stamp, 10, "a", "receipt", {}))
    assert [queue.pop().logical_key for _ in range(3)] == ["a", "b", "z"]
    assert queue.pending_events == 0
    assert queue.max_pending_events == 3
    assert queue.total_pushed == queue.total_popped == 3


def test_weighted_average_first_and_second_receipts_rounds_to_eight_places():
    first = weighted_moving_average(0, Decimal("0"), 3, Decimal("1.00000001"))
    second = weighted_moving_average(3, first, 1, Decimal("1.00000002"))
    assert first == Decimal("1.00000001")
    assert second == Decimal("1.00000001")
    assert second.as_tuple().exponent == -8


@pytest.mark.parametrize("quantity", (9, 12, 15))
def test_experimental_location_balanced_bootstrap_conserves_units(quantity):
    stores = [f"STORE-{index:02}" for index in range(10)]
    warehouses = [f"WH-{index:02}" for index in range(4)]

    first = _location_balanced_bootstrap_plan(quantity, 7, stores, warehouses)
    second = _location_balanced_bootstrap_plan(quantity, 7, stores, warehouses)

    assert first == second
    assert sum(units for _location, units in first) == quantity
    assert all(units > 0 for _location, units in first)


def test_weighted_average_uses_half_up_for_exact_eighth_decimal_tie():
    # Raw result is 529.181918925: PostgreSQL NUMERIC and the engine round the
    # tie away from zero to .93; Decimal's default HALF_EVEN would produce .92.
    assert weighted_moving_average(
        2, Decimal("565.20651660"), 6, Decimal("517.17371970")
    ) == Decimal("529.18191893")


def test_order_discount_cent_remainders_are_stable_and_conserved():
    eligible = [Decimal("1.00"), Decimal("1.00"), Decimal("1.00")]
    assert allocate_cents(Decimal("0.01"), eligible) == [Decimal("0.01"), Decimal("0.00"), Decimal("0.00")]
    assert allocate_cents(Decimal("0.02"), eligible) == [Decimal("0.01"), Decimal("0.01"), Decimal("0.00")]
    assert sum(allocate_cents(Decimal("0.02"), eligible), Decimal("0")) == Decimal("0.02")


def test_smoke_counts_causal_receipts_partial_replenishment_and_fulfillment(transaction_data, master_data, config):
    validate_transactional_data(transaction_data, master_data, config)
    counts = transaction_data.counts()
    assert counts["sales_orders"] == 300
    assert counts["sales_order_items"] == 630
    assert counts["purchase_orders"] >= 35
    assert counts["goods_receipts"] >= counts["purchase_orders"]
    assert counts["stock_positions"] < len(master_data.products) * len(master_data.stock_locations)
    assert transaction_data.summary()["units_received"] == transaction_data.summary()["units_fulfilled"] + transaction_data.summary()["ending_stock"]
    assert any(row.quantity_received < next(item.quantity_ordered for item in transaction_data.purchase_order_items if item.key == row.order_item_key) for row in transaction_data.goods_receipt_items)
    assert any(row.rejected_quantity for row in transaction_data.goods_receipt_items)
    assert any(row.event_type == "receipt" for row in transaction_data.stock_state_events)


def test_transactions_are_deterministic_and_domain_state_is_independent(master_data, config):
    first = generate_transactions(config, master_data)
    second = generate_transactions(config, master_data)
    assert first == second
    assert [row.number for row in first.purchase_orders] == [row.number for row in second.purchase_orders]
    assert [row.number for row in first.sales_orders] == [row.number for row in second.sales_orders]


def test_order_volume_comes_from_profile_configuration(master_data, config):
    configured = replace(config, generation={**config.generation, "sales_orders": 420})
    data = generate_transactions(configured, master_data)
    assert data.counts()["sales_orders"] == 420


def test_smoke_has_all_channels_anonymous_cancelled_discounted_and_split_orders(transaction_data):
    summary = transaction_data.summary()
    assert set(summary["orders_by_channel"]) == {"CH-PHYSICAL", "CH-ECOM", "CH-MARKET-A", "CH-MARKET-B"}
    assert summary["anonymous_physical_orders"] > 0
    assert summary["cancelled_orders"] > 0
    assert summary["discounts"] > 0
    assert summary["split_orders"] > 0
    assert any(order.discount == 0 for order in transaction_data.sales_orders)
    assert any(discount.scope == "line" for discount in transaction_data.applied_discounts)
    assert any(discount.scope == "order_allocation" for discount in transaction_data.applied_discounts)
    assert all(not any(item.order_key == order.key for item in transaction_data.fulfillment_items) for order in transaction_data.sales_orders if order.status == "cancelled")


def test_digital_order_without_customer_is_rejected(transaction_data, master_data, config):
    bad = deepcopy(transaction_data)
    index = next(i for i, row in enumerate(bad.sales_orders) if row.channel_type != "physical")
    bad.sales_orders[index] = replace(bad.sales_orders[index], customer_code=None)
    with pytest.raises(ValueError, match="digital sem cliente"):
        validate_transactional_data(bad, master_data, config)


def test_unassociated_supplier_purchase_is_rejected(transaction_data, master_data, config):
    bad = deepcopy(transaction_data)
    product = bad.purchase_order_items[0].product_sku
    associated = {row.supplier_code for row in master_data.product_suppliers if row.product_sku == product}
    supplier = next(row.code for row in master_data.suppliers if row.code not in associated)
    bad.purchase_orders[0] = replace(bad.purchase_orders[0], supplier_code=supplier)
    with pytest.raises(ValueError, match="não associado"):
        validate_transactional_data(bad, master_data, config)


def test_receipt_above_purchase_and_accepted_rejected_mismatch_are_rejected(transaction_data, master_data, config):
    bad = deepcopy(transaction_data)
    receipt = bad.goods_receipt_items[0]
    item = next(row for row in bad.purchase_order_items if row.key == receipt.order_item_key)
    bad.goods_receipt_items[0] = replace(receipt, quantity_received=item.quantity_ordered + 1,
                                         accepted_quantity=item.quantity_ordered + 1)
    with pytest.raises(ValueError, match="supera a quantidade"):
        validate_transactional_data(bad, master_data, config)
    bad = deepcopy(transaction_data)
    bad.goods_receipt_items[0] = replace(bad.goods_receipt_items[0], rejected_quantity=1)
    with pytest.raises(ValueError, match=r"accepted \+ rejected"):
        validate_transactional_data(bad, master_data, config)


def test_reservation_above_available_is_rejected(transaction_data, master_data, config):
    bad = deepcopy(transaction_data)
    index = next(i for i, row in enumerate(bad.stock_state_events) if row.event_type == "reserve")
    bad.stock_state_events[index] = replace(bad.stock_state_events[index], quantity=100000)
    with pytest.raises(ValueError, match="Reserva maior que o disponível"):
        validate_transactional_data(bad, master_data, config)


def test_fulfillment_allocation_above_sold_is_rejected(transaction_data, master_data, config):
    bad = deepcopy(transaction_data)
    fulfillment_item = bad.fulfillment_items[0]
    bad.fulfillment_items[0] = replace(fulfillment_item, quantity_allocated=100000)
    with pytest.raises(ValueError, match="excede a reserva"):
        validate_transactional_data(bad, master_data, config)


def test_cancelled_order_cannot_have_fulfillment(transaction_data, master_data, config):
    bad = deepcopy(transaction_data)
    order = next(row for row in bad.sales_orders if any(fi.order_key == row.key for fi in bad.fulfillment_items))
    bad.sales_orders[bad.sales_orders.index(order)] = replace(order, status="cancelled")
    history = next(i for i, event in enumerate(bad.order_status_history) if event.order_key == order.key and event.status == order.status)
    bad.order_status_history[history] = replace(bad.order_status_history[history], status="cancelled")
    with pytest.raises(ValueError, match="Pedido cancelado tem fulfillment"):
        validate_transactional_data(bad, master_data, config)


def test_discount_above_line_eligibility_and_negative_total_are_rejected(transaction_data, master_data, config):
    bad = deepcopy(transaction_data)
    bad.applied_discounts[0] = replace(bad.applied_discounts[0], amount=Decimal("99999999.99"))
    with pytest.raises(ValueError, match="supera o valor elegível"):
        validate_transactional_data(bad, master_data, config)
    bad = deepcopy(transaction_data)
    bad.sales_orders[0] = replace(bad.sales_orders[0], total=Decimal("-1.00"))
    with pytest.raises(ValueError, match="negativo"):
        validate_transactional_data(bad, master_data, config)


def test_out_of_vigency_price_and_invalid_receipt_chronology_are_rejected(transaction_data, master_data, config):
    bad = deepcopy(transaction_data)
    item = bad.sales_order_items[0]
    bad.sales_order_items[0] = replace(item, unit_sale_price=item.unit_sale_price + Decimal("1.00"))
    with pytest.raises(ValueError, match="vigência aplicada"):
        validate_transactional_data(bad, master_data, config)
    bad = deepcopy(transaction_data)
    receipt = bad.goods_receipts[0]
    order = next(row for row in bad.purchase_orders if row.key == receipt.order_key)
    bad.goods_receipts[0] = replace(receipt, received_at=order.ordered_at - timedelta(days=1))
    with pytest.raises(ValueError, match="anterior"):
        validate_transactional_data(bad, master_data, config)


def test_movement_direction_and_float_cost_are_rejected(transaction_data, master_data, config):
    bad = deepcopy(transaction_data)
    index = next(i for i, row in enumerate(bad.stock_movements) if row.movement_type == "fulfillment")
    bad.stock_movements[index] = replace(bad.stock_movements[index], quantity_delta=1)
    with pytest.raises(ValueError, match="Saída fulfillment diverge"):
        validate_transactional_data(bad, master_data, config)
    bad = deepcopy(transaction_data)
    bad.purchase_order_items[0] = replace(bad.purchase_order_items[0], unit_cost_ordered=1.25)
    with pytest.raises(ValueError, match="deve ser Decimal"):
        validate_transactional_data(bad, master_data, config)


def test_no_transaction_event_exceeds_cutoff(transaction_data, config):
    assert all(event.occurred_at.date() <= config.end_date for event in transaction_data.stock_state_events)
    assert all(order.placed_at.date() <= config.end_date for order in transaction_data.sales_orders)
    assert transaction_data.summary()["active_reserved"] == 0


def test_incremental_core_smoke_matches_legacy_and_releases_batches(master_data, transaction_data, config):
    sink = CollectingSink()
    streamed = generate_transactions_incremental(config, master_data, sink, batch_size=37)
    table_fields = (
        "purchase_orders", "purchase_order_items", "goods_receipts", "goods_receipt_items",
        "sales_orders", "sales_order_items", "order_status_history", "applied_discounts",
        "stock_reservations", "fulfillments", "fulfillment_items", "stock_movements",
        "stock_state_events",
    )
    for table in table_fields:
        assert sorted(sink.rows_by_table[table], key=repr) == sorted(getattr(transaction_data, table), key=repr), table
    assert sorted(sink.rows_by_table["stock_positions"], key=repr) == sorted(transaction_data.stock_positions.values(), key=repr)
    assert streamed.counts()["sales_orders"] == 300
    assert streamed.counts()["sales_order_items"] == 630
    assert streamed.aggregates["purchase_orders"] == 49
    assert streamed.aggregates["receipts"] == 50
    assert streamed.aggregates["fulfillments"] == 193
    assert streamed.aggregates["fulfilled_items"] == 227
    assert streamed.aggregates["units_received"] == 457
    assert streamed.aggregates["units_fulfilled"] == 238
    assert streamed.aggregates["ending_stock"] == 219
    assert streamed.aggregates["realized_cost"] == Decimal("369830.61051434")
    assert streamed.aggregates["cancelled_orders"] == 8
    assert streamed.aggregates["split_fulfillments"] == 23
    assert streamed.runtime_metrics["max_buffered_rows"] <= 37
    assert streamed.runtime_metrics["flush_count"] > 1
    assert streamed.runtime_metrics["current_active_orders"] == 0
    assert streamed.runtime_metrics["current_future_events_3c"] == 0


def test_incremental_core_digest_is_independent_of_batch_size(master_data, config):
    digests = []
    counts = []
    for batch_size in (31, 127):
        sink = CountingDiscardingSink()
        result = generate_transactions_incremental(config, master_data, sink, batch_size=batch_size)
        digests.append(sink.logical_digest)
        counts.append(sink.rows_by_table)
        assert result.runtime_metrics["max_buffered_rows"] <= batch_size
        assert result.runtime_metrics["total_rows_emitted"] == sink.total_rows_emitted
    assert digests[0] == digests[1]
    assert counts[0] == counts[1]
