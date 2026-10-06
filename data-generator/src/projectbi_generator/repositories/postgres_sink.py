"""Incremental PostgreSQL writer for the transaction sink contract.

The connection and transaction belong to the caller.  This sink never commits,
rolls back, reconnects, or stores emitted transaction rows after a flush.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from decimal import Decimal
from itertools import islice
from typing import Any, Iterable

from psycopg import Connection

from projectbi_generator.models.entities import MasterData
from projectbi_generator.models.transactions import StockStateEvent
from projectbi_generator.sinks import TransactionBatch


class TransientTransactionIdRegistry:
    """Only IDs whose logical key may be referenced again remain registered."""

    def __init__(self) -> None:
        self._ids: dict[str, dict[str, int]] = defaultdict(dict)
        self.max_entries = 0
        self.max_by_type: dict[str, int] = defaultdict(int)

    @property
    def current_entries(self) -> int:
        return sum(map(len, self._ids.values()))

    def retain(self, entity: str, key: str, value: int) -> None:
        registry = self._ids[entity]
        if key in registry:
            raise ValueError(f"Chave lógica duplicada em {entity}.")
        registry[key] = value
        self.max_entries = max(self.max_entries, self.current_entries)
        self.max_by_type[entity] = max(self.max_by_type[entity], len(registry))

    def get(self, entity: str, key: str) -> int:
        try:
            return self._ids[entity][key]
        except KeyError as exc:
            raise KeyError(f"Referência lógica ausente em {entity}.") from exc

    def release(self, entity: str, key: str) -> None:
        try:
            del self._ids[entity][key]
        except KeyError as exc:
            raise KeyError(f"Tentativa de liberar referência inexistente em {entity}.") from exc


@dataclass
class PostgreSQLSinkMetrics:
    flush_count: int = 0
    rows_received_from_emitter: int = 0
    rows_inserted: int = 0
    rows_inserted_without_returning: int = 0
    rows_inserted_with_returning: int = 0
    rows_updated: int = 0
    max_batch_rows: int = 0
    round_trips_approx: int = 0


class PostgreSQLTransactionSink:
    """Persist logical batches in FK-safe order using a caller-owned connection."""

    def __init__(self, connection: Connection, master: MasterData,
                 master_ids: dict[str, dict[str, int]], batch_size: int = 1000) -> None:
        if batch_size <= 0:
            raise ValueError("batch_size deve ser positivo.")
        self.connection = connection
        self.master = master
        self.master_ids = master_ids
        self.batch_size = batch_size
        self.ids = TransientTransactionIdRegistry()
        self.metrics = PostgreSQLSinkMetrics()
        self._products = {row.sku: row for row in master.products}
        self._positions: dict[tuple[int, int], tuple[int, int, int, Decimal]] = {}
        self._timestamps: dict[str, dict[str, Any]] = defaultdict(dict)
        self._transfer_locations: dict[str, tuple[int, int]] = {}
        self._transfer_locations_by_key: dict[str, tuple[int, int]] = {}
        self._purchase_item_orders: dict[str, str] = {}
        self._pending_movements: dict[str, Any] = {}
        self._pending_state_events: list[Any] = []
        self._pending_movement_event_keys: set[str] = set()
        self._order_refs: dict[str, dict[str, list[str]]] = defaultdict(lambda: defaultdict(list))

    def _many(self, statement: str, values: Iterable[tuple], *, returning: bool = False) -> list[int]:
        """Use psycopg 3 executemany/pipeline and preserve each RETURNING association."""
        cursor = self.connection.cursor()
        returned: list[int] = []
        try:
            iterator = iter(values)
            while chunk := list(islice(iterator, self.batch_size)):
                cursor.executemany(statement, chunk, returning=returning)
                self.metrics.round_trips_approx += 1
                if returning:
                    # Psycopg exposes one result set per parameter set when RETURNING is enabled.
                    for _ in chunk:
                        row = cursor.fetchone()
                        if row is None:
                            raise RuntimeError("INSERT RETURNING não retornou o ID esperado.")
                        returned.append(row[0])
                        cursor.nextset()
            return returned
        finally:
            cursor.close()

    def _id(self, entity: str, key: str) -> int:
        return self.ids.get(entity, key)

    def _master(self, entity: str, key: str | None) -> int | None:
        if key is None:
            return None
        try:
            return self.master_ids[entity][key]
        except KeyError as exc:
            raise KeyError(f"ID mestre ausente em {entity}.") from exc

    def _insert_returning(self, table: str, rows: tuple[Any, ...], keys: list[str], statement: str,
                          params: list[tuple]) -> None:
        if not rows:
            return
        returned = self._many(statement, params, returning=True)
        if len(returned) != len(keys):
            raise RuntimeError(f"Contagem RETURNING inesperada em {table}.")
        for row, key, value in zip(rows, keys, returned):
            if table not in {"payment_installments", "stock_reservations", "refunds"}:
                self.ids.retain(table, key, value)
            order_key = getattr(row, "order_key", None)
            if order_key and table in {"sales_order_items", "fulfillments", "fulfillment_items", "payments", "returns", "return_items"}:
                self._order_refs[order_key][table].append(key)
        self.metrics.rows_inserted += len(rows)
        self.metrics.rows_inserted_with_returning += len(rows)

    def _insert_many(self, rows: Iterable[tuple], statement: str) -> int:
        values = list(rows)
        if values:
            self._many(statement, values)
            self.metrics.rows_inserted += len(values)
            self.metrics.rows_inserted_without_returning += len(values)
        return len(values)

    def consume(self, batch: TransactionBatch) -> None:
        """Persist one emitter batch. Any exception is left for the runner to roll back."""
        self.metrics.flush_count += 1
        self.metrics.rows_received_from_emitter += batch.row_count
        self.metrics.max_batch_rows = max(self.metrics.max_batch_rows, batch.row_count)
        r = batch.rows_by_table
        ids = self.master_ids

        # Parent rows with identity IDs, then their children. executemany(returning=True)
        # associates each result set with the corresponding input parameter set.
        rows = r.get("purchase_orders", ())
        updates = batch.updates_by_table or {}
        self._write_mutable_parent("purchase_orders", rows, updates.get("purchase_orders", ()))
        rows = r.get("purchase_order_items", ())
        self._insert_returning("purchase_order_items", rows, [x.key for x in rows],
            """INSERT INTO procurement.purchase_order_items
               (purchase_order_id,line_number,product_id,quantity_ordered,unit_cost_ordered,created_at)
               VALUES (%s,%s,%s,%s,%s,%s) RETURNING purchase_order_item_id""",
            [(self._id("purchase_orders", x.order_key), x.line_number, self._master("products", x.product_sku),
              x.quantity_ordered, x.unit_cost_ordered, self._timestamps["purchase_orders"][x.order_key]) for x in rows])
        self._purchase_item_orders.update((x.key, x.order_key) for x in rows)
        for x in rows:
            self._timestamps["purchase_orders"].pop(x.order_key, None)

        # Remaining writers are table-batched where IDs are not required and identity-aware otherwise.
        self._write_receipts(r)
        self._write_sales(r, updates)
        self._write_payments(r)
        self._write_logistics(r)
        self._write_after_sales(r, updates)
        self._write_stock(r)
        for entity, key in batch.release_keys:
            self._release_id(entity, key)

    def _write_mutable_parent(self, table: str, rows: tuple[Any, ...], explicit_updates: tuple[Any, ...] = ()) -> None:
        if not rows and not explicit_updates:
            return
        seen: set[str] = set()
        initial = []
        updates = []
        for row in rows:
            if row.key in self.ids._ids.get(table, {}) or row.key in seen:
                updates.append(row)
            else:
                seen.add(row.key)
                initial.append(row)
        updates.extend(explicit_updates)
        if table == "purchase_orders":
            self._insert_returning(table, initial, [x.key for x in initial],
            """INSERT INTO procurement.purchase_orders
               (purchase_order_number,supplier_id,responsible_employee_id,status,ordered_at,expected_on,currency_code,created_at,updated_at)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s) RETURNING purchase_order_id""",
            [(x.number, self._master("suppliers", x.supplier_code), self._master("employees", x.responsible_employee_code),
              x.status, x.ordered_at, x.expected_on, x.currency_code, x.ordered_at, x.ordered_at) for x in initial])
            self._timestamps["purchase_orders"].update((x.key, x.ordered_at) for x in initial)
            if updates:
                self._many("UPDATE procurement.purchase_orders SET status=%s,updated_at=%s WHERE purchase_order_id=%s",
                           [(x.status,x.ordered_at,self._id(table,x.key)) for x in updates])
                self.metrics.rows_updated += len(updates)
        else:
            self._insert_returning(table, initial, [x.key for x in initial],
            """INSERT INTO sales.sales_orders
               (order_number,sales_channel_id,channel_type,customer_id,store_id,salesperson_employee_id,customer_address_id,order_status,placed_at,currency_code,subtotal_amount,discount_amount,shipping_amount,total_amount,recipient_name,postal_code_snapshot,street_snapshot,street_number_snapshot,complement_snapshot,district_snapshot,city_snapshot,state_code_snapshot,country_code_snapshot,created_at,updated_at)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,'BRL',%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) RETURNING sales_order_id""",
            [(x.number,self._master("sales_channels",x.channel_code),x.channel_type,self._master("customers",x.customer_code),
              self._master("stores",x.store_code),self._master("employees",x.salesperson_code),self._master("customer_addresses",x.address_key),
              x.status,x.placed_at,x.subtotal,x.discount,x.shipping,x.total,*(x.address_snapshot or (None,)*9),x.placed_at,x.placed_at) for x in initial])
            self._timestamps["sales_orders"].update((x.key,x.placed_at) for x in initial)
            if updates:
                self._many("UPDATE sales.sales_orders SET order_status=%s,updated_at=%s WHERE sales_order_id=%s",
                           [(x.status,x.placed_at,self._id(table,x.key)) for x in updates])
                self.metrics.rows_updated += len(updates)

    def _split_mutations(self, table: str, rows: tuple[Any, ...], explicit_updates: tuple[Any, ...] = ()) -> tuple[list[Any], list[Any]]:
        seen: set[str] = set()
        initial: list[Any] = []
        updates: list[Any] = []
        for row in rows:
            if row.key in self.ids._ids.get(table, {}) or row.key in seen:
                updates.append(row)
            else:
                seen.add(row.key)
                initial.append(row)
        updates.extend(explicit_updates)
        return initial, updates

    def _release_id(self, entity: str, key: str) -> None:
        if entity in {"purchase_orders", "sales_orders", "fulfillments", "payments", "returns", "goods_receipts", "stock_transfers"}:
            self._timestamps[entity].pop(key, None)
        if entity == "stock_transfer_items":
            self._transfer_locations.pop(key, None)
        if entity == "sales_orders":
            refs = self._order_refs.pop(key, {})
            for child_entity, child_keys in refs.items():
                for child_key in child_keys:
                    if child_key in self.ids._ids.get(child_entity, {}):
                        self.ids.release(child_entity, child_key)
            if key in self.ids._ids.get(entity, {}):
                self.ids.release(entity, key)
            return
        if entity == "purchase_order_items":
            self._purchase_item_orders.pop(key, None)
        if key in self.ids._ids.get(entity, {}):
            self.ids.release(entity, key)

    def _write_receipts(self, r: dict[str, tuple[Any, ...]]) -> None:
        rows = r.get("goods_receipts", ())
        self._insert_returning("goods_receipts", rows, [x.key for x in rows],
            """INSERT INTO procurement.goods_receipts
               (purchase_order_id,stock_location_id,checked_by_employee_id,receipt_number,status,received_at,created_at)
               VALUES (%s,%s,%s,%s,%s,%s,%s) RETURNING goods_receipt_id""",
            [(self._id("purchase_orders", x.order_key), self._master("stock_locations", x.location_code),
              self._master("employees", x.checked_by_employee_code), x.number, x.status, x.received_at, x.received_at) for x in rows])
        self._timestamps["goods_receipts"].update((x.key, x.received_at) for x in rows)
        rows = r.get("goods_receipt_items", ())
        po_items = {x.key: x for x in r.get("purchase_order_items", ())}
        # A receipt may be in a later flush; the parent PO ID remains live until the stream releases it.
        self._insert_returning("goods_receipt_items", rows, [x.key for x in rows],
            """INSERT INTO procurement.goods_receipt_items
               (purchase_order_id,goods_receipt_id,purchase_order_item_id,quantity_received,accepted_quantity,rejected_quantity,unit_acquisition_cost,created_at)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s) RETURNING goods_receipt_item_id""",
            [(self._id("purchase_orders", self._receipt_order_key(x)), self._id("goods_receipts", x.receipt_key),
              self._id("purchase_order_items", x.order_item_key), x.quantity_received, x.accepted_quantity,
              x.rejected_quantity, x.unit_acquisition_cost, self._timestamps["goods_receipts"][x.receipt_key]) for x in rows])
        for x in rows:
            self._release_id("goods_receipts", x.receipt_key)
            self._timestamps["goods_receipts"].pop(x.receipt_key, None)

    def _receipt_order_key(self, row: Any) -> str:
        return self._purchase_item_orders[row.order_item_key]

    def _write_sales(self, r: dict[str, tuple[Any, ...]], updates: dict[str, tuple[Any, ...]]) -> None:
        rows = r.get("sales_orders", ())
        self._write_mutable_parent("sales_orders", rows, updates.get("sales_orders", ()))
        rows = r.get("sales_order_items", ())
        self._insert_returning("sales_order_items", rows, [x.key for x in rows],
            """INSERT INTO sales.sales_order_items
               (sales_order_id,line_number,product_id,sku_snapshot,product_name_snapshot,quantity,unit_sale_price,created_at)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s) RETURNING sales_order_item_id""",
            [(self._id("sales_orders",x.order_key),x.line_number,self._master("products",x.product_sku),x.product_sku,
              self._products[x.product_sku].name,x.quantity,x.unit_sale_price,self._timestamps["sales_orders"][x.order_key]) for x in rows])
        rows = r.get("order_status_history", ())
        self._insert_many([(self._id("sales_orders",x.order_key),x.status,x.occurred_at,self._master("employees",x.changed_by_employee_code),x.reason,x.occurred_at) for x in rows],
            "INSERT INTO sales.order_status_history (sales_order_id,status,occurred_at,changed_by_employee_id,reason,created_at) VALUES (%s,%s,%s,%s,%s,%s)")
        rows = r.get("applied_discounts", ())
        self._insert_many([(self._id("sales_orders",x.order_key),self._id("sales_order_items",x.item_key),x.scope,x.code,None,x.description,x.amount,x.created_at) for x in rows],
            "INSERT INTO sales.applied_discounts (sales_order_id,sales_order_item_id,discount_scope,discount_code,campaign_reference,description,amount,created_at) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)")
        rows = r.get("stock_reservations", ())
        self._insert_returning("stock_reservations", rows,[x.key for x in rows],
            """INSERT INTO inventory.stock_reservations (sales_order_id,sales_order_item_id,product_id,stock_location_id,quantity,status,reserved_at,expires_at,released_at,created_at)
               VALUES (%s,%s,%s,%s,%s,%s,%s,NULL,%s,%s) RETURNING stock_reservation_id""",
            [(self._id("sales_orders",x.order_key),self._id("sales_order_items",x.item_key),self._master("products",x.product_sku),
              self._master("stock_locations",x.location_code),x.quantity,x.status,x.reserved_at,x.released_at,x.reserved_at) for x in rows])

    def _write_payments(self, r: dict[str, tuple[Any, ...]]) -> None:
        rows = r.get("payments", ())
        self._insert_returning("payments", rows,[x.key for x in rows],
            """INSERT INTO payments.payments (sales_order_id,payment_method_id,payment_reference,status,amount,currency_code,attempted_at,authorized_at,settled_at,external_reference,created_at,updated_at)
               VALUES (%s,%s,%s,%s,%s,'BRL',%s,%s,%s,%s,%s,%s) RETURNING payment_id""",
            [(self._id("sales_orders",x.order_key),self._master("payment_methods",x.method_code),x.reference,x.status,x.amount,
              x.attempted_at,x.authorized_at,x.settled_at,x.reference,x.attempted_at,x.settled_at or x.attempted_at) for x in rows])
        self._timestamps["payments"].update((x.key, x.settled_at or x.attempted_at) for x in rows)
        rows = r.get("payment_installments", ())
        self._insert_returning("payment_installments", rows,[x.key for x in rows],
            """INSERT INTO payments.payment_installments (payment_id,installment_number,due_on,amount,status,paid_at,external_reference,created_at,updated_at)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s) RETURNING payment_installment_id""",
            [(self._id("payments",x.payment_key),x.number,x.due_on,x.amount,x.status,x.paid_at,x.key,self._timestamps["payments"][x.payment_key],x.paid_at or self._timestamps["payments"][x.payment_key]) for x in rows])
        for key in {x.payment_key for x in rows}:
            self._timestamps["payments"].pop(key, None)

    def _write_logistics(self, r: dict[str, tuple[Any, ...]]) -> None:
        rows = r.get("fulfillments", ())
        self._insert_returning("fulfillments", rows,[x.key for x in rows],
            """INSERT INTO logistics.fulfillments (sales_order_id,fulfillment_number,fulfillment_type,status,stock_location_id,pickup_store_id,carrier_id,planned_at,dispatched_at,completed_at,created_at,updated_at)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) RETURNING fulfillment_id""",
            [(self._id("sales_orders",x.order_key),x.number,x.fulfillment_type,x.status,self._master("stock_locations",x.location_code),
              self._master("stores",x.pickup_store_code),self._master("carriers",x.carrier_code),x.planned_at,x.dispatched_at,x.completed_at,x.planned_at,x.completed_at or x.planned_at) for x in rows])
        self._timestamps["fulfillments"].update((x.key, x.planned_at) for x in rows)
        rows = r.get("fulfillment_items", ())
        self._insert_returning("fulfillment_items", rows,[x.key for x in rows],
            """INSERT INTO logistics.fulfillment_items (sales_order_id,fulfillment_id,sales_order_item_id,quantity_allocated,fulfilled_quantity,created_at,updated_at)
               VALUES (%s,%s,%s,%s,%s,%s,%s) RETURNING fulfillment_item_id""",
            [(self._id("sales_orders",x.order_key),self._id("fulfillments",x.fulfillment_key),self._id("sales_order_items",x.sale_item_key),
              x.quantity_allocated,x.fulfilled_quantity,self._timestamps["fulfillments"][x.fulfillment_key],self._timestamps["fulfillments"][x.fulfillment_key]) for x in rows])
        for key in {x.fulfillment_key for x in rows}:
            self._timestamps["fulfillments"].pop(key, None)
        rows = r.get("fulfillment_events", ())
        self._insert_many([(self._id("fulfillments",x.fulfillment_key),x.event_type,x.occurred_at,self._master("employees",x.recorded_by_employee_code),x.description,x.occurred_at) for x in rows],
            "INSERT INTO logistics.fulfillment_events (fulfillment_id,event_type,occurred_at,recorded_by_employee_id,description,created_at) VALUES (%s,%s,%s,%s,%s,%s)")

    def _write_after_sales(self, r: dict[str, tuple[Any, ...]], updates: dict[str, tuple[Any, ...]]) -> None:
        rows = r.get("stock_transfers", ())
        self._insert_returning("stock_transfers", rows,[x.key for x in rows],
            """INSERT INTO inventory.stock_transfers (transfer_number,source_stock_location_id,destination_stock_location_id,requested_by_employee_id,received_by_employee_id,status,requested_at,dispatched_at,received_at,created_at,updated_at,notes)
               VALUES (%s,%s,%s,NULL,NULL,%s,%s,%s,%s,%s,%s,%s) RETURNING stock_transfer_id""",
            [(x.number,self._master("stock_locations",x.source_location_code),self._master("stock_locations",x.destination_location_code),x.status,x.requested_at,x.dispatched_at,x.received_at,x.requested_at,x.received_at,"Rebalanceamento motivado por estoque baixo e excedente disponível.") for x in rows])
        self._timestamps["stock_transfers"].update((x.key, x.requested_at) for x in rows)
        self._transfer_locations_by_key.update((x.key, (self._master("stock_locations",x.source_location_code),self._master("stock_locations",x.destination_location_code))) for x in rows)
        rows = r.get("stock_transfer_items", ())
        self._insert_returning("stock_transfer_items", rows,[x.key for x in rows],
            "INSERT INTO inventory.stock_transfer_items (stock_transfer_id,product_id,line_number,quantity_planned,quantity_dispatched,quantity_received,created_at) VALUES (%s,%s,%s,%s,%s,%s,%s) RETURNING stock_transfer_item_id",
            [(self._id("stock_transfers",x.transfer_key),self._master("products",x.product_sku),x.line_number,x.quantity_planned,x.quantity_dispatched,x.quantity_received,self._timestamps["stock_transfers"][x.transfer_key]) for x in rows])
        for x in rows:
            self._transfer_locations[x.key] = self._transfer_locations_by_key.pop(x.transfer_key)
            self._release_id("stock_transfers", x.transfer_key)
            self._timestamps["stock_transfers"].pop(x.transfer_key, None)
        rows = r.get("returns", ())
        initial, return_updates = self._split_mutations("returns", rows, updates.get("returns", ()))
        self._insert_returning("returns", initial,[x.key for x in initial],
            """INSERT INTO after_sales.returns (sales_order_id,return_number,status,reason_code,requested_by_employee_id,approved_by_employee_id,requested_at,decided_at,created_at,updated_at,notes)
               VALUES (%s,%s,%s,%s,NULL,NULL,%s,%s,%s,%s,NULL) RETURNING return_id""",
            [(self._id("sales_orders",x.order_key),x.number,x.status,x.reason_code,x.requested_at,x.decided_at,x.requested_at,x.decided_at or x.requested_at) for x in initial])
        self._timestamps["returns"].update((x.key, x.requested_at) for x in initial)
        if return_updates:
            self._many("UPDATE after_sales.returns SET status=%s,decided_at=%s,updated_at=%s WHERE return_id=%s",
                       [(x.status,x.decided_at,x.decided_at or x.requested_at,self._id("returns",x.key)) for x in return_updates])
            self.metrics.rows_updated += len(return_updates)
        rows = r.get("return_items", ())
        initial, item_updates = self._split_mutations("return_items", rows, updates.get("return_items", ()))
        self._insert_returning("return_items", initial,[x.key for x in initial],
            """INSERT INTO after_sales.return_items (sales_order_id,return_id,sales_order_item_id,source_fulfillment_item_id,quantity_requested,quantity_approved,quantity_received,item_condition,stock_destination,received_at,created_at,notes)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,NULL) RETURNING return_item_id""",
            [(self._id("sales_orders",x.order_key),self._id("returns",x.return_key),self._id("sales_order_items",x.sale_item_key),self._id("fulfillment_items",x.source_fulfillment_item_key),
              x.quantity_requested,x.quantity_approved,x.quantity_received,x.item_condition,x.stock_destination,x.received_at,self._timestamps["returns"][x.return_key]) for x in initial])
        if item_updates:
            self._many("UPDATE after_sales.return_items SET quantity_approved=%s,quantity_received=%s,item_condition=%s,stock_destination=%s,received_at=%s WHERE return_item_id=%s",
                       [(x.quantity_approved,x.quantity_received,x.item_condition,x.stock_destination,x.received_at,self._id("return_items",x.key)) for x in item_updates])
            self.metrics.rows_updated += len(item_updates)
        for x in initial:
            self._timestamps["returns"].pop(x.return_key, None)
        rows = r.get("refunds", ())
        self._insert_returning("refunds", rows,[x.key for x in rows],
            """INSERT INTO payments.refunds (sales_order_id,payment_id,return_id,status,amount,reason_code,requested_at,processed_at,external_reference,created_at,updated_at)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) RETURNING refund_id""",
            [(self._id("sales_orders",x.order_key),self._id("payments",x.payment_key),self._id("returns",x.return_key) if x.return_key else None,x.status,x.amount,x.reason_code,x.requested_at,x.processed_at,x.key,x.requested_at,x.processed_at or x.requested_at) for x in rows])

    def _position(self, product_id: int, location_id: int, at: Any) -> tuple[int, int, int, Decimal]:
        key = (product_id, location_id)
        if key in self._positions:
            return self._positions[key]
        inserted = self.connection.execute("""INSERT INTO inventory.stock_positions (product_id,stock_location_id,on_hand_quantity,reserved_quantity,average_unit_cost,updated_at)
            VALUES (%s,%s,0,0,0,%s) ON CONFLICT (product_id,stock_location_id) DO NOTHING RETURNING stock_position_id""", (product_id,location_id,at)).fetchone()
        self.metrics.round_trips_approx += 1
        if inserted is not None:
            self.metrics.rows_inserted += 1
            self.metrics.rows_inserted_with_returning += 1
        row = self.connection.execute("SELECT stock_position_id,on_hand_quantity,reserved_quantity,average_unit_cost FROM inventory.stock_positions WHERE product_id=%s AND stock_location_id=%s FOR UPDATE",(product_id,location_id)).fetchone()
        if row is None:
            raise RuntimeError("Posição de estoque não encontrada após lock.")
        self._positions[key] = (row[0],row[1],row[2],row[3])
        return row

    def _write_stock(self, r: dict[str, tuple[Any, ...]]) -> None:
        # Inventory state is applied in causal event order; the ledger row is inserted at its event.
        movement_by_key = self._pending_movements
        movement_by_key.update((x.key, x) for x in r.get("stock_movements", ()))
        events = self._pending_state_events + list(r.get("stock_state_events", ()))
        self._pending_state_events = []
        for index, event in enumerate(events):
            product = self._master("products",event.product_sku)
            location = self._master("stock_locations",event.location_code)
            movement = movement_by_key.get(event.movement_key) if event.movement_key else None
            if movement is not None and event.event_type in {"transfer_out", "transfer_in"}:
                source_id, destination_id = self._transfer_locations[movement.transfer_item_key]
                for transfer_location_id in sorted((source_id, destination_id)):
                    self._position(product, transfer_location_id, event.occurred_at)
            position_id,on_hand,reserved,average = self._position(product,location,event.occurred_at)
            if event.movement_key and movement is None:
                self._pending_state_events.extend(events[index:])
                break
            if event.event_type == "receipt":
                self.connection.execute("INSERT INTO inventory.stock_movements (product_id,stock_location_id,movement_type,quantity_delta,unit_cost,goods_receipt_item_id,occurred_at,created_at) VALUES (%s,%s,'receipt',%s,%s,%s,%s,%s)",(product,location,event.quantity,event.unit_cost,self._id("goods_receipt_items",movement.receipt_item_key),event.occurred_at,event.occurred_at))
                self.metrics.rows_inserted += 1
                self.metrics.rows_inserted_without_returning += 1
                self.metrics.round_trips_approx += 1
                average = ((Decimal(on_hand)*average + Decimal(event.quantity)*event.unit_cost)/Decimal(on_hand+event.quantity)).quantize(Decimal("0.00000001")) if on_hand else event.unit_cost.quantize(Decimal("0.00000001")); on_hand += event.quantity
            elif event.event_type in {"fulfillment","transfer_out","transfer_in","customer_return"}:
                common=(product,location,movement.movement_type,movement.quantity_delta,movement.unit_cost)
                refs=(self._id("fulfillment_items",movement.fulfillment_item_key) if movement.fulfillment_item_key else None,
                      self._id("return_items",movement.return_item_key) if movement.return_item_key else None,
                      self._id("stock_transfer_items",movement.transfer_item_key) if movement.transfer_item_key else None)
                self.connection.execute("INSERT INTO inventory.stock_movements (product_id,stock_location_id,movement_type,quantity_delta,unit_cost,fulfillment_item_id,return_item_id,stock_transfer_item_id,occurred_at,created_at) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",(*common,*refs,event.occurred_at,event.occurred_at))
                self.metrics.rows_inserted += 1
                self.metrics.rows_inserted_without_returning += 1
                self.metrics.round_trips_approx += 1
                if event.event_type == "fulfillment":
                    on_hand -= event.quantity; reserved -= event.quantity
                elif event.event_type == "transfer_out": on_hand -= event.quantity
                else:
                    average = ((Decimal(on_hand)*average + Decimal(event.quantity)*event.unit_cost)/Decimal(on_hand+event.quantity)).quantize(Decimal("0.00000001")) if on_hand else event.unit_cost.quantize(Decimal("0.00000001")); on_hand += event.quantity
            elif event.event_type == "reserve": reserved += event.quantity
            elif event.event_type == "release": reserved -= event.quantity
            if event.movement_key:
                movement_by_key.pop(event.movement_key, None)
                if event.event_type == "receipt" and movement is not None:
                    self._release_id("goods_receipt_items", movement.receipt_item_key)
            if position_id:
                self.connection.execute("UPDATE inventory.stock_positions SET on_hand_quantity=%s,reserved_quantity=%s,average_unit_cost=%s,updated_at=%s WHERE stock_position_id=%s",(on_hand,reserved,average,event.occurred_at,position_id))
                self.metrics.rows_updated += 1
                self.metrics.round_trips_approx += 1
                self._positions[(product,location)] = (position_id,on_hand,reserved,average)
        self._pending_movements = movement_by_key
        # Final positions carry the authoritative engine state. Upsert preserves the computed ledger.
        for row in r.get("stock_positions", ()):
            product=self._master("products",row.product_sku); location=self._master("stock_locations",row.location_code)
            self.connection.execute("""INSERT INTO inventory.stock_positions (product_id,stock_location_id,on_hand_quantity,reserved_quantity,average_unit_cost,updated_at)
                VALUES (%s,%s,%s,%s,%s,now()) ON CONFLICT(product_id,stock_location_id) DO UPDATE SET on_hand_quantity=EXCLUDED.on_hand_quantity,reserved_quantity=EXCLUDED.reserved_quantity,average_unit_cost=EXCLUDED.average_unit_cost,updated_at=EXCLUDED.updated_at""",(product,location,row.on_hand_quantity,row.reserved_quantity,row.average_unit_cost))
            self.metrics.rows_updated += 1
            self.metrics.round_trips_approx += 1
            existing=self._positions.get((product,location))
            if existing: self._positions[(product,location)]=(existing[0],row.on_hand_quantity,row.reserved_quantity,row.average_unit_cost)
            else:
                got=self.connection.execute("SELECT stock_position_id FROM inventory.stock_positions WHERE product_id=%s AND stock_location_id=%s",(product,location)).fetchone()
                self._positions[(product,location)]=(got[0],row.on_hand_quantity,row.reserved_quantity,row.average_unit_cost)
