"""Bounded batching helpers shared by repository writers."""

from __future__ import annotations

from collections.abc import Iterable, Iterator
from typing import TypeVar

T = TypeVar("T")


def iter_batches(rows: Iterable[T], batch_size: int) -> Iterator[list[T]]:
    """Yield at most ``batch_size`` rows at a time without materializing the input."""
    if batch_size <= 0:
        raise ValueError("batch_size deve ser positivo.")
    batch: list[T] = []
    for row in rows:
        batch.append(row)
        if len(batch) == batch_size:
            yield batch
            batch = []
    if batch:
        yield batch
