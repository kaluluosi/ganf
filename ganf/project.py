import os
import glob
from typing import Callable
from ganf.config import GanfConfig, GANF_CONF
from gitignore_parser import parse_gitignore

IGNORE_FILE = ".ganfignore"
IgnoreFunction = Callable[[str], bool]


def iter_project(dir: str = "./"):
    old_cwd = os.getcwd()
    os.chdir(dir)
    if not os.path.exists(GANF_CONF):
        raise FileNotFoundError(f"{GANF_CONF}未发现配置文件。")

    ganf_conf = GanfConfig.load(GANF_CONF)

    if os.path.exists(IGNORE_FILE):
        ignore = parse_gitignore(IGNORE_FILE)
    else:
        ignore = lambda _: False

    globs = glob.glob(ganf_conf.source_dir + "/**/*.*", recursive=True)
    for file_path in globs:
        dirname = os.path.dirname(file_path)
        if not (ignore(file_path) or ignore(dirname)):
            yield file_path

    os.chdir(old_cwd)
