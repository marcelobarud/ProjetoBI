"""Run the accepted-order Portfolio planner in memory with a discarding sink."""

from __future__ import annotations

import argparse
import json
import tracemalloc
from collections import Counter, defaultdict
from dataclasses import replace
from decimal import Decimal, ROUND_HALF_UP
from time import perf_counter

from projectbi_generator.config import load_config
from projectbi_generator.generators.completion import generate_full_transactions_incremental
from projectbi_generator.generators.master import generate_master_data
from projectbi_generator.sales_plan import build_sales_intent_quotas
from projectbi_generator.validation.portfolio import classify_portfolio_distributions


class DiscardingSink:
    def __init__(self, master) -> None:
        self.max_batch_rows = 0
        self.rows_received = 0
        self.customer_types = {row.code: row.customer_type for row in master.customers}
        self.payment_types = {row.code: row.method_type for row in master.payment_methods}
        self.channel_types = {row.code: row.channel_type for row in master.sales_channels}
        self.product_categories = {row.sku: row.category_code for row in master.products}
        self.orders = {}
        self.order_shipping = {}
        self.items = {}
        self.purchase_items = {}
        self.received_by_sku = defaultdict(lambda: [0, Decimal("0.00")])
        self.receipts = defaultdict(lambda: [0, Decimal("0.00")])
        self.discounts = defaultdict(lambda: Decimal("0.00"))
        self.fulfillment_items = {}
        self.fulfillment_cost = defaultdict(Decimal)
        self.return_items = {}
        self.return_movement_cost = defaultdict(Decimal)
        self.return_movement_quantity = defaultdict(int)
        self.payments = {}
        self.installments = defaultdict(list)
        self.refunds = defaultdict(Decimal)
        self.cancellations = defaultdict(lambda: {"quantity": 0, "gross": Decimal("0.00"),
                                                  "discount": Decimal("0.00"), "net": Decimal("0.00"),
                                                  "shipping": Decimal("0.00")})
        self.fulfillment_events = defaultdict(list)
        self.fulfillments = {}
        self.transfers = {}
        self.transfer_items = {}
        self.transfer_movements = defaultdict(list)
        self.return_metadata = {}
        self.return_headers = {}
        self.cancellation_rows = {}
        self.refund_rows = []
        self.payment_counts = Counter()
        self.payment_status_counts = defaultdict(Counter)
        self.orders_with_return = set()

    def consume(self, batch) -> None:
        self.max_batch_rows = max(self.max_batch_rows, batch.row_count)
        self.rows_received += sum(len(rows) for rows in batch.rows_by_table.values())
        for order in batch.rows_by_table.get("sales_orders", ()):
            self._save_order(order)
        for order in (batch.updates_by_table or {}).get("sales_orders", ()):
            self._save_order(order)
        for item in batch.rows_by_table.get("sales_order_items", ()):
            self.items[item.key] = (item.order_key, item.quantity, item.unit_sale_price, item.product_sku)
        for item in batch.rows_by_table.get("purchase_order_items", ()):
            self.purchase_items[item.key] = item.product_sku
        for row in batch.rows_by_table.get("applied_discounts", ()):
            self.discounts[row.item_key] += row.amount
        for row in batch.rows_by_table.get("payments", ()):
            self.payments[row.key] = (row.order_key, row.amount, row.status)
            self.payment_status_counts[self.payment_types[row.method_code]][row.status] += 1
            if row.status in {"captured", "settled"}:
                self.payment_counts[self.payment_types[row.method_code]] += 1
        for row in batch.rows_by_table.get("fulfillment_items", ()):
            self.fulfillment_items[row.key] = (row.order_key, row.sale_item_key, row.fulfilled_quantity,
                                               row.quantity_allocated)
        for row in batch.rows_by_table.get("sales_order_item_cancellations", ()):
            values = self.cancellations[row.item_key]
            values["quantity"] += row.cancelled_quantity
            values["gross"] += row.gross_cancelled_amount
            values["discount"] += row.discount_cancelled_amount
            values["net"] += row.net_cancelled_amount
            values["shipping"] += row.shipping_cancelled_amount
            self.cancellation_rows[row.key] = row
        for row in batch.rows_by_table.get("payment_installments", ()):
            self.installments[row.payment_key].append((row.number, row.amount))
        for row in batch.rows_by_table.get("refunds", ()):
            self.refund_rows.append(row)
            if row.status == "completed":
                self.refunds[row.payment_key] += row.amount
        for row in batch.rows_by_table.get("fulfillments", ()):
            self.fulfillments[row.key] = (row.order_key, row.status, row.fulfillment_type)
        for row in batch.rows_by_table.get("fulfillment_events", ()):
            self.fulfillment_events[row.fulfillment_key].append((row.event_type, row.occurred_at))
        for row in batch.rows_by_table.get("stock_transfers", ()):
            self.transfers[row.key] = row
        for row in batch.rows_by_table.get("stock_transfer_items", ()):
            self.transfer_items[row.key] = row
        for row in batch.rows_by_table.get("return_items", ()):
            self.orders_with_return.add(row.order_key)
            self.return_items[row.key] = (row.source_fulfillment_item_key, row.stock_destination, row.quantity_received, row.order_key)
            self.return_metadata[row.key] = (row.return_key, row.sale_item_key, row.quantity_requested,
                                             row.quantity_approved, row.received_at)
        for row in batch.rows_by_table.get("returns", ()):
            self.return_headers[row.key] = (row.order_key, row.status, row.reason_code, row.requested_at, row.decided_at)
        for row in (batch.updates_by_table or {}).get("return_items", ()):
            self.return_items[row.key] = (row.source_fulfillment_item_key, row.stock_destination, row.quantity_received, row.order_key)
            self.return_metadata[row.key] = (row.return_key, row.sale_item_key, row.quantity_requested,
                                             row.quantity_approved, row.received_at)
        for row in (batch.updates_by_table or {}).get("returns", ()):
            self.return_headers[row.key] = (row.order_key, row.status, row.reason_code, row.requested_at, row.decided_at)
        for row in batch.rows_by_table.get("stock_movements", ()):
            if row.movement_type == "fulfillment" and row.fulfillment_item_key:
                self.fulfillment_cost[row.fulfillment_item_key] += abs(row.quantity_delta) * row.unit_cost
            elif row.movement_type == "customer_return" and row.return_item_key:
                self.return_movement_cost[row.return_item_key] += abs(row.quantity_delta) * row.unit_cost
                self.return_movement_quantity[row.return_item_key] += row.quantity_delta
            elif row.movement_type in {"transfer_out", "transfer_in"} and row.transfer_item_key:
                self.transfer_movements[row.transfer_item_key].append(row)
        for row in batch.rows_by_table.get("goods_receipt_items", ()):
            self.receipts[row.order_item_key][0] += row.accepted_quantity
            self.receipts[row.order_item_key][1] += Decimal(row.accepted_quantity) * row.unit_acquisition_cost
            sku = self.purchase_items.get(row.order_item_key)
            if sku:
                self.received_by_sku[sku][0] += row.accepted_quantity
                self.received_by_sku[sku][1] += Decimal(row.accepted_quantity) * row.unit_acquisition_cost

    def _save_order(self, order) -> None:
        self.orders[order.key] = (order.status, order.customer_code, order.channel_type,
                                  order.store_code, order.placed_at, order.subtotal, order.discount, order.total,
                                  order.channel_code)
        self.order_shipping[order.key] = order.shipping

    def distribution_metrics(self) -> dict:
        """Build the exact metric contract consumed by the Portfolio distribution gate."""
        orders_by_channel = Counter(row[8] for row in self.orders.values())
        orders_by_type = Counter(row[2] for row in self.orders.values())
        orders_by_year = Counter(row[4].year for row in self.orders.values())
        orders_by_year_type = defaultdict(Counter)
        monthly = defaultdict(lambda: {"orders": 0, "discounted": 0, "discount_rate": Decimal(0)})
        store_orders = Counter()
        anonymous_physical = 0
        digital_anonymous = 0
        customer_orders = Counter(row[1] for row in self.orders.values()
                                  if row[0] != "cancelled" and row[1] is not None)
        ticket_counts = Counter()
        ticket_totals = defaultdict(Decimal)
        for status, customer, channel, store, placed, subtotal, discount, total, _channel_code in self.orders.values():
            orders_by_year_type[placed.year][channel] += 1
            month = placed.strftime("%Y-%m")
            monthly[month]["orders"] += 1
            if discount > 0:
                monthly[month]["discounted"] += 1
                if subtotal:
                    monthly[month]["discount_rate"] += discount / subtotal
            if channel == "physical":
                store_orders[store or "unassigned"] += 1
                anonymous_physical += int(customer is None)
            else:
                digital_anonymous += int(customer is None)
            if status == "completed" and customer is not None:
                kind = self.customer_types[customer]
                ticket_counts[kind] += 1
                ticket_totals[kind] += total

        recurrence = {}
        for kind, counts in self._recurrence_by_type().items():
            customer_count = counts["customers"]
            recurrence[kind] = (
                counts["one"], counts["two_to_four"], counts["five_to_ten"], counts["eleven_plus"],
                (Decimal(counts["orders"]) / customer_count).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)
                if customer_count else Decimal(0), customer_count,
            )
        recurrence_overall = tuple(
            sum(values[index] for values in recurrence.values())
            for index in (0, 1, 2, 3, 5)
        )
        ticket_by_customer_type = {
            kind: (count, (ticket_totals[kind] / count).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP), ticket_totals[kind])
            for kind, count in ticket_counts.items()
        }
        discounts_count = sum(row[6] > 0 for row in self.orders.values())
        discounts_amount = sum((row[6] for row in self.orders.values()), Decimal(0))
        gross = sum((row[5] for row in self.orders.values()), Decimal(0))
        discounted_rates = [row[6] / row[5] for row in self.orders.values() if row[6] > 0 and row[5]]
        monthly_distribution = [
            (month, values["orders"], values["discounted"],
             (values["discount_rate"] / values["discounted"]).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)
             if values["discounted"] else None)
            for month, values in sorted(monthly.items())
        ]
        monthly_category_units = defaultdict(int)
        for order_key, quantity, _unit_price, sku in self.items.values():
            order = self.orders.get(order_key)
            if order:
                month = order[4].strftime("%Y-%m")
                category = self.product_categories[sku]
                monthly_category_units[(month, category)] += quantity
        return_order_keys = {
            order_key for _source_key, _destination, _quantity, order_key in self.return_items.values()
            if order_key is not None and self.orders.get(order_key, (None,))[0] == "completed"
        }
        completed_orders = sum(row[0] == "completed" for row in self.orders.values())
        return_items = list(self.return_items.values())
        sellable_items = [row for row in return_items if row[1] == "sellable"]
        non_sellable_items = [row for row in return_items if row[1] in {"quarantine", "repair", "discard"}]
        completed_units_by_sku = Counter()
        for order_key, quantity, _unit_price, sku in self.items.values():
            if self.orders.get(order_key, (None,))[0] == "completed":
                completed_units_by_sku[sku] += quantity
        payment_methods = {
            method: (
                sum(counts[status] for status in ("captured", "settled")),
                sum(counts[status] for status in ("declined", "failed")),
                sum(counts.values()),
            )
            for method, counts in self.payment_status_counts.items()
        }
        summary = {
            "customer_types": dict(Counter(self.customer_types.values())),
            "anonymous_physical": (anonymous_physical, orders_by_type.get("physical", 0)),
            "digital_anonymous": digital_anonymous,
            "orders_by_channel": dict(orders_by_channel),
            "orders_by_type": dict(orders_by_type),
            "orders_by_year": dict(orders_by_year),
            "orders_by_year_type": {year: dict(values) for year, values in orders_by_year_type.items()},
            "recurrence": recurrence,
            "recurrence_overall": recurrence_overall,
            "ticket_by_customer_type": ticket_by_customer_type,
            "orders_by_status": dict(Counter(row[0] for row in self.orders.values())),
            "discounts": (discounts_count, len(self.orders), discounts_amount, gross,
                          sum(discounted_rates, Decimal(0)) / len(discounted_rates) if discounted_rates else None),
            "payment_methods": payment_methods,
            "returns": (
                len(return_order_keys),
                sum(self.orders[key][2] != "physical" for key in return_order_keys),
                sum(self.orders[key][2] == "physical" for key in return_order_keys),
                sum(self.customer_types.get(self.orders[key][1]) == "business" for key in return_order_keys),
                len(return_items), len(sellable_items), len(non_sellable_items),
                sum(row[2] for row in sellable_items),
            ),
            "returns_completed_orders": completed_orders,
            "margin": (Decimal(self.summary_cache["completed_realized_revenue"]),
                       Decimal(self.summary_cache["completed_margin_cogs"])),
            "product_concentration": (
                max(completed_units_by_sku.values(), default=0), sum(completed_units_by_sku.values()),
                len(completed_units_by_sku),
            ),
            "monthly_distribution": monthly_distribution,
            "monthly_category_units": [(month, category, units) for (month, category), units in sorted(monthly_category_units.items())],
            "store_orders": sorted(store_orders.items()),
        }
        return summary

    def _recurrence_by_type(self) -> dict[str, Counter]:
        result = defaultdict(Counter)
        customer_orders = Counter(row[1] for row in self.orders.values()
                                  if row[0] != "cancelled" and row[1] is not None)
        for customer, frequency in customer_orders.items():
            kind = self.customer_types[customer]
            bucket = "one" if frequency == 1 else "two_to_four" if frequency <= 4 else "five_to_ten" if frequency <= 10 else "eleven_plus"
            result[kind][bucket] += 1
            result[kind]["orders"] += frequency
            result[kind]["customers"] += 1
        return result

    def summary(self) -> dict:
        statuses = Counter(row[0] for row in self.orders.values())
        monthly = Counter(row[4].strftime("%Y-%m") for row in self.orders.values())
        discounted = Counter()
        for status, customer, channel, store, placed, subtotal, discount, _total, _channel_code in self.orders.values():
            if discount > 0:
                discounted[placed.strftime("%Y-%m")] += 1
        customer_orders = Counter(row[1] for row in self.orders.values()
                                  if row[0] != "cancelled" and row[1] is not None)
        recurrence = Counter()
        recurrence_by_type = defaultdict(Counter)
        for customer, frequency in customer_orders.items():
            kind = self.customer_types[customer]
            bucket = "one" if frequency == 1 else "two_to_four" if frequency <= 4 else "five_to_ten" if frequency <= 10 else "eleven_plus"
            recurrence[bucket] += 1
            recurrence_by_type[kind][bucket] += 1
            recurrence_by_type[kind]["orders"] += frequency
            recurrence_by_type[kind]["customers"] += 1
        revenue = Decimal("0.00")
        cogs = Decimal("0.00")
        canonical_fulfillment_cogs = Decimal("0.00")
        sellable_cogs_reversed_total = Decimal("0.00")
        revenue_by_sku = defaultdict(Decimal)
        cogs_by_sku = defaultdict(Decimal)
        non_sellable_loss_by_sku = defaultdict(Decimal)
        sellable_return_cogs = defaultdict(Decimal)
        non_sellable_return_loss = defaultdict(Decimal)
        returned_units = defaultdict(int)
        for return_item_key, cost in self.return_movement_cost.items():
            source_key, destination, _quantity, _order_key = self.return_items.get(return_item_key, (None, None, 0, None))
            if destination == "sellable":
                sellable_return_cogs[source_key] += cost
            elif destination in {"quarantine", "repair", "discard"}:
                non_sellable_return_loss[source_key] += cost
        for source_key, _destination, quantity_received, _order_key in self.return_items.values():
            if source_key is not None:
                returned_units[source_key] += quantity_received
        for source_key, destination, quantity_received, _order_key in self.return_items.values():
            if destination not in {"quarantine", "repair", "discard"} or quantity_received <= 0:
                continue
            source = self.fulfillment_items.get(source_key)
            if source and source[2] > 0:
                historical_unit_cost = (self.fulfillment_cost[source_key] / Decimal(source[2])).quantize(
                    Decimal("0.00000001"), rounding=ROUND_HALF_UP
                )
                non_sellable_return_loss[source_key] += (
                    historical_unit_cost * quantity_received
                )
        units_by_sku = defaultdict(int)
        price_by_sku = defaultdict(Decimal)
        for item_order, quantity, unit_price, sku in self.items.values():
            order = self.orders.get(item_order)
            if order and order[0] == "completed":
                units_by_sku[sku] += quantity
                price_by_sku[sku] += Decimal(quantity) * unit_price
        for key, (order_key, item_key, fulfilled, _allocated) in self.fulfillment_items.items():
            order = self.orders.get(order_key)
            item = self.items.get(item_key)
            if not order or not item or order[0] != "completed":
                continue
            remaining = max(fulfilled - returned_units[key], 0)
            qty, unit_price, sku = item[1], item[2], item[3]
            line_revenue = Decimal(remaining) * (unit_price - self.discounts[item_key] / qty)
            revenue += line_revenue
            canonical_fulfillment_cogs += self.fulfillment_cost[key]
            net_margin_cogs = self.fulfillment_cost[key] - sellable_return_cogs[key]
            cogs += net_margin_cogs
            sellable_cogs_reversed_total += sellable_return_cogs[key]
            revenue_by_sku[sku] += line_revenue
            cogs_by_sku[sku] += net_margin_cogs
            non_sellable_loss_by_sku[sku] += non_sellable_return_loss[key]
        type_counts = Counter(self.customer_types.values())
        ticket_count = Counter()
        ticket_total = defaultdict(Decimal)
        for status, customer, _channel, _store, _placed, _subtotal, _discount, total, _channel_code in self.orders.values():
            if status == "completed" and customer is not None:
                kind = self.customer_types[customer]
                ticket_count[kind] += 1
                ticket_total[kind] += total
        ticket_average = {kind: ticket_total[kind] / ticket_count[kind]
                          for kind in ticket_count if ticket_count[kind]}
        pf_ticket = ticket_average.get("individual", Decimal(0))
        pj_ticket = ticket_average.get("business", Decimal(0))
        customer_revenue_total = sum(ticket_total.values(), Decimal(0))
        recurrence_total = sum(recurrence.values())
        total_payment = sum(self.payment_counts.values())
        months = sorted(monthly)
        avg_month = sum(monthly.values()) / max(len(monthly), 1)
        bf_months = [month for month in months if month.endswith("-11") and month[:4] in {"2023", "2024", "2025"}]
        regular_months = [month for month in months if month not in bf_months]
        bf_discount_rate = sum(discounted[month] for month in bf_months) * 100 / max(sum(monthly[month] for month in bf_months), 1)
        regular_discount_rate = sum(discounted[month] for month in regular_months) * 100 / max(sum(monthly[month] for month in regular_months), 1)
        returned_completed = sum(
            row[0] == "completed" and key in self.orders_with_return
            for key, row in self.orders.items()
        )
        physical_orders = sum(row[2] == "physical" for row in self.orders.values())
        total_orders = len(self.orders)
        summary = {
            "orders_by_status": dict(statuses),
            "orders_by_month": dict(monthly),
            "channel_types": dict(Counter(row[2] for row in self.orders.values())),
            "channel_type_percent": {key: round(value * 100 / max(total_orders, 1), 2)
                                      for key, value in Counter(row[2] for row in self.orders.values()).items()},
            "store_orders": dict(Counter(row[3] for row in self.orders.values() if row[2] == "physical")),
            "largest_store_percent_of_physical": round(max(Counter(row[3] for row in self.orders.values() if row[2] == "physical").values()) * 100 / max(physical_orders, 1), 2),
            "identified_customers_by_type": dict(type_counts),
            "anonymous_physical": sum(row[2] == "physical" and row[1] is None for row in self.orders.values()),
            "anonymous_physical_percent": round(sum(row[2] == "physical" and row[1] is None for row in self.orders.values()) * 100 / max(physical_orders, 1), 2),
            "recurrence": {key: dict(value) for key, value in recurrence_by_type.items()},
            "recurrence_average_orders_by_type": {
                key: round(value["orders"] / max(value["customers"], 1), 4)
                for key, value in recurrence_by_type.items()
            },
            "average_completed_ticket_by_customer_type": {
                key: str(value.quantize(Decimal("0.01"))) for key, value in ticket_average.items()
            },
            "pj_to_pf_ticket_ratio": str((pj_ticket / pf_ticket).quantize(Decimal("0.0001"))) if pf_ticket else None,
            "completed_revenue_share_by_customer_type_percent": {
                key: str((amount * 100 / customer_revenue_total).quantize(Decimal("0.01")))
                for key, amount in ticket_total.items()
            } if customer_revenue_total else {},
            "recurrence_buckets": dict(recurrence),
            "recurrence_bucket_percent": {key: round(value * 100 / max(recurrence_total, 1), 2) for key, value in recurrence.items()},
            "payments_by_method_type": dict(self.payment_counts),
            "payment_mix_percent": {key: round(value * 100 / total_payment, 2) for key, value in self.payment_counts.items()} if total_payment else {},
            "orders_with_return": returned_completed,
            "discounted_orders": sum(discounted.values()),
            "discount_rate_percent": round(sum(discounted.values()) * 100 / max(len(self.orders), 1), 2),
            "black_friday_discount_incidence_percent": round(bf_discount_rate, 2),
            "regular_discount_incidence_percent": round(regular_discount_rate, 2),
            "november_orders_average": round(sum(monthly[m] for m in bf_months) / max(len(bf_months), 1), 2),
            "regular_month_orders_average": round(sum(monthly[m] for m in regular_months) / max(len(regular_months), 1), 2),
            "january_average": round(sum(v for m, v in monthly.items() if m.endswith("-01")) / max(sum(m.endswith("-01") for m in monthly), 1), 2),
            "december_average": round(sum(v for m, v in monthly.items() if m.endswith("-12")) / max(sum(m.endswith("-12") for m in monthly), 1), 2),
            "average_month": round(avg_month, 2),
            "completed_realized_revenue": str(revenue.quantize(Decimal("0.01"))),
            "completed_canonical_fulfillment_cogs": str(canonical_fulfillment_cogs.quantize(Decimal("0.01"))),
            "completed_margin_cogs": str(cogs.quantize(Decimal("0.01"))),
            "completed_sellable_return_cogs_reversed": str(sellable_cogs_reversed_total.quantize(Decimal("0.01"))),
            "completed_non_sellable_return_loss_included": str(sum(non_sellable_loss_by_sku.values(), Decimal(0)).quantize(Decimal("0.01"))),
            "gross_margin_percent": str(((revenue-cogs)*100/revenue).quantize(Decimal("0.01"))) if revenue else None,
            "cost_to_net_revenue_percent": str((cogs*100/revenue).quantize(Decimal("0.01"))) if revenue else None,
            "top_sku_cost_ratios": [
                {"sku": sku, "net_revenue": str(amount.quantize(Decimal("0.01"))),
                 "cogs": str(cogs_by_sku[sku].quantize(Decimal("0.01"))),
                 "non_sellable_return_loss_included_in_cogs": str(non_sellable_loss_by_sku[sku].quantize(Decimal("0.01"))),
                 "cogs_percent": str((cogs_by_sku[sku]*100/amount).quantize(Decimal("0.01"))),
                 "completed_order_unit_price_avg": str((price_by_sku[sku]/max(units_by_sku[sku],1)).quantize(Decimal("0.01"))),
                 "receipt_unit_cost_avg": str((self.received_by_sku[sku][1]/max(self.received_by_sku[sku][0],1)).quantize(Decimal("0.01")))}
                for sku, amount in sorted(revenue_by_sku.items(), key=lambda pair: (-pair[1], pair[0]))[:10]
            ],
            "receipt_average_unit_cost": str((sum((x[1] for x in self.receipts.values()), Decimal(0)) /
                                               max(sum(x[0] for x in self.receipts.values()), 1)).quantize(Decimal("0.01"))),
            "returns_orders_rate_of_completed": round(returned_completed * 100 / max(statuses["completed"], 1), 2),
        }
        self.summary_cache = summary
        summary["distribution_audit"] = classify_portfolio_distributions(self.distribution_metrics())
        summary["logical_audit"] = self.logical_audit()
        return summary

    def logical_audit(self) -> dict:
        """Cross-table checks over bounded per-entity aggregates; no transaction rows are retained."""
        failures = []
        checked = {}

        def check(name: str, mismatches) -> None:
            samples = list(mismatches)[:5]
            count = len(mismatches)
            checked[name] = {"result": "PASS" if not count else "FAIL", "mismatches": count,
                             "samples": samples}
            if count:
                failures.append(name)

        subtotal_mismatch = []
        item_gross = defaultdict(Decimal)
        for item_key, (order_key, quantity, unit_price, _sku) in self.items.items():
            item_gross[order_key] += Decimal(quantity) * unit_price
        item_discount = defaultdict(Decimal)
        for item_key, amount in self.discounts.items():
            item = self.items.get(item_key)
            if item:
                item_discount[item[0]] += amount
        for key, order in self.orders.items():
            _status, _customer, _channel, _store, _placed, subtotal, discount, total, _channel_code = order
            if item_gross[key] != subtotal or item_discount[key] != discount or total != subtotal - discount + self.order_shipping[key]:
                subtotal_mismatch.append(key)
        check("order_item_and_discount_totals", subtotal_mismatch)

        fulfilled = Counter()
        allocated = Counter()
        for _key, (_order_key, item_key, qty, allocated_qty) in self.fulfillment_items.items():
            fulfilled[item_key] += qty
            allocated[item_key] += allocated_qty
        quantity_mismatch = []
        for item_key, (order_key, quantity, unit_price, _sku) in self.items.items():
            cancelled = self.cancellations[item_key]["quantity"]
            status = self.orders[order_key][0]
            if fulfilled[item_key] + cancelled > quantity or allocated[item_key] > quantity:
                quantity_mismatch.append({"item": item_key, "order_status": status, "sold": quantity,
                                          "fulfilled": fulfilled[item_key], "cancelled": cancelled,
                                          "allocated": allocated[item_key]})
            elif status == "completed" and fulfilled[item_key] + cancelled != quantity:
                quantity_mismatch.append({"item": item_key, "order_status": status, "sold": quantity,
                                          "fulfilled": fulfilled[item_key], "cancelled": cancelled,
                                          "allocated": allocated[item_key]})
            elif status == "cancelled" and cancelled and (fulfilled[item_key] or cancelled != quantity):
                quantity_mismatch.append({"item": item_key, "order_status": status, "sold": quantity,
                                          "fulfilled": fulfilled[item_key], "cancelled": cancelled,
                                          "allocated": allocated[item_key]})
        check("fulfillment_and_cancellation_quantities", quantity_mismatch)

        captured_by_order = defaultdict(Decimal)
        refunds_by_order = defaultdict(Decimal)
        payment_statuses_by_order = defaultdict(set)
        for payment_key, refund_amount in self.refunds.items():
            payment = self.payments.get(payment_key)
            if payment:
                refunds_by_order[payment[0]] += refund_amount
        installment_mismatch = []
        for payment_key, (order_key, amount, status) in self.payments.items():
            payment_statuses_by_order[order_key].add(status)
            if status in {"captured", "settled"}:
                captured_by_order[order_key] += amount
            installments = sorted(self.installments.get(payment_key, ()))
            if installments and ([number for number, _ in installments] != list(range(1, len(installments) + 1))
                                 or sum((amount for _, amount in installments), Decimal("0.00")) != amount):
                installment_mismatch.append(payment_key)
        check("payment_installment_reconciliation", installment_mismatch)
        payment_mismatch = []
        for order_key, order in self.orders.items():
            status, _customer, _channel, _store, _placed, _subtotal, _discount, total, _channel_code = order
            if status != "cancelled" and captured_by_order[order_key] != total:
                payment_mismatch.append(order_key)
            if refunds_by_order[order_key] > captured_by_order[order_key]:
                payment_mismatch.append(order_key)
            if status == "cancelled":
                if (captured_by_order[order_key] == 0 and "cancelled" not in payment_statuses_by_order[order_key]
                        or captured_by_order[order_key] > 0 and refunds_by_order[order_key] != captured_by_order[order_key]):
                    payment_mismatch.append(order_key)
        check("payment_and_refund_reconciliation", payment_mismatch)

        returned_by_source = Counter()
        return_mismatch = []
        for return_key, (source_key, destination, quantity, _order_key) in self.return_items.items():
            returned_by_source[source_key] += quantity
            moved = self.return_movement_quantity[return_key]
            if destination == "sellable":
                source = self.fulfillment_items.get(source_key)
                if quantity and (moved != quantity or source is None or source[2] <= 0):
                    return_mismatch.append(return_key)
                elif quantity:
                    historical_unit = (self.fulfillment_cost[source_key] / Decimal(source[2])).quantize(
                        Decimal("0.00000001"), rounding=ROUND_HALF_UP
                    )
                    if self.return_movement_cost[return_key] != historical_unit * quantity:
                        return_mismatch.append(return_key)
            elif moved:
                return_mismatch.append(return_key)
            header_key, sale_item_key, requested, approved, received_at = self.return_metadata[return_key]
            header = self.return_headers.get(header_key)
            source = self.fulfillment_items.get(source_key)
            sale_item = self.items.get(sale_item_key)
            if (header is None or header[0] != _order_key or source is None or sale_item is None
                    or sale_item[0] != _order_key or source[1] != sale_item_key
                    or not 0 <= quantity <= approved <= requested or (quantity and received_at is None)):
                return_mismatch.append(return_key)
        for source_key, _order_key_item, fulfilled_qty, _allocated_qty in self.fulfillment_items.values():
            if returned_by_source[source_key] > fulfilled_qty:
                return_mismatch.append(source_key)
        check("returns_against_original_fulfillment", return_mismatch)

        lifecycle_mismatch = []
        for fulfillment_key, (order_key, status, kind) in self.fulfillments.items():
            events = sorted(self.fulfillment_events.get(fulfillment_key, ()), key=lambda row: (row[1], row[0]))
            types = [event_type for event_type, _at in events]
            if status == "completed":
                if not types or types[0] != "prepared":
                    lifecycle_mismatch.append(fulfillment_key)
                elif kind == "delivery" and ("dispatched" not in types or "delivered" not in types
                                               or events[types.index("dispatched")][1] >= events[types.index("delivered")][1]):
                    lifecycle_mismatch.append(fulfillment_key)
                elif kind == "store_pickup" and ("pickup_ready" not in types or "picked_up" not in types
                                                  or events[types.index("pickup_ready")][1] >= events[types.index("picked_up")][1]):
                    lifecycle_mismatch.append(fulfillment_key)
        check("completed_fulfillment_event_lifecycle", lifecycle_mismatch)

        refund_mismatch = []
        refunds_by_cancellation = defaultdict(Decimal)
        for row in self.refund_rows:
            payment = self.payments.get(row.payment_key)
            if (payment is None or payment[0] != row.order_key or payment[2] not in {"captured", "settled"}
                    or row.return_key is not None and row.cancellation_key is not None):
                refund_mismatch.append(row.key)
            if row.status == "completed" and row.cancellation_key:
                refunds_by_cancellation[row.cancellation_key] += row.amount
        for key, cancellation in self.cancellation_rows.items():
            expected = cancellation.net_cancelled_amount + cancellation.shipping_cancelled_amount
            if refunds_by_cancellation[key] != expected:
                refund_mismatch.append(key)
            item = self.items.get(cancellation.item_key)
            if (item is None or item[0] != cancellation.order_key
                    or cancellation.gross_cancelled_amount != item[2] * cancellation.cancelled_quantity
                    or cancellation.net_cancelled_amount != cancellation.gross_cancelled_amount - cancellation.discount_cancelled_amount):
                refund_mismatch.append(key)
        check("refund_links_and_cancellation_amounts", refund_mismatch)

        original_cogs = sum((self.fulfillment_cost[key] for key, (order_key, _item, _qty, _allocated) in self.fulfillment_items.items()
                             if self.orders.get(order_key, (None,))[0] == "completed"), Decimal("0.00")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        sellable_reversal = sum((self.return_movement_cost[key] for key, (_source, destination, _qty, order_key) in self.return_items.items()
                                 if destination == "sellable" and self.orders.get(order_key, (None,))[0] == "completed"), Decimal("0.00")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        analytical_cogs = Decimal(self.summary_cache["completed_margin_cogs"])
        financial_mismatch = []
        if original_cogs - sellable_reversal != analytical_cogs:
            financial_mismatch.append({"check": "fulfillment_cogs_minus_sellable_returns",
                                      "original_cogs": str(original_cogs),
                                      "sellable_reversal": str(sellable_reversal),
                                      "analytical_cogs": str(analytical_cogs)})
        if Decimal(self.summary_cache["completed_non_sellable_return_loss_included"]) > analytical_cogs:
            financial_mismatch.append("non_sellable_loss_exceeds_retained_cogs")
        check("margin_cogs_and_return_loss_no_double_count", financial_mismatch)

        transfer_mismatch = []
        for item_key, item in self.transfer_items.items():
            moves = self.transfer_movements[item_key]
            outgoing = [row for row in moves if row.movement_type == "transfer_out"]
            incoming = [row for row in moves if row.movement_type == "transfer_in"]
            if (len(outgoing) != 1 or len(incoming) != 1
                    or outgoing[0].quantity_delta != -item.quantity_dispatched
                    or incoming[0].quantity_delta != item.quantity_received
                    or outgoing[0].unit_cost != incoming[0].unit_cost):
                transfer_mismatch.append(item_key)
        check("transfer_movement_pairs", transfer_mismatch)
        return {"result": "PASS" if not failures else "FAIL", "failure_count": len(failures),
                "failed_checks": sorted(set(failures)), "checks": checked,
                "retained_entity_counts": {"orders": len(self.orders), "sale_items": len(self.items),
                                           "fulfillment_items": len(self.fulfillment_items),
                                           "payments": len(self.payments), "return_items": len(self.return_items)}}



def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--orders", type=int, default=10_000, help="pedidos aceitos-alvo do piloto")
    parser.add_argument("--stock-audit", action="store_true", help="inclui auditoria detalhada de estoque, com maior uso de memória")
    parser.add_argument("--no-tracemalloc", action="store_true", help="desliga o rastreamento do heap para ensaios longos")
    args = parser.parse_args()
    if args.orders <= 0:
        parser.error("--orders deve ser positivo")

    base = load_config("portfolio")
    config = replace(base, generation={
        **base.generation,
        "sales_orders": args.orders,
        "estimated_order_items": args.orders * 22 // 10,
        "estimated_transaction_rows": args.orders * 20,
        "stock_audit": int(args.stock_audit),
    })
    if not args.no_tracemalloc:
        tracemalloc.start()
    master_started = perf_counter()
    master = generate_master_data(config)
    master_seconds = perf_counter() - master_started
    sink = DiscardingSink(master)
    started = perf_counter()
    result = generate_full_transactions_incremental(config, master, sink, batch_size=config.batch_size)
    elapsed = perf_counter() - started
    if not args.no_tracemalloc:
        current_bytes, peak_bytes = tracemalloc.get_traced_memory()
        tracemalloc.stop()
    else:
        current_bytes = peak_bytes = None
    expected_quotas = build_sales_intent_quotas(
        accepted_target=args.orders,
        start_date=config.start_date,
        end_date=config.end_date,
        annual_shares_percent=config.order_plan["annual_shares_percent"],
        channel_shares_percent=config.order_plan["channel_shares_percent"],
        month_weights=config.order_plan["month_weights"],
        physical_attempt_multiplier_percent=config.order_plan["physical_attempt_multiplier_percent"],
        intention_cap=config.order_plan["intention_cap"],
    )
    expected_cells = {
        f"{row.year}-{row.month:02d}:{row.channel_code}": row.accepted_orders
        for row in expected_quotas
    }
    observed_cells = result.runtime_metrics.get("sales_orders_accepted_by_year_month_channel", {})
    quota_mismatches = {
        key: {"expected": expected_cells.get(key, 0), "actual": observed_cells.get(key, 0)}
        for key in sorted(set(expected_cells) | set(observed_cells))
        if expected_cells.get(key, 0) != observed_cells.get(key, 0)
    }
    expected_by_year_channel = defaultdict(int)
    observed_by_year_channel = defaultdict(int)
    for cell, count in expected_cells.items():
        year, channel = cell.split(":", 1)
        expected_by_year_channel[(year[:4], channel)] += count
    for cell, count in observed_cells.items():
        year, channel = cell.split(":", 1)
        observed_by_year_channel[(year[:4], channel)] += count
    quota_audit = {
        "result": "PASS" if not quota_mismatches and result.counts()["sales_orders"] == args.orders else "FAIL",
        "expected_accepted_orders": args.orders,
        "actual_accepted_orders": result.counts()["sales_orders"],
        "mismatched_month_channel_cells": len(quota_mismatches),
        "mismatch_samples": dict(list(quota_mismatches.items())[:12]),
        "by_year_channel": {
            f"{year}:{channel}": {"expected": expected_by_year_channel[(year, channel)],
                                  "actual": observed_by_year_channel[(year, channel)]}
            for year, channel in sorted(set(expected_by_year_channel) | set(observed_by_year_channel))
        },
    }
    portfolio_audit = sink.summary()
    print(json.dumps({
        "profile": config.profile,
        "accepted_target": args.orders,
        "accepted_orders": result.counts()["sales_orders"],
        "intent_metrics": {
            key: value for key, value in result.runtime_metrics.items()
            if key.startswith("sales_intention") or key.startswith("sales_orders_")
            or key.startswith("customer_frequency_")
        },
        "accepted_quota_audit": quota_audit,
        "portfolio_audit": portfolio_audit,
        "stock_audit": result.runtime_metrics.get("stock_audit_summary"),
        "counts": result.counts(),
        "aggregates": {
            key: value for key, value in result.aggregates.items()
            if isinstance(value, (int, float, str)) or value.__class__.__name__ == "Decimal"
        },
        "duration_seconds": round(elapsed, 2),
        "master_generation_seconds": round(master_seconds, 2),
        "python_heap_current_mib": round(current_bytes / 1048576, 2) if current_bytes is not None else None,
        "python_heap_peak_mib": round(peak_bytes / 1048576, 2) if peak_bytes is not None else None,
        "max_batch_rows": sink.max_batch_rows,
        "rows_discarded": sink.rows_received,
        "max_pending_events": result.runtime_metrics.get("transaction_events_max_pending"),
        "max_active_orders": result.runtime_metrics.get("max_active_orders"),
        "max_active_backorders": result.runtime_metrics.get("max_stock_backorder_orders"),
    }, ensure_ascii=False, indent=2, default=str))


if __name__ == "__main__":
    main()
