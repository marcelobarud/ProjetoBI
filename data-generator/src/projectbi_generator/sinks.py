"""Bounded transaction batch contracts and in-memory sink implementations."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
import hashlib
import json
from typing import Any, Protocol


@dataclass(frozen=True)
class TransactionBatch:
    """A bounded set of logical transaction records waiting for consumption."""

    rows_by_table: dict[str, tuple[Any, ...]]
    release_keys: tuple[tuple[str, str], ...] = ()
    updates_by_table: dict[str, tuple[Any, ...]] | None = None

    @property
    def row_count(self) -> int:
        return sum(len(rows) for rows in self.rows_by_table.values()) + sum(
            len(rows) for rows in (self.updates_by_table or {}).values()
        )


class TransactionSink(Protocol):
    """Consumer boundary for causally complete transaction batches."""

    def consume(self, batch: TransactionBatch) -> None: ...


def _canonical(value: Any) -> Any:
    if isinstance(value, Decimal):
        return format(value, "f")
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if hasattr(value, "__dataclass_fields__"):
        return {
            name: _canonical(getattr(value, name))
            for name in value.__dataclass_fields__
        }
    if isinstance(value, dict):
        return {str(key): _canonical(value[key]) for key in sorted(value, key=str)}
    if isinstance(value, (tuple, list)):
        return [_canonical(item) for item in value]
    return value


class CollectingSink:
    """Retain consumed rows; intended for smoke-sized regression fixtures."""

    def __init__(self) -> None:
        self.rows_by_table: dict[str, list[Any]] = {}
        self.max_batch_rows = 0
        self._row_indexes: dict[str, dict[str, int]] = {}

    def consume(self, batch: TransactionBatch) -> None:
        self.max_batch_rows = max(self.max_batch_rows, batch.row_count)
        for table, rows in batch.rows_by_table.items():
            target = self.rows_by_table.setdefault(table, [])
            index = self._row_indexes.setdefault(table, {})
            for row in rows:
                key = getattr(row, "key", None)
                if key is not None and key in index:
                    raise ValueError(f"Registro lógico duplicado no sink coletor: {table}.")
                if key is not None:
                    index[key] = len(target)
                target.append(row)
        for table, rows in (batch.updates_by_table or {}).items():
            target = self.rows_by_table.setdefault(table, [])
            index = self._row_indexes.setdefault(table, {})
            for row in rows:
                key = getattr(row, "key", None)
                if key is None or key not in index:
                    raise ValueError(f"Atualização lógica sem linha inicial no sink coletor: {table}.")
                target[index[key]] = row


class CountingDiscardingSink:
    """Count and hash logical records, releasing each batch on return."""

    def __init__(self) -> None:
        self.rows_by_table: dict[str, int] = {}
        self._hashes: dict[str, Any] = {}
        self.max_batch_rows = 0
        self.updated_rows_by_table: dict[str, int] = {}

    def consume(self, batch: TransactionBatch) -> None:
        self.max_batch_rows = max(self.max_batch_rows, batch.row_count)
        for table, rows in batch.rows_by_table.items():
            self.rows_by_table[table] = self.rows_by_table.get(table, 0) + len(rows)
            digest = self._hashes.setdefault(table, hashlib.sha256())
            for row in rows:
                encoded = json.dumps(
                    _canonical(row), ensure_ascii=False, sort_keys=True, separators=(",", ":")
                ).encode("utf-8")
                digest.update(len(encoded).to_bytes(8, "big"))
                digest.update(encoded)
        for table, rows in (batch.updates_by_table or {}).items():
            self.updated_rows_by_table[table] = self.updated_rows_by_table.get(table, 0) + len(rows)

    @property
    def total_rows_emitted(self) -> int:
        return sum(self.rows_by_table.values())

    @property
    def logical_digest(self) -> str:
        combined = hashlib.sha256()
        for table in sorted(self._hashes):
            combined.update(table.encode("utf-8"))
            combined.update(self._hashes[table].digest())
        return combined.hexdigest()


class TransactionBatchEmitter:
    """Buffer rows up to a shared threshold and hand batches to a sink."""

    def __init__(self, sink: TransactionSink, batch_size: int) -> None:
        if batch_size <= 0:
            raise ValueError("batch_size deve ser positivo.")
        self.sink = sink
        self.batch_size = batch_size
        self._buffer: dict[str, list[Any]] = {}
        self._updates: dict[str, list[Any]] = {}
        self.total_updates_emitted = 0
        self.buffered_rows = 0
        self.max_buffered_rows = 0
        self.flush_count = 0
        self.total_rows_emitted = 0
        self._release_keys: list[tuple[str, str]] = []

    def release(self, table: str, key: str) -> None:
        """Tell the sink that a logical ID can no longer be referenced."""
        self._release_keys.append((table, key))

    def add(self, table: str, row: Any) -> None:
        self._buffer.setdefault(table, []).append(row)
        self.buffered_rows += 1
        self.max_buffered_rows = max(self.max_buffered_rows, self.buffered_rows)
        if self.buffered_rows >= self.batch_size:
            self.flush()

    def update(self, table: str, row: Any) -> None:
        self._updates.setdefault(table, []).append(row)
        self.buffered_rows += 1
        self.max_buffered_rows = max(self.max_buffered_rows, self.buffered_rows)
        if self.buffered_rows >= self.batch_size:
            self.flush()

    def flush(self) -> None:
        if not self.buffered_rows and not self._release_keys:
            return
        batch = TransactionBatch(
            {table: tuple(rows) for table, rows in self._buffer.items()},
            tuple(self._release_keys),
            {table: tuple(rows) for table, rows in self._updates.items()},
        )
        self._buffer.clear()
        self._updates.clear()
        self._release_keys.clear()
        self.buffered_rows = 0
        self.sink.consume(batch)
        self.flush_count += 1
        inserted = sum(len(rows) for rows in batch.rows_by_table.values())
        updated = sum(len(rows) for rows in (batch.updates_by_table or {}).values())
        self.total_rows_emitted += inserted
        self.total_updates_emitted += updated

    def close(self) -> None:
        self.flush()
