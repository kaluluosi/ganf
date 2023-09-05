import os
import pytest
from functools import lru_cache
from ganf.config import GanfConfig
from click.testing import CliRunner


@pytest.fixture
def sample() -> str:
    print("sample called")
    with open("tests/sample/file.md") as f:
        return f.read()


@pytest.fixture
def ganf_config():
    return GanfConfig.load("tests/ganf.toml")


@pytest.fixture
def clirunner():
    runner = CliRunner()
    return runner


@pytest.fixture
def test_cwd():
    old = os.getcwd()
    os.chdir("tests")
    yield
    os.chdir(old)
