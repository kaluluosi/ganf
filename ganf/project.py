import os
import glob
from typing import Any, Callable, overload
from ganf.config import GanfConfig, GANF_CONF, MetaConfig, META_CONF
from gitignore_parser import parse_gitignore

IGNORE_FILE = ".ganfignore"
IgnoreFunction = Callable[[str], bool]


class Project:
    GLOB = glob.glob("**/*.*", recursive=True)

    def __init__(
        self,
        ganf_config: GanfConfig | str = GANF_CONF,
        ignore_file: str = IGNORE_FILE,
    ) -> None:
        if isinstance(ganf_config, str):
            # 如果 `ganf_config` 不存在就抛错
            dir_path = os.path.dirname(ganf_config)
            os.chdir(dir_path)
            self.ganf_config = GanfConfig.load(ganf_config)
        elif isinstance(ganf_config, GanfConfig):
            self.ganf_config = ganf_config

        # 如果有传ignore文件就加载
        if ignore_file:
            self._ignore = parse_gitignore(ignore_file)
        else:
            # 如果都没有就用默认的 ignore 检查函数
            self._ignore = lambda _: True

    def __iter__(self) -> Any:
        for file_path in self.GLOB:
            if not self._ignore(file_path):
                yield file_path
