import os
import pytest
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

    mock_load = mocker.patch("toml.load")
    open_file = mocker.patch("builtins.open")

    config2 = OpenAIConfig.load(file_name)
    mock_load.assert_called_once()
    open_file.assert_called_once_with(file_name)

    mock_load.reset_mock()
    open_file.reset_mock()

    mock_dump = mocker.patch("toml.dump")
    config2.save("shit.toml")
    mock_dump.assert_called()
    open_file.assert_called_with("shit.toml", "w")

    mock_dump.reset_mock()
    open_file.reset_mock()

    config2.save()
    mock_dump.assert_called()
    open_file.assert_called_with(config2.file_name, "w")

    mock_dump.reset_mock()
    open_file.reset_mock()

    config2.file_name = None
    with pytest.raises(ValueError, match="file_name"):
        config2.save()
