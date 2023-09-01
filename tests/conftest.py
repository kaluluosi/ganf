import pytest
from functools import lru_cache


@pytest.fixture
def sample() -> str:
    print("sample called")
    with open("tests/sample/sample_en.md") as f:
        return f.read()
