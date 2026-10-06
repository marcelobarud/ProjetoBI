"""Stable domain-specific seeds and independent random number generators."""

from __future__ import annotations

import hashlib
import random
from dataclasses import dataclass

DOMAINS = (
    "catalog",
    "customers",
    "employees",
    "sales",
    "sales_intents",
    "procurement",
    "inventory",
    "payments",
    "logistics",
    "returns",
)


def derive_subseed(root_seed: int, domain: str, generator_version: str) -> int:
    if domain not in DOMAINS:
        raise ValueError(f"Domínio de seed não aprovado: {domain}")
    payload = f"{root_seed}:{domain}:{generator_version}".encode("utf-8")
    return int.from_bytes(hashlib.sha256(payload).digest()[:8], "big", signed=False)


@dataclass
class DomainRandom:
    seed: int
    rng: random.Random


def create_domain_randoms(root_seed: int, generator_version: str) -> dict[str, DomainRandom]:
    return {
        domain: DomainRandom(
            seed=seed,
            rng=random.Random(seed),
        )
        for domain in DOMAINS
        for seed in (derive_subseed(root_seed, domain, generator_version),)
    }
