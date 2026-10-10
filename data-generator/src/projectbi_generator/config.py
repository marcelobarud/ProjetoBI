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
    order_plan: dict
    stores: tuple[StoreConfig, ...]

    @property
    def sales_order_target(self) -> int:
        return self.generation["sales_orders"]

    @property
    def batch_size(self) -> int:
        return self.generation["batch_size"]


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
    generation = profile_data.get("generation", {})
    if not isinstance(generation, dict) or any(
        not isinstance(value, int) or isinstance(value, bool) or value < 0
        for value in generation.values()
    ):
        raise ConfigurationError("Configurações de geração devem ser inteiros não negativos.")
    if not generation.get("sales_orders") or not generation.get("batch_size"):
        raise ConfigurationError("O profile deve declarar sales_orders e batch_size positivos.")
    composition = profile_data.get("composition", {})
    if composition:
        if any(not isinstance(value, int) or value < 0 for value in composition.values()):
            raise ConfigurationError("A composição de clientes deve conter inteiros não negativos.")
        if composition.get("individual_customers", 0) + composition.get("business_customers", 0) != volumes.get("customers"):
            raise ConfigurationError("A composição PF/PJ deve totalizar o volume de clientes.")

    order_plan = profile_data.get("order_plan", {"mode": "intentions"})
    mode = order_plan.get("mode") if isinstance(order_plan, dict) else None
    if mode not in {"intentions", "accepted_quotas"}:
        raise ConfigurationError("order_plan.mode deve ser intentions ou accepted_quotas.")
    if mode == "accepted_quotas":
        try:
            annual_shares = {int(year): value for year, value in order_plan["annual_shares_percent"].items()}
            channel_shares = {
                int(year): {str(channel): value for channel, value in weights.items()}
                for year, weights in order_plan["channel_shares_percent"].items()
            }
            month_weights = {int(month): value for month, value in order_plan["month_weights"].items()}
            physical_multipliers = {
                int(year): value for year, value in order_plan["physical_attempt_multiplier_percent"].items()
            }
            frequency_shares = {
                str(kind): {str(bucket): value for bucket, value in values.items()}
                for kind, values in order_plan["customer_frequency_shares_percent"].items()
            }
            intention_cap = order_plan["intention_cap"]
        except (KeyError, TypeError, ValueError, AttributeError) as exc:
            raise ConfigurationError("Order plan aceito está incompleto ou inválido.") from exc
        expected_years = set(range(start_date.year, end_date.year + 1))
        numeric_values = [*annual_shares.values(), *month_weights.values(), *physical_multipliers.values()]
        numeric_values.extend(value for row in channel_shares.values() for value in row.values())
        if (set(annual_shares) != expected_years or set(channel_shares) != expected_years
                or set(physical_multipliers) != expected_years
                or sum(annual_shares.values()) != 100
                or any(not isinstance(value, int) or isinstance(value, bool) or value < 0 for value in numeric_values)
                or any(sum(row.values()) != 100 for row in channel_shares.values())
                or any(set(row) != {"physical", "ecommerce", "marketplace"} for row in channel_shares.values())
                or set(month_weights) != set(range(1, 13))
                or any(value <= 0 for value in month_weights.values())
                or any(value < 100 for value in physical_multipliers.values())
                or set(frequency_shares) != {"individual", "business"}
                or any(set(row) != {"one", "two_to_four", "five_to_ten", "eleven_plus"}
                       or sum(row.values()) != 100
                       or any(not isinstance(value, int) or isinstance(value, bool) or value < 0 for value in row.values())
                       for row in frequency_shares.values())
                or not isinstance(intention_cap, int) or isinstance(intention_cap, bool)
                or intention_cap < generation["sales_orders"]):
            raise ConfigurationError("Order plan deve cobrir horizonte, bandas e limite de intenções válidos.")
        order_plan = {
            "mode": mode,
            "intention_cap": intention_cap,
            "annual_shares_percent": annual_shares,
            "channel_shares_percent": channel_shares,
            "month_weights": month_weights,
            "physical_attempt_multiplier_percent": physical_multipliers,
            "customer_frequency_shares_percent": frequency_shares,
        }

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
        composition=composition,
        generation=generation,
        order_plan=order_plan,
        stores=stores,
    )
