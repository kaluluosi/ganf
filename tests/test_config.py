import os
import tempfile
from ganf.config import GanfConfig, GANF_CONFIG
from .util import tmpdir


def test_create_save():
    with tmpdir():
        config = GanfConfig()
        my_prompt = "this is a prompt"
        config.prompts.append(my_prompt)
        config.save(GANF_CONFIG)
        assert os.path.exists(GANF_CONFIG)

        config = GanfConfig.load(GANF_CONFIG)
        assert config.source_dir == "docs"
        assert my_prompt in config.prompts
