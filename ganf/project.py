import os
import glob
from typing import Any, Callable, overload
from ganf.config import GanfConfig, GANF_CONF, MetaConfig, META_CONF, GANFIGNORE_FILE
from gitignore_parser import parse_gitignore

IGNORE_FILE = ".ganfignore"
IgnoreFunction = Callable[[str], bool]


class Project:
    def __init__(
        self,
        ganf_config: GanfConfig | str = GANF_CONF,
        ignore_file: str = IGNORE_FILE,
    ) -> None:
        if isinstance(ganf_config, str):
            # 如果 `ganf_config` 不存在就抛错
            self.ganf_config = GanfConfig.load(ganf_config)
        elif isinstance(ganf_config, GanfConfig):
            self.ganf_config = ganf_config

        # 设置工作目录
        dir_path = os.path.dirname(os.path.abspath(ganf_config.file_name))
        os.chdir(dir_path)

        # 如果有传ignore文件就加载
        if ignore_file and os.path.exists(ignore_file):
            self._ignore = parse_gitignore(ignore_file)
        else:
            # 如果都没有就用默认不忽略所有文件
            self._ignore = lambda _: False

    def __iter__(self) -> Any:
        for file_path in glob.glob(
            f"{self.ganf_config.source_dir}/**/*.*", recursive=True
        ):
            dirname = os.path.dirname(file_path)
            if not self._ignore(file_path) and not self._ignore(dirname):
                yield os.path.abspath(file_path)
