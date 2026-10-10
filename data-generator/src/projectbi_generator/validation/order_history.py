"""Shared contract for chronological order status history."""

from __future__ import annotations

from itertools import pairwise


ORDER_STATUS_TRANSITIONS = {
    "draft": frozenset({"placed"}),
    "placed": frozenset({"confirmed", "cancelled"}),
    "confirmed": frozenset({"completed", "cancelled"}),
    "cancelled": frozenset(),
    "completed": frozenset(),
}


def validate_order_history(events, placed_at, current_status: str) -> None:
    """Raise ValueError when an order history violates its documented lifecycle."""
    if not events:
        raise ValueError("Histórico de status do pedido está vazio.")

    if any(previous.occurred_at > current.occurred_at for previous, current in pairwise(events)):
        raise ValueError("Histórico de status fora de ordem cronológica.")

    drafts = [event for event in events if event.status == "draft"]
    placed_events = [event for event in events if event.status == "placed"]
    if len(drafts) != 1 or drafts[0].occurred_at >= placed_at:
        raise ValueError("O pedido deve ter um único evento draft antes de placed_at.")
    if len(placed_events) != 1 or placed_events[0].occurred_at != placed_at:
        raise ValueError("O evento placed deve ocorrer exatamente em placed_at.")

    for event in events:
        if event.status != "draft" and event.occurred_at < placed_at:
            raise ValueError("Status diferente de draft não pode anteceder placed_at.")

    for previous, current in pairwise(events):
        if current.status not in ORDER_STATUS_TRANSITIONS.get(previous.status, frozenset()):
            raise ValueError(f"Transição de status inválida: {previous.status} → {current.status}.")

    if events[-1].status != current_status:
        raise ValueError("Status final do pedido diverge do histórico.")
