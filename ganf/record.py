"""
用来记录文件翻译md5，用来判断翻译进度和是否需要更新翻译。
"""
import json
import os
from pydantic import RootModel
from .utils import file_md5


class Record(RootModel[dict[str, str]]):
    root: dict[str, str] = {}

    @classmethod
    def load(cls, file_path: str):
        if os.path.exists(file_path):
            with open(file_path, "r") as f:
                return cls.model_validate_json(f.read())

    def save(self, file_path: str):
        with open(file_path, "w") as f:
            json.dump(self.model_dump(), f, indent=4)

    def add(self, path: str):
        self.root[path] = file_md5(path).hexdigest()

    def remove(self, path: str):
        del self.root[path]

    def __str__(self):
        return str(self.root)

    def is_modified(self, file_path: str):
        if file_path in self.root:
            return file_md5(file_path).hexdigest() != self.root[file_path]
        else:
            return True
