import toml
from pydantic import BaseModel, Field


class TomlConfig(BaseModel):
    file_name: str = Field(default="", description="配置文件名")

    @classmethod
    def load(cls, file_name: str):
        with open(file_name) as f:
            data = toml.load(f)

        config = cls(file_name=file_name, **data)
        return config

    def save(self, file_name: str | None = None):
        file_name = self.file_name or file_name
        if file_name:
            with open(file_name, "w") as f:
                toml.dump(self.model_dump(), f)
        else:
            raise ValueError("file_name is empty")
