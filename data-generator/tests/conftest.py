from pathlib import Path
from copy import deepcopy

import pytest

from projectbi_generator.config import load_config
from projectbi_generator.generators.master import generate_master_data
from projectbi_generator.generators.completion import extend_transactions
from projectbi_generator.generators.transactions import generate_transactions


@pytest.fixture(scope="session")
def config():
    return load_config("smoke")


@pytest.fixture(scope="session")
def master_data(config):
    return generate_master_data(config)


@pytest.fixture(scope="session")
def transaction_data(config, master_data):
    return generate_transactions(config, master_data)


@pytest.fixture(scope="session")
def completed_data(config, master_data, transaction_data):
    data = deepcopy(transaction_data)
    extend_transactions(config, master_data, data)
    return data
