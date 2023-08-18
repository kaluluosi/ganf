import pytest
from ganf.translator import MessageList, Message, translate, translate_file
from ganf.config import load_openai_config, GLOBAL_OPENAI_CONFIG_FILE


def test_messagelist():
    messages = MessageList(
        [
            Message(
                role="user",
                content="Hello World!",
            )
        ]
    )

    print(messages.model_dump())


@pytest.mark.asyncio
async def test_translate_file():
    load_openai_config(GLOBAL_OPENAI_CONFIG_FILE)
    await translate_file("tests\session_events.rst")
