import os
import openai
import toml
from typing import Callable, Literal
from gitignore_parser import parse_gitignore
from pydantic import BaseModel, Field
from contextvars import ContextVar

USER_DIR = os.path.expanduser("~")
GANF_DIR = os.path.join(USER_DIR, ".ganf")
OPENAI_CONFIG_FILE = "openai.toml"
GLOBAL_OPENAI_CONFIG_FILE = os.path.join(GANF_DIR, OPENAI_CONFIG_FILE)
GANF_CONFIG = "ganf.toml"
IGNORE_FILE = ".ganfignore"

GitignoreMethod = Callable[[str], bool]

openai_config_var = ContextVar["OpenAIConfig"]("openai_config_var")
ganf_config_var = ContextVar["GanfConfig"]("ganf_config_var")
gitignore_var = ContextVar[GitignoreMethod]("gitignore", default=lambda file: False)


class TomlConfig(BaseModel):
    def save(self, file_path: str):
        with open(file_path, mode="w") as f:
            toml.dump(self.model_dump(), f)

    @classmethod
    def load(cls, file_path: str):
        data = toml.load(file_path)
        return cls.model_validate(data)


class OpenAIConfig(TomlConfig):
    """
    OpenAI配置文件
    """

    api_key: str = Field(default=openai.api_key or "input_your_openai_api_key")
    api_base: str = Field(default=openai.api_base)
    api_type: Literal["azure", "open_ai"] = Field(default=openai.api_type)
    api_version: str = Field(default=openai.api_version)
    model: str = Field(default=os.environ.get("MODEL", "gpt-3.5-turbo"))
    deployment_id: str | None = Field(
        default=os.environ.get("DEPLOYMENT_ID", "your_deployment_id")
    )
    RPM: int = 10
    max_tokens: int = 5000
    cost: float = Field(default=0.0015, description="每1000 tokens费用，单位是美元。")


class GanfConfig(TomlConfig):
    """
    翻译项目配置文件
    """

    source_dir: str = "docs"
    dist_dir: str = "./"
    locales: list[str] = ["zh"]
    prompts: list[str] = Field(default_factory=list[str], description="额外题词，用来微调翻译结果的")


def load_openai_config(file_path: str, setup: bool = True):
    config = OpenAIConfig.load(file_path)
    openai_config_var.set(config)
    if setup:
        setup_openai(config)
    return config


def setup_openai(openai_config: OpenAIConfig):
    openai.api_key = openai_config.api_key
    openai.api_base = openai_config.api_base
    openai.api_version = openai_config.api_version
    openai.api_type = openai_config.api_type


def load_ganf_config(file_path: str):
    config = GanfConfig.load(file_path)
    ganf_config_var.set(config)
    return config


def load_gitignore(file_path: str, base_dir: str):
    gitignore = parse_gitignore(file_path, base_dir)
    gitignore_var.set(gitignore)
    return gitignore
