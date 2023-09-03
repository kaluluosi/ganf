import glob
import os
from ganf.project import iter_project
from ganf.config import GanfConfig


def test_iter_project():
    file1 = r"sample\file.md"
    file2 = r"sample\sub_dir\file.md"
    ignore1 = r"sample\ignore\ignore.md"
    ignore2 = r"sample\sub_dir\ignore.txt"

    for file_path, locale in iter_project("./tests"):
        assert file_path

    files = list(fi[0] for fi in iter_project("./tests"))

    assert file1 in files
    assert file2 in files
    assert ignore1 not in files
    assert ignore2 not in files
