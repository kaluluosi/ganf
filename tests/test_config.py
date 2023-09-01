import os
import pytest_mock
from ganf.config import OpenAIConfig, OPENAI_CONF


def test_openai_config(tmp_path: str, mocker: pytest_mock.MockerFixture):
    config = OpenAIConfig(
        api_key="test_api_key",
        api_base="test_api_base",
        api_type="azure",
        api_version="2023-05-15",
        model="gpt-3.5-turbo",
        deployment_id="test_deployment_id",
    )

    file_name = os.path.join(tmp_path, OPENAI_CONF)
    config.save(file_name)

    assert config.file_name == file_name

    mocker.patch("toml.load")

    config2 = OpenAIConfig.load(file_name)
