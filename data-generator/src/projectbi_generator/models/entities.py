"""Logical-key-first entities; PostgreSQL identity values are assigned on load."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from typing import Any


@dataclass(frozen=True)
class Store:
    code: str
    name: str
    postal_code: str
    street: str
    street_number: str
    complement: str | None
    district: str
    city: str
    state_code: str
    country_code: str
    status: str
    opened_on: date
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True)
class EmployeeRole:
    code: str
    name: str
    is_active: bool
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True)
class Employee:
    code: str
    first_name: str
    last_name: str
    email: str
    phone: str | None
    hired_on: date
    terminated_on: date | None
    status: str
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True)
class EmployeeAssignment:
    logical_key: str
    employee_code: str
    role_code: str
    store_code: str | None
    valid_from: date
    valid_to: date | None
    created_at: datetime


@dataclass(frozen=True)
class SalesChannel:
    code: str
    name: str
    channel_type: str
    is_active: bool
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True)
class PaymentMethod:
    code: str
    name: str
    method_type: str
    is_installment_capable: bool
    is_active: bool
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True)
class Supplier:
    code: str
    legal_name: str
    trade_name: str
    tax_identifier: str
    email: str
    status: str
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True)
class Carrier:
    code: str
    name: str
    tax_identifier: str | None
    is_active: bool
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True)
class Category:
    code: str
    name: str
    parent_code: str | None
    is_active: bool
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True)
class Brand:
    code: str
    name: str
    is_active: bool
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True)
class Product:
    sku: str
    category_code: str
    brand_code: str | None
    name: str
    description: str
    specifications: dict[str, Any]
    unit_of_measure: str
    status: str
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True)
class ProductSupplier:
    product_sku: str
    supplier_code: str
    supplier_product_code: str
    is_preferred: bool
    is_active: bool
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True)
class ProductPrice:
    product_sku: str
    channel_code: str
    amount: Decimal
    valid_from: datetime
    valid_to: datetime | None
    created_at: datetime
    created_by_employee_code: str | None


@dataclass(frozen=True)
class Customer:
    code: str
    customer_type: str
    display_name: str
    status: str
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True)
class IndividualProfile:
    customer_code: str
    cpf: str
    birth_date: date
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True)
class BusinessProfile:
    customer_code: str
    legal_name: str
    trade_name: str
    cnpj: str
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True)
class CustomerContact:
    logical_key: str
    customer_code: str
    contact_type: str
    contact_value: str
    is_primary: bool
    is_active: bool
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True)
class CustomerAddress:
    logical_key: str
    customer_code: str
    address_label: str
    recipient_name: str
    postal_code: str
    street: str
    street_number: str
    complement: str | None
    district: str
    city: str
    state_code: str
    country_code: str
    is_default: bool
    is_active: bool
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True)
class StockLocation:
    code: str
    name: str
    location_type: str
    status: str
    store_code: str | None
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True)
class MasterData:
    stores: tuple[Store, ...]
    employee_roles: tuple[EmployeeRole, ...]
    employees: tuple[Employee, ...]
    employee_assignments: tuple[EmployeeAssignment, ...]
    sales_channels: tuple[SalesChannel, ...]
    payment_methods: tuple[PaymentMethod, ...]
    suppliers: tuple[Supplier, ...]
    carriers: tuple[Carrier, ...]
    categories: tuple[Category, ...]
    brands: tuple[Brand, ...]
    products: tuple[Product, ...]
    product_suppliers: tuple[ProductSupplier, ...]
    product_prices: tuple[ProductPrice, ...]
    customers: tuple[Customer, ...]
    individual_profiles: tuple[IndividualProfile, ...]
    business_profiles: tuple[BusinessProfile, ...]
    customer_contacts: tuple[CustomerContact, ...]
    customer_addresses: tuple[CustomerAddress, ...]
    stock_locations: tuple[StockLocation, ...]

    def counts(self) -> dict[str, int]:
        return {
            field: len(getattr(self, field))
            for field in self.__dataclass_fields__
        }
