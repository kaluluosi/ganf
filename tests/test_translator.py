import asyncio
from ganf.segment import segments
from ganf.translator import Translator
from ganf.config import GLOBAL_OPENAI_CONF, OpenAIConfig


def test_tranlator(test_cwd):
    openai_conf = OpenAIConfig.load(GLOBAL_OPENAI_CONF)

    translator = Translator(openai_conf)

    result = asyncio.run(
        translator.translate("hello world.This is a book.", "english", "zh", prompts=[])
    )
