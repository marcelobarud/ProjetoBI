"""TOML configuration loader; configuration files contain no credentials."""

from __future__ import annotations

import tomllib
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


@dataclass(frozen=True)
class StoreConfig:
    code: str
    name: str
    city: str
    state_code: str
    postal_code: str
    street: str
    street_number: str
    district: str
    opened_on: date


@dataclass(frozen=True)
class GeneratorConfig:
    schema_version: int
    generator_version: str
    root_seed: int
    profile: str
    start_date: date
    end_date: date
    bootstrap_start_date: date
    bootstrap_end_date: date
    timezone: ZoneInfo
    volumes: dict[str, int]
    composition: dict[str, int]
    generation: dict[str, int]
    stores: tuple[StoreConfig, ...]


class ConfigurationError(ValueError):
    """Raised for an invalid TOML configuration."""


def _parse_date(source: dict, key: str) -> date:
    try:
        value = date.fromisoformat(source[key])
    except (KeyError, TypeError, ValueError) as exc:
        raise ConfigurationError(f"Data ausente ou inválida em '{key}'.") from exc
    return value


def load_config(profile: str | None = None, config_dir: Path | None = None) -> GeneratorConfig:
    base = config_dir or Path(__file__).resolve().parents[2] / "config"
    try:
        with (base / "generator.toml").open("rb") as stream:
            root = tomllib.load(stream)
        selected = profile or root["default_profile"]
        if selected not in {"smoke", "portfolio", "large"}:
            raise ConfigurationError("Profile deve ser smoke, portfolio ou large.")
        with (base / "profiles" / f"{selected}.toml").open("rb") as stream:
            profile_data = tomllib.load(stream)
    except OSError as exc:
        raise ConfigurationError("Arquivos TOML de configuração não encontrados.") from exc
    except (KeyError, tomllib.TOMLDecodeError) as exc:
        raise ConfigurationError("Configuração TOML ausente ou inválida.") from exc

    if profile_data.get("profile") != selected:
        raise ConfigurationError("Nome do profile diverge do arquivo carregado.")
    if not isinstance(root.get("schema_version"), int) or root["schema_version"] != 1:
        raise ConfigurationError("schema_version de configuração deve ser 1.")
    if not isinstance(root.get("root_seed"), int) or root["root_seed"] < 0:
        raise ConfigurationError("root_seed deve ser inteiro não negativo.")

    start_date = _parse_date(root, "start_date")
    end_date = _parse_date(root, "end_date")
    bootstrap_start = _parse_date(root, "bootstrap_start_date")
    bootstrap_end = _parse_date(root, "bootstrap_end_date")
    if start_date > end_date or bootstrap_start > bootstrap_end or bootstrap_end >= start_date:
        raise ConfigurationError("Janelas comercial e de bootstrap são incoerentes.")
    try:
        timezone = ZoneInfo(root["timezone"])
    except (KeyError, ZoneInfoNotFoundError) as exc:
        raise ConfigurationError("Fuso horário ausente ou inválido.") from exc

    volumes = profile_data.get("volumes", {})
    if set(volumes) != {
        "stores", "employees", "employee_roles", "employee_assignments", "customers",
        "individual_profiles", "business_profiles", "customer_contacts", "customer_addresses",
        "categories", "brands", "products", "product_suppliers", "product_prices",
        "stock_locations", "payment_methods", "carriers", "sales_channels", "suppliers",
    } or any(not isinstance(value, int) or value < 0 for value in volumes.values()):
        raise ConfigurationError("Volumes devem declarar exatamente as 19 tabelas master com inteiros não negativos.")

    stores = tuple(
        StoreConfig(
            code=item["code"],
            name=item["name"],
            city=item["city"],
            state_code=item["state_code"],
            postal_code=item["postal_code"],
            street=item["street"],
            street_number=item["street_number"],
            district=item["district"],
            opened_on=_parse_date(item, "opened_on"),
        )
        for item in profile_data.get("stores", [])
    )
    if selected == "smoke" and len(stores) != volumes["stores"]:
        raise ConfigurationError("A quantidade de endereços configurados diverge do volume de lojas.")

    return GeneratorConfig(
        schema_version=root["schema_version"],
        generator_version=root["generator_version"],
        root_seed=root["root_seed"],
        profile=selected,
        start_date=start_date,
        end_date=end_date,
        bootstrap_start_date=bootstrap_start,
        bootstrap_end_date=bootstrap_end,
        timezone=timezone,
        volumes=volumes,
        composition=profile_data.get("composition", {}),
        generation=profile_data.get("generation", {}),
        stores=stores,
    )
