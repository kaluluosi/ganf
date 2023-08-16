from ganf.translator import MessageList, Message


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
