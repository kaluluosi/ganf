from typing import Literal
import openai
import toml
import os
from collections import defaultdict
from pydantic import BaseModel, Field
from contextvars import ContextVar
from .util import file_md5

USER_DIR = os.path.expanduser("~")
GANF_DIR = os.path.join(USER_DIR, ".ganf")

OPENAI_CONF = "openai.toml"
GLOBAL_OPENAI_CONF = os.path.join(GANF_DIR, OPENAI_CONF)

GANF_CONF = "ganf.toml"

META_CONF = "meta.toml"


class TomlConfig(BaseModel):
    file_name: str | None = Field(default=None, description="配置文件名", exclude=True)

    @classmethod
    def load(cls, file_name: str):
        """从配置文件加载。加载后将 `file_name` 赋值给 `self.file_name`。

        Args:
            file_name (str): _description_

        Returns:
            _type_: _description_
        """
        with open(file_name) as f:
            data = toml.load(f)

        config = cls(file_name=file_name, **data)
        return config

    def save(self, file_name: str | None = None):
        """保存文件，默认保存回 `load` 时的文件。

        Args:
            file_name (str | None, optional): 文件名. Defaults to None.

        Raises:
            ValueError: 文件名错误时
        """
        if file_name:
            with open(file_name, "w") as f:
                toml.dump(self.model_dump(), f)
            self.file_name = file_name
        elif self.file_name:
            with open(self.file_name, "w") as f:
                toml.dump(self.model_dump(), f)
        else:
            raise ValueError("file_name is None")


class OpenAIConfig(TomlConfig):
    api_key: str = Field(default=openai.api_key, description="OpenAI API Key")
    api_base: str = Field(default=openai.api_base, description="OpenAI API Base")
    api_type: str | Literal["open_ai", "azure"] = Field(
        default=openai.api_type, description="OpenAI API Type"
    )
    api_version: str = Field(default="2023-05-15", description="OpenAI API Version")
    model: str = Field(default="gpt-3.5-turbo", description="OpenAI Model")
    deployment_id: str = Field(
        default="", description="OpenAI Deployment ID (Azure Need)"
    )
    RPM: int = Field(default=10, description="OpenAI RPM")
    max_tokens: int = Field(default=1000, description="OpenAI Max Tokens")
    cost_per_k_token: float = Field(
        default=0.0015, description="OpenAI Cost Per K Token"
    )


class GanfConfig(TomlConfig):
    source_dir: str = Field(default="docs", description="Source Directory")
    dist_dir: str = Field(default="dist", description="Dist Directory")
    locales: list[str] = Field(default=["zh"], description="Locales")
    prompts: list[str] = Field(default_factory=list, description="Prompts")


class MetaConfig(TomlConfig):
    root: dict[str, str] = Field(
        default_factory=defaultdict[str, str], description="Root"
    )

    def update(self, path: str):
        self.root[path] = file_md5(path)

    def is_modified(self, path: str):
        """检测文件是否被修改过

        Args:
            path (str): 文件路径

        Returns:
            bool: True修改过，False未修改
        """
        if self.root[path]:
            return file_md5(path) != self.root[path]
        return True


openai_conf_var = ContextVar[OpenAIConfig]("openai_conf_var")
