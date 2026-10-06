from pathlib import Path

import pytest

from projectbi_generator.config import load_config
from projectbi_generator.generators.master import generate_master_data


@pytest.fixture(scope="session")
def config():
    return load_config("smoke")


@pytest.fixture(scope="session")
def master_data(config):
    return generate_master_data(config)
