import tempfile
import os
from click.testing import CliRunner
from ganf.cli import cost, init, GANF_CONFIG, GanfConfig


def test_init():
    runner = CliRunner()
    with runner.isolated_filesystem():
        os.mkdir("docs")
        result = runner.invoke(init, ["docs"], input="dist\nmd,txt\nzh,jp\n")
        assert not result.exception
        assert os.path.exists(GANF_CONFIG), "配置文件不存在"

        config = GanfConfig.load(GANF_CONFIG)

        assert config.source_dir == "docs"
        assert config.dist_dir == "dist"
        assert config.extensions == ["md", "txt"]
        assert config.locales == ["zh", "jp"]
