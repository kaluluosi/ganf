"""
文本滑动窗口工具类

由于openai接口最大单次请求只支持8000个token，因此超过8000个token的文章需要分段发送翻译。然而直接粗暴的按文本长度截断会导致破坏语义，甚至破坏单词。
因此需要按行、按句，根据累计的token数来做一个滑动窗口。

思路是用生成器的方式，产出文章片段。
"""
import nltk
from .exceptions import OutOfMaxTokensError


def segments(doc: str, language: str = "english", max_tokens: int = 8000):
    """将大文本按max_tokens大小分片

    Args:
        doc (str): 文本
        max_tokens (int, optional): 单片最大tokens数.

    Yields:
        str: 单片文本
    """

    # 先将文章按行切割（切割后换行符没了）
    lines = doc.splitlines()

    # 按行处理
    for lno, line in enumerate(lines):
        # 按句分割，一句话的token总量怎么样也不可能超过8000，除非是源码。
        sents = nltk.sent_tokenize(line, language=language)
        for sent in sents:
            tokens = nltk.word_tokenize(sent, language=language)
            if len(tokens) > max_tokens:
                raise OutOfMaxTokensError(lno, sent, max_tokens)
            yield sent
        yield "\n"  # 换行
