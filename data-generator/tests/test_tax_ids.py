import random

from projectbi_generator.validation.tax_ids import generate_cnpj, generate_cpf, valid_cnpj, valid_cpf


def test_cpf_generation_checksum_digits_and_uniqueness():
    used = set()
    rng = random.Random(4581)
    values = [generate_cpf(rng, used) for _ in range(40)]
    assert len(set(values)) == len(values)
    assert all(value.isdigit() and valid_cpf(value) for value in values)


def test_cnpj_generation_checksum_digits_and_uniqueness():
    used = set()
    rng = random.Random(7812)
    values = [generate_cnpj(rng, used) for _ in range(20)]
    assert len(set(values)) == len(values)
    assert all(value.isdigit() and valid_cnpj(value) for value in values)


def test_invalid_cpf_and_cnpj_are_rejected():
    assert not valid_cpf("11111111111")
    assert not valid_cpf("12345678900")
    assert not valid_cnpj("00000000000000")
    assert not valid_cnpj("12345678000100")
