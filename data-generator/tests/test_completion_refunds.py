from decimal import Decimal
from types import SimpleNamespace

from projectbi_generator.validation.completion import _cancelled_order_financially_resolved


def test_cancelled_order_can_be_financially_resolved_by_full_stock_wait_refund():
    captured = Decimal("125.50")
    assert _cancelled_order_financially_resolved([], captured, captured)
    assert not _cancelled_order_financially_resolved([], captured, Decimal("100.00"))


def test_unpaid_cancelled_order_still_requires_cancelled_payment_attempt():
    assert _cancelled_order_financially_resolved([SimpleNamespace(status="cancelled")], Decimal("0"), Decimal("0"))
    assert not _cancelled_order_financially_resolved([SimpleNamespace(status="declined")], Decimal("0"), Decimal("0"))
