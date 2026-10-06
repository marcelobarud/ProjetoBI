"""Checksum-valid synthetic CPF/CNPJ generation and validation."""

from __future__ import annotations

import random


def _check_digit(digits: str, weights: tuple[int, ...]) -> str:
    remainder = sum(int(value) * weight for value, weight in zip(digits, weights)) % 11
    return str(0 if remainder < 2 else 11 - remainder)


def valid_cpf(value: str) -> bool:
    if len(value) != 11 or not value.isdigit() or len(set(value)) == 1:
        return False
    first = _check_digit(value[:9], tuple(range(10, 1, -1)))
    second = _check_digit(value[:9] + first, tuple(range(11, 1, -1)))
    return value[-2:] == first + second


def valid_cnpj(value: str) -> bool:
    if len(value) != 14 or not value.isdigit() or len(set(value)) == 1:
        return False
    first_weights = (5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2)
    second_weights = (6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2)
    first = _check_digit(value[:12], first_weights)
    second = _check_digit(value[:12] + first, second_weights)
    return value[-2:] == first + second


def generate_cpf(rng: random.Random, used: set[str]) -> str:
    while True:
        base = "".join(str(rng.randrange(10)) for _ in range(9))
        if len(set(base)) == 1:
            continue
        first = _check_digit(base, tuple(range(10, 1, -1)))
        second = _check_digit(base + first, tuple(range(11, 1, -1)))
        result = base + first + second
        if result not in used:
            used.add(result)
            return result


def generate_cnpj(rng: random.Random, used: set[str]) -> str:
    first_weights = (5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2)
    second_weights = (6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2)
    while True:
        base = "".join(str(rng.randrange(10)) for _ in range(12))
        if len(set(base)) == 1:
            continue
        first = _check_digit(base, first_weights)
        second = _check_digit(base + first, second_weights)
        result = base + first + second
        if result not in used:
            used.add(result)
            return result
