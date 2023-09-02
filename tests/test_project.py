import glob
import os
from ganf.project import Project
from ganf.config import GanfConfig
from gitignore_parser import parse_gitignore


def test_iter_project(ganf_config: GanfConfig):
    project = Project(ganf_config)

    file1 = os.path.abspath(r"sample\file.md")
    file2 = os.path.abspath(r"sample\sub_dir\file.md")
    ignore = os.path.abspath(r"sample\sub_dir\ignore.txt")
    ignore2 = os.path.abspath(r"sample\ignore\ignore.md")

    files = list(project)

    assert file1 in files
    assert file2 in files
    assert ignore not in files
    assert ignore2 not in files
