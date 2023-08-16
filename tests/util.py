import tempfile
import os
from contextlib import contextmanager


@contextmanager
def tmpdir():
    with tempfile.TemporaryDirectory() as tmpdirname:
        cwd = os.getcwd()
        os.chdir(tmpdirname)
        print("cwd", tmpdirname)
        yield
        os.chdir(cwd)
