import pytest
from functools import lru_cache
from ganf.config import GanfConfig


@pytest.fixture
def sample() -> str:
    print("sample called")
    with open("tests/sample/sample_en.md") as f:
        return f.read()


@pytest.fixture
def ganf_config():
    return GanfConfig.load("tests/ganf.toml")
