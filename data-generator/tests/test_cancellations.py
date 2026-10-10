from datetime import datetime, timezone
from decimal import Decimal

import pytest

from projectbi_generator.cancellations import allocate_refund, cancellation_amounts, discount_slice


def test_one_of_three_discounted_units_reconciles_exactly():
    assert cancellation_amounts(Decimal("100.00"), 3, Decimal("30.00"), 2, 1) == (
        Decimal("100.00"), Decimal("10.00"), Decimal("90.00")
    )


def test_indivisible_discount_cents_are_allocated_by_stable_unit_order():
    slices = [discount_slice(Decimal("0.05"), 3, offset, 1) for offset in range(3)]
    assert slices == [Decimal("0.02"), Decimal("0.02"), Decimal("0.01")]
    assert sum(slices, Decimal("0.00")) == Decimal("0.05")


def test_multiple_cancellations_reconcile_without_rounding_drift():
    first = cancellation_amounts(Decimal("0.10"), 7, Decimal("0.03"), 2, 2)
    second = cancellation_amounts(Decimal("0.10"), 7, Decimal("0.03"), 4, 3)
    all_units = cancellation_amounts(Decimal("0.10"), 7, Decimal("0.03"), 0, 7)
    assert first[1] + second[1] + discount_slice(Decimal("0.03"), 7, 0, 2) == all_units[1]


def test_refund_consumes_split_payments_by_capture_time_then_key():
    t0 = datetime(2025, 1, 1, tzinfo=timezone.utc)
    t1 = datetime(2025, 1, 2, tzinfo=timezone.utc)
    rows = [
        ("PAY-B", Decimal("120.00"), Decimal("0.00"), t1),
        ("PAY-A", Decimal("150.00"), Decimal("80.00"), t0),
    ]
    assert allocate_refund(Decimal("90.00"), rows) == [("PAY-A", Decimal("70.00")), ("PAY-B", Decimal("20.00"))]


def test_refund_cannot_exceed_remaining_captured_amount():
    t0 = datetime(2025, 1, 1, tzinfo=timezone.utc)
    with pytest.raises(ValueError, match="saldos capturados"):
        allocate_refund(Decimal("2.00"), [("PAY-A", Decimal("1.00"), Decimal("0.50"), t0)])


def test_cancellation_rejects_units_outside_original_range():
    with pytest.raises(ValueError):
        cancellation_amounts(Decimal("100.00"), 3, Decimal("0.00"), 3, 1)
