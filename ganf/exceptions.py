import textwrap


class OutOfMaxTokensError(Exception):
    def __init__(
        self, line_no: int, content: str, max_tokens: int, *args: object
    ) -> None:
        super().__init__(
            f"line:{line_no} 句子'{textwrap.shorten(content,width=20,placeholder='...')}'的token数量超过了{max_tokens}",
            *args,
        )
