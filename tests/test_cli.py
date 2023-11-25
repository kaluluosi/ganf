import os
from click.testing import CliRunner
from ganf.cli import cost, openai, build
from pytest_mock import MockerFixture
from gitignore_parser import parse_gitignore

from ganf.config import OPENAI_CONF
# hehe


def test_ignore(test_cwd):
    ignore = parse_gitignore(".ganfignore")
    assert ignore(r"sqla_arch_small.png") == True


def test_cost(clirunner: CliRunner, test_cwd):
    result = clirunner.invoke(cost)
    assert "总翻译语言" in result.output
    assert result.exception is None


def test_setup(clirunner: CliRunner, mocker: MockerFixture, tmp_path: str):
    # 测试本地配置
    os.chdir(tmp_path)

    mock_openai_conf_wizard = mocker.patch(
        "ganf.cli.openai_conf_wizard", return_value=None
    )

    result = clirunner.invoke(openai, ["-l"])
    mock_openai_conf_wizard.assert_called_once_with(OPENAI_CONF)

    assert "正在配置项目配置文件" in result.output

    with open(OPENAI_CONF, "w") as f:
        pass

    mock_openai_conf_wizard.reset_mock()

    result = clirunner.invoke(openai, ["-l"])
    assert "项目配置文件已存在，请删除后再试。" in result.output
    mock_openai_conf_wizard.assert_not_called()


def test_build(clirunner: CliRunner, mocker: MockerFixture, test_cwd):
    mocker.patch(
        "openai.ChatCompletion.acreate",
        return_value={"choices": [{"message": {"content": "hello"}}]},
    )

    result = clirunner.invoke(build)
    assert result.exception == None
