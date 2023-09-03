import os
import glob
from typing import Callable
from ganf.config import GanfConfig, GANF_CONF
from gitignore_parser import parse_gitignore

IGNORE_FILE = ".ganfignore"
IgnoreFunction = Callable[[str], bool]


def iter_project(dir: str = "./", filter: Callable[[str], bool] = lambda path: True):
    old_cwd = os.getcwd()
    os.chdir(dir)

    if os.path.exists(IGNORE_FILE):
        ignore = parse_gitignore(IGNORE_FILE)
    else:
        ignore = lambda _: False

    for locale in ganf_conf.locales:
        globs = glob.glob(ganf_conf.source_dir + "/**/*.*", recursive=True)
        for file_path in globs:
            dirname = os.path.dirname(file_path)
            if not (ignore(file_path) or ignore(dirname)):
                yield file_path, locale

    os.chdir(old_cwd)
